"""Owner-run GET-only A6 checks. Never logs tokens, identities or plan payloads."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://start23-production.up.railway.app"


class NoRedirect(HTTPRedirectHandler):
    """Do not forward tester credentials to a redirected destination."""

    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Request | None:
        return None


def get(path: str, token: str = "") -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(BASE + path, headers=headers, method="GET")
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, None


def main() -> int:
    code, ready = get("/ready")
    if code != 200 or not isinstance(ready, dict):
        print("NO-GO: public readiness is unavailable.")
        return 2
    if ready.get("environment") != "production":
        print("NO-GO: production configuration is not verified; no account checks ran.")
        return 2
    code, schema = get("/openapi.json")
    route = schema.get("paths", {}).get("/api/v1/weekly-plans/recovery", {})
    if code != 200 or "get" not in route:
        print("NO-GO: A6 GET is not advertised; no account checks ran.")
        return 2
    tokens = [os.environ.get(f"WOMBO_TESTER_{who}_ACCESS_TOKEN", "") for who in "AB"]
    if not all(tokens):
        print("NOT VERIFIED: two existing tester tokens must be provided locally.")
        return 2
    identities: list[str] = []
    recoveries: list[dict[str, Any]] = []
    for token in tokens:
        code, identity = get("/api/v1/me", token)
        if code != 200 or identity.get("role") != "authenticated":
            print("NOT VERIFIED: an existing tester session is invalid.")
            return 2
        identities.append(str(identity["athlete_id"]))
        code, recovery = get("/api/v1/weekly-plans/recovery", token)
        if code != 200 or not isinstance(recovery, dict):
            print("NO-GO: authenticated recovery failed.")
            return 2
        if set(recovery) != {"active", "pending", "draft"}:
            print("NO-GO: recovery envelope differs from the accepted contract.")
            return 2
        recoveries.append(recovery)
    if identities[0] == identities[1]:
        print("NOT VERIFIED: two distinct verified athlete identities are required.")
        return 2
    cross_reads = 0
    for owner in (0, 1):
        for kind in ("active", "pending"):
            plan = recoveries[owner][kind]
            if plan is None:
                continue
            code, _ = get(f"/api/v1/weekly-plans/{plan['id']}", tokens[1 - owner])
            if code != 404:
                print("NO-GO: foreign-plan read did not produce the expected denial.")
                return 2
            cross_reads += 1
    print(
        json.dumps(
            {
                "two_owned_recovery_reads": "PASS",
                "cross_owner_denials": cross_reads,
                "unexercised_plan_states": cross_reads == 0,
                "deployment_identity_verified": False,
                "writes_executed": False,
            }
        )
    )
    print(
        "Read-only probe only. Revision/stale/retry and exact deployment gates "
        "remain separate."
    )
    return 0 if cross_reads else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (URLError, ValueError, KeyError, TypeError, AttributeError):
        print(
            "NOT VERIFIED: network or response-contract failure; no absence inferred."
        )
        raise SystemExit(2) from None
