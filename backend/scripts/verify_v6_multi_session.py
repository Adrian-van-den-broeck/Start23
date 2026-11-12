"""Opt-in real loopback PostgreSQL multi-session lifecycle; synthetic authority.

Uses normal onboarding, A5 attachment, existing receipts and the actual spawned
planner. No hosted access, .env, new approval states or replay ledger.
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from fastapi import FastAPI

from app.modules.physiology.models import Discipline
from app.modules.planning.v6_frequency import SessionFrequency
from app.modules.planning.v6_selection import V6Controls
from scripts.verify_v6_evidence_rescheduling import evidence, measured
from scripts.verify_v6_lifecycle_completion import (
    client_for,
    fail_trigger,
    prepare_checkin,
    remove_trigger,
    request,
    state,
)
from scripts.verify_v6_postgres import (
    ROOT,
    USERS,
    LocalPostgres,
    TransitionBarrier,
    identity,
    literal,
)


def authorization(db: LocalPostgres, week: str, user: UUID = USERS[0]) -> V6Controls:
    return V6Controls(
        athlete_scope=identity(db, user),
        week_scope=date.fromisoformat(week),
        session_frequency=tuple(
            SessionFrequency(
                s,
                n,
                "TEST_ONLY explicit multi-session request; no product "
                "frequency resolver",
                n,
            )
            for s, n in (
                (Discipline.RUN, 2),
                (Discipline.BIKE, 2),
                (Discipline.SWIM, 1),
            )
        ),
    )


def preserved(
    before: dict[str, Any], after: dict[str, Any], target: str, *, physical: bool
) -> None:
    assert {w["id"] for w in before["workouts"]} == {w["id"] for w in after["workouts"]}
    for old in before["workouts"]:
        new = next(w for w in after["workouts"] if w["id"] == old["id"])
        if old["id"] != target:
            ignored = set() if physical else {"physical_workout_id"}
            assert {k: v for k, v in old.items() if k not in ignored} == {
                k: v for k, v in new.items() if k not in ignored
            }
        else:
            assert old["scheduled_date"] == new["scheduled_date"] or physical
            if physical:
                assert old["physical_workout_id"] != new["physical_workout_id"]


def reload_plan(db: LocalPostgres, file: Path) -> None:
    trace = json.loads(file.read_text(encoding="utf-8"))
    _, client = client_for(db)
    with client:
        assert (
            request(client, "GET", "/weekly-plans/" + trace["latest"]["id"])
            == trace["latest"]
        )
        assert (
            request(client, "GET", "/calendar?from=2026-10-26&to=2026-11-02")
            == trace["calendar"]
        )
    print("Independent process reload: exact logical/physical/date/source mapping PASS")


def concurrency(db: LocalPostgres, output: Path) -> None:
    """Second synthetic athlete, real serialized RPCs on repeated-sport weeks."""
    repo, client = client_for(db)
    user = USERS[1]
    headers = {"Authorization": "Bearer " + str(user)}
    checks: list[str] = []
    cast(FastAPI, client.app).state.v6_controls = authorization(db, "2026-10-26", user)
    with client:
        proposed = request(
            client,
            "POST",
            "/weekly-plans/proposals",
            user=user,
            expected=201,
            body={
                "week_start": "2026-10-26",
                "available_dates": [
                    "2026-10-26",
                    "2026-10-27",
                    "2026-10-28",
                    "2026-10-29",
                    "2026-10-30",
                    "2026-10-31",
                    "2026-11-01",
                ],
            },
        )
        assert len(proposed["plan"]["workouts"]) == 5
        request(
            client,
            "POST",
            "/change-proposals/" + proposed["proposal"]["id"] + "/approve",
            user=user,
            body={"expected_base_revision": 0},
        )
        active = request(
            client, "GET", "/weekly-plans/" + proposed["plan"]["id"], user=user
        )
        cid = prepare_checkin(client, "2026-10-26", user)
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/create_v6_weekly_plan_proposal"})
        with ThreadPoolExecutor(2) as pool:
            attached = list(
                pool.map(
                    lambda _: request(
                        client,
                        "POST",
                        "/checkins/" + cid + "/plan-proposals",
                        user=user,
                    ),
                    range(2),
                )
            )
        repo.race_barrier = None
        assert attached[0] == attached[1]
        pending = attached[0]["plan"]
        assert len(pending["workouts"]) == 5
        checks.append(
            "two check-in generations converge on one five-occurrence A5 attachment"
        )
        target = next(w for w in pending["workouts"] if w["discipline"] == "run")
        edit_path = (
            "/api/v1/weekly-plans/"
            + pending["id"]
            + "/pending-workouts/"
            + target["id"]
            + "/edit-proposals"
        )
        choices = request(
            client,
            "GET",
            "/weekly-plans/"
            + pending["id"]
            + "/pending-workouts/"
            + target["id"]
            + "/alternatives?expected_revision="
            + str(pending["revision"]),
            user=user,
        )["alternatives"]
        assert len(choices) >= 2
        repo.race_barrier = TransitionBarrier()

        def editing(replacement: str) -> Any:
            return client.post(
                edit_path,
                headers=headers,
                json={
                    "expected_revision": pending["revision"],
                    "expected_proposal_id": pending["proposal"]["id"],
                    "replacement_template_id": replacement,
                },
            )

        with ThreadPoolExecutor(2) as pool:
            responses = list(pool.map(editing, [c["id"] for c in choices[:2]]))
        repo.race_barrier = None
        assert sorted(r.status_code for r in responses) == [201, 409]
        winner = next(r.json()["plan"] for r in responses if r.status_code == 201)
        preserved(pending, winner, target["id"], physical=False)
        checks.append(
            "two concurrent same-sport swipes: one successor, one stale CAS; "
            "sibling preserved"
        )
        old = active["workouts"][0]
        move_path = "/api/v1/planned-workouts/" + old["physical_workout_id"]
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/create_v6_weekly_plan_proposal"}
        )
        pending = winner
        target = next(w for w in pending["workouts"] if w["id"] == target["id"])
        with ThreadPoolExecutor(2) as pool:
            move = pool.submit(
                client.patch,
                move_path,
                headers=headers,
                json={
                    "expected_revision": active["revision"],
                    "scheduled_date": "2026-11-01",
                },
            )
            edit = pool.submit(editing, target["template_id"])
            moved, edited = move.result(), edit.result()
        repo.race_barrier = None
        assert moved.status_code == 409 and edited.status_code == 201, (
            moved.text,
            edited.text,
        )
        pending = edited.json()["plan"]
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/approve_plan_proposal"}
        )
        with ThreadPoolExecutor(2) as pool:
            move = pool.submit(
                client.patch,
                move_path,
                headers=headers,
                json={
                    "expected_revision": active["revision"],
                    "scheduled_date": "2026-11-01",
                },
            )
            approval = pool.submit(
                client.post,
                "/api/v1/change-proposals/" + pending["proposal"]["id"] + "/approve",
                headers=headers,
                json={"expected_base_revision": active["revision"]},
            )
            moved, approved = move.result(), approval.result()
        repo.race_barrier = None
        assert moved.status_code in {404, 409} and approved.status_code == 200, (
            moved.text,
            approved.text,
        )
        result = request(client, "GET", "/weekly-plans/" + pending["id"], user=user)
        assert result["revision_state"] == "active" and len(result["workouts"]) == 5
        checks.append(
            "move versus pending swipe and move versus confirmation retain CAS "
            "and five occurrences"
        )
        assert (
            request(client, "POST", "/checkins/" + cid + "/plan-proposals", user=user)[
                "proposal"
            ]["state"]
            == "expired"
        )
        cast(FastAPI, client.app).state.v6_controls = authorization(
            db, "2026-11-02", user
        )
        cid2 = prepare_checkin(client, "2026-11-02", user)
        rejected = request(
            client, "POST", "/checkins/" + cid2 + "/plan-proposals", user=user
        )
        request(
            client,
            "POST",
            "/change-proposals/" + rejected["proposal"]["id"] + "/reject",
            user=user,
        )
        assert (
            request(client, "POST", "/checkins/" + cid2 + "/plan-proposals", user=user)[
                "proposal"
            ]["state"]
            == "rejected"
        )
        checks.append(
            "rejection replay preserves exact terminal attachment; no regeneration"
        )
    output.write_text(
        json.dumps({"checks": checks, "active_count": 5}, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Multi-session concurrency and rejection PASS:", len(checks), "groups")


def run(db: LocalPostgres, output: Path) -> None:
    assert db.execute("select to_jsonb(count(*)) from auth.users") == 0, (
        "Use a fresh migrated disposable database"
    )
    fixture = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text(
        encoding="utf-8"
    )
    marker = "select v_user, s, 0, 'phase-13-joren-ruleset-1'"
    assert fixture.count(marker) == 1
    # Explicit synthetic history, not a private-budget override or product rule.
    # The normal approved Start-TSS resolver and SQL target-evidence guards run.
    fixture = fixture.replace(
        marker, "select v_user, s, 35, 'phase-13-joren-ruleset-1'"
    )
    subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
        input=fixture,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    repo, client = client_for(db)
    controls = authorization(db, "2026-10-26")
    cast(FastAPI, client.app).state.v6_controls = controls
    trace: dict[str, Any] = {}
    checks: list[str] = []
    with client:
        cid = prepare_checkin(client, "2026-10-26")
        path = "/checkins/" + cid + "/plan-proposals"
        initial_counts = state(db)
        fail_trigger(db, "public.weekly_checkins", "multi_abort_attachment", "update")
        request(client, "POST", path, expected=409)
        remove_trigger(db, "public.weekly_checkins", "multi_abort_attachment")
        assert state(db) == initial_counts
        checks.append("A5 attachment failure rolls back every multi-session row")
        repo.lose_path = "rpc/create_v6_weekly_plan_proposal"
        request(client, "POST", path, expected=503)
        pending = request(client, "POST", path)
        assert pending == request(client, "POST", path)
        assert len(pending["plan"]["workouts"]) == 5
        assert [
            sum(w["discipline"] == s for w in pending["plan"]["workouts"])
            for s in ("run", "bike", "swim")
        ] == [2, 2, 1]
        assert pending["plan"]["revision_state"] == "pending_approval"
        assert (
            request(client, "GET", "/calendar?from=2026-10-26&to=2026-11-02")[
                "workouts"
            ]
            == []
        )
        trace["checkinPending"] = pending["plan"]
        request(client, "POST", path, user=USERS[1], expected=404)
        checks.append(
            "check-in-driven 2 RUN/2 BIKE/1 SWIM; lost acknowledgement exact "
            "attachment replay; owner isolation"
        )
        runs = [w for w in pending["plan"]["workouts"] if w["discipline"] == "run"]
        assert runs[0]["template_id"] == runs[1]["template_id"]
        assert (
            runs[0]["id"] != runs[1]["id"]
            and runs[0]["physical_workout_id"] != runs[1]["physical_workout_id"]
        )
        selected = runs[1]
        alternatives_path = (
            "/weekly-plans/"
            + pending["plan"]["id"]
            + "/pending-workouts/"
            + selected["id"]
        )
        alternatives = request(
            client, "GET", alternatives_path + "/alternatives?expected_revision=1"
        )
        assert alternatives["alternatives"]
        edit_body = {
            "expected_revision": 1,
            "expected_proposal_id": pending["proposal"]["id"],
            "replacement_template_id": alternatives["alternatives"][0]["id"],
        }
        edited = request(
            client,
            "POST",
            alternatives_path + "/edit-proposals",
            body=edit_body,
            expected=201,
        )
        assert (
            request(
                client,
                "POST",
                alternatives_path + "/edit-proposals",
                body=edit_body,
                expected=201,
            )
            == edited
        )
        preserved(pending["plan"], edited["plan"], selected["id"], physical=False)
        assert edited["plan"]["revision_state"] == "pending_approval"
        request(
            client,
            "GET",
            alternatives_path + "/alternatives?expected_revision=1",
            expected=404,
        )
        assert request(client, "POST", path)["proposal"]["state"] == "expired"
        trace["swiped"] = edited["plan"]
        checks.append(
            "duplicate-template RUN-B swipe retains RUN-A/logical "
            "IDs/dates/other sources; exact retry and stale CAS"
        )
        request(
            client,
            "POST",
            "/change-proposals/" + edited["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
        )
        active = request(client, "GET", "/weekly-plans/" + edited["plan"]["id"])
        trace["active"] = active
        stored = db.execute(
            "select jsonb_build_object('snapshot',s.payload->'v6_frozen_snapshot',"
            "'rows',(select jsonb_agg(to_jsonb(o) order by o.ordinal) from "
            "private.v6_occurrence_snapshots o where o.revision_id=s.revision_id)) "
            "from private.v6_plan_snapshots s where s.revision_id="
            + literal(active["revision_id"])
        )
        trace["privateFrozen"] = stored
        assert len(stored["rows"]) == 5
        assert stored["snapshot"]["controls"]["session_frequency"]
        checks.append(
            "separate athlete confirmation; five durable "
            "source/method/prescription mappings"
        )
        for sport in ("run", "bike"):
            first = next(w for w in active["workouts"] if w["discipline"] == sport)
            measured(client, first)
        before = request(client, "GET", "/weekly-plans/" + active["id"])
        trace["before"] = before
        original_evidence = evidence(db)
        for sport in ("run", "bike"):
            unfinished = next(
                w
                for w in before["workouts"]
                if w["discipline"] == sport and w["status"] == "scheduled"
            )
            move_path = "/planned-workouts/" + unfinished["physical_workout_id"]
            body = {
                "expected_revision": before["revision"],
                "scheduled_date": "2026-11-01",
            }
            initial_counts = state(db)
            fail_trigger(db, "private.v6_edit_results", "multi_abort_move")
            request(client, "PATCH", move_path, body=body, expected=409)
            remove_trigger(db, "private.v6_edit_results", "multi_abort_move")
            assert state(db) == initial_counts and evidence(db) == original_evidence
            repo.lose_path = "rpc/move_v6_planned_workout"
            request(client, "PATCH", move_path, body=body, expected=503)
            after = request(client, "PATCH", move_path, body=body)
            assert after == request(client, "PATCH", move_path, body=body)
            preserved(before, after, unfinished["id"], physical=True)
            assert evidence(db) == original_evidence
            request(
                client,
                "PATCH",
                move_path,
                body={**body, "scheduled_date": "2026-10-31"},
                expected=404,
            )
            if sport == "run":
                trace["after"] = after
            before = after
        trace["latest"] = before
        checks.append(
            "completed RUN-A/BIKE-A unchanged through unfinished same-sport "
            "sibling moves; rollback; commit loss exact receipts"
        )
        trace["calendar"] = request(
            client, "GET", "/calendar?from=2026-10-26&to=2026-11-02"
        )
        assert len(trace["calendar"]["workouts"]) == 5
        assert len({w["id"] for w in trace["calendar"]["workouts"]}) == 5
        # Competing date changes share the established plan lock and CAS.
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/move_v6_planned_workout"})
        unfinished = next(
            w
            for w in before["workouts"]
            if w["discipline"] == "run" and w["status"] == "scheduled"
        )

        def race_move(day: str) -> int:
            return int(
                client.patch(
                    "/api/v1/planned-workouts/" + unfinished["physical_workout_id"],
                    headers={"Authorization": "Bearer " + str(USERS[0])},
                    json={
                        "expected_revision": before["revision"],
                        "scheduled_date": day,
                    },
                ).status_code
            )

        with ThreadPoolExecutor(2) as pool:
            outcomes = sorted(pool.map(race_move, ("2026-10-30", "2026-10-31")))
        repo.race_barrier = None
        assert outcomes == [200, 409], outcomes
        assert evidence(db) == original_evidence
        trace["latest"] = request(client, "GET", "/weekly-plans/" + active["id"])
        trace["calendar"] = request(
            client, "GET", "/calendar?from=2026-10-26&to=2026-11-02"
        )
        checks.append(
            "real concurrent sibling moves: one commit, one stale revision; "
            "unchanged activity evidence"
        )
        # Stored evidence owns edits after restart without request authorization.
        cast(FastAPI, client.app).state.v6_controls = V6Controls()
        trace["checks"] = checks
        output.write_text(
            json.dumps(trace, indent=2, default=str) + "\n", encoding="utf-8"
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.verify_v6_multi_session",
                "--execute-disposable-local-only",
                "--reload",
                str(output),
            ],
            check=True,
        )
        checks.append(
            "new Python process restores five logical/physical/date/source mappings"
        )
    trace["checks"] = checks
    output.write_text(json.dumps(trace, indent=2, default=str) + "\n", encoding="utf-8")
    print("Multi-session PostgreSQL lifecycle PASS:", len(checks), "groups")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--reload", type=Path)
    parser.add_argument("--concurrency-output", type=Path)
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        parser.error("Explicit local opt-in required")
    db = LocalPostgres()
    if args.concurrency_output:
        concurrency(db, args.concurrency_output)
    elif args.reload:
        reload_plan(db, args.reload)
    elif args.private_output:
        run(db, args.private_output)
    else:
        parser.error("Output or reload required")


if __name__ == "__main__":
    main()
