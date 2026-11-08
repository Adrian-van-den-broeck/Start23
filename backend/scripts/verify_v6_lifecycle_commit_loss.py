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
from typing import Any
from urllib.parse import urlparse

import httpx
import jwt

from app.modules.planning.repository import PlanningRepositoryUnavailableError
from scripts.verify_v6_lifecycle_completion import client_for, prepare_checkin, request
from scripts.verify_v6_postgres import LocalPostgres, literal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--url", required=True)
    parser.add_argument("--week-start", type=date.fromisoformat, required=True)
    parser.add_argument("--signing-secret-file", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
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
            request(
                client,
                "POST",
                "/change-proposals/" + pending["proposal"]["id"] + "/approve",
                body={"expected_base_revision": 0},
            )
            plan = request(client, "GET", "/weekly-plans/" + pending["plan"]["id"])
            workout = next(w for w in plan["workouts"] if w["discipline"] == "bike")
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
            moved = request(client, "PATCH", endpoint, body=payload)
            assert moved == request(client, "PATCH", endpoint, body=payload)
            assert moved["revision"] == plan["revision"] + 1
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
    args.private_output.write_text(
        json.dumps(
            {
                "postgrest_http_statuses": results,
                "real_tcp_disconnects": 2,
                "a5_authoritative_attachment_recovered": True,
                "move_original_receipt_recovered": True,
                "plan_revision_count": 2,
                "new_catalog_activations": 0,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "Real PostgREST commits + two TCP acknowledgement losses + exact recovery PASS"
    )


if __name__ == "__main__":
    main()
