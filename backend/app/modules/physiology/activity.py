"""Deterministic Phase 7 activity-load and match-matrix rules."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from app.modules.physiology.models import DurationMinutes, IntensityBucket, InternalLoad
from app.modules.physiology.progression import snapshot_personalized_load


class ActivityMatchResult(str, Enum):
    """Public qualitative outcome of one completed activity."""

    PERFECT_MATCH = "perfect_match"
    OVERSHOOT = "overshoot"
    HIDDEN_FATIGUE = "hidden_fatigue"
    DEVIATION = "deviation"
    UNPLANNED = "unplanned"


class ActivityCorrectionReason(str, Enum):
    """Typed reason for proposing, but never applying, a plan correction."""

    VOLUME_OVERSHOOT = "volume_overshoot"
    HIDDEN_FATIGUE = "hidden_fatigue"
    UNPLANNED_LOAD = "unplanned_load"


@dataclass(frozen=True, slots=True)
class PlannedActivityExpectation:
    """Server-owned planned facts used by the match matrix."""

    load: InternalLoad = field(repr=False)
    expected_rpe_min: int
    expected_rpe_max: int
    intensity_bucket: IntensityBucket

    def __post_init__(self) -> None:
        if not 1 <= self.expected_rpe_min <= self.expected_rpe_max <= 10:
            raise ValueError("Expected RPE must be an ordered range from 1 to 10.")


@dataclass(frozen=True, slots=True)
class ActivityMatch:
    """TSS-private calculation result plus safe qualitative explanation."""

    result: ActivityMatchResult
    correction_reason: ActivityCorrectionReason | None
    public_message: str
    realized_load: InternalLoad = field(repr=False)


def calculate_realized_activity_load(
    *,
    duration: DurationMinutes,
    rpe: int,
) -> InternalLoad:
    """Calculate canonical-summary session load as RPE times actual hours."""
    if not 1 <= rpe <= 10:
        raise ValueError("RPE must be between 1 and 10.")
    return snapshot_personalized_load(
        expected_rpe=Decimal(rpe),
        duration=duration,
    )


def classify_activity_match(
    *,
    duration: DurationMinutes,
    rpe: int,
    planned: PlannedActivityExpectation | None,
) -> ActivityMatch:
    """Apply the locked Phase 7 matrix without exposing either load value.

    Hidden fatigue is evaluated before load overshoot because the phase-one
    canonical path uses session RPE as its load proxy. Without that precedence,
    a high RPE on an easy workout could never retain its distinct safety signal.
    """
    realized = calculate_realized_activity_load(duration=duration, rpe=rpe)
    if planned is None:
        return ActivityMatch(
            result=ActivityMatchResult.UNPLANNED,
            correction_reason=ActivityCorrectionReason.UNPLANNED_LOAD,
            public_message=(
                "Deze extra training stond niet in je actieve planning. "
                "Een eventuele aanpassing blijft eerst een voorstel."
            ),
            realized_load=realized,
        )

    if planned.intensity_bucket is IntensityBucket.LOW and rpe >= 7:
        return ActivityMatch(
            result=ActivityMatchResult.HIDDEN_FATIGUE,
            correction_reason=ActivityCorrectionReason.HIDDEN_FATIGUE,
            public_message=(
                "Deze rustige training voelde duidelijk zwaarder dan verwacht. "
                "Controleer een eventueel herstelvoorstel."
            ),
            realized_load=realized,
        )

    if realized.value > planned.load.value * Decimal("1.15"):
        return ActivityMatch(
            result=ActivityMatchResult.OVERSHOOT,
            correction_reason=ActivityCorrectionReason.VOLUME_OVERSHOOT,
            public_message=(
                "Deze training viel zwaarder uit dan gepland. "
                "Een eventuele aanpassing blijft eerst een voorstel."
            ),
            realized_load=realized,
        )

    load_inside_match_band = (
        planned.load.value * Decimal("0.90")
        <= realized.value
        <= planned.load.value * Decimal("1.10")
    )
    rpe_inside_expected_band = (
        planned.expected_rpe_min <= rpe <= (planned.expected_rpe_max)
    )
    if load_inside_match_band and rpe_inside_expected_band:
        return ActivityMatch(
            result=ActivityMatchResult.PERFECT_MATCH,
            correction_reason=None,
            public_message="De training sloot goed aan op de geplande inspanning.",
            realized_load=realized,
        )

    return ActivityMatch(
        result=ActivityMatchResult.DEVIATION,
        correction_reason=None,
        public_message=(
            "De uitvoering week af van de planning, maar vraagt niet automatisch "
            "om een correctie."
        ),
        realized_load=realized,
    )
