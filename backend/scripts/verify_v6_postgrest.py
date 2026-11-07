"""Opt-in signed JWT checks against an already running disposable PostgREST.

Uses synthetic accounts from verify_v6_postgres. Never reads .env, launches an
app, creates cloud users or prints JWTs/private response bodies. This verifies
PostgREST signatures and database isolation, not a GoTrue login/session flow.
"""

import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import jwt

from scripts.verify_v6_postgres import USERS, LocalPostgres, literal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--url", required=True)
    parser.add_argument("--signing-secret-file", required=True, type=Path)
    parser.add_argument("--private-output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.url)
    if (
        not args.execute_disposable_local_only
        or url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "localhost", "::1"}
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise SystemExit("Explicit disposable loopback target required")
    db = LocalPostgres()
    secret = args.signing_secret_file.read_text(encoding="utf-8")
    results: list[dict[str, object]] = []
    plans = [
        db.execute(
            "select to_jsonb(p) from public.weekly_plans p where athlete_id = "
            + literal(user)
        )
        for user in USERS
    ]
    proposals = [
        db.execute(
            "select to_jsonb(p) from public.change_proposals p "
            "where athlete_id = " + literal(user) + " order by created_at desc limit 1"
        )
        for user in USERS
    ]

    def token(subject: str, *, key: str = secret, expired: bool = False) -> str:
        return jwt.encode(
            {
                "sub": subject,
                "role": "authenticated",
                "aud": "authenticated",
                "exp": int(time.time()) + (-60 if expired else 3600),
            },
            key,
            algorithm="HS256",
        )

    def public_only(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                assert not any(
                    word in key.lower()
                    for word in (
                        "tss",
                        "planned_load",
                        "realized_load",
                        "source_snapshot",
                    )
                ), "Private field in athlete response"
                public_only(child)
        elif isinstance(value, list):
            for child in value:
                public_only(child)

    with httpx.Client(base_url=args.url, timeout=15, trust_env=False) as client:

        def check(
            label: str,
            method: str,
            path: str,
            bearer: str | None,
            statuses: set[int],
            body: object = None,
            *,
            empty: bool = False,
            extra_headers: dict[str, str] | None = None,
        ) -> httpx.Response:
            response = client.request(
                method,
                path,
                headers={
                    **({"Authorization": "Bearer " + bearer} if bearer else {}),
                    **(extra_headers or {}),
                },
                json=body,
            )
            results.append({"case": label, "status": response.status_code})
            args.private_output.write_text(
                json.dumps(results, indent=2), encoding="utf-8"
            )
            assert response.status_code in statuses, label
            if response.status_code == 500:
                # PostgREST maps P0002 to 500; FastAPI maps it to owner-safe 404.
                assert response.json().get("code") == "P0002", label
            if response.content:
                public_only(response.json())
            if empty:
                assert response.json() == [], label
            return response

        for i, user in enumerate(USERS):
            own, foreign = plans[i], plans[1 - i]
            bearer = token(str(user))
            response = check(
                f"owner {i} reads own immutable V6 plan",
                "POST",
                "/rpc/get_v6_weekly_plan",
                bearer,
                {200},
                {"p_plan_id": own["id"]},
            )
            assert response.json()["id"] == own["id"]
            if proposals[i]["state"] in {"pending", "applied"}:
                approved = check(
                    f"owner {i} confirms own exact proposal",
                    "POST",
                    "/rpc/approve_plan_proposal",
                    bearer,
                    {200},
                    {
                        "p_proposal_id": proposals[i]["id"],
                        "p_expected_base_revision": 0,
                    },
                ).json()
                assert approved["state"] == "applied"
                replay = check(
                    f"owner {i} confirmation retry preserves receipt",
                    "POST",
                    "/rpc/approve_plan_proposal",
                    bearer,
                    {200},
                    {
                        "p_proposal_id": proposals[i]["id"],
                        "p_expected_base_revision": 0,
                    },
                ).json()
                assert replay == approved
                confirmed = check(
                    f"owner {i} reloads confirmed snapshot over HTTP",
                    "POST",
                    "/rpc/get_v6_weekly_plan",
                    bearer,
                    {200},
                    {"p_plan_id": own["id"]},
                ).json()
                assert confirmed["revision_state"] == "active"
            check(
                f"owner {i} cannot read foreign V6 plan",
                "POST",
                "/rpc/get_v6_weekly_plan",
                bearer,
                {404, 500},
                {"p_plan_id": foreign["id"]},
            )
            for table, key in (
                ("weekly_plans", "id"),
                ("plan_revisions", "plan_id"),
                ("planned_workouts", "plan_id"),
            ):
                path = f"/{table}?{key}=eq.{foreign['id']}&select=id"
                check(
                    f"owner {i} foreign {table} read",
                    "GET",
                    path,
                    bearer,
                    {200},
                    empty=True,
                )
                check(
                    f"owner {i} foreign {table} update",
                    "PATCH",
                    path,
                    bearer,
                    {204, 403},
                    {"id": foreign["id"]},
                )
            check(
                f"owner {i} cannot confirm foreign proposal",
                "POST",
                "/rpc/approve_plan_proposal",
                bearer,
                {404, 500},
                {
                    "p_proposal_id": proposals[1 - i]["id"],
                    "p_expected_base_revision": 0,
                },
            )
            check(
                f"owner {i} cannot spoof generated-write athlete",
                "POST",
                "/rpc/create_v6_weekly_plan_proposal",
                bearer,
                {403, 404},
                {"p_athlete_id": str(USERS[1 - i]), "p_payload": {}},
            )
            check(
                f"owner {i} cannot read service catalog",
                "POST",
                "/rpc/get_inactive_v6_catalog_for_planning",
                bearer,
                {403, 404},
                {},
            )
            check(
                f"owner {i} cannot activate catalog",
                "PATCH",
                "/workout_templates?inactive_v6=eq.true",
                bearer,
                {403},
                {"inactive_v6": False},
            )
            check(
                f"owner {i} inactive catalog hidden",
                "GET",
                "/workout_templates?inactive_v6=eq.true&select=id",
                bearer,
                {200},
                empty=True,
            )
            check(
                f"owner {i} private source schema inaccessible",
                "GET",
                "/v6_source_revisions",
                bearer,
                {406},
                extra_headers={"Accept-Profile": "private"},
            )
        service_token = jwt.encode(
            {"role": "service_role", "exp": int(time.time()) + 300},
            secret,
            algorithm="HS256",
        )
        privileged = client.post(
            "/rpc/get_inactive_v6_catalog_for_planning",
            headers={"Authorization": "Bearer " + service_token},
            json={},
        )
        assert privileged.status_code == 200 and len(privileged.json()) == 77
        results.append(
            {
                "case": "service catalog RPC authorized; private body retained locally",
                "status": 200,
            }
        )
        args.private_output.write_text(json.dumps(results, indent=2), encoding="utf-8")
        for label, invalid_bearer in (
            ("missing token", None),
            ("invalid signature", token(str(USERS[0]), key="wrong-local-key-" * 3)),
            ("expired token", token(str(USERS[0]), expired=True)),
        ):
            check(
                label,
                "POST",
                "/rpc/get_v6_weekly_plan",
                invalid_bearer,
                {401, 403},
                {"p_plan_id": plans[0]["id"]},
            )
    print(f"Signed-token PostgREST isolation: {len(results)} checks passed.")


if __name__ == "__main__":
    main()
