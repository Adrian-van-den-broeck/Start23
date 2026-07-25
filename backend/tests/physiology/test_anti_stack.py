"""Boundary and timezone tests for BR-006 anti-stack intervals."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.modules.physiology.anti_stack import (
    ScheduledWorkout,
    find_anti_stack_violations,
)
from app.modules.physiology.models import Discipline, IntensityBucket


def _workout(
    workout_id: str,
    discipline: Discipline | frozenset[Discipline],
    starts_at: datetime,
    *,
    intensity: IntensityBucket = IntensityBucket.HIGH,
) -> ScheduledWorkout:
    disciplines = (
        discipline if isinstance(discipline, frozenset) else frozenset({discipline})
    )
    return ScheduledWorkout(
        workout_id=workout_id,
        disciplines=disciplines,
        intensity=intensity,
        starts_at=starts_at,
    )


@pytest.mark.parametrize(
    ("discipline", "required_hours"),
    [
        (Discipline.RUN, 72),
        (Discipline.BIKE, 48),
        (Discipline.SWIM, 48),
    ],
)
def test_exact_anti_stack_boundary_is_allowed(
    discipline: Discipline,
    required_hours: int,
) -> None:
    start = datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    result = find_anti_stack_violations(
        (
            _workout("first", discipline, start),
            _workout(
                "second",
                discipline,
                start + timedelta(hours=required_hours),
            ),
        )
    )

    assert result == ()


@pytest.mark.parametrize(
    ("discipline", "required_hours"),
    [
        (Discipline.RUN, 72),
        (Discipline.BIKE, 48),
        (Discipline.SWIM, 48),
    ],
)
def test_one_minute_inside_anti_stack_boundary_is_a_violation(
    discipline: Discipline,
    required_hours: int,
) -> None:
    start = datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    result = find_anti_stack_violations(
        (
            _workout("first", discipline, start),
            _workout(
                "second",
                discipline,
                start + timedelta(hours=required_hours, minutes=-1),
            ),
        )
    )

    assert len(result) == 1
    assert result[0].required_hours == required_hours


def test_low_intensity_and_cross_discipline_workouts_do_not_stack() -> None:
    start = datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    result = find_anti_stack_violations(
        (
            _workout("run-high", Discipline.RUN, start),
            _workout(
                "run-low",
                Discipline.RUN,
                start + timedelta(hours=1),
                intensity=IntensityBucket.LOW,
            ),
            _workout(
                "bike-high",
                Discipline.BIKE,
                start + timedelta(hours=2),
            ),
        )
    )

    assert result == ()


def test_brick_participates_in_each_of_its_disciplines() -> None:
    start = datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    brick = _workout(
        "brick",
        frozenset({Discipline.BIKE, Discipline.RUN}),
        start,
    )
    result = find_anti_stack_violations(
        (
            brick,
            _workout("run", Discipline.RUN, start + timedelta(hours=49)),
            _workout("bike", Discipline.BIKE, start + timedelta(hours=49)),
        )
    )

    assert [(item.discipline, item.later_workout_id) for item in result] == [
        (Discipline.RUN, "run")
    ]


def test_absolute_instants_prevent_dst_from_changing_elapsed_spacing() -> None:
    amsterdam = ZoneInfo("Europe/Amsterdam")
    first = datetime(2026, 3, 28, 10, tzinfo=amsterdam)
    second = datetime(2026, 3, 30, 10, tzinfo=amsterdam)

    result = find_anti_stack_violations(
        (
            _workout("first", Discipline.BIKE, first),
            _workout("second", Discipline.BIKE, second),
        )
    )

    assert len(result) == 1
    assert result[0].actual_interval == timedelta(hours=47)


def test_workout_start_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _workout(
            "naive",
            Discipline.RUN,
            datetime(2026, 1, 1, 8),
        )
