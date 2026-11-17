"""Prepare fail-closed owner REVIEW bundles offline; never connect or execute SQL.

Default bundles prohibit every new client EXECUTE right. The optional exact
proposed allowlist remains subject to separate owner approval before execution.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.assess_v6_hosted_migrations import QUERIES
from scripts.v6_rollout_policy import (
    CORRECTIONS,
    infrastructure_guard,
    permission_guard,
    privilege_snapshot,
    reviewed_exceptions,
)
from scripts.verify_v6_hosted_auth import ROOT

EVIDENCE = ROOT / "docs/catalog/implementation/migration-readiness-20261116"
GROUP_COUNTS = (1, 11, 4)
NO_ENROLLMENT = """
do $no_enrollment$ declare enrolled boolean; begin
if exists(select 1 from pg_roles where rolname in
 ('v6_frequency_registrar','v6_frequency_test_executor')
 and (rolcanlogin or rolsuper or rolcreatedb or rolcreaterole
      or rolreplication or rolbypassrls)) then
 raise exception 'Unexpected privileged frequency role';
end if;
if exists(select 1 from pg_auth_members m join pg_roles r on r.oid=m.roleid
  where r.rolname in ('v6_frequency_registrar','v6_frequency_test_executor')) then
  raise exception 'Unexpected frequency role membership';
end if;
if to_regclass('private.frequency_reviewers') is not null then
  execute 'select exists(select 1 from private.frequency_reviewers)' into enrolled;
  if enrolled then raise exception 'Unexpected reviewer enrollment'; end if;
end if;
if to_regclass('private.frequency_decisions') is not null then
  execute 'select exists(select 1 from private.frequency_decisions)' into enrolled;
  if enrolled then raise exception 'Unexpected frequency authorization'; end if;
end if;
end; $no_enrollment$;
"""


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def baseline_guard() -> str:
    observed = json.loads((EVIDENCE / "hosted-detail-final.json").read_text())
    sql = ""
    for label in (
        "function_fingerprints",
        "effective_execution",
        "effective_table_privileges",
        "default_privileges",
    ):
        expected = json.dumps(observed["metadata"][label])
        sql += (
            "do $reviewed_baseline$ begin if (select jsonb_agg(to_jsonb(r)) from ("
            + QUERIES[label]
            + ") r) is distinct from "
            + literal(expected)
            + "::jsonb then raise exception "
            "'Reviewed permission/schema baseline changed: "
            + label
            + "';end if;end;$reviewed_baseline$;\n"
        )
    return sql


def prepare(output: Path, proposed_allowlist: Path | None = None) -> None:
    preflight = json.loads((EVIDENCE / "hosted-before.json").read_text())
    comparison = preflight["migration_comparison"]
    all_files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    files = [f for f in all_files if f.name not in CORRECTIONS]
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    missing = [f for f in files if f.name in comparison["missing"]]
    if (
        hashes != comparison["accepted_sha256"]
        or len(files) != 63
        or len(missing) != 16
        or comparison["hosted_extra_versions"]
    ):
        raise RuntimeError("Accepted chain differs from reviewed inventory")
    expected = [row["version"] for row in preflight["metadata"]["migrations"]]
    if len(expected) != 47 or files != files[:47] + missing:
        raise RuntimeError("Reviewed 47/63 boundary changed")
    corrections = {f.name: f for f in all_files if f.name in CORRECTIONS}
    if len(all_files) != 65 or set(corrections) != set(CORRECTIONS):
        raise RuntimeError("Unexpected forward correction inventory")
    candidate = json.loads(
        (
            ROOT
            / "docs/catalog/implementation/blocker-resolution-20261117"
            / "forward-migrations.json"
        ).read_text()
    )
    if {
        n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in corrections.items()
    } != candidate:
        raise RuntimeError("Reviewed forward migration bytes changed")
    exceptions = reviewed_exceptions(proposed_allowlist)
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "status": "BLOCKED REVIEW BUNDLES; NOT APPROVED FOR PRODUCTION",
        "hosted_execution": False,
        "strict_client_execute_guard": True,
        "proposed_allowlist_selected": proposed_allowlist is not None,
        "production_execution_approved": False,
        "reviewed_baseline_sha256": hashlib.sha256(
            (EVIDENCE / "hosted-detail-final.json").read_bytes()
        ).hexdigest(),
        "proposed_allowlist_sha256": (
            hashlib.sha256(proposed_allowlist.read_bytes()).hexdigest()
            if proposed_allowlist
            else None
        ),
        "groups": [],
    }
    cursor = 0
    registered: list[Path] = []
    for number, count in enumerate(GROUP_COUNTS, 1):
        before_versions = sorted(expected)
        members = missing[cursor : cursor + count]
        if number in (2, 3):
            members = members + [corrections[CORRECTIONS[number - 2]]]
        versions = "array[" + ",".join(map(literal, sorted(expected))) + "]::text[]"
        sql = """-- OWNER REVIEW ONLY. Recovery, runtime and permission gates OPEN.
-- Never use the workstation's Wombo production task to execute this bundle.
\\set ON_ERROR_STOP on
begin;
set local lock_timeout='5s';
set local statement_timeout='120s';
select pg_advisory_xact_lock(hashtextextended('start23:v6-migration-rollout',0));
do $execution_owner$ begin
 if current_user <> 'postgres' then
  raise exception 'Reviewed application migration owner required';
 end if;
end; $execution_owner$;
"""
        sql += NO_ENROLLMENT
        if number == 1:
            sql += baseline_guard()
        sql += (
            "do $boundary$ begin\n"
            "if (select array_agg(version::text order by version) from "
            "supabase_migrations.schema_migrations) is distinct from "
            + versions
            + " then raise exception 'Migration ledger boundary changed'; end if;\n"
            "end; $boundary$;\n"
        )
        for prior in registered:
            version, name = prior.stem.split("_", 1)
            body = prior.read_bytes().decode("utf-8")
            tag = "$prior_" + version + "$"
            sql += (
                "do $prior_ledger$ begin if not exists(select 1 from "
                "supabase_migrations.schema_migrations where version="
                + literal(version)
                + " and name="
                + literal(name)
                + " and statements is not distinct from array["
                + tag
                + body
                + tag
                + "]) then raise exception 'Prior group ledger bytes changed'; "
                "end if; end; $prior_ledger$;\n"
            )
        # Existing rows must still have the observed names and fingerprints.
        observed = json.dumps(preflight["metadata"]["migrations"])
        sql += (
            "do $fingerprints$ begin\nif exists(select 1 from "
            "jsonb_to_recordset(" + literal(observed) + "::jsonb) "
            "e(version text,name text,statements_md5 text) left join "
            "supabase_migrations.schema_migrations m on m.version=e.version "
            "where m.version is null or m.name is distinct from e.name or "
            "md5(array_to_string(m.statements,E'\\n')) is distinct from "
            "e.statements_md5) then raise exception 'Observed migration drift'; "
            "end if; end; $fingerprints$;\n"
        )
        sql += """create temporary table readiness_client_execute_before
on commit drop as
select replace(n.nspname||'.'||p.proname||'('||
  oidvectortypes(p.proargtypes)||')',' ','') as signature,
  role_name from pg_proc p join pg_namespace n on n.oid=p.pronamespace
cross join (values ('anon'),('authenticated')) roles(role_name)
where n.nspname in ('public','private') and p.prokind='f'
and has_function_privilege(role_name,p.oid,'EXECUTE');
"""
        sql += privilege_snapshot("before")
        for file in members:
            body = file.read_bytes().decode("utf-8")
            version, name = file.stem.split("_", 1)
            tag = "$readiness_" + version + "$"
            if tag in body:
                raise RuntimeError("SQL payload delimiter collision")
            sql += "\n-- EXACT MIGRATION " + file.name + "\n" + body + "\n"
            # Normal installation registration, atomically with new DDL.
            # No UPDATE, DELETE, repair or ON CONFLICT against existing history.
            sql += (
                "insert into supabase_migrations.schema_migrations"
                "(version,name,statements) values ("
                + literal(version)
                + ","
                + literal(name)
                + ",array["
                + tag
                + body
                + tag
                + "]);\n"
            )
            expected.append(version)
            registered.append(file)
        sql += permission_guard(exceptions, number)
        sql += infrastructure_guard()
        sql += NO_ENROLLMENT + "commit;\n"
        path = output / f"group-{number}.review.sql"
        path.write_text(sql, encoding="utf-8", newline="\n")
        manifest["groups"].append(
            {
                "group": number,
                "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "migrations": [f.name for f in members],
                "ledger_before": before_versions,
                "ledger_after": sorted(expected),
                "migration_sha256": {
                    f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in members
                },
            }
        )
        cursor += count
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Prepared blocked owner review bundles offline. No SQL was executed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--proposed-authenticated-allowlist", type=Path)
    args = parser.parse_args()
    prepare(args.output_directory, args.proposed_authenticated_allowlist)


if __name__ == "__main__":
    main()
