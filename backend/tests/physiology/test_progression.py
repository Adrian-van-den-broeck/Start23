"""Boundary tests for BR-004 progression and the 42-day baseline."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.physiology.models import DurationMinutes, InternalLoad
from app.modules.physiology.progression import (
    ProgressionBasis,
    WeeklyLoad,
    calculate_42_day_average,
    calculate_progressive_target,
    snapshot_personalized_load,
)


def _load(value: str) -> InternalLoad:
    return InternalLoad(Decimal(value))


def test_42_day_model_includes_zero_and_uses_only_available_samples() -> None:
    as_of = date(2026, 7, 26)
    samples = (
        WeeklyLoad(week_start=date(2026, 6, 8), load=_load("1000")),
        WeeklyLoad(week_start=date(2026, 6, 15), load=_load("0")),
        WeeklyLoad(week_start=date(2026, 7, 20), load=_load("20")),
    )

    result = calculate_42_day_average(samples, as_of=as_of)

    assert result is not None
    assert result.value == Decimal("10")


def test_42_day_model_can_exclude_recovery_samples() -> None:
    as_of = date(2026, 7, 26)
    samples = (
        WeeklyLoad(week_start=date(2026, 7, 20), load=_load("20")),
        WeeklyLoad(
            week_start=date(2026, 7, 13),
            load=_load("1000"),
            is_recovery_week=True,
        ),
    )

    result = calculate_42_day_average(
        samples,
        as_of=as_of,
        exclude_recovery_weeks=True,
    )

    assert result is not None
    assert result.value == Decimal("20")


def test_42_day_model_returns_none_without_available_history() -> None:
    result = calculate_42_day_average((), as_of=date(2026, 7, 25))

    assert result is None


def test_42_day_model_rejects_duplicate_calendar_days() -> None:
    sample = WeeklyLoad(week_start=date(2026, 7, 20), load=_load("10"))

    with pytest.raises(ValueError, match="unique start dates"):
        calculate_42_day_average((sample, sample), as_of=date(2026, 7, 26))


def test_weekly_sample_requires_monday_start() -> None:
    with pytest.raises(ValueError, match="start on Monday"):
        WeeklyLoad(week_start=date(2026, 7, 21), load=_load("10"))


def test_exactly_80_percent_uses_regular_growth_from_planned_load() -> None:
    result = calculate_progressive_target(
        prior_planned=_load("100"),
        prior_realized=_load("80"),
        baseline=_load("70"),
    )

    assert result.basis is ProgressionBasis.REGULAR
    assert result.target.value == Decimal("110.00")


def test_overshoot_does_not_replace_planned_growth_anchor() -> None:
    result = calculate_progressive_target(
        prior_planned=_load("100"),
        prior_realized=_load("180"),
        baseline=_load("70"),
    )

    assert result.target.value == Decimal("110.00")


def test_below_80_percent_uses_available_baseline() -> None:
    result = calculate_progressive_target(
        prior_planned=_load("100"),
        prior_realized=_load("79.99"),
        baseline=_load("62.5"),
    )

    assert result.basis is ProgressionBasis.BASELINE
    assert result.target.value == Decimal("62.5")


def test_heavy_undershoot_without_history_fails_closed() -> None:
    with pytest.raises(ValueError, match="baseline is required"):
        calculate_progressive_target(
            prior_planned=_load("100"),
            prior_realized=_load("79"),
            baseline=None,
        )


def test_personalized_load_snapshot_is_expected_rpe_times_hours() -> None:
    result = snapshot_personalized_load(
        expected_rpe=Decimal("8"),
        duration=DurationMinutes(Decimal("90")),
    )

    assert result.value == Decimal("12")


@pytest.mark.parametrize(
    "expected_rpe",
    [Decimal("0.99"), Decimal("10.01"), Decimal("NaN")],
)
def test_personalized_snapshot_rejects_invalid_rpe(
    expected_rpe: Decimal,
) -> None:
    with pytest.raises(ValueError, match="between 1 and 10"):
        snapshot_personalized_load(
            expected_rpe=expected_rpe,
            duration=DurationMinutes(Decimal("60")),
        )
