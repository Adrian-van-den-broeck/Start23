"""Real TCP acknowledgement-loss regression for A5 V6 creation and date moves.

Opt-in disposable loopback SQL/PostgREST only. A proxy closes the client socket
AFTER the actual PostgREST transaction has committed, before sending headers.
Synthetic local signed claims are not GoTrue sessions or gateway verification.
"""

import argparse
import json
import socket
import threading
import time
from contextlib import ExitStack
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import httpx
import jwt
from fastapi import FastAPI

from app.modules.planning.repository import PlanningRepositoryUnavailableError
from scripts.verify_v6_evidence_rescheduling import evidence, measured
from scripts.verify_v6_frequency_policy import fill_swipe
from scripts.verify_v6_lifecycle_completion import client_for, prepare_checkin, request
from scripts.verify_v6_postgres import USERS, LocalPostgres, literal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--url", required=True)
    parser.add_argument("--week-start", type=date.fromisoformat, required=True)
    parser.add_argument("--signing-secret-file", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--multi-session-test-only", action="store_true")
    parser.add_argument("--frequency-suspension-retry", action="store_true")
    args = parser.parse_args()
    url = urlparse(args.url)
    if (
        not args.execute_disposable_local_only
        or url.scheme != "http"
        or url.hostname != "127.0.0.1"
        or url.path not in ("", "/")
        or url.query
        or url.fragment
        or url.username
    ):
        raise SystemExit("Explicit disposable loopback target required")
    db = LocalPostgres()
    token = jwt.encode(
        {"role": "service_role", "exp": int(time.time()) + 600},
        args.signing_secret_file.read_text(),
        algorithm="HS256",
    )
    committed = threading.Event()
    results: list[int] = []

    class DropAcknowledgement(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            with httpx.Client(trust_env=False, timeout=30) as upstream:
                result = upstream.post(
                    args.url.rstrip("/") + self.path,
                    content=body,
                    headers={
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/json",
                    },
                )
            results.append(result.status_code)
            if result.status_code == 200:
                committed.set()
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    repo, client = client_for(db)
    if args.multi_session_test_only:
        from scripts.verify_v6_multi_session import authorization

        cast(FastAPI, client.app).state.v6_controls = authorization(
            db, args.week_start.isoformat()
        )
    original = repo._request
    target = "rpc/create_v6_weekly_plan_proposal"
    with (
        HTTPServer(("127.0.0.1", 0), DropAcknowledgement) as proxy,
        ExitStack() as cleanup,
    ):
        thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        thread.start()
        cleanup.callback(thread.join, timeout=5)
        cleanup.callback(proxy.shutdown)
        proxy_url = f"http://127.0.0.1:{proxy.server_port}"

        async def lose_reply(method: str, path: str, **kwargs: Any) -> Any:
            if path == target:
                try:
                    async with httpx.AsyncClient(trust_env=False, timeout=40) as http:
                        await http.post(proxy_url + "/" + path, json=kwargs["json"])
                except httpx.TransportError:
                    raise PlanningRepositoryUnavailableError from None
                raise AssertionError("Acknowledgement unexpectedly received")
            return await original(method, path, **kwargs)

        with client:
            cid = prepare_checkin(client, args.week_start.isoformat())
            endpoint = "/checkins/" + cid + "/plan-proposals"
            repo._request = lose_reply  # type: ignore[method-assign]
            request(client, "POST", endpoint, expected=503)
            assert committed.wait(5) and results == [200], results
            repo._request = original  # type: ignore[method-assign]
            pending = request(client, "POST", endpoint)
            assert pending == request(client, "POST", endpoint)
            if args.multi_session_test_only:
                assert len(pending["plan"]["workouts"]) == 5
            request(
                client,
                "POST",
                "/change-proposals/" + pending["proposal"]["id"] + "/approve",
                body={"expected_base_revision": 0},
            )
            plan = request(client, "GET", "/weekly-plans/" + pending["plan"]["id"])
            sibling = next(w for w in plan["workouts"] if w["discipline"] == "run")
            measured(client, sibling)
            saved = evidence(db)
            workout = next(
                w
                for w in plan["workouts"]
                if w["discipline"]
                == ("run" if args.multi_session_test_only else "bike")
                and w["id"] != sibling["id"]
            )
            endpoint = "/planned-workouts/" + workout["physical_workout_id"]
            payload = {
                "expected_revision": plan["revision"],
                "scheduled_date": (args.week_start + timedelta(days=6)).isoformat(),
            }
            target = "rpc/move_v6_planned_workout"
            committed.clear()
            repo._request = lose_reply  # type: ignore[method-assign]
            request(client, "PATCH", endpoint, body=payload, expected=503)
            assert committed.wait(5) and results == [200, 200], results
            repo._request = original  # type: ignore[method-assign]
            if args.frequency_suspension_retry:
                request(
                    client,
                    "POST",
                    "/me/frequency-preferences/interruption",
                    body={
                        "operation_id": "fc100000-0000-0000-0000-000000000001",
                        "reason": "training_interruption",
                    },
                )
            moved = request(client, "PATCH", endpoint, body=payload)
            assert moved == request(client, "PATCH", endpoint, body=payload)
            assert moved["revision"] == plan["revision"] + 1
            assert evidence(db) == saved
            retained = next(w for w in moved["workouts"] if w["id"] == sibling["id"])
            assert retained["physical_workout_id"] == sibling["physical_workout_id"]
            assert retained["status"] == "completed"
            assert (
                db.execute(
                    "select to_jsonb(count(*)) from public.plan_revisions "
                    "where plan_id=" + literal(plan["id"])
                )
                == 2
            )
            assert (
                request(client, "GET", "/checkins/" + cid)["plan_proposal_id"]
                == pending["proposal"]["id"]
            )
            if args.frequency_suspension_retry:
                cid_b = prepare_checkin(client, args.week_start.isoformat(), USERS[1])
                endpoint_b = "/checkins/" + cid_b + "/plan-proposals"
                target = "rpc/create_v6_weekly_plan_proposal"
                committed.clear()
                repo._request = lose_reply  # type: ignore[method-assign]
                request(client, "POST", endpoint_b, user=USERS[1], expected=503)
                assert committed.wait(5) and results == [200, 200, 200], results
                repo._request = original  # type: ignore[method-assign]
                request(
                    client,
                    "POST",
                    "/me/frequency-preferences/interruption",
                    user=USERS[1],
                    body={
                        "operation_id": "fc100000-0000-0000-0000-000000000002",
                        "reason": "illness",
                    },
                )
                recovered = request(client, "POST", endpoint_b, user=USERS[1])
                assert recovered == request(client, "POST", endpoint_b, user=USERS[1])
                request(
                    client,
                    "POST",
                    "/change-proposals/" + recovered["proposal"]["id"] + "/approve",
                    user=USERS[1],
                    body={"expected_base_revision": 0},
                    expected=409,
                )
                pref = request(
                    client, "GET", "/me/frequency-preferences", user=USERS[1]
                )
                request(
                    client,
                    "PUT",
                    "/me/frequency-preferences",
                    user=USERS[1],
                    body={
                        "expected_revision": pref["revision"],
                        "operation_id": "fc100000-0000-0000-0000-000000000003",
                        "preferences": {"run": None, "bike": None, "swim": None},
                    },
                )
                draft = fill_swipe(
                    client, (args.week_start + timedelta(days=7)).isoformat(), USERS[1]
                )
                submit_endpoint = f"/weekly-plans/swipe-drafts/{draft['id']}/submit"
                submit_body = {
                    "expected_revision": draft["revision"],
                    "placement_mode": "automatic",
                }
                target = "rpc/create_v6_frequency_swipe_proposal"
                committed.clear()
                repo._request = lose_reply  # type: ignore[method-assign]
                request(
                    client,
                    "POST",
                    submit_endpoint,
                    user=USERS[1],
                    body=submit_body,
                    expected=503,
                )
                assert committed.wait(5) and results == [200, 200, 200, 200], results
                repo._request = original  # type: ignore[method-assign]
                request(
                    client,
                    "POST",
                    "/me/frequency-preferences/interruption",
                    user=USERS[1],
                    body={
                        "operation_id": "fc100000-0000-0000-0000-000000000004",
                        "reason": "training_interruption",
                    },
                )
                submitted = request(
                    client,
                    "POST",
                    submit_endpoint,
                    user=USERS[1],
                    body=submit_body,
                    expected=201,
                )
                assert submitted == request(
                    client,
                    "POST",
                    submit_endpoint,
                    user=USERS[1],
                    body=submit_body,
                    expected=201,
                )
                request(
                    client,
                    "POST",
                    "/change-proposals/" + submitted["proposal"]["id"] + "/approve",
                    user=USERS[1],
                    body={"expected_base_revision": 0},
                    expected=409,
                )
    args.private_output.write_text(
        json.dumps(
            {
                "postgrest_http_statuses": results,
                "real_tcp_disconnects": len(results),
                "a5_authoritative_attachment_recovered": True,
                "move_original_receipt_recovered": True,
                "plan_revision_count": 2,
                "new_catalog_activations": 0,
                "completed_sibling_identity_and_evidence_preserved": True,
                "multi_session_test_only": args.multi_session_test_only,
                "frequency_suspension_retry": args.frequency_suspension_retry,
                "atomic_swipe_submit_recovered": args.frequency_suspension_retry,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"Real PostgREST commits + {len(results)} TCP acknowledgement losses "
        "+ exact recovery PASS"
    )


if __name__ == "__main__":
    main()
