"""Read-only exact synthetic record inventory; never generates DELETE SQL.

Only primary keys are returned. Every row predicate binds the two manifested
Auth/opaque identities, and generated identifiers come from inspected catalogs.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

from scripts.verify_v6_hosted_auth import PROJECT_REF, cli_management_token, write_json

OWNER_COLUMNS = (
    "athlete_id",
    "internal_athlete_id",
    "auth_user_id",
    "user_id",
    "owner_id",
    "owner",
)


def identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", value):
        raise ValueError("Unexpected catalog identifier; stop.")
    return '"' + value + '"'


def query(client: httpx.Client, sql: str) -> list[dict[str, Any]]:
    if not sql.lower().startswith("select "):
        raise ValueError("The inventory permits SELECT only.")
    response = client.post(
        f"/v1/projects/{PROJECT_REF}/database/query/read-only", json={"query": sql}
    )
    if response.status_code not in (200, 201):
        raise RuntimeError("Read-only inventory query failed; no write fallback.")
    data: Any = response.json()
    if not isinstance(data, list):
        raise RuntimeError("Unexpected inventory response.")
    return data


def inventory(directory: Path, stage: str) -> None:
    manifest_path = directory / "manifest.private.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("project_ref") != PROJECT_REF or set(manifest["accounts"]) != {
        "A",
        "B",
    }:
        raise ValueError("Only the exact two-account manifest is accepted.")
    ids = {
        str(UUID(account[field]))
        for account in manifest["accounts"].values()
        for field in ("auth_user_id", "athlete_id")
    }
    if len(ids) != 4:
        raise ValueError("Two distinct Auth and opaque identities are required.")
    values = ",".join("'" + value + "'" for value in sorted(ids))
    with httpx.Client(
        base_url="https://api.supabase.com",
        timeout=20,
        headers={"Authorization": "Bearer " + cli_management_token()},
    ) as client:
        columns = query(
            client,
            "select n.nspname as schema,c.relname as table,a.attname as column,"
            "pg_catalog.format_type(a.atttypid,a.atttypmod) as type "
            "from pg_catalog.pg_attribute a join pg_catalog.pg_class c "
            "on c.oid=a.attrelid "
            "join pg_catalog.pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname in ('public','private','auth','storage') "
            "and c.relkind in ('r','p') and a.attnum>0 and not a.attisdropped "
            "order by n.nspname,c.relname,a.attnum",
        )
        keys = query(
            client,
            "select n.nspname as schema,c.relname as table,a.attname as column "
            "from pg_catalog.pg_index i join pg_catalog.pg_class c on c.oid=i.indrelid "
            "join pg_catalog.pg_namespace n on n.oid=c.relnamespace "
            "join pg_catalog.pg_attribute a on a.attrelid=c.oid "
            "and a.attnum=any(i.indkey) "
            "where i.indisprimary "
            "and n.nspname in ('public','private','auth','storage')",
        )
        tables: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for row in columns:
            tables.setdefault((row["schema"], row["table"]), []).append(row)
        output = {}
        for (schema, table), cols in tables.items():
            owners = [
                row
                for row in cols
                if row["column"] in OWNER_COLUMNS
                and row["type"]
                in ("uuid", "text", "character varying(255)", "character varying")
            ]
            if (schema, table) == ("auth", "users"):
                owners = [{"column": "id", "type": "uuid"}]
            if not owners:
                continue
            primary = [
                row["column"]
                for row in keys
                if row["schema"] == schema and row["table"] == table
            ]
            if not primary:
                raise RuntimeError("An owned table has no inspectable primary key.")
            predicate = " or ".join(
                identifier(row["column"]) + " in (" + values + ")" for row in owners
            )
            rows = query(
                client,
                "select "
                + ",".join(identifier(key) for key in primary)
                + " from "
                + identifier(schema)
                + "."
                + identifier(table)
                + " where "
                + predicate,
            )
            output[schema + "." + table] = rows
        # Security audit entries may intentionally outlive account deletion.
        auth_ids = ",".join(
            "'" + str(UUID(a["auth_user_id"])) + "'"
            for a in manifest["accounts"].values()
        )
        audit = query(
            client,
            "select id from auth.audit_log_entries where payload->>'actor_id' in ("
            + auth_ids
            + ")",
        )
    write_json(directory / ("inventory-" + stage + ".private.json"), output)
    write_json(
        directory / ("inventory-" + stage + "-summary.json"),
        {
            "stage": stage,
            "table_counts": {name: len(rows) for name, rows in output.items()},
            "security_audit_entries_retained": len(audit),
            "unrelated_rows_read": 0,
        },
    )
    manifest.setdefault("record_inventory", {})[stage] = output
    manifest.setdefault("security_audit_ids", {})[stage] = audit
    write_json(manifest_path, manifest)
    print("Read-only synthetic primary-key inventory recorded:", stage)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-directory", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("before-cleanup", "after-cleanup"), required=True
    )
    args = parser.parse_args()
    inventory(args.private_directory, args.stage)


if __name__ == "__main__":
    main()
