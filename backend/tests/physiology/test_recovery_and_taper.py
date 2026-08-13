"""Boundary tests for BR-007 recovery and BR-008 taper rules."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfoNotFoundError

import pytest

from app.modules.physiology.models import InternalLoad
from app.modules.physiology.progression import WeeklyLoad
from app.modules.physiology.recovery import (
    WeekPhase,
    calculate_recovery_target,
    forward_mesocycle_phase,
    resolve_week_phase,
    retrospective_mesocycle_phase,
)
from app.modules.physiology.taper import (
    RaceEvent,
    RacePriority,
    TaperPeriod,
    athlete_week_bounds,
    calculate_taper_baseline,
    calculate_taper_target,
    select_controlling_race,
)


def _load(value: str) -> InternalLoad:
    return InternalLoad(Decimal(value))


def test_forward_cycle_marks_each_fifth_week_as_recovery() -> None:
    phases = [forward_mesocycle_phase(week) for week in range(1, 11)]

    assert phases == [
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.RECOVERY,
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.BUILD,
        WeekPhase.RECOVERY,
    ]


def test_eight_week_retrospective_example_has_recovery_weeks_three_and_eight() -> None:
    recovery_weeks = [
        week
        for week in range(1, 9)
        if retrospective_mesocycle_phase(
            week_number=week,
            total_weeks_to_a_race=8,
        )
        is WeekPhase.RECOVERY
    ]

    assert recovery_weeks == [3, 8]


def test_taper_overrides_recovery() -> None:
    assert resolve_week_phase(recovery_due=True, taper_due=True) is WeekPhase.TAPER


def test_recovery_target_defaults_to_exactly_60_percent() -> None:
    result = calculate_recovery_target(week_four_planned=_load("100"))

    assert result.factor == Decimal("0.60")
    assert result.target.value == Decimal("60.00")


def test_recovery_target_allows_approved_40_to_60_percent_range() -> None:
    lower = calculate_recovery_target(
        week_four_planned=_load("100"),
        factor=Decimal("0.40"),
    )

    assert lower.target.value == Decimal("40.00")
    with pytest.raises(ValueError, match="between 0.40 and 0.60"):
        calculate_recovery_target(
            week_four_planned=_load("100"),
            factor=Decimal("0.61"),
        )


@pytest.mark.parametrize("week_number", [0, -1])
def test_forward_cycle_rejects_invalid_week_numbers(week_number: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        forward_mesocycle_phase(week_number)


@pytest.mark.parametrize(
    ("week_number", "total_weeks"),
    [(1, 0), (0, 8), (9, 8)],
)
def test_retrospective_cycle_rejects_invalid_horizons(
    week_number: int,
    total_weeks: int,
) -> None:
    with pytest.raises(ValueError):
        retrospective_mesocycle_phase(
            week_number=week_number,
            total_weeks_to_a_race=total_weeks,
        )


@pytest.mark.parametrize("factor", [Decimal("0.39"), Decimal("NaN")])
def test_recovery_target_rejects_invalid_factors(factor: Decimal) -> None:
    with pytest.raises(ValueError, match="between 0.40 and 0.60"):
        calculate_recovery_target(
            week_four_planned=_load("100"),
            factor=factor,
        )


def test_taper_baseline_uses_available_42_days_and_excludes_recovery() -> None:
    as_of = date(2026, 7, 26)
    samples = (
        WeeklyLoad(week_start=date(2026, 7, 20), load=_load("100")),
        WeeklyLoad(week_start=date(2026, 7, 13), load=_load("0")),
        WeeklyLoad(
            week_start=date(2026, 7, 6),
            load=_load("900"),
            is_recovery_week=True,
        ),
    )

    result = calculate_taper_baseline(samples, as_of=as_of)

    assert result is not None
    assert result.value == Decimal("50")


@pytest.mark.parametrize(
    ("priority", "period", "expected"),
    [
        (RacePriority.A, TaperPeriod.A_T_MINUS_2, Decimal("60.00")),
        (RacePriority.A, TaperPeriod.A_T_MINUS_1, Decimal("35.00")),
        (RacePriority.B, TaperPeriod.B_TAPER_WEEK, Decimal("50.00")),
    ],
)
def test_approved_taper_targets(
    priority: RacePriority,
    period: TaperPeriod,
    expected: Decimal,
) -> None:
    result = calculate_taper_target(
        priority=priority,
        period=period,
        baseline=_load("100"),
    )

    assert result is not None
    assert result.target.value == expected


def test_c_race_has_no_taper() -> None:
    assert (
        calculate_taper_target(
            priority=RacePriority.C,
            period=None,
            baseline=_load("100"),
        )
        is None
    )


@pytest.mark.parametrize(
    ("priority", "period"),
    [
        (RacePriority.A, TaperPeriod.B_TAPER_WEEK),
        (RacePriority.B, TaperPeriod.A_T_MINUS_1),
        (RacePriority.C, TaperPeriod.B_TAPER_WEEK),
    ],
)
def test_invalid_priority_period_combinations_are_rejected(
    priority: RacePriority,
    period: TaperPeriod,
) -> None:
    with pytest.raises(ValueError):
        calculate_taper_target(
            priority=priority,
            period=period,
            baseline=_load("100"),
        )


def test_race_hierarchy_controls_overlapping_tapers() -> None:
    base = datetime(2026, 8, 1, tzinfo=timezone.utc)
    races = (
        RaceEvent("b", RacePriority.B, base),
        RaceEvent("a-later", RacePriority.A, base + timedelta(days=7)),
        RaceEvent("a-earlier", RacePriority.A, base + timedelta(days=2)),
    )

    result = select_controlling_race(races)

    assert result is not None
    assert result.race_id == "a-earlier"


def test_athlete_week_is_monday_to_sunday_in_local_timezone() -> None:
    sunday_utc = datetime(2026, 7, 26, 22, 30, tzinfo=timezone.utc)

    assert athlete_week_bounds(
        sunday_utc,
        timezone_name="Europe/Amsterdam",
    ) == (date(2026, 7, 27), date(2026, 8, 2))


def test_race_requires_identifier_and_timezone_aware_start() -> None:
    aware = datetime(2026, 8, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="identifier cannot be blank"):
        RaceEvent(" ", RacePriority.A, aware)
    with pytest.raises(ValueError, match="timezone-aware"):
        RaceEvent("race", RacePriority.A, datetime(2026, 8, 1))


def test_athlete_week_rejects_naive_instant() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        athlete_week_bounds(
            datetime(2026, 7, 26, 22, 30),
            timezone_name="Europe/Amsterdam",
        )


def test_athlete_week_rejects_unknown_timezone() -> None:
    with pytest.raises(ZoneInfoNotFoundError, match="No time zone found"):
        athlete_week_bounds(
            datetime(2026, 7, 26, 22, 30, tzinfo=timezone.utc),
            timezone_name="Not/A_Timezone",
        )
