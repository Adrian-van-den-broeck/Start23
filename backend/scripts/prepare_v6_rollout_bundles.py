"""Prepare fail-closed owner REVIEW bundles offline; never connect or execute SQL.

The accepted chain adds authenticated EXECUTE rights. Under the owner's current
strict no-new-client-EXECUTE requirement these bundles MUST roll back. A separate
reviewed permission decision and recovery/runtime gates precede any live rollout.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.verify_v6_hosted_auth import ROOT

EVIDENCE = ROOT / "docs/catalog/implementation/migration-readiness-20261116"
GROUP_COUNTS = (1, 11, 4)
NO_ENROLLMENT = """
do $no_enrollment$ declare enrolled boolean; begin
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


def prepare(output: Path) -> None:
    preflight = json.loads((EVIDENCE / "hosted-before.json").read_text())
    comparison = preflight["migration_comparison"]
    files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
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
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "status": "BLOCKED REVIEW BUNDLES; NOT APPROVED FOR PRODUCTION",
        "hosted_execution": False,
        "strict_client_execute_guard": True,
        "groups": [],
    }
    cursor = 0
    for number, count in enumerate(GROUP_COUNTS, 1):
        members = missing[cursor : cursor + count]
        versions = "array[" + ",".join(map(literal, sorted(expected))) + "]::text[]"
        sql = """-- OWNER REVIEW ONLY. Recovery, runtime and permission gates OPEN.
-- Never use the workstation's Wombo production task to execute this bundle.
\\set ON_ERROR_STOP on
begin;
set local lock_timeout='5s';
set local statement_timeout='120s';
select pg_advisory_xact_lock(hashtextextended('start23:v6-migration-rollout',0));
"""
        sql += NO_ENROLLMENT
        sql += (
            "do $boundary$ begin\n"
            "if (select array_agg(version::text order by version) from "
            "supabase_migrations.schema_migrations) is distinct from "
            + versions
            + " then raise exception 'Migration ledger boundary changed'; end if;\n"
            "end; $boundary$;\n"
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
select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid) as args,
  role_name from pg_proc p join pg_namespace n on n.oid=p.pronamespace
cross join (values ('anon'),('authenticated')) roles(role_name)
where n.nspname in ('public','private') and p.prokind='f'
and has_function_privilege(role_name,p.oid,'EXECUTE');
"""
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
        sql += """
-- This currently FAILS: the chain grants new owner-scoped client RPCs.
-- Do not remove or bypass this guard without a separate approved ACL design.
do $no_new_execute$ begin
if exists (
 select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 cross join (values ('anon'),('authenticated')) roles(role_name)
 where n.nspname in ('public','private') and p.prokind='f'
 and has_function_privilege(role_name,p.oid,'EXECUTE')
 and not exists (select 1 from readiness_client_execute_before b
   where b.nspname=n.nspname and b.proname=p.proname
   and b.args=pg_get_function_identity_arguments(p.oid)
   and b.role_name=roles.role_name)
) then raise exception 'New client EXECUTE conflicts with inactive-rollout requirement';
end if;
end; $no_new_execute$;
"""
        sql += NO_ENROLLMENT + "commit;\n"
        path = output / f"group-{number}.review.sql"
        path.write_text(sql, encoding="utf-8", newline="\n")
        manifest["groups"].append(
            {
                "group": number,
                "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "migrations": [f.name for f in members],
            }
        )
        cursor += count
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Prepared blocked owner review bundles offline. No SQL was executed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    prepare(parser.parse_args().output_directory)


if __name__ == "__main__":
    main()
