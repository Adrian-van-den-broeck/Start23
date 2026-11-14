"""Narrow hosted verification preflight; never a disposable database runner.

Only fixed metadata SELECTs and allowlisted Management API GETs are permitted.
This script has no migration, role-change, project-resume or arbitrary-SQL mode.
Credentials stay in memory. Outputs contain allowlisted metadata only.
"""

import argparse
import ctypes
import hashlib
import json
import logging
import os
import re
from ctypes import wintypes
from pathlib import Path
from typing import Any

import httpx

PROJECT_REF = "isfumhgqphieoayqahjv"
PROJECT_URL = f"https://{PROJECT_REF}.supabase.co"
ROOT = Path(__file__).resolve().parents[2]

QUERIES = {
    "server": "select version() as version, current_database() as database",
    "migrations": (
        "select version,name,md5(array_to_string(statements,E'\\n')) as statements_md5 "
        "from supabase_migrations.schema_migrations order by version"
    ),
    "extensions": (
        "select extname,extversion from pg_catalog.pg_extension order by extname"
    ),
    "relations": (
        "select n.nspname as schema,c.relname as name,c.relkind as kind,"
        "c.relrowsecurity as rls,c.relforcerowsecurity as force_rls "
        "from pg_catalog.pg_class c join pg_catalog.pg_namespace n "
        "on n.oid=c.relnamespace where n.nspname in ('auth','public','private') "
        "and c.relkind in ('r','p','v','m') order by n.nspname,c.relname"
    ),
    "triggers": (
        "select n.nspname as schema,c.relname as table,t.tgname as name,"
        "t.tgenabled as enabled,pn.nspname as function_schema,p.proname as function "
        "from pg_catalog.pg_trigger t join pg_catalog.pg_class c on c.oid=t.tgrelid "
        "join pg_catalog.pg_namespace n on n.oid=c.relnamespace "
        "join pg_catalog.pg_proc p on p.oid=t.tgfoid "
        "join pg_catalog.pg_namespace pn on pn.oid=p.pronamespace "
        "where not t.tgisinternal and n.nspname in ('auth','public','private') "
        "order by n.nspname,c.relname,t.tgname"
    ),
    "policies": (
        "select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check "
        "from pg_catalog.pg_policies where schemaname in ('public','private') "
        "order by schemaname,tablename,policyname"
    ),
    "grants": (
        "select grantee,table_schema,table_name,privilege_type "
        "from information_schema.role_table_grants "
        "where table_schema in ('public','private') "
        "and grantee in ('anon','authenticated','service_role') "
        "order by table_schema,table_name,grantee,privilege_type"
    ),
    "rpcs": (
        "select n.nspname as schema,p.proname as name,"
        "pg_catalog.pg_get_function_identity_arguments(p.oid) as arguments,"
        "p.prosecdef as security_definer,p.proacl::text as acl "
        "from pg_catalog.pg_proc p join pg_catalog.pg_namespace n "
        "on n.oid=p.pronamespace where n.nspname in ('public','private') "
        "order by n.nspname,p.proname,p.oid"
    ),
    "side_effect_relations": (
        "select n.nspname as schema,c.relname as name from pg_catalog.pg_class c "
        "join pg_catalog.pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname in ('cron','supabase_functions','pgmq','net') "
        "and c.relkind in ('r','p') order by n.nspname,c.relname"
    ),
    "signup_function": (
        "select pg_catalog.pg_get_functiondef("
        "'private.ensure_athlete_identity_map()'::regprocedure) as definition"
    ),
    "foreign_keys": (
        "select n.nspname as schema,c.relname as table,con.conname as name,"
        "pg_catalog.pg_get_constraintdef(con.oid) as definition "
        "from pg_catalog.pg_constraint con join pg_catalog.pg_class c "
        "on c.oid=con.conrelid join pg_catalog.pg_namespace n on n.oid=c.relnamespace "
        "where con.contype='f' and n.nspname in ('public','private','storage','auth') "
        "order by n.nspname,c.relname,con.conname"
    ),
    "network_functions": (
        "select n.nspname as schema,p.proname as name from pg_catalog.pg_proc p "
        "join pg_catalog.pg_namespace n on n.oid=p.pronamespace "
        "where n.nspname in ('public','private') and p.prosrc ~* "
        "'(http_post|http_get|http_request|net\\.|dblink|plpython|"
        "pg_notify|cron\\.|pgmq\\.)' "
        "order by n.nspname,p.proname"
    ),
}


def cli_management_token() -> str:
    """Read only the CLI's two documented credential targets; never enumerate."""
    if value := os.environ.get("SUPABASE_ACCESS_TOKEN"):
        return value
    if os.name != "nt":
        raise RuntimeError("Supply the existing Management API credential securely.")

    class Credential(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    api = ctypes.WinDLL("advapi32", use_last_error=True)
    api.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(Credential)),
    ]
    api.CredReadW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    for target in ("Supabase CLI:supabase", "Supabase CLI:access-token"):
        pointer = ctypes.POINTER(Credential)()
        if api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
            try:
                value = ctypes.string_at(
                    pointer.contents.CredentialBlob,
                    pointer.contents.CredentialBlobSize,
                ).decode("utf-8")
                if re.fullmatch(r"sbp_(?:oauth_)?[a-f0-9]{40}", value):
                    return value
            finally:
                api.CredFree(pointer)
    raise RuntimeError("Existing Supabase CLI credential unavailable.")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode())


def management_request(
    client: httpx.Client, label: str, query: str | None = None
) -> tuple[int, Any]:
    paths = {
        "project": "",
        "auth": "/config/auth",
        "branches": "/branches",
        "security_advisors": "/advisors/security",
    }
    if query is not None:
        if label not in QUERIES or query != QUERIES[label]:
            raise ValueError("Only fixed metadata queries are allowed.")
        response = client.post(
            f"/v1/projects/{PROJECT_REF}/database/query/read-only",
            json={"query": query},
        )
    else:
        response = client.get(f"/v1/projects/{PROJECT_REF}{paths[label]}")
    return response.status_code, response.json()


def preflight(output: Path) -> None:
    """No user rows, signup, login, project changes or data mutations."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    result: dict[str, Any] = {
        "project_ref": PROJECT_REF,
        "endpoint": PROJECT_URL,
        "hosted_data_writes": 0,
        "synthetic_accounts_created": 0,
        "metadata": {},
        "checks": [],
    }
    with httpx.Client(
        base_url="https://api.supabase.com",
        timeout=20,
        follow_redirects=False,
        headers={"Authorization": "Bearer " + cli_management_token()},
    ) as client:
        status, project = management_request(client, "project")
        result["checks"].append({"case": "project_identity", "http_status": status})
        if status != 200 or project.get("id") != PROJECT_REF:
            raise RuntimeError("The authorized project identity was not verified.")
        result["project"] = {
            key: project.get(key) for key in ("id", "name", "region", "status")
        }
        status, auth = management_request(client, "auth")
        result["checks"].append({"case": "auth_config", "http_status": status})
        if status == 200:
            safe_auth = {
                "disable_signup",
                "external_email_enabled",
                "mailer_autoconfirm",
                "jwt_exp",
                "refresh_token_rotation_enabled",
                "security_refresh_token_reuse_interval",
                "password_min_length",
                "sessions_timebox",
                "sessions_inactivity_timeout",
            }
            result["auth"] = {
                key: value
                for key, value in auth.items()
                if key in safe_auth
                or (key.startswith("hook_") and key.endswith("_enabled"))
            }
            result["auth"].update(
                {
                    key: value
                    for key, value in auth.items()
                    if key.startswith("mailer_notifications_")
                    and key.endswith("_enabled")
                }
            )
        status, branches = management_request(client, "branches")
        result["checks"].append({"case": "branch_list", "http_status": status})
        result["branch_count"] = len(branches or []) if status == 200 else None
        for label, path in {
            "log_drains": f"/v2/projects/{PROJECT_REF}/analytics/log-drains",
            "project_webhooks": f"/v2/projects/{PROJECT_REF}/webhooks/endpoints",
            "security_advisors": f"/v1/projects/{PROJECT_REF}/advisors/security",
        }.items():
            response = client.get(path)
            body = response.json()
            rows = body.get("data", []) if isinstance(body, dict) else body or []
            result["checks"].append(
                {"case": label, "http_status": response.status_code}
            )
            result[label] = {
                "http_status": response.status_code,
                "entry_count": len(rows)
                if response.is_success and isinstance(rows, list)
                else None,
            }
            if label == "security_advisors" and response.is_success:
                result[label]["entry_count"] = len(body.get("lints", []))
                result[label]["findings"] = [
                    {key: row.get(key) for key in ("name", "level", "categories")}
                    for row in body.get("lints", [])
                ]
        for label, query in QUERIES.items():
            status, data = management_request(client, label, query)
            result["checks"].append({"case": label, "http_status": status})
            if status in (200, 201):
                result["metadata"][label] = data
            else:
                result["metadata"][label] = {"status": "BLOCKED", "http_status": status}
        if isinstance(hosted := result["metadata"].get("migrations"), list):
            local = {
                p.name.split("_", 1)[0]: p
                for p in (ROOT / "supabase/migrations").glob("*.sql")
            }
            versions = {row["version"] for row in hosted}
            result["migration_comparison"] = {
                "accepted_count": len(local),
                "hosted_count": len(versions),
                "missing": [local[v].name for v in sorted(local.keys() - versions)],
                "hosted_extra_versions": sorted(versions - local.keys()),
                "accepted_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(local.values())
                },
            }
    write_json(output, result)
    print("Read-only hosted preflight recorded; no hosted data/account writes.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-output", type=Path, required=True)
    args = parser.parse_args()
    preflight(args.preflight_output)


if __name__ == "__main__":
    main()
