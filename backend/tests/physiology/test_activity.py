"""Phase 7 deterministic activity-load and match-matrix tests."""

from decimal import Decimal

import pytest

from app.modules.physiology.activity import (
    ActivityCorrectionReason,
    ActivityMatchResult,
    PlannedActivityExpectation,
    calculate_realized_activity_load,
    classify_activity_match,
)
from app.modules.physiology.models import DurationMinutes, IntensityBucket, InternalLoad


def _planned(
    load: str = "4",
    *,
    intensity: IntensityBucket = IntensityBucket.LOW,
    expected_min: int = 3,
    expected_max: int = 5,
) -> PlannedActivityExpectation:
    return PlannedActivityExpectation(
        load=InternalLoad(Decimal(load)),
        expected_rpe_min=expected_min,
        expected_rpe_max=expected_max,
        intensity_bucket=intensity,
    )


def test_realized_load_uses_actual_rpe_times_duration_hours() -> None:
    load = calculate_realized_activity_load(
        duration=DurationMinutes(Decimal("90")),
        rpe=6,
    )

    assert load.value == Decimal("9")
    assert "9" not in repr(load)


def test_match_matrix_perfect_band_is_inclusive() -> None:
    lower = classify_activity_match(
        duration=DurationMinutes(Decimal("54")),
        rpe=4,
        planned=_planned(),
    )
    upper = classify_activity_match(
        duration=DurationMinutes(Decimal("66")),
        rpe=4,
        planned=_planned(),
    )

    assert lower.result is ActivityMatchResult.PERFECT_MATCH
    assert upper.result is ActivityMatchResult.PERFECT_MATCH
    assert lower.correction_reason is None


def test_overshoot_is_strictly_above_fifteen_percent() -> None:
    boundary = classify_activity_match(
        duration=DurationMinutes(Decimal("69")),
        rpe=4,
        planned=_planned(),
    )
    above = classify_activity_match(
        duration=DurationMinutes(Decimal("69.01")),
        rpe=4,
        planned=_planned(),
    )

    assert boundary.result is ActivityMatchResult.DEVIATION
    assert above.result is ActivityMatchResult.OVERSHOOT
    assert above.correction_reason is ActivityCorrectionReason.VOLUME_OVERSHOOT


def test_hidden_fatigue_precedes_session_load_overshoot_for_easy_workout() -> None:
    result = classify_activity_match(
        duration=DurationMinutes(Decimal("60")),
        rpe=7,
        planned=_planned(load="3.5"),
    )

    assert result.result is ActivityMatchResult.HIDDEN_FATIGUE
    assert result.correction_reason is ActivityCorrectionReason.HIDDEN_FATIGUE


def test_high_intensity_workout_with_high_rpe_is_not_hidden_fatigue() -> None:
    result = classify_activity_match(
        duration=DurationMinutes(Decimal("60")),
        rpe=8,
        planned=_planned(
            load="8",
            intensity=IntensityBucket.HIGH,
            expected_min=7,
            expected_max=9,
        ),
    )

    assert result.result is ActivityMatchResult.PERFECT_MATCH


def test_unplanned_activity_requests_a_pending_correction() -> None:
    result = classify_activity_match(
        duration=DurationMinutes(Decimal("30")),
        rpe=3,
        planned=None,
    )

    assert result.result is ActivityMatchResult.UNPLANNED
    assert result.correction_reason is ActivityCorrectionReason.UNPLANNED_LOAD


@pytest.mark.parametrize("rpe", [0, 11])
def test_realized_load_rejects_invalid_rpe(rpe: int) -> None:
    with pytest.raises(ValueError, match="RPE"):
        calculate_realized_activity_load(
            duration=DurationMinutes(Decimal("60")),
            rpe=rpe,
        )
