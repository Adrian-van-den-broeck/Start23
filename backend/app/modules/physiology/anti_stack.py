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
    PHASE_3_RULESET_V1,
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


def find_anti_stack_violations(
    workouts: tuple[ScheduledWorkout, ...],
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> tuple[AntiStackViolation, ...]:
    """Compare high-intensity workout starts as absolute UTC instants."""
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
            if interval < timedelta(hours=required_hours):
                violations.append(
                    AntiStackViolation(
                        ruleset_version=specification.version,
                        discipline=discipline,
                        earlier_workout_id=earlier.workout_id,
                        later_workout_id=later.workout_id,
                        required_hours=required_hours,
                        actual_interval=interval,
                    )
                )
    return tuple(violations)
