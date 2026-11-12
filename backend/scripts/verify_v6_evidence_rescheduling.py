"""Actual FastAPI/PostgreSQL evidence-safe V6 moves, with simulated SQL claims.

Opt-in disposable loopback database only. No mocked storage, hosted connection,
GoTrue session or physical-device result is claimed.
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.modules.planning.repository import PlanningRepositoryConflictError
from scripts.verify_v6_lifecycle_completion import (
    client_for,
    fail_trigger,
    headers,
    prepare_checkin,
    remove_trigger,
    request,
)
from scripts.verify_v6_postgres import (
    ROOT,
    USERS,
    LocalPostgres,
    TransitionBarrier,
    literal,
)


def measured(
    client: Any, workout: dict[str, Any], user: UUID = USERS[0]
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/activities",
        headers={**headers(user), "Idempotency-Key": str(uuid4())},
        json={
            "planned_workout_id": workout["physical_workout_id"],
            "discipline": workout["discipline"],
            "started_at": workout["scheduled_date"] + "T08:00:00+01:00",
            "timezone": "Europe/Amsterdam",
            "duration_minutes": "30",
            "performed_duration_confirmed": True,
            "metrics": {"zone_minutes": ["30", "0", "0", "0", "0"]},
        },
    )
    assert response.status_code == 201, response.text
    activity = response.json()
    completed = request(
        client,
        "PUT",
        "/activities/" + activity["id"] + "/rpe",
        user=user,
        body={"rpe": 3},
    )
    assert completed["planned_workout_id"] == workout["physical_workout_id"]
    return dict(completed)


def evidence(db: LocalPostgres) -> Any:
    tables = (
        "public.activities",
        "private.activity_loads",
        "public.activity_metrics",
        "private.realized_v2_activity_inputs",
        "private.realized_v2_calculations",
        "private.workout_registration_events",
    )
    return {
        table: db.execute(
            "select coalesce(jsonb_agg(to_jsonb(r) order by "
            "to_jsonb(r)::text),'[]') from " + table + " r"
        )
        for table in tables
    }


def counts(db: LocalPostgres) -> Any:
    tables = (
        "public.weekly_plans",
        "public.plan_revisions",
        "public.planned_workouts",
        "private.v6_revision_memberships",
        "private.v6_occurrence_snapshots",
        "private.v6_plan_snapshots",
        "private.v6_edit_results",
    )
    return {
        table: db.execute("select to_jsonb(count(*)) from " + table) for table in tables
    }


def prescribed(db: LocalPostgres, plan: str) -> Any:
    return db.execute(
        "select jsonb_agg(to_jsonb(w)-'status' order by id) from "
        "public.planned_workouts w where plan_id=" + literal(plan)
    )


def create(client: Any, week: str, user: UUID = USERS[0]) -> dict[str, Any]:
    start = date.fromisoformat(week)
    proposed = request(
        client,
        "POST",
        "/weekly-plans/proposals",
        expected=201,
        user=user,
        body={
            "week_start": week,
            "available_dates": [
                (start + timedelta(days=i)).isoformat() for i in range(7)
            ],
        },
    )
    request(
        client,
        "POST",
        "/change-proposals/" + proposed["proposal"]["id"] + "/approve",
        user=user,
        body={"expected_base_revision": 0},
    )
    return dict(
        request(client, "GET", "/weekly-plans/" + proposed["plan"]["id"], user=user)
    )


def move(
    client: Any,
    plan: dict[str, Any],
    sport: str,
    day: str,
    user: UUID = USERS[0],
    expected: int = 200,
) -> Any:
    workout = next(w for w in plan["workouts"] if w["discipline"] == sport)
    return request(
        client,
        "PATCH",
        "/planned-workouts/" + workout["physical_workout_id"],
        user=user,
        expected=expected,
        body={"expected_revision": plan["revision"], "scheduled_date": day},
    )


def check_mapping(before: dict[str, Any], after: dict[str, Any], moved: str) -> None:
    assert (
        after["revision"] > before["revision"] and after["revision_state"] == "active"
    )
    assert {w["id"] for w in before["workouts"]} == {w["id"] for w in after["workouts"]}
    for old in before["workouts"]:
        new = next(w for w in after["workouts"] if w["id"] == old["id"])
        assert old["source_prescription"] == new["source_prescription"]
        assert old["template_id"] == new["template_id"]
        if old["discipline"] == moved:
            assert old["physical_workout_id"] != new["physical_workout_id"]
        else:
            assert old == new


def run(output: Path) -> None:
    db = LocalPostgres()
    if not db.execute("select to_jsonb(count(*)) from auth.users"):
        subprocess.run(
            ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
            input=(
                ROOT / "supabase/tests/fixtures/v6_persistence_users.sql"
            ).read_text(),
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
    repo, client = client_for(db)
    trace: dict[str, Any] = {}
    checks: list[str] = []
    with client:
        initial = create(client, "2026-10-26")
        run_workout = next(w for w in initial["workouts"] if w["discipline"] == "run")
        completed = measured(client, run_workout)
        original_evidence = evidence(db)
        original_prescription = prescribed(db, initial["id"])
        before = request(client, "GET", "/weekly-plans/" + initial["id"])
        trace["before"] = before
        assert (
            next(w for w in before["workouts"] if w["id"] == run_workout["id"])[
                "status"
            ]
            == "completed"
        )
        c0 = counts(db)
        fail_trigger(db, "private.v6_edit_results", "evidence_abort_move")
        move(client, before, "bike", "2026-11-01", expected=409)
        remove_trigger(db, "private.v6_edit_results", "evidence_abort_move")
        assert counts(db) == c0 and evidence(db) == original_evidence
        assert prescribed(db, initial["id"]) == original_prescription
        assert request(client, "GET", "/weekly-plans/" + initial["id"]) == before
        checks.append(
            "failure after target/membership/pointer writes rolls back every "
            "change and retains evidence"
        )
        after = move(client, before, "bike", "2026-11-01")
        check_mapping(before, after, "bike")
        assert evidence(db) == original_evidence
        assert (
            counts(db)["public.planned_workouts"] == c0["public.planned_workouts"] + 1
        )
        retained = {w["id"]: w for w in prescribed(db, initial["id"])}
        assert all(retained[w["id"]] == w for w in original_prescription)
        old = request(client, "GET", "/weekly-plans/" + initial["id"] + "?revision=1")
        assert old["workouts"] == before["workouts"]
        trace["after"] = after
        # Independent SQL attempts cannot rewrite lineage or append a mapping
        # to an already confirmed revision. Each rejected transaction rolls back.
        membership_before = counts(db)
        attempts = (
            ("update private.v6_revision_memberships set ordinal=ordinal", "42501"),
            ("delete from private.v6_revision_memberships", "42501"),
            (
                "insert into private.v6_revision_memberships "
                "select * from private.v6_revision_memberships limit 1",
                "23514",
            ),
        )
        for sql, code in attempts:
            try:
                db.execute(sql, rollback=True)
            except PlanningRepositoryConflictError as error:
                assert error.code == code, error.code
            else:
                raise AssertionError("Immutable membership accepted an invalid write")
        assert counts(db) == membership_before and evidence(db) == original_evidence
        checks.append(
            "direct lineage updates, deletion and late mapping insertion "
            "reject and roll back"
        )
        checks.append(
            "one completed sibling retains exact original physical FK, "
            "prescription, date, measurement and source basis"
        )
        # Another valid move carries the first moved BIKE as a scheduled sibling.
        third = move(client, after, "swim", "2026-10-31")
        check_mapping(after, third, "swim")
        assert evidence(db) == original_evidence
        bike = next(w for w in third["workouts"] if w["discipline"] == "bike")
        activity2 = measured(client, bike)
        fourth_before = request(client, "GET", "/weekly-plans/" + initial["id"])
        before_second_move = evidence(db)
        fourth = move(client, fourth_before, "swim", "2026-10-30")
        check_mapping(fourth_before, fourth, "swim")
        assert evidence(db) == before_second_move
        assert sum(w["status"] == "completed" for w in fourth["workouts"]) == 2
        trace["multipleCompleted"] = fourth
        # Source processing uses origin revisions, not the new membership revision.
        for activity, origin in [
            (completed, initial["revision_id"]),
            (activity2, after["revision_id"]),
        ]:
            context = db.execute(
                "select public.get_activity_processing_context_v2("
                + literal(USERS[0])
                + ","
                + literal(activity["id"])
                + ")",
                service=True,
            )
            assert context["approved_workout_basis"]["revision_id"] == origin
            assert (
                context["approved_workout_basis"]["planned_method"]
                == "joren-v6-planned-if2-1"
            )
            assert context["selected_realized_v2"]["realized_tss"] is None
            assert (
                context["selected_realized_v2"]["unavailable_reason"]
                == "observation_selected"
            )
        assert {a["id"] for a in request(client, "GET", "/activities")} >= {
            completed["id"],
            activity2["id"],
        }
        checks.append(
            "multiple completed siblings survive successive moves; later "
            "activity uses original source and measured-data priority"
        )
        # Exactly the shared physical IDs are expected, with each measured record once.
        history = db.execute(
            "select jsonb_agg(r) from public.get_plan_load_history_for_planning_v16("
            + literal(USERS[0])
            + ",'2026-11-02') r",
            service=True,
        )
        week = next(r for r in history if r["week_start"] == "2026-10-26")[
            "weekly_registration"
        ]
        assert set(week["expected_occurrences"]) == {
            w["physical_workout_id"] for w in fourth["workouts"]
        }
        assert (
            len(
                [
                    r
                    for r in week["registrations"]
                    if r.get("activity_id") in {completed["id"], activity2["id"]}
                ]
            )
            == 2
        )
        assert (
            db.execute(
                "select to_jsonb(count(*)) from public.activities a left join "
                "public.planned_workouts w on w.id=a.planned_workout_id and "
                "w.athlete_id=a.athlete_id where a.planned_workout_id is not "
                "null and w.id is null"
            )
            == 0
        )
        move(client, fourth, "run", "2026-10-29", expected=409)
        move(client, fourth, "bike", "2026-10-29", expected=409)
        move(client, before, "bike", "2026-10-30", expected=404)
        move(client, fourth, "swim", "2026-11-02", expected=409)
        move(client, fourth, "swim", "2026-10-29", user=USERS[1], expected=404)
        assert evidence(db) == before_second_move
        checks.append(
            "weekly registration expected IDs include original evidence "
            "exactly once; completed/stale/foreign/cross-week moves rejected"
        )
        # Explicit registration, including unknown history, protects its target.
        swim = next(w for w in fourth["workouts"] if w["discipline"] == "swim")
        registration = request(
            client,
            "GET",
            "/planned-workouts/" + swim["physical_workout_id"] + "/registration",
        )
        request(
            client,
            "PUT",
            "/planned-workouts/" + swim["physical_workout_id"] + "/registration",
            body={
                "plan_revision_id": registration["plan_revision_id"],
                "expected_registration_revision": registration["registration_revision"],
                "status": "skipped",
            },
        )
        move(client, fourth, "swim", "2026-10-29", expected=409)
        # A pending proposal created before completion is incompatible afterward.
        active2 = create(client, "2026-11-02", USERS[1])
        cid = prepare_checkin(client, "2026-11-02", USERS[1])
        pending = request(
            client, "POST", "/checkins/" + cid + "/plan-proposals", user=USERS[1]
        )
        measured(
            client,
            next(w for w in active2["workouts"] if w["discipline"] == "run"),
            USERS[1],
        )
        saved_evidence = evidence(db)
        move(client, active2, "bike", "2026-11-08", user=USERS[1], expected=409)
        request(
            client,
            "POST",
            "/change-proposals/" + pending["proposal"]["id"] + "/approve",
            user=USERS[1],
            body={"expected_base_revision": 1},
            expected=409,
        )
        request(
            client,
            "POST",
            "/change-proposals/" + pending["proposal"]["id"] + "/reject",
            user=USERS[1],
        )
        active2 = request(
            client, "GET", "/weekly-plans/" + active2["id"], user=USERS[1]
        )
        moved2 = move(client, active2, "bike", "2026-11-08", USERS[1])
        assert evidence(db) == saved_evidence
        checks.append(
            "incompatible pending confirmation cannot drop recorded "
            "evidence; rejection restores permitted sibling rescheduling"
        )
        # Competing move transactions finish validation before either writes.
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/move_v6_planned_workout"})
        target = next(w for w in moved2["workouts"] if w["discipline"] == "swim")
        url = "/api/v1/planned-workouts/" + target["physical_workout_id"]
        with ThreadPoolExecutor(2) as pool:
            responses = list(
                pool.map(
                    lambda d: client.patch(
                        url,
                        headers=headers(USERS[1]),
                        json={
                            "expected_revision": moved2["revision"],
                            "scheduled_date": d,
                        },
                    ),
                    ["2026-11-06", "2026-11-07"],
                )
            )
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert sorted(r.status_code for r in responses) == [200, 409], [
            (r.status_code, r.text) for r in responses
        ]
        latest = next(r.json() for r in responses if r.status_code == 200)
        assert evidence(db) == saved_evidence
        checks.append(
            "two competing post-activity moves commit only one authoritative revision"
        )
        # Identical operations share one immutable receipt, not two transitions.
        target = next(w for w in latest["workouts"] if w["discipline"] == "bike")
        body = {"expected_revision": latest["revision"], "scheduled_date": "2026-11-07"}
        url = "/api/v1/planned-workouts/" + target["physical_workout_id"]
        c1 = counts(db)
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/move_v6_planned_workout"})
        with ThreadPoolExecutor(2) as pool:
            same = list(
                pool.map(
                    lambda _: client.patch(url, headers=headers(USERS[1]), json=body),
                    range(2),
                )
            )
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert [r.status_code for r in same] == [200, 200], [r.text for r in same]
        assert same[0].json() == same[1].json()
        latest = same[0].json()
        assert counts(db)["public.plan_revisions"] == c1["public.plan_revisions"] + 1
        assert evidence(db) == saved_evidence
        checks.append(
            "duplicate concurrent operation keys recover one exact committed response"
        )
        # Target skip/registration racing move: one may win; no evidence is lost.
        target = next(w for w in latest["workouts"] if w["discipline"] == "swim")
        registration = request(
            client,
            "GET",
            "/planned-workouts/" + target["physical_workout_id"] + "/registration",
            user=USERS[1],
        )
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/confirm_workout_registration"}
        )
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                "/api/v1/planned-workouts/" + target["physical_workout_id"],
                headers=headers(USERS[1]),
                json={
                    "expected_revision": latest["revision"],
                    "scheduled_date": "2026-11-05",
                },
            )
            registering = pool.submit(
                client.put,
                "/api/v1/planned-workouts/"
                + target["physical_workout_id"]
                + "/registration",
                headers=headers(USERS[1]),
                json={
                    "plan_revision_id": registration["plan_revision_id"],
                    "expected_registration_revision": registration[
                        "registration_revision"
                    ],
                    "status": "skipped",
                },
            )
            race = [moving.result(), registering.result()]
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert sum(r.status_code == 200 for r in race) == 1, [
            (r.status_code, r.text) for r in race
        ]
        assert all(r.status_code in {200, 404, 409} for r in race)
        checks.append(
            "move versus target registration serializes and preserves the "
            "winning physical evidence"
        )
        # Pending creation versus move, with an already completed sibling.
        extra = create(client, "2026-09-07", USERS[1])
        measured(
            client,
            next(w for w in extra["workouts"] if w["discipline"] == "run"),
            USERS[1],
        )
        extra = request(client, "GET", "/weekly-plans/" + extra["id"], user=USERS[1])
        cid2 = prepare_checkin(client, "2026-09-07", USERS[1])
        before_race = evidence(db)
        target = next(w for w in extra["workouts"] if w["discipline"] == "bike")
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/create_v6_weekly_plan_proposal"}
        )
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                "/api/v1/planned-workouts/" + target["physical_workout_id"],
                headers=headers(USERS[1]),
                json={
                    "expected_revision": extra["revision"],
                    "scheduled_date": "2026-09-13",
                },
            )
            generating = pool.submit(
                client.post,
                "/api/v1/checkins/" + cid2 + "/plan-proposals",
                headers=headers(USERS[1]),
            )
            raced = [moving.result(), generating.result()]
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert sorted(r.status_code for r in raced) == [200, 409], [
            (r.status_code, r.text) for r in raced
        ]
        assert evidence(db) == before_race
        # Ensure a pending revision exists for the actual confirmation race.
        pending2 = request(
            client, "POST", "/checkins/" + cid2 + "/plan-proposals", user=USERS[1]
        )
        extra = request(client, "GET", "/weekly-plans/" + extra["id"], user=USERS[1])
        target = next(w for w in extra["workouts"] if w["discipline"] == "bike")
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/approve_plan_proposal"}
        )
        c2 = counts(db)
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                "/api/v1/planned-workouts/" + target["physical_workout_id"],
                headers=headers(USERS[1]),
                json={
                    "expected_revision": extra["revision"],
                    "scheduled_date": "2026-09-12",
                },
            )
            confirming = pool.submit(
                client.post,
                "/api/v1/change-proposals/" + pending2["proposal"]["id"] + "/approve",
                headers=headers(USERS[1]),
                json={"expected_base_revision": extra["revision"]},
            )
            raced = [moving.result(), confirming.result()]
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert [r.status_code for r in raced] == [409, 409], [r.text for r in raced]
        assert counts(db) == c2 and evidence(db) == before_race
        request(
            client,
            "POST",
            "/change-proposals/" + pending2["proposal"]["id"] + "/reject",
            user=USERS[1],
        )
        extra = move(client, extra, "bike", "2026-09-12", USERS[1])
        assert evidence(db) == before_race
        checks.append(
            "move versus pending creation is CAS-safe; incompatible confirmation "
            "and move both reject without losing evidence"
        )
        # Actual activity attachment races the target move under the plan lock.
        target = next(w for w in extra["workouts"] if w["discipline"] == "bike")
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/create_activity_summary_v2"}
        )
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                "/api/v1/planned-workouts/" + target["physical_workout_id"],
                headers=headers(USERS[1]),
                json={
                    "expected_revision": extra["revision"],
                    "scheduled_date": "2026-09-13",
                },
            )
            attaching = pool.submit(
                client.post,
                "/api/v1/activities",
                headers={**headers(USERS[1]), "Idempotency-Key": str(uuid4())},
                json={
                    "planned_workout_id": target["physical_workout_id"],
                    "discipline": "bike",
                    "started_at": "2026-09-12T08:00:00+02:00",
                    "timezone": "Europe/Amsterdam",
                    "duration_minutes": "30",
                    "performed_duration_confirmed": True,
                    "metrics": {"zone_minutes": ["30", "0", "0", "0", "0"]},
                },
            )
            raced = [moving.result(), attaching.result()]
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert sum(r.status_code in {200, 201} for r in raced) == 1, [
            (r.status_code, r.text) for r in raced
        ]
        assert all(r.status_code in {200, 201, 404, 409} for r in raced)
        if raced[1].status_code == 201:
            linked = request(
                client, "GET", "/weekly-plans/" + extra["id"], user=USERS[1]
            )
            move(client, linked, "bike", "2026-09-13", user=USERS[1], expected=409)
        else:
            linked = raced[0].json()
            target = next(w for w in linked["workouts"] if w["discipline"] == "bike")
            request(
                client,
                "POST",
                "/activities",
                user=USERS[1],
                expected=201,
                body={
                    "planned_workout_id": target["physical_workout_id"],
                    "discipline": "bike",
                    "started_at": "2026-09-13T08:00:00+02:00",
                    "timezone": "Europe/Amsterdam",
                    "duration_minutes": "30",
                    "performed_duration_confirmed": True,
                    "metrics": {"zone_minutes": ["30", "0", "0", "0", "0"]},
                },
            )
        # A linked sibling awaiting RPE is carried by reference, too.
        linked = request(client, "GET", "/weekly-plans/" + extra["id"], user=USERS[1])
        attached = evidence(db)
        carried = move(client, linked, "swim", "2026-09-11", user=USERS[1])
        check_mapping(linked, carried, "swim")
        assert evidence(db) == attached
        assert (
            db.execute(
                "select to_jsonb(count(*)) from (select planned_workout_id "
                "from public.activities where planned_workout_id is not null "
                "group by planned_workout_id having count(*)>1) duplicate"
            )
            == 0
        )
        checks.append(
            "move versus actual activity attachment has one winner; linked but "
            "unfinished targets remain protected"
        )
        trace["latest"] = request(client, "GET", "/weekly-plans/" + initial["id"])
        trace["calendar"] = request(
            client, "GET", "/calendar?from=2026-10-26&to=2026-11-02"
        )
        trace["activities"] = request(client, "GET", "/activities")
        assert len(trace["calendar"]["workouts"]) == 3
        assert len({w["id"] for w in trace["calendar"]["workouts"]}) == 3
        assert evidence(db)["public.activities"][:2] != []
    output.mkdir(parents=True, exist_ok=False)
    (output / "trace.json").write_text(json.dumps(trace, indent=2) + "\n")
    (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.verify_v6_evidence_rescheduling",
            "--execute-disposable-local-only",
            "--output",
            str(output),
            "--reload",
        ],
        check=True,
    )
    print(
        json.dumps(
            {
                "passed_groups": len(checks),
                "database_transactions": "real",
                "status": "PASS",
            }
        )
    )


def reload(output: Path) -> None:
    trace = json.loads((output / "trace.json").read_text())
    _, client = client_for(LocalPostgres())
    with client:
        assert (
            request(client, "GET", "/weekly-plans/" + trace["latest"]["id"])
            == trace["latest"]
        )
        assert (
            request(client, "GET", "/calendar?from=2026-10-26&to=2026-11-02")
            == trace["calendar"]
        )
        assert request(client, "GET", "/activities") == trace["activities"]
    print(
        "New Python process: original evidence, completed calendar and "
        "new mappings PASS"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        raise SystemExit("Explicit disposable loopback target required")
    (reload if args.reload else run)(args.output)


if __name__ == "__main__":
    main()
