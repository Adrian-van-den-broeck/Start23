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


@pytest.mark.parametrize("discipline", [Discipline.BIKE, Discipline.SWIM])
def test_48_hour_rule_requires_two_complete_local_rest_dates(
    discipline: Discipline,
) -> None:
    amsterdam = ZoneInfo("Europe/Amsterdam")
    wednesday = datetime(2026, 8, 5, 12, tzinfo=amsterdam)
    friday = datetime(2026, 8, 7, 12, tzinfo=amsterdam)
    saturday = datetime(2026, 8, 8, 12, tzinfo=amsterdam)

    too_early = find_anti_stack_violations(
        (
            _workout("first", discipline, wednesday),
            _workout("second", discipline, friday),
        )
    )
    allowed = find_anti_stack_violations(
        (
            _workout("first", discipline, wednesday),
            _workout("second", discipline, saturday),
        )
    )

    assert len(too_early) == 1
    assert too_early[0].required_complete_rest_dates == 2
    assert too_early[0].actual_complete_rest_dates == 1
    assert allowed == ()


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
        (Discipline.RUN, "run"),
        (Discipline.BIKE, "bike"),
    ]


def test_spring_dst_does_not_shorten_calendar_date_spacing() -> None:
    amsterdam = ZoneInfo("Europe/Amsterdam")
    first = datetime(2026, 3, 28, 10, tzinfo=amsterdam)
    second = datetime(2026, 3, 31, 10, tzinfo=amsterdam)

    result = find_anti_stack_violations(
        (
            _workout("first", Discipline.BIKE, first),
            _workout("second", Discipline.BIKE, second),
        )
    )

    assert result == ()
    assert second.astimezone(timezone.utc) - first.astimezone(
        timezone.utc
    ) == timedelta(hours=71)


def test_fall_dst_does_not_replace_two_complete_rest_dates() -> None:
    amsterdam = ZoneInfo("Europe/Amsterdam")
    first = datetime(2026, 10, 24, 10, tzinfo=amsterdam)
    second = datetime(2026, 10, 26, 10, tzinfo=amsterdam)

    result = find_anti_stack_violations(
        (
            _workout("first", Discipline.BIKE, first),
            _workout("second", Discipline.BIKE, second),
        )
    )

    assert len(result) == 1
    assert result[0].actual_complete_rest_dates == 1
    assert second.astimezone(timezone.utc) - first.astimezone(
        timezone.utc
    ) == timedelta(hours=49)


def test_workout_start_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _workout(
            "naive",
            Discipline.RUN,
            datetime(2026, 1, 1, 8),
        )


def test_workout_identifier_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="identifier cannot be blank"):
        _workout(
            " ",
            Discipline.RUN,
            datetime(2026, 1, 1, 8, tzinfo=timezone.utc),
        )


def test_workout_requires_at_least_one_discipline() -> None:
    with pytest.raises(ValueError, match="at least one discipline"):
        _workout(
            "empty",
            frozenset(),
            datetime(2026, 1, 1, 8, tzinfo=timezone.utc),
        )
