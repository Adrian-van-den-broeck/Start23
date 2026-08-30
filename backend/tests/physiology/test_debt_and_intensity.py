"""Boundary tests for BR-002 and BR-003."""

from decimal import Decimal

import pytest

from app.modules.physiology.debt import (
    calculate_intensity_debt,
    calculate_reliable_intensity_debt,
    calculate_volume_debt,
)
from app.modules.physiology.intensity import (
    STANDARD_RACE_INTENSITY_TARGET,
    IntensitySegment,
    WorkoutIntensity,
    calculate_time_distribution,
    classify_segment,
    classify_workout,
    display_time_distribution,
    intensive_duration_warning,
)
from app.modules.physiology.models import (
    DurationMinutes,
    Fraction,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)


def _load(value: str) -> InternalLoad:
    return InternalLoad(Decimal(value))


def _duration(value: str) -> DurationMinutes:
    return DurationMinutes(Decimal(value))


def _fraction(value: str) -> Fraction:
    return Fraction(Decimal(value))


def _segment(
    duration: str,
    zone: TrainingZone | None = None,
    *,
    technique: bool = False,
) -> IntensitySegment:
    return IntensitySegment(
        duration=_duration(duration),
        zone=zone,
        is_swim_technique=technique,
    )


def test_volume_debt_does_not_activate_at_exactly_110_percent() -> None:
    result = calculate_volume_debt(
        prior_planned=_load("600"),
        prior_realized=_load("660"),
    )

    assert result.activated is False
    assert result.debt.value == Decimal(0)
    assert result.regular_projection.value == Decimal("660.00")
    assert result.corrected_target is not None
    assert result.corrected_target.value == Decimal("660.00")


def test_volume_debt_activates_strictly_above_110_percent() -> None:
    result = calculate_volume_debt(
        prior_planned=_load("600"),
        prior_realized=_load("660.01"),
    )

    assert result.activated is True
    assert result.debt.value == Decimal("60.01")
    assert result.corrected_target is not None
    assert result.corrected_target.value == Decimal("599.99")


def test_volume_debt_reproduces_approved_600_680_example() -> None:
    result = calculate_volume_debt(
        prior_planned=_load("600"),
        prior_realized=_load("680"),
    )

    assert result.debt.value == Decimal("80")
    assert result.corrected_target is not None
    assert result.corrected_target.value == Decimal("580.00")


def test_volume_debt_fails_safe_when_target_would_be_zero_or_negative() -> None:
    result = calculate_volume_debt(
        prior_planned=_load("100"),
        prior_realized=_load("500"),
    )

    assert result.corrected_target is None
    assert result.requires_review is True

    exceptional = calculate_volume_debt(
        prior_planned=_load("100"),
        prior_realized=_load("500"),
        exceptional_zero_allowed=True,
    )
    assert exceptional.corrected_target is not None
    assert exceptional.corrected_target.value == Decimal(0)


def test_intensity_debt_uses_excess_and_normal_floor() -> None:
    ordinary = calculate_intensity_debt(
        planned_high_fraction=_fraction("0.20"),
        realized_high_fraction=_fraction("0.30"),
    )
    floored = calculate_intensity_debt(
        planned_high_fraction=_fraction("0.20"),
        realized_high_fraction=_fraction("0.45"),
    )

    assert ordinary.debt.value == Decimal("0.10")
    assert ordinary.corrected_high_fraction.value == Decimal("0.10")
    assert floored.debt.value == Decimal("0.25")
    assert floored.corrected_high_fraction.value == Decimal("0.05")


def test_intensity_debt_zero_floor_is_injured_discipline_only() -> None:
    result = calculate_intensity_debt(
        planned_high_fraction=_fraction("0.20"),
        realized_high_fraction=_fraction("0.45"),
        discipline_injury_confirmed=True,
    )

    assert result.corrected_high_fraction.value == Decimal(0)


@pytest.mark.parametrize(
    ("zone", "expected"),
    [
        (TrainingZone.ZONE_1, IntensityBucket.LOW),
        (TrainingZone.ZONE_2, IntensityBucket.LOW),
        (TrainingZone.ZONE_3, IntensityBucket.HIGH),
        (TrainingZone.ZONE_4, IntensityBucket.HIGH),
        (TrainingZone.ZONE_5, IntensityBucket.HIGH),
    ],
)
def test_each_training_zone_has_an_approved_bucket(
    zone: TrainingZone,
    expected: IntensityBucket,
) -> None:
    assert classify_segment(_segment("10", zone)) is expected


def test_swim_technique_is_low_intensity() -> None:
    assert classify_segment(_segment("10", technique=True)) is IntensityBucket.LOW


def test_reviewed_protocol_bucket_is_classified_without_fabricating_a_zone() -> None:
    segment = IntensitySegment(
        duration=_duration("10"),
        explicit_bucket=IntensityBucket.HIGH,
    )

    assert segment.zone is None
    assert classify_segment(segment) is IntensityBucket.HIGH


def test_explicit_bucket_can_preserve_swim_technique_execution_detail() -> None:
    segment = IntensitySegment(
        duration=_duration("10"),
        is_swim_technique=True,
        explicit_bucket=IntensityBucket.LOW,
    )

    assert classify_segment(segment) is IntensityBucket.LOW


def test_protocol_bucket_cannot_also_imply_a_zone() -> None:
    with pytest.raises(ValueError, match="cannot imply a zone"):
        IntensitySegment(
            duration=_duration("10"),
            zone=TrainingZone.ZONE_2,
            explicit_bucket=IntensityBucket.LOW,
        )


def test_segment_requires_zone_or_swim_technique() -> None:
    with pytest.raises(ValueError, match="requires a zone"):
        _segment("10")


def test_workout_requires_positive_total_duration() -> None:
    with pytest.raises(ValueError, match="positive total duration"):
        WorkoutIntensity((_segment("0", TrainingZone.ZONE_1),))


def test_mixed_workout_uses_dominant_category() -> None:
    low_dominant = WorkoutIntensity(
        (_segment("40", TrainingZone.ZONE_2), _segment("20", TrainingZone.ZONE_4))
    )

    assert classify_workout(low_dominant) is IntensityBucket.LOW


def test_exact_mixed_workout_tie_is_conservatively_high() -> None:
    tied = WorkoutIntensity(
        (_segment("10", TrainingZone.ZONE_1), _segment("10", TrainingZone.ZONE_3))
    )

    assert classify_workout(tied) is IntensityBucket.HIGH


def test_weekly_distribution_assigns_whole_mixed_workouts() -> None:
    low_dominant = WorkoutIntensity(
        (_segment("40", TrainingZone.ZONE_2), _segment("20", TrainingZone.ZONE_4))
    )
    high_dominant = WorkoutIntensity(
        (_segment("9", TrainingZone.ZONE_1), _segment("11", TrainingZone.ZONE_3))
    )

    result = calculate_time_distribution((low_dominant, high_dominant))

    assert result.evaluated is True
    assert result.low_duration.value == Decimal("60")
    assert result.high_duration.value == Decimal("20")
    assert result.low_fraction is not None
    assert result.low_fraction.value == Decimal("0.75")
    assert result.high_fraction is not None
    assert result.high_fraction.value == Decimal("0.25")


def test_display_distribution_uses_half_up_and_complementary_percentages() -> None:
    result = calculate_time_distribution(
        (
            WorkoutIntensity((_segment("82.5", TrainingZone.ZONE_1),)),
            WorkoutIntensity((_segment("17.5", TrainingZone.ZONE_4),)),
        )
    )

    display = display_time_distribution(result)

    assert display.low_percent == 83
    assert display.high_percent == 17
    assert display.low_percent + display.high_percent == 100
    assert display.low_minutes.value == Decimal("82.5")
    assert display.high_minutes.value == Decimal("17.5")


def test_realized_intensity_debt_requires_sixty_percent_reliable_coverage() -> None:
    insufficient = calculate_reliable_intensity_debt(
        planned_high=_duration("20"),
        planned_total=_duration("100"),
        realized_high=_duration("30"),
        realized_classified=_duration("59"),
        realized_total=_duration("100"),
    )
    exact = calculate_reliable_intensity_debt(
        planned_high=_duration("20"),
        planned_total=_duration("100"),
        realized_high=_duration("30"),
        realized_classified=_duration("60"),
        realized_total=_duration("100"),
    )

    assert insufficient.evaluated is False
    assert insufficient.result is None
    assert exact.evaluated is True
    assert exact.result is not None
    assert exact.result.debt.value == Decimal("0.30")
    assert exact.result.corrected_high_fraction.value == Decimal("0.05")


def test_empty_week_is_not_evaluated_instead_of_returning_zero_over_zero() -> None:
    result = calculate_time_distribution(())

    assert result.evaluated is False
    assert result.low_fraction is None
    assert result.high_fraction is None


def test_standard_race_target_is_80_20() -> None:
    assert STANDARD_RACE_INTENSITY_TARGET.low_fraction.value == Decimal("0.80")
    assert STANDARD_RACE_INTENSITY_TARGET.high_fraction.value == Decimal("0.20")


def test_intensive_duration_warning_is_strictly_above_30_percent() -> None:
    assert (
        intensive_duration_warning(planned=_duration("100"), realized=_duration("130"))
        is False
    )
    assert (
        intensive_duration_warning(
            planned=_duration("100"),
            realized=_duration("130.01"),
        )
        is True
    )
    assert (
        intensive_duration_warning(planned=_duration("0"), realized=_duration("1"))
        is True
    )
