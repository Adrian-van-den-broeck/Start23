"""Lose a real committed PostgREST write acknowledgement, then retry its key.

Only synthetic fixture accounts and an explicitly selected disposable loopback
PostgREST/DSN are supported. The proxy closes the real client socket after the
upstream transaction commits, before sending any HTTP acknowledgement.
"""

import argparse
import asyncio
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx
import jwt

from app.modules.planning.repository import PlanningRepositoryUnavailableError
from app.modules.planning.schemas import PendingWorkoutEditRequest
from scripts.verify_v6_postgres import USERS, LocalPostgres, identity, literal, service


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
    service_token = jwt.encode(
        {"role": "service_role", "exp": int(time.time()) + 300},
        args.signing_secret_file.read_text(encoding="utf-8"),
        algorithm="HS256",
    )
    committed = threading.Event()

    class DropAcknowledgement(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            with httpx.Client(trust_env=False, timeout=20) as client:
                response = client.post(
                    args.url.rstrip("/") + self.path,
                    content=body,
                    headers={
                        "Authorization": "Bearer " + service_token,
                        "Content-Type": "application/json",
                    },
                )
            if response.status_code == 200:
                committed.set()
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    with HTTPServer(("127.0.0.1", 0), DropAcknowledgement) as proxy:
        proxy_url = f"http://127.0.0.1:{proxy.server_port}"
        thread = threading.Thread(target=proxy.handle_request, daemon=True)
        thread.start()

        async def exercise() -> None:
            repo, planner = service(db)
            owner = USERS[1]
            athlete = identity(db, owner)
            locator = db.execute(
                "select to_jsonb(p) from public.weekly_plans p where athlete_id="
                + literal(owner)
            )
            plan = await planner.get_plan(str(owner), UUID(locator["id"]), None)
            assert (
                plan.proposal is not None and plan.revision_state == "pending_approval"
            )
            workout = next(w for w in plan.workouts if w.discipline.value == "run")
            choices = await planner.get_pending_workout_alternatives(
                str(owner), athlete, plan.id, workout.id, plan.revision
            )
            request = PendingWorkoutEditRequest(
                expected_revision=plan.revision,
                expected_proposal_id=plan.proposal.id,
                replacement_template_id=choices.alternatives[0].id,
            )
            original_request = repo._request

            async def lose_reply(method: str, path: str, **kwargs: Any) -> Any:
                if path == "rpc/create_v6_weekly_plan_proposal":
                    try:
                        async with httpx.AsyncClient(
                            trust_env=False, timeout=25
                        ) as client:
                            await client.post(
                                proxy_url + "/" + path, json=kwargs["json"]
                            )
                    except httpx.TransportError:
                        raise PlanningRepositoryUnavailableError from None
                    raise AssertionError(
                        "The client unexpectedly received an acknowledgement"
                    )
                return await original_request(method, path, **kwargs)

            repo._request = lose_reply  # type: ignore[method-assign]
            try:
                await planner.edit_pending_workout(
                    str(owner), athlete, plan.id, workout.id, request
                )
            except PlanningRepositoryUnavailableError:
                assert committed.wait(5), "Upstream write did not commit"
            else:
                raise AssertionError("Unknown outcome was not reported")
            repo._request = original_request  # type: ignore[method-assign]
            first = await planner.edit_pending_workout(
                str(owner), athlete, plan.id, workout.id, request
            )
            second = await planner.edit_pending_workout(
                str(owner), athlete, plan.id, workout.id, request
            )
            assert first == second and first.plan.revision == plan.revision + 1
            count = db.execute(
                "select to_jsonb(count(*)) from public.plan_revisions where plan_id="
                + literal(plan.id)
            )
            assert count == first.plan.revision
            await repo._client.aclose()

        asyncio.run(exercise())
        thread.join(timeout=5)
    args.private_output.write_text(
        json.dumps(
            {
                "real_commit": True,
                "client_acknowledgement_lost": True,
                "same_key_receipt_recovered": True,
                "extra_revisions": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Real HTTP commit acknowledgement loss and same-key recovery passed.")


if __name__ == "__main__":
    main()
