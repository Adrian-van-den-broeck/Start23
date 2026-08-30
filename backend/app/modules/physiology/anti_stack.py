"""BR-006 deterministic high-intensity spacing validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PHASE_10_RULESET_V1,
    PhysiologySpecification,
)

_REQUIRED_HOURS = {
    Discipline.RUN: 72,
    Discipline.BIKE: 48,
    Discipline.SWIM: 48,
}


@dataclass(frozen=True, slots=True)
class ScheduledWorkout:
    """Minimum schedule facts needed for anti-stack validation."""

    workout_id: str
    disciplines: frozenset[Discipline]
    intensity: IntensityBucket
    starts_at: datetime

    def __post_init__(self) -> None:
        if not self.workout_id.strip():
            raise ValueError("Workout identifier cannot be blank.")
        if not self.disciplines:
            raise ValueError("A workout requires at least one discipline.")
        if self.starts_at.tzinfo is None or self.starts_at.utcoffset() is None:
            raise ValueError("Workout start time must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class AntiStackViolation:
    """One same-discipline interval below the approved minimum."""

    ruleset_version: RulesetVersion
    discipline: Discipline
    earlier_workout_id: str
    later_workout_id: str
    required_hours: int
    actual_interval: timedelta
    required_complete_rest_dates: int | None = None
    actual_complete_rest_dates: int | None = None


def find_anti_stack_violations(
    workouts: tuple[ScheduledWorkout, ...],
    *,
    specification: PhysiologySpecification = PHASE_10_RULESET_V1,
) -> tuple[AntiStackViolation, ...]:
    """Apply the approved mixed elapsed-hour/local-rest-date BR-006 policy."""
    specification.require_approved(frozenset({RuleId.ANTI_STACK}))

    violations: list[AntiStackViolation] = []
    for discipline, required_hours in _REQUIRED_HOURS.items():
        relevant = sorted(
            (
                workout
                for workout in workouts
                if workout.intensity is IntensityBucket.HIGH
                and discipline in workout.disciplines
            ),
            key=lambda workout: workout.starts_at.astimezone(timezone.utc),
        )
        for earlier, later in zip(relevant, relevant[1:], strict=False):
            interval = later.starts_at.astimezone(
                timezone.utc
            ) - earlier.starts_at.astimezone(timezone.utc)
            complete_rest_dates = (
                later.starts_at.date() - earlier.starts_at.date()
            ).days - 1
            uses_local_rest_dates = required_hours == 48
            violates = (
                complete_rest_dates < 2
                if uses_local_rest_dates
                else interval < timedelta(hours=required_hours)
            )
            if violates:
                violations.append(
                    AntiStackViolation(
                        ruleset_version=specification.version,
                        discipline=discipline,
                        earlier_workout_id=earlier.workout_id,
                        later_workout_id=later.workout_id,
                        required_hours=required_hours,
                        actual_interval=interval,
                        required_complete_rest_dates=(
                            2 if uses_local_rest_dates else None
                        ),
                        actual_complete_rest_dates=(
                            complete_rest_dates if uses_local_rest_dates else None
                        ),
                    )
                )
    return tuple(violations)
