"""Opt-in actual FastAPI + disposable PostgreSQL lifecycle regression.

SQL transport uses new psql connections and simulated claims, never mocked storage.
No GoTrue, Supabase gateway or physical-device verification is claimed.
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.local_v6 import install_local_v6
from app.main import create_app
from app.modules.checkins.repository import (
    CheckInRepositoryConflictError,
    CheckInRepositoryNotFoundError,
    CheckInRepositoryUnavailableError,
    SupabaseCheckInRepository,
)
from app.modules.onboarding.repository import (
    RepositoryNotFoundError,
    SupabaseOnboardingRepository,
)
from app.modules.planning.repository import (
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
    PlanningRepositoryUnavailableError,
)
from app.modules.planning.v6_repository import InactiveSupabaseV6CatalogProvider
from scripts.verify_v6_mobile_lifecycle import SqlActivities
from scripts.verify_v6_postgres import (
    ROOT,
    USERS,
    LocalPostgres,
    SqlRepository,
    TransitionBarrier,
    identity,
    literal,
)


class Checkins(SupabaseCheckInRepository):
    def __init__(self, repo: SqlRepository) -> None:
        super().__init__(
            Settings(environment="test", _env_file=None), client=repo._client
        )
        self.repo = repo

    async def _rpc_athlete_id(self, athlete_id: UUID) -> UUID:
        return await self.repo._rpc_athlete_id(athlete_id)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            return await self.repo._request(method, path, **kwargs)
        except PlanningRepositoryNotFoundError as e:
            raise CheckInRepositoryNotFoundError from e
        except PlanningRepositoryConflictError as e:
            raise CheckInRepositoryConflictError("checkin_context_stale") from e
        except PlanningRepositoryUnavailableError as e:
            raise CheckInRepositoryUnavailableError from e


class Onboarding(SupabaseOnboardingRepository):
    def __init__(self, repo: SqlRepository) -> None:
        super().__init__(
            Settings(environment="test", _env_file=None), client=repo._client
        )
        self.repo = repo

    async def _request(
        self, method: str, path: str, access_token: str, **kwargs: Any
    ) -> Any:
        try:
            return await self.repo._request(
                method, path, access_token=access_token, **kwargs
            )
        except PlanningRepositoryNotFoundError as e:
            raise RepositoryNotFoundError from e


class Verifier:
    def __init__(self, db: LocalPostgres) -> None:
        self.owners = {str(u): identity(db, u) for u in USERS}

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        if access_token not in self.owners:
            raise InvalidAccessTokenError
        return AuthenticatedIdentity(
            UUID(access_token), "authenticated", self.owners[access_token]
        )


class Repository(SqlRepository):
    lose_path: str | None = None
    captured_payload: dict[str, Any] | None = None
    race_barrier: TransitionBarrier | None = None
    race_paths: frozenset[str] = frozenset()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self.race_barrier is not None and path in self.race_paths:
            await self.race_barrier.wait()
        if path in {
            "rpc/create_v6_weekly_plan_proposal",
            "rpc/move_v6_planned_workout",
        }:
            self.captured_payload = kwargs["json"]["p_payload"]
        result = await super()._request(method, path, **kwargs)
        if self.lose_path == path:
            self.lose_path = None
            raise PlanningRepositoryUnavailableError(
                "Withheld committed acknowledgement"
            )
        return result


def client_for(db: LocalPostgres) -> tuple[Repository, TestClient]:
    repo = Repository(db)
    catalog = InactiveSupabaseV6CatalogProvider(repo)
    app = create_app(
        Settings(
            environment="test",
            supabase_url="http://127.0.0.1:55442",
            realized_v2_storage_ready=True,
            realized_v2_selection_enabled=True,
            _env_file=None,
        ),
        access_token_verifier=Verifier(db),
        planning_repository=repo,
        planning_catalog_provider=catalog,
        checkin_repository=Checkins(repo),
        activity_repository=SqlActivities(repo),
        onboarding_repository=Onboarding(repo),
    )
    install_local_v6(app, repo, catalog)
    return repo, TestClient(app)


def headers(user: UUID = USERS[0]) -> dict[str, str]:
    return {"Authorization": "Bearer " + str(user)}


def request(
    client: TestClient,
    method: str,
    path: str,
    *,
    expected: int = 200,
    user: UUID = USERS[0],
    body: Any = None,
) -> Any:
    response = client.request(
        method,
        "/api/v1" + path,
        headers={
            **headers(user),
            "Idempotency-Key": "ca000000-0000-0000-0000-000000000001",
        },
        json=body,
    )
    assert response.status_code == expected, (path, response.status_code, response.text)
    return response.json()


def prepare_checkin(client: TestClient, week: str, user: UUID = USERS[0]) -> str:
    checkin = request(client, "POST", "/checkins", user=user, body={"week_start": week})
    path = "/checkins/" + checkin["id"]
    data = request(
        client,
        "PUT",
        path + "/context",
        user=user,
        body={
            "expected_revision": 0,
            "blocked_dates": [],
            "fatigue_level": "none",
            "missed_workout_reasons": [],
            "recurring_activities_confirmed": True,
            "external_activities": [],
            "restrictions": [
                {
                    "discipline": s,
                    "status": "none",
                    "source": "athlete",
                    "athlete_plan_choice": "resume_unrestricted",
                }
                for s in ["swim", "bike", "run"]
            ],
            "alarm_symptoms_acknowledged": True,
        },
    )
    request(
        client,
        "POST",
        path + "/context-confirmation",
        user=user,
        body={
            "expected_revision": data["context_revision"],
            "context_fingerprint": data["context"]["fingerprint"],
        },
    )
    return str(checkin["id"])


def state(db: LocalPostgres) -> Any:
    return db.execute(
        "select jsonb_build_object('plans',(select count(*) from public.weekly_plans),"
        "'revisions',(select count(*) from public.plan_revisions),'workouts',"
        "(select count(*) from public.planned_workouts),"
        "'receipts',(select count(*) from private.v6_edit_results),'snapshots"
        "',(select count(*) from private.v6_plan_snapshots))"
    )


def snapshot(db: LocalPostgres, revision: str) -> Any:
    return db.execute(
        "select jsonb_build_object('revision',to_jsonb(r)-'state', 'snapshot'"
        ",to_jsonb(s),"
        "'workouts',(select jsonb_agg(to_jsonb(w) order by id) from public.pl"
        "anned_workouts w where revision_id=r.id),"
        "'loads',(select jsonb_agg(to_jsonb(l) order by planned_workout_id) f"
        "rom private.planned_workout_loads l "
        "join public.planned_workouts w on w.id=l.planned_workout_id where w."
        "revision_id=r.id)) "
        "from public.plan_revisions r join private.v6_plan_snapshots s on s.r"
        "evision_id=r.id where r.id=" + literal(revision)
    )


def fail_trigger(
    db: LocalPostgres, table: str, name: str, event: str = "insert"
) -> None:
    db.execute(
        "create function private.lifecycle_test_abort() returns trigger langu"
        "age plpgsql as $$ begin "
        "raise exception 'synthetic interrupted transaction' using errcode='P"
        "T409'; end $$; "
        f"create trigger {name} before {event} on {table} "
        "for each row execute function private.lifecycle_test_abort()"
    )


def remove_trigger(db: LocalPostgres, table: str, name: str) -> None:
    db.execute(
        f"drop trigger {name} on {table}; drop function private.lifecycle_test_abort()"
    )


def run(output: Path) -> None:
    db = LocalPostgres()
    fixture = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text()
    # Explicit opt-in fresh local database; fixtures use normal onboarding completion.
    if not db.execute("select to_jsonb(count(*)) from auth.users"):
        result = subprocess.run(
            ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db.dsn],
            input=fixture,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
        assert result.returncode == 0
    repo, client = client_for(db)
    checks: list[str] = []
    trace: dict[str, Any] = {}
    with client:
        cid = prepare_checkin(client, "2026-10-26")
        url = "/checkins/" + cid + "/plan-proposals"
        before = state(db)
        fail_trigger(
            db, "public.weekly_checkins", "lifecycle_abort_attachment", "update"
        )
        request(client, "POST", url, expected=409)
        remove_trigger(db, "public.weekly_checkins", "lifecycle_abort_attachment")
        assert state(db) == before
        assert request(client, "GET", "/checkins/" + cid)["status"] == "open"
        checks.append(
            "A5 failed attachment rolls back every plan/revision/workout/snapshot"
        )
        repo.lose_path = "rpc/create_v6_weekly_plan_proposal"
        request(client, "POST", url, expected=503)
        pending = request(client, "POST", url)
        assert pending == request(client, "POST", url)
        assert len(pending["plan"]["workouts"]) == 3
        assert all(w["source_prescription"] for w in pending["plan"]["workouts"])
        linked = request(client, "GET", "/checkins/" + cid)
        assert (
            linked["plan_proposal_id"] == pending["proposal"]["id"]
            and linked["status"] == "completed"
        )
        checks.append(
            "A5 lost commit acknowledgement replays one authoritative frozen proposal"
        )
        trace["checkinPending"] = pending["plan"]
        request(client, "POST", url, user=USERS[1], expected=404)
        assert (
            request(client, "GET", "/calendar?from=2026-10-26&to=2026-11-02")[
                "workouts"
            ]
            == []
        )
        request(
            client,
            "POST",
            "/change-proposals/" + pending["proposal"]["id"] + "/approve",
            body={"expected_base_revision": 0},
        )
        active = request(client, "GET", "/weekly-plans/" + pending["plan"]["id"])
        assert request(client, "POST", url)["proposal"]["state"] == "applied"
        checks.append(
            "explicit A5 approval activates V6 calendar; foreign attachment denied"
        )
        trace["beforeMove"] = active
        old = snapshot(db, active["revision_id"])
        target = next(w for w in active["workouts"] if w["discipline"] == "bike")
        physical = target["physical_workout_id"]
        move = "/planned-workouts/" + physical
        body = {"expected_revision": active["revision"], "scheduled_date": "2026-11-01"}
        request(client, "PATCH", move, user=USERS[1], body=body, expected=404)
        request(
            client, "PATCH", move, body={**body, "expected_revision": 9}, expected=409
        )
        request(
            client,
            "PATCH",
            move,
            body={**body, "scheduled_date": "2026-11-02"},
            expected=409,
        )
        before = state(db)
        fail_trigger(db, "private.v6_edit_results", "lifecycle_abort_move")
        request(client, "PATCH", move, body=body, expected=409)
        remove_trigger(db, "private.v6_edit_results", "lifecycle_abort_move")
        assert state(db) == before and snapshot(db, active["revision_id"]) == old
        assert request(client, "GET", "/weekly-plans/" + active["id"]) == active
        checks.append(
            "move interruption after pointer update rolls back all writes; stale/"
            "foreign/outside week denied"
        )
        repo.lose_path = "rpc/move_v6_planned_workout"
        request(client, "PATCH", move, body=body, expected=503)
        moved = request(client, "PATCH", move, body=body)
        assert moved == request(client, "PATCH", move, body=body)
        assert (
            moved["revision"] == active["revision"] + 1
            and moved["revision_state"] == "active"
        )
        assert {w["id"] for w in active["workouts"]} == {
            w["id"] for w in moved["workouts"]
        }
        for previous in active["workouts"]:
            new = next(w for w in moved["workouts"] if w["id"] == previous["id"])
            assert new["physical_workout_id"] != previous["physical_workout_id"]
            for key in previous.keys() - {"scheduled_date", "physical_workout_id"}:
                assert previous[key] == new[key], key
            assert new["scheduled_date"] == (
                "2026-11-01"
                if previous["id"] == target["id"]
                else previous["scheduled_date"]
            )
        assert snapshot(db, active["revision_id"]) == old
        newer = snapshot(db, moved["revision_id"])
        assert newer["snapshot"]["input_snapshot"] == old["snapshot"]["input_snapshot"]
        old_payload, new_payload = (
            old["snapshot"]["payload"],
            newer["snapshot"]["payload"],
        )
        assert {k: v for k, v in old_payload.items() if k != "workouts"} == {
            k: v for k, v in new_payload.items() if k != "workouts"
        }
        assert sorted(
            str({k: v for k, v in row.items() if k != "planned_workout_id"})
            for row in old["loads"]
        ) == sorted(
            str({k: v for k, v in row.items() if k != "planned_workout_id"})
            for row in newer["loads"]
        )
        checks.append(
            "confirmed move retains exact source/prescription/logical IDs; old ph"
            "ysical rows immutable; identical replay"
        )
        trace["afterMove"] = moved
        # A repeated old receipt stays exact after another move (logical route).
        other = next(w for w in moved["workouts"] if w["discipline"] == "run")
        race = "/planned-workouts/" + other["id"]
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/move_v6_planned_workout"})
        with ThreadPoolExecutor(2) as pool:
            responses = list(
                pool.map(
                    lambda d: client.patch(
                        "/api/v1" + race,
                        headers=headers(),
                        json={
                            "expected_revision": moved["revision"],
                            "scheduled_date": d,
                        },
                    ),
                    ["2026-10-30", "2026-10-31"],
                )
            )
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        assert sorted(r.status_code for r in responses) == [200, 409], [
            (r.status_code, r.text) for r in responses
        ]
        latest = next(r.json() for r in responses if r.status_code == 200)
        assert request(client, "PATCH", move, body=body) == moved
        checks.append(
            "two concurrent date moves commit exactly one new authoritative revis"
            "ion; old receipt remains exact"
        )
        # Attach to the latest exact physical row, retaining measured-data priority.
        bike = next(w for w in latest["workouts"] if w["id"] == target["id"])
        activity = request(
            client,
            "POST",
            "/activities",
            expected=201,
            body={
                "planned_workout_id": bike["physical_workout_id"],
                "discipline": "bike",
                "started_at": "2026-11-01T10:00:00+01:00",
                "timezone": "Europe/Amsterdam",
                "duration_minutes": "30",
                "performed_duration_confirmed": True,
                "metrics": {"zone_minutes": ["30", "0", "0", "0", "0"]},
            },
        )
        request(
            client, "PUT", "/activities/" + activity["id"] + "/rpe", body={"rpe": 3}
        )
        assert activity["planned_workout_id"] == bike["physical_workout_id"]
        recorded = snapshot(db, latest["revision_id"])
        request(
            client,
            "PATCH",
            "/planned-workouts/" + bike["id"],
            body={
                "expected_revision": latest["revision"],
                "scheduled_date": "2026-10-29",
            },
            expected=409,
        )
        assert snapshot(db, latest["revision_id"]) == recorded
        checks.append(
            "supported measured activity binds new physical/source occurrence; co"
            "mpleted evidence blocks further moves"
        )
        # An active week plus a pending check-in must not lose a swipe/approval.
        initial = request(
            client,
            "POST",
            "/weekly-plans/proposals",
            expected=201,
            user=USERS[1],
            body={
                "week_start": "2026-11-02",
                "available_dates": [
                    "2026-11-02",
                    "2026-11-03",
                    "2026-11-04",
                    "2026-11-05",
                    "2026-11-06",
                    "2026-11-07",
                    "2026-11-08",
                ],
            },
        )
        request(
            client,
            "POST",
            "/change-proposals/" + initial["proposal"]["id"] + "/approve",
            user=USERS[1],
            body={"expected_base_revision": 0},
        )
        cid2 = prepare_checkin(client, "2026-11-02", USERS[1])
        url2 = "/checkins/" + cid2 + "/plan-proposals"
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset({"rpc/create_v6_weekly_plan_proposal"})
        with ThreadPoolExecutor(2) as pool:
            proposals = list(
                pool.map(
                    lambda _: request(client, "POST", url2, user=USERS[1]), range(2)
                )
            )
        assert proposals[0] == proposals[1]
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        pending2 = proposals[0]["plan"]
        active_workout = initial["plan"]["workouts"][0]
        edit_workout = pending2["workouts"][0]
        move_path = "/api/v1/planned-workouts/" + active_workout["physical_workout_id"]
        edit_path = (
            "/api/v1/weekly-plans/"
            + pending2["id"]
            + "/pending-workouts/"
            + edit_workout["id"]
            + "/edit-proposals"
        )
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/create_v6_weekly_plan_proposal"}
        )
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                move_path,
                headers=headers(USERS[1]),
                json={"expected_revision": 1, "scheduled_date": "2026-11-08"},
            )
            editing = pool.submit(
                client.post,
                edit_path,
                headers=headers(USERS[1]),
                json={
                    "expected_revision": pending2["revision"],
                    "expected_proposal_id": pending2["proposal"]["id"],
                    "replacement_template_id": edit_workout["template_id"],
                },
            )
            move_result, edit_result = moving.result(), editing.result()
        assert move_result.status_code == 409, move_result.text
        assert edit_result.status_code == 201, edit_result.text
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        edited2 = edit_result.json()["plan"]
        repo.race_barrier = TransitionBarrier()
        repo.race_paths = frozenset(
            {"rpc/move_v6_planned_workout", "rpc/approve_plan_proposal"}
        )
        with ThreadPoolExecutor(2) as pool:
            moving = pool.submit(
                client.patch,
                move_path,
                headers=headers(USERS[1]),
                json={"expected_revision": 1, "scheduled_date": "2026-11-08"},
            )
            confirming = pool.submit(
                client.post,
                "/api/v1/change-proposals/" + edited2["proposal"]["id"] + "/approve",
                headers=headers(USERS[1]),
                json={"expected_base_revision": 1},
            )
            move_result, confirmation = moving.result(), confirming.result()
        assert move_result.status_code in {404, 409}, move_result.text
        assert confirmation.status_code == 200, confirmation.text
        assert repo.race_barrier.arrivals == 2
        repo.race_barrier = None
        checks.append("move versus pending edit and confirmation is stale-safe")
        assert (
            request(client, "POST", url2, user=USERS[1])["proposal"]["state"]
            == "expired"
        )
        cid3 = prepare_checkin(client, "2026-11-09", USERS[1])
        url3 = "/checkins/" + cid3 + "/plan-proposals"
        rejected = request(client, "POST", url3, user=USERS[1])
        request(
            client,
            "POST",
            "/change-proposals/" + rejected["proposal"]["id"] + "/reject",
            user=USERS[1],
        )
        assert (
            request(client, "POST", url3, user=USERS[1])["proposal"]["state"]
            == "rejected"
        )
        checks.append(
            "concurrent duplicate check-ins converge; rejection recovery preserve"
            "s terminal authoritative state"
        )
        trace["latest"] = request(client, "GET", "/weekly-plans/" + active["id"])
        trace["calendar"] = request(
            client, "GET", "/calendar?from=2026-10-26&to=2026-11-02"
        )
        assert {w["id"] for w in trace["calendar"]["workouts"]} == {
            w["id"] for w in latest["workouts"]
        }
    output.mkdir(parents=True, exist_ok=False)
    (output / "trace.json").write_text(json.dumps(trace, indent=2) + "\n")
    (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.verify_v6_lifecycle_completion",
            "--execute-disposable-local-only",
            "--private-output",
            str(output),
            "--reload",
        ],
        check=True,
    )
    print(json.dumps({"checks": len(checks), "status": "PASS"}))


def reload(output: Path) -> None:
    trace = json.loads((output / "trace.json").read_text())
    db = LocalPostgres()
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
        old = trace["beforeMove"]["workouts"][0]
        request(
            client,
            "PATCH",
            "/planned-workouts/" + old["physical_workout_id"],
            body={
                "expected_revision": trace["beforeMove"]["revision"],
                "scheduled_date": "2026-10-29",
            },
            expected=404,
        )
        rejected = db.execute(
            "select jsonb_build_object('id',w.id,'revision',r.revision_number,"
            "'date',w.scheduled_date) from public.planned_workouts w "
            "join public.plan_revisions r on r.id=w.revision_id "
            "where r.state='rejected' limit 1"
        )
        assert rejected is not None
        request(
            client,
            "PATCH",
            "/planned-workouts/" + rejected["id"],
            user=USERS[1],
            body={
                "expected_revision": rejected["revision"],
                "scheduled_date": rejected["date"],
            },
            expected=404,
        )
    print(
        "Independent Python process + fresh SQL connections: confirmed calend"
        "ar reload PASS"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        raise SystemExit("Explicit disposable database opt-in required")
    (reload if args.reload else run)(args.private_output)


if __name__ == "__main__":
    main()
