"""Real-PG execution of offline bundles in a NEW disposable local database only."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from scripts.assess_v6_hosted_migrations import QUERIES
from scripts.prepare_v6_rollout_bundles import EVIDENCE, literal, prepare
from scripts.verify_v6_blocker_sql import reproduce_hosted_acls
from scripts.verify_v6_final_sql import ROOT, Replay


def run(args: argparse.Namespace) -> None:
    replay = Replay(args)
    server = json.loads(
        replay.checked(
            "select jsonb_build_object('directory',current_setting('data_directory'),"
            "'address',inet_server_addr(),'port',inet_server_port())",
            "postgres",
            "identity",
        )
    )
    if (
        Path(server["directory"]).resolve() != args.cluster_directory.resolve()
        or server["address"] != "127.0.0.1"
        or server["port"] != args.port
    ):
        raise RuntimeError("Wrong disposable cluster")
    observed = json.loads((EVIDENCE / "hosted-before.json").read_text(encoding="utf-8"))
    files = sorted((ROOT / "supabase/migrations").glob("*.sql"))[:47]
    replay.checked("create database " + args.database, "postgres", "create")
    db = args.database
    replay.checked(
        (
            ROOT / "supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql"
        ).read_text(encoding="utf-8"),
        db,
        "bootstrap",
    )
    for file in files:
        replay.checked(
            "begin;" + file.read_text(encoding="utf-8") + "commit;", db, file.stem
        )
    if args.reproduce_hosted_drift:
        details = json.loads(args.reproduce_hosted_drift.read_text(encoding="utf-8"))
        definitions = [
            r["definition"]
            for r in details["metadata"]["dynamic_prerequisites"]
            if r["signature"].startswith(("save_zone_profile(", "rls_auto_enable("))
        ]
        replay.checked(
            ";\n".join(definitions) + ";", db, "observed-hosted-function-bodies"
        )
        reproduce_hosted_acls(replay, db, details)
    # Bind the locally reproduced fixture baseline, not a claim that portable PG
    # has the managed project's exact catalog/pg_get_functiondef representation.
    baseline = json.loads((EVIDENCE / "hosted-detail-final.json").read_text())
    baseline_substitutions = []
    for label in (
        "function_fingerprints",
        "effective_execution",
        "effective_table_privileges",
        "default_privileges",
    ):
        actual = json.loads(
            replay.checked(
                "select jsonb_agg(to_jsonb(r)) from (" + QUERIES[label] + ") r",
                db,
                "fixture-" + label,
            )
        )
        baseline_substitutions.append(
            (
                literal(json.dumps(baseline["metadata"][label])),
                literal(json.dumps(actual)),
            )
        )
    ledger = (
        "create schema supabase_migrations;create table supabase_migr"
        "ations.schema_migrations(version text primary key,name text,"
        "statements text[]);"
    )
    substitutions = []
    for file, row in zip(files, observed["metadata"]["migrations"], strict=True):
        body = file.read_text(encoding="utf-8")
        digest = hashlib.md5(body.encode()).hexdigest()
        substitutions.append((row["statements_md5"], digest))
        ledger += (
            "insert into supabase_migrations.schema_migrations values ('"
            + row["version"]
            + "','"
            + row["name"]
            + "',array[$fixture$"
            + body
            + "$fixture$]);"
        )
    replay.checked(ledger, db, "local-fixture-ledger")
    # Only local fixture fingerprints are substituted, explicitly recorded.
    # Exact migration body bytes and original hosted preflight remain unchanged.
    for name, allowlist in (
        ("strict", None),
        (
            "proposed",
            ROOT
            / (
                "docs/catalog/implementation/blocker-resolution-20261117/auth"
                "enticated-execute-allowlist.json"
            ),
        ),
    ):
        prepare(replay.out / name, allowlist)

    def bundle(name: str, group: int) -> str:
        source = (replay.out / name / f"group-{group}.review.sql").read_text(
            encoding="utf-8"
        )
        for old, new in substitutions:
            source = source.replace(old, new)
        for old, new in baseline_substitutions:
            source = source.replace(old, new)
        return source.replace("\\set ON_ERROR_STOP on", "")

    outcomes: list[dict[str, Any]] = []

    def refused(label: str, sql: str, count: int) -> None:
        result = replay.sql(sql, db)
        if result.returncode == 0:
            raise RuntimeError("Guard failed to refuse " + label)
        expected_error = {
            "unexpected-private-table": "Unexpected table privilege delta",
            "unexpected-server-function": "Unexpected server EXECUTE delta",
            "unexpected-default-acl": "Unexpected default ACL delta",
            "unexpected-grant-option": "Unreviewed privilege grant options",
            "unexpected-rls-bypass": "Unexpected role powers or membership",
            "unexpected-role-membership": "Unexpected role powers or membership",
            "unexpected-schema-authority": "Unexpected application schema authority",
            "atomic-g2-injected-failure": "injected",
            "unknown-commit-repeat-stops": "Migration ledger boundary changed",
        }.get(label, "Unexpected client EXECUTE delta")
        if expected_error not in result.stderr:
            raise RuntimeError("Wrong refusal reason for " + label)
        after = replay.checked(
            "select count(*) from supabase_migrations.schema_migrations",
            db,
            label + "-ledger",
        )
        if int(after.strip()) != count:
            raise RuntimeError("Refused bundle changed ledger")
        outcomes.append(
            {
                "case": label,
                "status": "PASS",
                "ledger_unchanged": True,
                "error_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            }
        )

    refused("default-no-exceptions", bundle("strict", 1), 47)
    attacks = {
        "unexpected-grant-option": (
            "grant execute on function public.get_checkin_plan_proposal(uuid) "
            "to authenticated with grant option;"
        ),
        "unexpected-rls-bypass": "alter role authenticated bypassrls;",
        "unexpected-role-membership": "grant service_role to authenticated;",
        "unexpected-schema-authority": (
            "grant create on schema public to authenticated;"
        ),
        ("unexpected-anonymous-execute"): (
            "grant execute on function public.create_weekly_plan_proposal"
            "_v3(uuid,jsonb) to anon;"
        ),
        ("unexpected-authenticated-writer"): (
            "grant execute on function public.create_weekly_plan_proposal"
            "_v3(uuid,jsonb) to authenticated;"
        ),
        ("unexpected-overload"): (
            "create function public.get_checkin_plan_proposal(text) retur"
            "ns jsonb language sql as $$select '{}'::jsonb$$;grant execut"
            "e on function public.get_checkin_plan_proposal(text) to auth"
            "enticated;"
        ),
        ("unexpected-private-table"): (
            "grant select on private.activity_loads to authenticated;"
        ),
        ("unexpected-server-function"): (
            "create function public.blocker_unreviewed() returns int lang"
            "uage sql as $$select 1$$;revoke all on function public.block"
            "er_unreviewed() from public;grant execute on function public"
            ".blocker_unreviewed() to service_role;"
        ),
        ("unexpected-default-acl"): (
            "alter default privileges for role postgres in schema public "
            "grant select on tables to authenticated;"
        ),
    }
    marker = "-- Exact delta only:"
    for label, attack in attacks.items():
        sql = bundle("proposed", 1).replace(marker, attack + "\n" + marker)
        refused(label, sql, 47)
    replay.checked(bundle("proposed", 1), db, "accepted-g1")
    refused(
        "atomic-g2-injected-failure",
        bundle("proposed", 2).replace(
            marker, "do $$begin raise exception 'injected';end;$$;\n" + marker
        ),
        48,
    )
    replay.checked(bundle("proposed", 2), db, "accepted-g2")
    # G3 must retain the new private dependency; do not silently remove it.
    refused(
        "missing-private-invoker-dependency",
        bundle("proposed", 3).replace(
            marker,
            (
                "revoke execute on function private.v6_revision_workouts(uuid"
                ") from authenticated;\n"
            )
            + marker,
        ),
        60,
    )
    replay.checked(bundle("proposed", 3), db, "accepted-g3")
    final = json.loads(
        replay.checked(
            (
                "select jsonb_agg(jsonb_build_object('version',version,'name'"
                ",name,'md5',md5(array_to_string(statements,E'\\n'))) order by"
                " version) from supabase_migrations.schema_migrations"
            ),
            db,
            "final-ledger",
        )
    )
    if len(final) != 65:
        raise RuntimeError("Wrong final ledger count")
    actual = {r["version"]: r["md5"] for r in final}
    for file in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if (
            actual[file.stem.split("_", 1)[0]]
            != hashlib.md5(file.read_text(encoding="utf-8").encode()).hexdigest()
        ):
            raise RuntimeError("Ledger does not match executed file")
    refused("unknown-commit-repeat-stops", bundle("proposed", 3), 65)
    replay.save(
        "guard-results.json",
        {
            "hosted_execution": False,
            "fixture_fingerprint_substitution": True,
            "exact_bodies": True,
            "final_ledger_count": 65,
            "cases": outcomes,
            "all_three_groups_committed": True,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--cluster-directory", type=Path, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--reproduce-hosted-drift", type=Path)
    args = parser.parse_args()
    if not args.execute_disposable_local_only or not re.fullmatch(
        r"wombo_v6_boundary_[a-z0-9_]+", args.database
    ):
        parser.error("New disposable local database required")
    run(args)


if __name__ == "__main__":
    main()
