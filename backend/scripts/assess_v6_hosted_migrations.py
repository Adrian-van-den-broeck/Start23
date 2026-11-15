"""Fixed read-only hosted migration/recovery metadata assessment. No athlete rows.

Uses the existing authorized CLI credential in memory. No arbitrary SQL, restore,
DDL, provisioning, migration repair, account, or configuration mutation mode.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from scripts.verify_v6_hosted_auth import PROJECT_REF, ROOT, cli_management_token

QUERIES = {
    "function_fingerprints": """
      select n.nspname as schema, p.proname as name,
        pg_get_function_identity_arguments(p.oid) as arguments,
        pg_get_function_result(p.oid) as result,
        md5(regexp_replace(p.prosrc, '[[:space:]]', '', 'g')) as source_normalized_md5,
        md5(pg_get_functiondef(p.oid)) as definition_md5,
        p.prosecdef as security_definer, p.proconfig, p.proacl::text as acl
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname in ('public','private') and p.prokind='f'
      order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)
    """,
    "effective_execution": """
      select n.nspname as schema,p.proname as name,
        pg_get_function_identity_arguments(p.oid) as arguments,
        has_function_privilege('anon',p.oid,'EXECUTE') as anon,
        has_function_privilege('authenticated',p.oid,'EXECUTE') as authenticated,
        has_function_privilege('service_role',p.oid,'EXECUTE') as service_role
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname in ('public','private') and p.prokind='f'
      order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)
    """,
    "effective_table_privileges": """
      select n.nspname as schema,c.relname as name,c.relacl::text as acl,
        c.relrowsecurity as rls,c.relforcerowsecurity as force_rls,
        role_name,has_schema_privilege(role_name,n.oid,'USAGE') as schema_usage,
        has_table_privilege(role_name,c.oid,'SELECT') as can_select,
        has_table_privilege(role_name,c.oid,'INSERT') as can_insert,
        has_table_privilege(role_name,c.oid,'UPDATE') as can_update,
        has_table_privilege(role_name,c.oid,'DELETE') as can_delete
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
      cross join (values ('anon'),('authenticated'),('service_role')) roles(role_name)
      where n.nspname in ('public','private') and c.relkind in ('r','v')
      order by n.nspname,c.relname,role_name
    """,
    "default_privileges": """
      select r.rolname,n.nspname,d.defaclobjtype,d.defaclacl::text as acl
      from pg_default_acl d join pg_roles r on r.oid=d.defaclrole
      left join pg_namespace n on n.oid=d.defaclnamespace
      order by r.rolname,n.nspname,d.defaclobjtype
    """,
    "ddl": """
      select 'constraint' as kind,n.nspname as schema,c.relname as relation,
        x.conname as name,pg_get_constraintdef(x.oid) as definition
      from pg_constraint x join pg_class c on c.oid=x.conrelid
      join pg_namespace n on n.oid=c.relnamespace
      where n.nspname in ('public','private')
      union all
      select 'trigger',n.nspname,c.relname,t.tgname,pg_get_triggerdef(t.oid)
      from pg_trigger t join pg_class c on c.oid=t.tgrelid
      join pg_namespace n on n.oid=c.relnamespace
      where n.nspname in ('public','private','auth') and not t.tgisinternal
      union all
      select 'index',schemaname,tablename,indexname,indexdef
      from pg_indexes where schemaname in ('public','private')
      order by kind,schema,relation,name
    """,
    "roles": """
      select r.rolname,r.rolcanlogin,r.rolsuper,r.rolbypassrls,
        coalesce((select jsonb_agg(m.rolname order by m.rolname)
          from pg_auth_members a join pg_roles m on m.oid=a.member
          where a.roleid=r.oid),'[]'::jsonb) as members
      from pg_roles r where r.rolname in
        ('anon','authenticated','service_role','v6_frequency_registrar',
         'v6_frequency_test_executor') order by r.rolname
    """,
    "relation_sizes": """
      select n.nspname as schema,c.relname as name,
        pg_total_relation_size(c.oid) as total_bytes,
        c.reltuples::bigint as estimated_rows
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where n.nspname in ('public','private') and c.relkind='r'
      order by n.nspname,c.relname
    """,
    "dynamic_prerequisites": """
      select p.oid::regprocedure::text as signature,
        md5(pg_get_functiondef(p.oid)) as definition_md5,
        pg_get_functiondef(p.oid) as definition
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where (n.nspname,p.proname) in
        (('public','get_plan_load_history_for_planning_v13'),
         ('public','get_plan_load_history_for_planning_v14'),
         ('public','get_plan_load_history_for_planning_v15'),
         ('public','confirm_weekly_checkin_context'),
         ('public','save_zone_profile'),('public','rls_auto_enable'),
         ('public','create_swipe_week_draft'),('public','update_swipe_week_draft'),
         ('public','move_planned_workout_date')) order by signature
    """,
}


def assess(output: Path) -> None:
    result: dict[str, Any] = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_ref": PROJECT_REF,
        "hosted_mutations": 0,
        "athlete_rows_downloaded": 0,
        "metadata": {},
        "http_status": {},
    }
    with httpx.Client(
        base_url="https://api.supabase.com",
        headers={"Authorization": "Bearer " + cli_management_token()},
        timeout=30,
        follow_redirects=False,
    ) as client:
        project = client.get(f"/v1/projects/{PROJECT_REF}")
        project.raise_for_status()
        if project.json().get("id") != PROJECT_REF:
            raise RuntimeError("Authorized project identity mismatch")
        for label, query in QUERIES.items():
            response = client.post(
                f"/v1/projects/{PROJECT_REF}/database/query/read-only",
                json={"query": query},
            )
            result["http_status"][label] = response.status_code
            if response.is_success:
                result["metadata"][label] = response.json()
        response = client.get(f"/v1/projects/{PROJECT_REF}/database/backups")
        result["http_status"]["backups"] = response.status_code
        if response.is_success:
            # Backup metadata only; never download a backup or a signed object URL.
            body = response.json()
            result["backups_response_keys"] = sorted(body)
            result["backups"] = {
                key: body[key]
                for key in (
                    "region",
                    "pitr_enabled",
                    "walg_enabled",
                    "physical_backup_data",
                )
                if key in body
            }
            result["backups"]["backups"] = [
                {
                    key: row[key]
                    for key in (
                        "status",
                        "inserted_at",
                        "updated_at",
                        "is_physical_backup",
                    )
                    if key in row
                }
                for row in body.get("backups", [])
            ]
    result["accepted_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "supabase/migrations").glob("*.sql"))
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Recorded fixed read-only migration/backup metadata; zero hosted writes.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    assess(parser.parse_args().output)


if __name__ == "__main__":
    main()
