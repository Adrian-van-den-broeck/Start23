"""Fixed GET-only account recovery/branching inspection. No athlete data or writes."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from scripts.verify_v6_hosted_auth import PROJECT_REF, cli_management_token


def inspect(output: Path) -> None:
    result: dict[str, Any] = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_ref": PROJECT_REF,
        "hosted_mutations": 0,
        "athlete_rows_downloaded": 0,
        "checks": {},
    }
    with httpx.Client(
        base_url="https://api.supabase.com",
        headers={"Authorization": "Bearer " + cli_management_token()},
        follow_redirects=False,
        timeout=30,
    ) as client:
        project_response = client.get("/v1/projects/" + PROJECT_REF)
        project_response.raise_for_status()
        project = project_response.json()
        if project.get("id") != PROJECT_REF:
            raise RuntimeError("Authorized project mismatch")
        result["project"] = {
            k: project.get(k)
            for k in (
                "id",
                "name",
                "region",
                "status",
                "organization_id",
                "organization_slug",
            )
        }
        paths = {
            "addons": "billing/addons",
            "backups": "database/backups",
            "restore_point": "database/backups/restore-point",
            "backup_schedule": "database/backups/schedule",
            "branches": "branches",
        }
        for name, path in paths.items():
            response = client.get(f"/v1/projects/{PROJECT_REF}/{path}")
            check: dict[str, Any] = {"http_status": response.status_code}
            if response.is_success:
                data = response.json()
                if name == "backups":
                    check["data"] = {
                        k: data.get(k)
                        for k in (
                            "region",
                            "pitr_enabled",
                            "walg_enabled",
                            "physical_backup_data",
                        )
                    }
                    check["data"]["backups"] = [
                        {
                            k: r.get(k)
                            for k in (
                                "id",
                                "status",
                                "inserted_at",
                                "is_physical_backup",
                            )
                        }
                        for r in data.get("backups", [])
                    ]
                elif name == "addons":
                    check["selected"] = [
                        {
                            "type": r.get("type"),
                            "variant": {
                                k: r.get("variant", {}).get(k)
                                for k in ("id", "name", "price")
                            },
                        }
                        for r in data.get("selected_addons", [])
                    ]
                    check["available"] = [
                        {
                            "type": r.get("type"),
                            "name": r.get("name"),
                            "variants": [
                                {k: v.get(k) for k in ("id", "name", "price")}
                                for v in r.get("variants", [])
                            ],
                        }
                        for r in data.get("available_addons", [])
                    ]
                elif name == "branches":
                    check["branches"] = [
                        {
                            k: r.get(k)
                            for k in (
                                "id",
                                "project_ref",
                                "parent_project_ref",
                                "name",
                                "status",
                            )
                        }
                        for r in data
                    ]
                else:
                    check["data"] = {
                        k: v
                        for k, v in data.items()
                        if k
                        in {
                            "schedule_for",
                            "updated_at",
                            "earliest_restore_time",
                            "latest_restore_time",
                            "latest_restore_point",
                            "earliest_restore_point",
                            "recovery_point",
                            "status",
                        }
                    }
                    check["response_keys"] = sorted(data)
            result["checks"][name] = check
        organization = project.get("organization_slug") or project.get(
            "organization_id"
        )
        if isinstance(organization, str) and organization.replace("-", "").isalnum():
            for name, ending in (
                ("organization", ""),
                ("entitlements", "/entitlements"),
            ):
                response = client.get("/v1/organizations/" + organization + ending)
                check = {"http_status": response.status_code}
                if response.is_success:
                    data = response.json()
                    if name == "organization":
                        check["data"] = {
                            k: data.get(k)
                            for k in ("id", "slug", "name", "plan", "subscription_tier")
                            if k in data
                        }
                        check["response_keys"] = sorted(data)
                    else:
                        # Documented entitlement names/limits only; no billing identity.
                        check["data"] = data
                result["checks"][name] = check
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Recorded GET-only recovery options and account entitlements; no changes.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    inspect(parser.parse_args().output)


if __name__ == "__main__":
    main()
