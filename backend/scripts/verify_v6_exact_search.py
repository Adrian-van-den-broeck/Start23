"""Opt-in disposable SQL lifecycle for the formerly incomplete onboarding week.

105 minutes/sport use the normal budget resolver. Frequency remains TEST_ONLY;
the existing explicitly permissioned synthetic harness role is required. No real
reviewer/authorization is issued, and no application migration is changed.
"""

import argparse
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from fastapi import FastAPI

from benchmarks.v6_exact_search import peak_memory
from scripts.verify_v6_evidence_rescheduling import evidence, measured
from scripts.verify_v6_lifecycle_completion import (
    client_for,
    prepare_checkin,
    request,
    snapshot,
    state,
)
from scripts.verify_v6_multi_session import authorization, preserved
from scripts.verify_v6_postgres import ROOT, USERS, LocalPostgres


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


def reload(db: LocalPostgres, path: Path) -> None:
    trace = json.loads(path.read_text(encoding="utf-8"))
    _, client = client_for(db)
    with client:
        assert (
            request(client, "GET", "/weekly-plans/" + trace["latest"]["id"])
            == trace["latest"]
        )
        assert request(client, "POST", trace["create_path"]) == trace["create_receipt"]
        assert digest(evidence(db)) == trace["activity_evidence_sha256"]
        assert (
            digest(snapshot(db, trace["original_revision"]))
            == trace["original_snapshot_sha256"]
        )
    print("Fresh process: exact high-budget receipt, calendar and evidence restored")


def run(db: LocalPostgres, output: Path) -> None:
    assert db.execute("select to_jsonb(count(*)) from auth.users") == 0
    fixture = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text(
        encoding="utf-8"
    )
    marker = "select v_user, s, 0, 'phase-13-joren-ruleset-1'"
    assert fixture.count(marker) == 1
    fixture = fixture.replace(
        marker, "select v_user, s, 105, 'phase-13-joren-ruleset-1'"
    )
    subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
        input=fixture,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    repo, client = client_for(db)
    app = cast(FastAPI, client.app)
    controls = authorization(db, "2026-10-26")
    assert controls.authorized_target is None
    app.state.v6_controls = replace(controls, maximum_search_nodes=1)
    trace: dict[str, Any] = {"test_only": True, "onboarding_minutes_per_sport": 105}
    with client:
        cid = prepare_checkin(client, "2026-10-26")
        create_path = "/checkins/" + cid + "/plan-proposals"
        before = state(db)
        request(client, "POST", create_path, expected=422)
        assert state(db) == before
        app.state.v6_controls = controls
        began = perf_counter()
        pending = request(client, "POST", create_path)
        trace["create_http_seconds"] = perf_counter() - began
        assert len(pending["plan"]["workouts"]) == 5
        assert pending["plan"]["revision_state"] == "pending_approval"
        assert pending == request(client, "POST", create_path)
        request(
            client,
            "GET",
            "/weekly-plans/" + pending["plan"]["id"],
            user=USERS[1],
            expected=404,
        )
        original_revision = pending["plan"]["revision_id"]
        original_snapshot = snapshot(db, original_revision)
        stored = original_snapshot["snapshot"]["payload"]["v6_frozen_snapshot"]
        assert stored["target"]["target"]["value"] == "300.2", stored["target"]
        trace["private_initial_snapshot"] = stored
        selected = next(
            w for w in pending["plan"]["workouts"] if w["discipline"] == "run"
        )
        path = (
            "/weekly-plans/"
            + pending["plan"]["id"]
            + "/pending-workouts/"
            + selected["id"]
        )
        choices = request(client, "GET", path + "/alternatives?expected_revision=1")
        assert choices["alternatives"]
        edited = request(
            client,
            "POST",
            path + "/edit-proposals",
            expected=201,
            body={
                "expected_revision": 1,
                "expected_proposal_id": pending["proposal"]["id"],
                "replacement_template_id": choices["alternatives"][0]["id"],
            },
        )
        preserved(pending["plan"], edited["plan"], selected["id"], physical=False)
        assert snapshot(db, original_revision) == original_snapshot
        request(
            client,
            "POST",
            "/change-proposals/" + edited["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
        )
        active = request(client, "GET", "/weekly-plans/" + pending["plan"]["id"])
        first = next(w for w in active["workouts"] if w["discipline"] == "run")
        measured(client, first)
        before_move = request(client, "GET", "/weekly-plans/" + active["id"])
        saved = evidence(db)
        sibling = next(
            w
            for w in before_move["workouts"]
            if w["discipline"] == "run" and w["status"] == "scheduled"
        )
        endpoint = "/planned-workouts/" + sibling["physical_workout_id"]
        body = {
            "expected_revision": before_move["revision"],
            "scheduled_date": "2026-11-01",
        }
        repo.lose_path = "rpc/move_v6_planned_workout"
        request(client, "PATCH", endpoint, expected=503, body=body)
        moved = request(client, "PATCH", endpoint, body=body)
        assert moved == request(client, "PATCH", endpoint, body=body)
        assert evidence(db) == saved
        retained = next(w for w in moved["workouts"] if w["id"] == first["id"])
        assert retained["physical_workout_id"] == first["physical_workout_id"]
        assert retained["status"] == "completed"
        calendar = request(client, "GET", "/calendar?from=2026-10-26&to=2026-11-02")
        assert len(calendar["workouts"]) == 5
        assert client.portal is not None
        trace["worker_peak_working_set_bytes"] = client.portal.call(
            app.state.planning_computation.run, peak_memory
        )
        trace.update(
            latest=moved,
            original_revision=original_revision,
            original_snapshot_sha256=digest(original_snapshot),
            activity_evidence_sha256=digest(saved),
            create_path=create_path,
            create_receipt=request(client, "POST", create_path),
            checks=[
                "incomplete computation writes nothing",
                "normal resolved 300.2 budget",
                "A5 exact retry and account isolation",
                "pending swipe preserves siblings",
                "immutable original snapshot",
                "separate athlete confirmation",
                "physical activity registration",
                "completed sibling preserved on move",
                "committed move loss exact retry",
                "five-occurrence calendar readback",
            ],
        )
    output.write_text(json.dumps(trace, indent=2, default=str) + "\n", encoding="utf-8")
    reload(db, output)
    assert db.execute("select to_jsonb(count(*)) from private.frequency_reviewers") == 0
    assert db.execute("select to_jsonb(count(*)) from private.frequency_decisions") == 0
    print("High-budget real SQL lifecycle PASS:", len(trace["checks"]), "groups")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--reload", type=Path)
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        parser.error("Explicit local opt-in required")
    db = LocalPostgres()
    if args.reload:
        reload(db, args.reload)
    elif args.private_output:
        run(db, args.private_output)
    else:
        parser.error("Output or reload required")


if __name__ == "__main__":
    main()
