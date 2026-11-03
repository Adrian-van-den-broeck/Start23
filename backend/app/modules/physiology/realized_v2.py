"""Owner-approved, unvalidated Session-RPE heuristic. Private, pure and versioned.

Historical zone/calibration helpers deliberately keep their original semantics.
The numerator is divided last; stored results use the fixed context without
display quantization. Numerator/denominator retain a reproducible exact ratio.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

from .models import TrainingZone
from .rpe_zones import zone_for_rpe_value

VERSION = "joren-realized-tss-matrix-2"
LEGACY_MAPPING = "phase-13-joren-ruleset-1"
NUMERIC_POLICY = "decimal-50-half-even-divide-last-1"
METHOD = "duration_adjusted_session_rpe"
_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)


def session_rpe_zone(rpe: int, *, version: str = VERSION) -> TrainingZone:
    """Dispatch Session-RPE only; calibration-block anchors are independent."""
    if type(rpe) is not int or not 1 <= rpe <= 10:
        raise ValueError("Session RPE must be an integer from 1 through 10.")
    if version == VERSION:
        return TrainingZone((rpe + 1) // 2)
    if version == LEGACY_MAPPING:
        return zone_for_rpe_value(rpe)
    raise ValueError("Unsupported Session-RPE mapping version.")


def correction_factor(planned_zone: int, reported_zone: int) -> Decimal:
    for zone in (planned_zone, reported_zone):
        if type(zone) is not int or not 1 <= zone <= 5:
            raise ValueError("A canonical zone is required.")
    with localcontext(_CONTEXT):
        return max(
            Decimal("0.600"),
            min(
                Decimal("1.250"),
                Decimal("1.000") + Decimal("0.125") * (reported_zone - planned_zone),
            ),
        )


@dataclass(frozen=True, slots=True, repr=False)
class RealizedEstimate:
    """Never serialize this object into public responses, diagnostics or LLMs."""

    value: Decimal
    factor: Decimal
    actual_minutes: Decimal
    planned_minutes: Decimal
    duration_ratio: Decimal
    reported_zone: int
    version: str = VERSION
    numeric_policy: str = NUMERIC_POLICY


def estimate_realized(
    *,
    planned_load: Decimal,
    planned_minutes: Decimal,
    actual_minutes: Decimal,
    planned_zone: int,
    rpe: int,
    version: str = VERSION,
) -> RealizedEstimate:
    """Arithmetic only. Eligibility and evidence selection belong to callers."""
    if version != VERSION:
        raise ValueError("Unsupported realized calculation version.")
    for value in (planned_load, planned_minutes, actual_minutes):
        if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
            raise ValueError("Finite nonnegative Decimal inputs are required.")
    if planned_minutes == 0 or actual_minutes == 0:
        raise ValueError("Positive planned and performed durations are required.")
    reported = session_rpe_zone(rpe, version=version).value
    factor = correction_factor(planned_zone, reported)
    with localcontext(_CONTEXT):
        return RealizedEstimate(
            value=planned_load * actual_minutes * factor / planned_minutes,
            factor=factor,
            actual_minutes=actual_minutes,
            planned_minutes=planned_minutes,
            duration_ratio=actual_minutes / planned_minutes,
            reported_zone=reported,
        )
