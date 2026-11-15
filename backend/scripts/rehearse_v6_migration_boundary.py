"""Rehearse the observed 47/63 boundary in a new loopback-only synthetic PG17 DB.

Reuses the accepted portable bootstrap and TAP parser. Never reads credentials,
production rows or .env. Does not modify any existing database or migration file.
"""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from scripts.assess_v6_hosted_migrations import QUERIES
from scripts.verify_v6_final_sql import A5, ROOT, Replay
from scripts.verify_v6_hosted_auth import QUERIES as BASE_QUERIES

GROUPS = (1, 11, 4)


def metadata(replay: Replay, database: str, stage: str) -> dict[str, Any]:
    result = {}
    for label, query in {**BASE_QUERIES, **QUERIES}.items():
        if label in {"migrations", "relation_sizes", "dynamic_prerequisites"}:
            continue
        result[label] = json.loads(
            replay.checked(
                "select coalesce(jsonb_agg(row),'[]') from (" + query + ") row",
                database,
                stage + "-" + label,
            )
        )
    replay.save(stage + "-metadata.json", result)
    return result


def snapshots(replay: Replay, database: str, stage: str) -> dict[str, Any]:
    tables = json.loads(
        replay.checked(
            "select jsonb_agg(quote_ident(n.nspname)||'.'||quote_ident(c.relname) "
            "order by n.nspname,c.relname) from pg_class c join pg_namespace n "
            "on n.oid=c.relnamespace where n.nspname in ('public','private') "
            "and c.relkind='r'",
            database,
            stage + "-tables",
        )
    )
    result = {}
    for table in tables:
        where = ""
        if table == "public.workout_templates":
            where = " where not coalesce((to_jsonb(t)->>'inactive_v6')::boolean,false)"
        sql = (
            "select jsonb_build_object('rows',count(*),'md5',"
            "md5(coalesce(string_agg((to_jsonb(t)-'inactive_v6')::text,E'\\n' "
            "order by (to_jsonb(t)-'inactive_v6')::text),''))) from "
            + table
            + " t"
            + where
        )
        result[table] = json.loads(
            replay.checked(sql, database, stage + "-hash-" + table)
        )
    replay.save(stage + "-data-hashes.json", result)
    return result


def run(args: argparse.Namespace) -> None:
    replay = Replay(args)
    server = json.loads(
        replay.checked(
            "select jsonb_build_object('data_directory',"
            "current_setting('data_directory'),"
            "'address',inet_server_addr(),'port',inet_server_port(),'version',version())",
            "postgres",
            "server",
        )
    )
    if (
        Path(server["data_directory"]).resolve() != args.cluster_directory.resolve()
        or server["address"] != "127.0.0.1"
        or server["port"] != args.port
        or not server["version"].startswith("PostgreSQL 17.")
    ):
        raise RuntimeError("Wrong disposable cluster")
    replay.save("server.json", server)
    observed = json.loads(args.hosted_preflight.read_text(encoding="utf-8"))
    expected = observed["migration_comparison"]
    files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    if hashes != expected["accepted_sha256"] or expected["hosted_extra_versions"]:
        raise RuntimeError("Accepted chain changed or hosted contains extra versions")
    missing = [f for f in files if f.name in expected["missing"]]
    present = [f for f in files if f not in missing]
    if len(present) != 47 or len(missing) != 16 or files != present + missing:
        raise RuntimeError("Observed boundary differs from reviewed contiguous chain")
    db = args.database
    replay.checked("create database " + db, "postgres", "create-database")
    replay.checked(
        (
            ROOT / "supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql"
        ).read_text(encoding="utf-8"),
        db,
        "bootstrap",
    )
    ledger = []
    for file in present:
        replay.checked(
            "begin;\n" + file.read_text(encoding="utf-8") + "\ncommit;", db, file.stem
        )
        ledger.append({"file": file.name, "sha256": hashes[file.name]})
    replay.save("boundary-replay.json", ledger)
    if args.reproduce_hosted_drift:
        details = json.loads(args.reproduce_hosted_drift.read_text(encoding="utf-8"))
        definitions = [
            row["definition"]
            for row in details["metadata"]["dynamic_prerequisites"]
            if row["signature"].startswith(("save_zone_profile(", "rls_auto_enable("))
        ]
        if len(definitions) != 2:
            raise RuntimeError("Expected exactly two observed drift definitions")
        replay.checked(
            "begin;" + ";\n".join(definitions) + ";commit;",
            db,
            "observed-hosted-drift-local-only",
        )
    metadata(replay, db, "boundary")
    # Persist ordinary synthetic onboarding and a historical confirmed rest plan.
    seed = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text()
    seed = seed.replace("a6000000-", "c7000000-").replace("b6000000-", "d7000000-")
    replay.checked(seed, db, "seed-onboarding")
    owner = "c7000000-0000-0000-0000-000000000006"
    payload = {
        "expected_base_revision": 0,
        "week_start": "2026-08-03",
        "timezone": "Europe/Amsterdam",
        "phase": "base",
        "target_basis": "injury_rest_only",
        "input_fingerprint": "a" * 32,
        "generation_fingerprint": "b" * 64,
        "total_duration_minutes": 0,
        "low_intensity_percent": 0,
        "high_intensity_percent": 0,
        "confirmed_injuries": ["run"],
        "low_only_disciplines": [],
        "goal_disciplines": ["run"],
        "availability": [],
        "available_dates": [],
        "availability_source": "checkin",
        "workouts": [],
        "warnings": [],
        "target_tss": 0,
        "planned_tss": 0,
        "ruleset_version": "phase-13-joren-ruleset-1",
        "planning_ruleset_version": "joren-planning-ruleset-2",
    }
    plan = json.loads(
        replay.checked(
            'begin; set local request.jwt.claims=\'{"role":"service_role"}\'; '
            "set local role service_role; "
            "select public.create_weekly_plan_proposal_v3('"
            + owner
            + "','"
            + json.dumps(payload)
            + "'::jsonb); commit;",
            db,
            "seed-plan",
        )
    )
    replay.checked(
        "begin; set local role authenticated; set local request.jwt.claims='"
        + json.dumps({"role": "authenticated", "sub": owner})
        + "'; select public.approve_plan_proposal('"
        + plan["proposal_id"]
        + "',0); commit;",
        db,
        "seed-approve",
    )
    replay.checked(
        "begin; set local role authenticated; set local request.jwt.claims='"
        + json.dumps({"role": "authenticated", "sub": owner})
        + "'; select public.create_activity_summary("
        "'c7000000-0000-0000-0000-000000000099',"
        "'"
        + "c" * 64
        + "','"
        + json.dumps(
            {
                "discipline": "run",
                "source": "manual",
                "started_at": "2026-08-03T08:00:00+02:00",
                "timezone": "Europe/Amsterdam",
                "duration_minutes": 30,
                "metrics": {"average_heart_rate_bpm": 140},
            }
        )
        + "'::jsonb); commit;",
        db,
        "seed-activity",
    )
    # Commit a namespaced copy of the accepted historical activity fixture only
    # in this disposable DB, retaining physical workouts and realized evidence.
    historical_seed = (
        ROOT / "supabase/tests/phase_7_activity_feedback_test.sql"
    ).read_text()
    historical_seed = re.sub(
        r"\b[89][0-9a-f]{7}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b",
        lambda match: str(uuid5(NAMESPACE_URL, "migration-readiness:" + match[0])),
        historical_seed,
    )
    if historical_seed.count("rollback;") != 1:
        raise RuntimeError("Historical seed transaction changed")
    historical_seed = historical_seed.replace("rollback;", "commit;")
    seed_result = replay.checked(historical_seed, db, "seed-historical-evidence")
    if "not ok " in seed_result:
        raise RuntimeError("Historical evidence seed assertions failed")
    replay.save(
        "historical-seed.json",
        {
            "executed_sha256": hashlib.sha256(historical_seed.encode()).hexdigest(),
            "description": "Namespaced phase-7 seed with committed synthetic evidence",
        },
    )
    before = snapshots(replay, db, "before")
    # Run all historical suites available at the observed boundary.
    final_only = {A5, "joren_realized_v2_test.sql"}
    historical_tests = [
        f
        for f in sorted((ROOT / "supabase/tests").glob("*.sql"))
        if not f.name.startswith("v6_") and f.name not in final_only
    ]
    root_output = replay.out
    replay.out = root_output / "boundary-tap"
    replay.out.mkdir()
    pre_results = [replay.tap(f, db) for f in historical_tests]
    replay.out = root_output
    replay.save("boundary-tap.json", pre_results)
    cursor = 0
    timings = []
    for group, count in enumerate(GROUPS, 1):
        members = missing[cursor : cursor + count]
        sql = (
            "begin; set local lock_timeout='5s'; set local statement_timeout='120s';\n"
        )
        sql += "\n".join(f.read_text(encoding="utf-8") for f in members) + "\ncommit;"
        started = time.monotonic()
        replay.checked(sql, db, "group-" + str(group))
        timings.append(
            {
                "group": group,
                "files": [f.name for f in members],
                "seconds": round(time.monotonic() - started, 3),
            }
        )
        cursor += count
        metadata(replay, db, "group-" + str(group))
        current = snapshots(replay, db, "group-" + str(group))
        if any(current.get(table) != value for table, value in before.items()):
            raise RuntimeError("Preexisting synthetic/historical rows changed")
        replay.save("migration-groups.json", timings)
        replay.out = root_output / ("group-" + str(group) + "-smokes")
        replay.out.mkdir()
        smoke_names = [
            "phase_6_weekly_planning_test.sql",
            "phase_7_activity_feedback_test.sql",
            "phase_8_structured_weekly_checkin_test.sql",
            "phase_r2_r3_identity_onboarding_calibration_test.sql",
            "phase_r4_r5_onboarding_race_activity_test.sql",
            A5,
        ]
        smokes = [
            replay.tap(ROOT / "supabase/tests" / name, db, overlay=name == A5)
            for name in smoke_names
        ]
        replay.out = root_output
        replay.save("group-" + str(group) + "-smokes.json", smokes)
        if any(result["status"] != "EXECUTED / PASS" for result in smokes):
            raise RuntimeError("Historical group smoke failed")
    replay.save("a5-final-original.json", replay.tap(ROOT / "supabase/tests" / A5, db))
    results = []
    for file in sorted((ROOT / "supabase/tests").glob("*.sql")):
        results.append(replay.tap(file, db, overlay=file.name == A5))
        replay.save("pgtap-results.json", results)
        print(file.name, results[-1]["status"], flush=True)
    replay.save(
        "data-preservation.json",
        {
            "all_boundary_tables_equal": True,
            "tables": len(before),
            "hosted_data_used": False,
        },
    )
    if not all(r["status"] == "EXECUTED / PASS" for r in results):
        raise RuntimeError("Final TAP failed; inspect evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--cluster-directory", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--hosted-preflight", type=Path, required=True)
    parser.add_argument("--reproduce-hosted-drift", type=Path)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute_disposable_local_only or not re.fullmatch(
        r"wombo_v6_boundary_[a-z0-9_]+", args.database
    ):
        parser.error("Explicit new disposable database required")
    run(args)


if __name__ == "__main__":
    main()
