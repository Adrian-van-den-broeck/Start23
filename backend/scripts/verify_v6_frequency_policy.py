"""Actual local RPC/HTTP revision invalidation races, without invented operators.

Uses ordinary synthetic athletes, preferences and suspension reports. No real
authorization is issued: the reviewer registry remains empty. Pure resolver
fixtures cover numerical maxima separately; this runner proves commit custody.
"""

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.local_v6 import install_local_v6
from app.main import create_app
from app.modules.planning.v6_repository import InactiveSupabaseV6CatalogProvider
from app.modules.planning.v6_service import private_json
from scripts.verify_v6_lifecycle_completion import (
    Checkins,
    Onboarding,
    Repository,
    Verifier,
    fail_trigger,
    headers,
    prepare_checkin,
    remove_trigger,
    request,
    snapshot,
    state,
)
from scripts.verify_v6_mobile_lifecycle import SqlActivities
from scripts.verify_v6_postgres import ROOT, USERS, LocalPostgres


class BarrierRepository(Repository):
    def __init__(self, db: LocalPostgres) -> None:
        super().__init__(db)
        self.hold: str | None = None
        self.arrived = threading.Event()
        self.release = threading.Event()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if path == self.hold:
            self.arrived.set()
            if not await asyncio.to_thread(self.release.wait, 30):
                raise RuntimeError("test barrier timed out")
        return await super()._request(method, path, **kwargs)


def client_for(db: LocalPostgres) -> tuple[BarrierRepository, TestClient]:
    repo = BarrierRepository(db)
    catalog = InactiveSupabaseV6CatalogProvider(repo)
    app = create_app(
        Settings(
            environment="test",
            _env_file=None,
            supabase_url="http://127.0.0.1:55446",
            realized_v2_storage_ready=True,
            realized_v2_selection_enabled=True,
        ),
        access_token_verifier=Verifier(db),
        planning_repository=repo,
        planning_catalog_provider=catalog,
        checkin_repository=Checkins(repo),
        onboarding_repository=Onboarding(repo),
        activity_repository=SqlActivities(repo),
    )
    install_local_v6(app, repo, catalog)
    return repo, TestClient(app)


def save(client: TestClient) -> Any:
    current = request(client, "GET", "/me/frequency-preferences")
    return request(
        client,
        "PUT",
        "/me/frequency-preferences",
        body={
            "expected_revision": current["revision"],
            "operation_id": str(uuid4()),
            "preferences": {"run": 2, "bike": 2, "swim": 1},
        },
    )


def suspend(client: TestClient) -> Any:
    return request(
        client,
        "POST",
        "/me/frequency-preferences/interruption",
        body={"operation_id": str(uuid4()), "reason": "training_interruption"},
    )


def pending(client: TestClient, week: str) -> tuple[str, Any]:
    save(client)
    cid = prepare_checkin(client, week)
    url = "/checkins/" + cid + "/plan-proposals"
    proposal = request(client, "POST", url)
    assert len(proposal["plan"]["workouts"]) <= 3
    assert all(
        r["requested"] == {"run": 2, "bike": 2, "swim": 1}[r["sport"]]
        for r in proposal["plan"]["frequency_summary"]
    )
    return url, proposal


def fill_swipe(client: TestClient, week: str, user: UUID = USERS[0]) -> Any:
    from datetime import date, timedelta

    start = date.fromisoformat(week)
    draft = request(
        client,
        "POST",
        "/weekly-plans/swipe-drafts",
        expected=201,
        user=user,
        body={
            "week_start": week,
            "available_dates": [
                (start + timedelta(days=i)).isoformat() for i in range(7)
            ],
            "confirmed_injuries": [],
        },
    )
    for _ in range(24):
        if draft["state"] == "placement":
            return draft
        candidate = draft["current_candidate"]
        draft = request(
            client,
            "POST",
            f"/weekly-plans/swipe-drafts/{draft['id']}/transitions",
            user=user,
            body={
                "expected_revision": draft["revision"],
                "action": "accept",
                "candidate_template_id": candidate["id"],
                "candidate_occurrence_id": candidate["occurrence_id"],
            },
        )
    raise AssertionError("bounded swipe did not complete")


def holding_transaction(db: LocalPostgres, sql: str) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        ["psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write("begin;" + sql + ";select 'frequency_ready';\n")
    process.stdin.flush()
    with ThreadPoolExecutor(1) as pool:
        ready = pool.submit(process.stdout.readline).result(20)
    assert ready.strip() == "frequency_ready", ready
    return process


def commit_holder(process: subprocess.Popen[str]) -> None:
    assert process.stdin is not None
    process.stdin.write("commit;\n\\q\n")
    process.stdin.flush()
    assert process.wait(20) == 0


def await_database_wait(db: LocalPostgres, query_fragment: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if db.execute(
            "select to_jsonb(count(*)) from pg_stat_activity "
            "where pid<>pg_backend_pid() and wait_event='advisory' "
            "and query like '%" + query_fragment + "%'"
        ):
            return
        time.sleep(0.02)
    raise AssertionError("expected overlapping database lock wait was not observed")


def run(output: Path) -> None:
    db = LocalPostgres()
    assert db.execute("select to_jsonb(count(*)) from auth.users") == 0, (
        "requires a new empty migrated database"
    )
    fixture = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text()
    subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
        input=fixture,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    repo, client = client_for(db)
    checks = []
    trace: dict[str, Any] = {}
    with client:
        saved = save(client)
        assert (
            request(client, "GET", "/me/frequency-preferences", user=USERS[1])[
                "revision"
            ]
            == 0
        )
        assert (
            db.execute("select to_jsonb(count(*)) from private.frequency_reviewers")
            == 0
        )
        checks.append(
            "durable owner preference; no enrolled operator or issued maximum"
        )
        # Hold a fully calculated worker immediately before the authoritative RPC.
        cid = prepare_checkin(client, "2026-11-16")
        url = "/checkins/" + cid + "/plan-proposals"
        before = state(db)
        repo.hold = "rpc/create_v6_weekly_plan_proposal"
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(
                lambda: client.post("/api/v1" + url, headers=headers())
            )
            assert repo.arrived.wait(30)
            suspend(client)
            repo.release.set()
            response = future.result(30)
        repo.hold = None
        assert response.status_code == 409, response.text
        assert state(db) == before
        assert request(client, "GET", "/checkins/" + cid)["status"] == "open"
        checks.append(
            "suspension during generation prevents plan/snapshot/attachment writes"
        )
        # Fresh confirmation retains the default one-per-sport envelope.
        save(client)
        repo.lose_path = "rpc/create_v6_weekly_plan_proposal"
        request(client, "POST", url, expected=503)
        created = request(client, "POST", url)
        frozen = snapshot(db, created["plan"]["revision_id"])
        suspend(client)
        assert request(client, "POST", url) == created
        request(
            client,
            "POST",
            "/change-proposals/" + created["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
            expected=409,
        )
        assert snapshot(db, created["plan"]["revision_id"]) == frozen
        checks.append(
            "lost acknowledgement replays original A5 receipt after suspension; "
            "new confirmation denied"
        )
        trace = {
            "url": url,
            "created": created,
            "frozen": frozen,
            "frozen_sha256": hashlib.sha256(private_json(frozen).encode()).hexdigest(),
        }
        # Concurrent pending edit: existing revision and its receipt cannot change.
        edit_url, edit = pending(client, "2026-11-23")
        workout = edit["plan"]["workouts"][0]
        path = f"/weekly-plans/{edit['plan']['id']}/pending-workouts/{workout['id']}"
        options = request(
            client,
            "GET",
            path + f"/alternatives?expected_revision={edit['plan']['revision']}",
        )
        assert options["alternatives"]
        body = {
            "expected_revision": edit["plan"]["revision"],
            "expected_proposal_id": edit["proposal"]["id"],
            "replacement_template_id": options["alternatives"][0]["id"],
        }
        repo.hold = "rpc/create_v6_weekly_plan_proposal"
        repo.arrived.clear()
        repo.release.clear()
        before = state(db)
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(
                lambda: client.post(
                    "/api/v1" + path + "/edit-proposals", headers=headers(), json=body
                )
            )
            assert repo.arrived.wait(30)
            suspend(client)
            repo.release.set()
            result = future.result(30)
        repo.hold = None
        assert result.status_code == 409, result.text
        assert state(db) == before
        assert request(client, "POST", edit_url) == edit
        checks.append(
            "concurrent replacement rejects late commit; immutable attachment preserved"
        )
        # An in-flight swipe has the same private epoch and authoritative trigger.
        save(client)
        draft = request(
            client,
            "POST",
            "/weekly-plans/swipe-drafts",
            expected=201,
            body={
                "week_start": "2026-11-30",
                "available_dates": [f"2026-12-{n:02d}" for n in range(1, 7)]
                + ["2026-11-30"],
                "confirmed_injuries": [],
            },
        )
        current = draft["current_candidate"]
        repo.hold = "rpc/update_v6_frequency_swipe_draft"
        repo.arrived.clear()
        repo.release.clear()
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(
                lambda: client.post(
                    f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
                    headers=headers(),
                    json={
                        "expected_revision": draft["revision"],
                        "action": "accept",
                        "candidate_template_id": current["id"],
                        "candidate_occurrence_id": current["occurrence_id"],
                    },
                )
            )
            assert repo.arrived.wait(30)
            suspend(client)
            repo.release.set()
            result = future.result(30)
        repo.hold = None
        assert result.status_code == 409, result.text
        stored = db.execute(
            "select to_jsonb(revision) from public.swipe_week_drafts where id='"
            + draft["id"]
            + "'"
        )
        assert stored == draft["revision"]
        checks.append(
            "concurrent suspension rejects late swipe without accepting a card"
        )
        # Revocation holds the frequency lock while approval starts.
        _, confirm = pending(client, "2026-12-07")
        pref = request(client, "GET", "/me/frequency-preferences")
        report_id = str(uuid4())
        holder = holding_transaction(
            db,
            "set local request.jwt.claims='"
            + json.dumps({"role": "authenticated", "sub": str(USERS[0])})
            + "';set local role authenticated;do $$ begin perform "
            "public.report_frequency_interruption('"
            + report_id
            + "','training_interruption');end $$",
        )
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(
                lambda: client.post(
                    "/api/v1/change-proposals/"
                    + confirm["proposal"]["id"]
                    + "/approve",
                    headers=headers(),
                    json={"expected_base_revision": 0},
                )
            )
            await_database_wait(db, "approve_plan_proposal")
            commit_holder(holder)
            result = future.result(30)
        assert result.status_code == 409, result.text
        assert (
            request(client, "GET", "/me/frequency-preferences")["revision"]
            > pref["revision"]
        )
        checks.append(
            "final approval revalidates current frequency revisions; "
            "preference confirmation never restores authority"
        )
        # Writer owns the frequency lock before attachment; suspension waits.
        save(client)
        cid = prepare_checkin(client, "2026-12-14")
        attach_url = "/checkins/" + cid + "/plan-proposals"
        db.execute(
            "create function private.frequency_test_attachment_wait() "
            "returns trigger language plpgsql as $$ begin "
            "perform pg_advisory_xact_lock(77899064456);return new;end $$;"
            "create trigger frequency_test_attachment_wait before update of status "
            "on public.weekly_checkins for each row when(new.status='completed') "
            "execute function private.frequency_test_attachment_wait()"
        )
        holder = holding_transaction(
            db, "do $$ begin perform pg_advisory_xact_lock(77899064456);end $$"
        )
        with ThreadPoolExecutor(2) as pool:
            creation = pool.submit(
                lambda: client.post("/api/v1" + attach_url, headers=headers())
            )
            await_database_wait(db, "create_v6_weekly_plan_proposal")
            invalidation = pool.submit(lambda: suspend(client))
            await_database_wait(db, "report_frequency_interruption")
            commit_holder(holder)
            attached = creation.result(30)
            invalidation.result(30)
        db.execute(
            "drop trigger frequency_test_attachment_wait on public.weekly_checkins;"
            "drop function private.frequency_test_attachment_wait()"
        )
        assert attached.status_code == 200, attached.text
        receipt = attached.json()
        assert request(client, "POST", attach_url) == receipt
        request(
            client,
            "POST",
            "/change-proposals/" + receipt["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
            expected=409,
        )
        checks.append(
            "overlapping A5 attachment and suspension serialize; receipt "
            "is preserved and subsequent activation is denied"
        )
        save(client)
        submitted = fill_swipe(client, "2026-12-21")
        submit_url = f"/weekly-plans/swipe-drafts/{submitted['id']}/submit"
        body = {
            "expected_revision": submitted["revision"],
            "placement_mode": "automatic",
        }
        before = state(db)
        fail_trigger(db, "public.swipe_week_drafts", "frequency_submit_abort", "update")
        request(client, "POST", submit_url, body=body, expected=409)
        remove_trigger(db, "public.swipe_week_drafts", "frequency_submit_abort")
        assert state(db) == before
        repo.lose_path = "rpc/create_v6_frequency_swipe_proposal"
        request(client, "POST", submit_url, body=body, expected=503)
        suspend(client)
        recovered_submit = request(client, "POST", submit_url, body=body, expected=201)
        assert recovered_submit == request(
            client, "POST", submit_url, body=body, expected=201
        )
        request(
            client,
            "POST",
            "/change-proposals/" + recovered_submit["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
            expected=409,
        )
        checks.append(
            "swipe submit atomically rolls back or commits its original locator; "
            "lost acknowledgement recovers after suspension without new generation"
        )
        current_b = request(client, "GET", "/me/frequency-preferences", user=USERS[1])
        request(
            client,
            "PUT",
            "/me/frequency-preferences",
            user=USERS[1],
            body={
                "expected_revision": current_b["revision"],
                "operation_id": str(uuid4()),
                "preferences": {"run": 0, "bike": 0, "swim": 0},
            },
        )
        cid_b = prepare_checkin(client, "2026-12-21", USERS[1])
        zero = request(
            client, "POST", "/checkins/" + cid_b + "/plan-proposals", user=USERS[1]
        )
        assert zero["plan"]["workouts"] == []
        assert all(
            r["requested"] == r["proposed"] == 0
            for r in zero["plan"]["frequency_summary"]
        )
        current_b = request(client, "GET", "/me/frequency-preferences", user=USERS[1])
        request(
            client,
            "PUT",
            "/me/frequency-preferences",
            user=USERS[1],
            body={
                "expected_revision": current_b["revision"],
                "operation_id": str(uuid4()),
                "preferences": {"run": None, "bike": None, "swim": None},
            },
        )
        cid_b = prepare_checkin(client, "2026-12-28", USERS[1])
        default = request(
            client, "POST", "/checkins/" + cid_b + "/plan-proposals", user=USERS[1]
        )
        assert len(default["plan"]["workouts"]) == 3
        assert all(
            r["requested"] is None and r["proposed"] == 1
            for r in default["plan"]["frequency_summary"]
        )
        checks.append(
            "SQL-backed zero preference creates no new sessions; "
            "null restores the default request only"
        )
        assert (
            saved["preferences"]
            == request(client, "GET", "/me/frequency-preferences")["preferences"]
        )
        assert (
            db.execute("select to_jsonb(count(*)) from private.frequency_decisions")
            == 0
        )
        assert (
            db.execute("select to_jsonb(count(*)) from private.frequency_reviewers")
            == 0
        )
    trace["checks"] = checks
    output.write_text(json.dumps(trace, default=str, indent=2) + "\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.verify_v6_frequency_policy",
            "--execute-disposable-local-only",
            "--reload",
            str(output),
        ],
        check=True,
    )
    print("Frequency policy local RPC/HTTP checks PASS:", len(checks), "groups")


def reload(output: Path) -> None:
    db = LocalPostgres()
    trace = json.loads(output.read_text())
    _, client = client_for(db)
    with client:
        assert request(client, "POST", trace["url"]) == trace["created"]
        assert (
            hashlib.sha256(
                private_json(
                    snapshot(db, trace["created"]["plan"]["revision_id"])
                ).encode()
            ).hexdigest()
            == trace["frozen_sha256"]
        )
    print("Fresh process: immutable receipt and denied renewed authority preserved")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--reload", type=Path)
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        parser.error("Explicit local opt-in required")
    if args.reload:
        reload(args.reload)
    elif args.private_output:
        run(args.private_output)
    else:
        parser.error("Output or reload required")


if __name__ == "__main__":
    main()
