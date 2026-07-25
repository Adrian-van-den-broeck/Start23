"""BR-009 canonical zone units and structural validation."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.modules.physiology.models import Discipline, RuleId
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)


class ZoneMetricKind(str, Enum):
    """Canonical discipline-specific threshold metrics."""

    SWIM_CSS_SECONDS_PER_100M = "swim_css_seconds_per_100m"
    BIKE_FTP_WATTS = "bike_ftp_watts"
    BIKE_THRESHOLD_HEART_RATE_BPM = "bike_threshold_heart_rate_bpm"
    RUN_THRESHOLD_PACE_SECONDS_PER_KM = "run_threshold_pace_seconds_per_km"
    RUN_LTHR_BPM = "run_lthr_bpm"


_METRIC_DISCIPLINE = {
    ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M: Discipline.SWIM,
    ZoneMetricKind.BIKE_FTP_WATTS: Discipline.BIKE,
    ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM: Discipline.BIKE,
    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM: Discipline.RUN,
    ZoneMetricKind.RUN_LTHR_BPM: Discipline.RUN,
}


class ZoneClinicalLimitsMissingError(RuntimeError):
    """Raised until product supplies clinically reviewed numeric ranges."""


@dataclass(frozen=True, slots=True)
class ZoneMetric:
    """Positive canonical metric without an inferred clinical range."""

    discipline: Discipline
    kind: ZoneMetricKind
    value: Decimal

    def __post_init__(self) -> None:
        if self.discipline is not _METRIC_DISCIPLINE[self.kind]:
            raise ValueError("Zone metric does not belong to this discipline.")
        if not self.value.is_finite() or self.value <= 0:
            raise ValueError("Zone metric must be finite and positive.")


@dataclass(frozen=True, slots=True)
class ClinicalRange:
    """Inclusive product-supplied validation limits for one metric."""

    minimum: Decimal
    maximum: Decimal

    def __post_init__(self) -> None:
        if (
            not self.minimum.is_finite()
            or not self.maximum.is_finite()
            or self.minimum <= 0
            or self.maximum < self.minimum
        ):
            raise ValueError("Clinical range must be positive and ordered.")


@dataclass(frozen=True, slots=True)
class ZoneBoundary:
    """One ordered zone interval in canonical metric units."""

    zone: int
    lower: Decimal
    upper: Decimal

    def __post_init__(self) -> None:
        if self.zone not in range(1, 6):
            raise ValueError("Zone number must be between 1 and 5.")
        if (
            not self.lower.is_finite()
            or not self.upper.is_finite()
            or self.lower < 0
            or self.upper <= self.lower
        ):
            raise ValueError("Zone boundary must be finite and increasing.")


def validate_metric_with_limits(
    metric: ZoneMetric,
    limits: Mapping[ZoneMetricKind, ClinicalRange],
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> None:
    """Validate against explicit limits; never invent missing ranges."""
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    clinical_range = limits.get(metric.kind)
    if clinical_range is None:
        raise ZoneClinicalLimitsMissingError(
            f"No approved clinical range for {metric.kind.value}."
        )
    if not clinical_range.minimum <= metric.value <= clinical_range.maximum:
        raise ValueError("Zone metric falls outside the approved clinical range.")


def validate_zone_boundaries(
    boundaries: tuple[ZoneBoundary, ...],
    *,
    allow_adjacent_equality: bool,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> None:
    """Validate zone ordering and the explicit adjacent-equality policy."""
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    if [boundary.zone for boundary in boundaries] != list(range(1, 6)):
        raise ValueError("Zone boundaries must contain consecutive Zones 1 through 5.")
    for previous, current in zip(boundaries, boundaries[1:], strict=False):
        if current.lower < previous.upper:
            raise ValueError("Zone boundaries cannot overlap.")
        if current.lower == previous.upper and not allow_adjacent_equality:
            raise ValueError("Adjacent zone equality is not approved.")
