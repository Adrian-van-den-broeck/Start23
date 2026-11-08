"""Opt-in local PG calendar/activity verification after verify_v6_postgres stages.

No HTTP/Auth/gateway claim: actual SQL roles and transactions, synthetic users.
Never reads .env or uses a hosted connection. Public-only result ledger.
"""

import argparse
import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.core.config import Settings
from app.modules.activities.repository import SupabaseActivityRepository
from app.modules.activities.schemas import (
    ActivityRpeSubmission,
    ActivitySummaryInput,
    WorkoutRegistrationConfirmation,
)
from app.modules.activities.service import ActivityService
from app.modules.planning.domain import PlanningConstraintError
from app.modules.planning.repository import PlanningRepositoryNotFoundError
from app.modules.planning.schemas import PlannedWorkoutMoveRequest
from scripts.verify_v6_postgres import (
    USERS,
    LocalPostgres,
    SqlRepository,
    identity,
    service,
)


class SqlActivities(SupabaseActivityRepository):
    def __init__(self, repository: SqlRepository) -> None:
        super().__init__(
            Settings(
                environment="test",
                _env_file=None,
                realized_v2_storage_ready=True,
                realized_v2_selection_enabled=True,
            ),
            client=repository._client,
        )
        self.planning = repository

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return await self.planning._request(method, path, **kwargs)

    async def _rpc_athlete_id(self, athlete_id: UUID) -> UUID:
        return await self.planning._rpc_athlete_id(athlete_id)


async def verify(snapshot: Path, output: Path) -> None:
    db = LocalPostgres()
    expected = json.loads(snapshot.read_text(encoding="utf-8"))
    repo, planner = service(db)
    owner = identity(db, USERS[0])
    plan = await planner.get_plan(
        str(USERS[0]), UUID(expected["id"]), expected["revision"]
    )

    def immutable_plan(value: dict[str, Any]) -> dict[str, Any]:
        return {
            **value,
            "workouts": [
                {k: v for k, v in row.items() if k != "status"}
                for row in value["workouts"]
            ],
        }

    assert immutable_plan(plan.model_dump(mode="json")) == immutable_plan(expected)
    calendar = await planner.get_calendar(
        str(USERS[0]), date(2026, 10, 26), date(2026, 11, 2)
    )
    assert {w.id for w in calendar.workouts} == {w.id for w in plan.workouts}
    assert len(calendar.workouts) == 3
    for w in calendar.workouts:
        assert w.physical_workout_id is not None and w.physical_workout_id != w.id
        mapping = db.execute(
            "select jsonb_build_object('logical', occurrence_id, "
            "'revision', revision_id) "
            "from private.v6_occurrence_snapshots where planned_workout_id = '"
            + str(w.physical_workout_id)
            + "'"
        )
        assert mapping == {"logical": str(w.id), "revision": str(plan.revision_id)}
        assert w.source_prescription is not None
    foreign = await planner.get_calendar(
        str(USERS[1]), date(2026, 10, 26), date(2026, 11, 2)
    )
    assert foreign.workouts == ()
    try:
        await planner.get_plan(str(USERS[1]), plan.id, plan.revision)
    except PlanningRepositoryNotFoundError:
        pass
    else:
        raise AssertionError("foreign plan was visible")
    workout = next(w for w in plan.workouts if w.discipline.value == "bike")
    assert workout.physical_workout_id is not None
    activities = ActivityService(SqlActivities(repo), enable_estimates=True)

    def existing_key(physical: UUID | None) -> UUID:
        value = db.execute(
            "select to_jsonb(idempotency_key) from public.activities "
            "where athlete_id = '"
            + str(USERS[0])
            + "' and planned_workout_id = '"
            + str(physical)
            + "' limit 1"
        )
        return UUID(value) if value else uuid4()

    key = existing_key(workout.physical_workout_id)
    summary = ActivitySummaryInput.model_validate(
        {
            "planned_workout_id": str(workout.physical_workout_id),
            "discipline": "bike",
            "started_at": "2026-10-26T10:00:00+01:00",
            "timezone": "Europe/Amsterdam",
            "duration_minutes": "30",
            "performed_duration_confirmed": True,
            "metrics": {"zone_minutes": ["30", "0", "0", "0", "0"]},
        }
    )
    saved = await activities.create(str(USERS[0]), key, summary)
    assert saved == await activities.create(str(USERS[0]), key, summary)
    assert saved.planned_workout_id == workout.physical_workout_id
    context = await activities._repository.fetch_processing_context(owner, saved.id)
    assert (
        context["approved_workout_basis"]["planned_method"] == "joren-v6-planned-if2-1"
    )
    completed = (
        saved
        if saved.rpe is not None
        else await activities.submit_rpe(owner, saved.id, ActivityRpeSubmission(rpe=3))
    )
    assert completed.planned_workout_id == workout.physical_workout_id
    assert str(completed.duration_minutes) == "30"
    reloaded = await activities.get(str(USERS[0]), saved.id)
    assert reloaded == completed
    updated = await planner.get_calendar(
        str(USERS[0]), date(2026, 10, 26), date(2026, 11, 2)
    )
    assert next(w for w in updated.workouts if w.id == workout.id).status == "completed"
    try:
        await planner.move_workout(
            str(USERS[0]),
            owner,
            workout.physical_workout_id,
            PlannedWorkoutMoveRequest(
                expected_revision=plan.revision, scheduled_date=workout.scheduled_date
            ),
        )
    except PlanningConstraintError as error:
        assert error.code == "recorded_workout_move_unsupported"
    else:
        raise AssertionError("completed workout date move unexpectedly succeeded")
    run = next(w for w in plan.workouts if w.discipline.value == "run")
    unsupported = await activities.create(
        str(USERS[0]),
        existing_key(run.physical_workout_id),
        ActivitySummaryInput.model_validate(
            {
                "planned_workout_id": str(run.physical_workout_id),
                "discipline": "run",
                "started_at": "2026-10-31T10:00:00+01:00",
                "timezone": "Europe/Amsterdam",
                "duration_minutes": "10",
                "performed_duration_confirmed": True,
            }
        ),
    )
    if unsupported.rpe is None:
        await activities.submit_rpe(owner, unsupported.id, ActivityRpeSubmission(rpe=3))
    rejected = await activities._repository.fetch_processing_context(
        owner, unsupported.id
    )
    selected = rejected["selected_realized_v2"]
    assert selected["unavailable_reason"] == "unsupported_planned_method_version"
    assert selected["realized_tss"] is None and selected["planner_eligible"] is False
    swim = next(w for w in plan.workouts if w.discipline.value == "swim")
    assert swim.physical_workout_id is not None
    registration = await activities.workout_registration(
        str(USERS[0]), swim.physical_workout_id
    )
    assert registration.plan_revision_id == plan.revision_id
    skipped = await activities.workout_registration(
        str(USERS[0]),
        swim.physical_workout_id,
        WorkoutRegistrationConfirmation(
            plan_revision_id=registration.plan_revision_id,
            expected_registration_revision=registration.registration_revision,
            status="skipped",
        ),
    )
    assert skipped.status == "skipped"
    restored = await activities.workout_registration(
        str(USERS[0]),
        swim.physical_workout_id,
        WorkoutRegistrationConfirmation(
            plan_revision_id=skipped.plan_revision_id,
            expected_registration_revision=skipped.registration_revision,
            status="unknown",
        ),
    )
    assert restored.status == "unknown"
    output.write_text(
        json.dumps(
            {
                "evidence": "real PostgreSQL / simulated JWT claims / synthetic users",
                "check_groups_passed": 14,
                "calendar_identity": True,
                "exact_mapping": True,
                "restart_read": True,
                "source_blocks": True,
                "account_isolation": True,
                "immutable_move_rejected": True,
                "activity_exact_attachment": True,
                "activity_retry": True,
                "source_method_preserved": True,
                "measured_processing": True,
                "completed_calendar": True,
                "activity_reload": True,
                "unsupported_fallback_rejected": True,
                "physical_registration_skip_undo": True,
                "gotrue_sessions": 0,
                "gateway_checks": 0,
                "device_checks": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    await repo._client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        raise SystemExit("Explicit disposable database authorization required")
    asyncio.run(verify(args.snapshot, args.output))


if __name__ == "__main__":
    main()
