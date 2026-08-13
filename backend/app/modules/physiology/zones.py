"""BR-009 deterministic zone parsing, validation, and fallback calculations."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from re import fullmatch

from app.modules.physiology.models import (
    Discipline,
    RuleId,
    RulesetVersion,
    TrainingZone,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V3,
    PhysiologySpecification,
)


class ZoneMetricKind(str, Enum):
    """Canonical discipline-specific threshold metrics."""

    SWIM_CSS_SECONDS_PER_100M = "swim_css_seconds_per_100m"
    BIKE_FTP_WATTS = "bike_ftp_watts"
    BIKE_THRESHOLD_HEART_RATE_BPM = "bike_threshold_heart_rate_bpm"
    RUN_THRESHOLD_PACE_SECONDS_PER_KM = "run_threshold_pace_seconds_per_km"
    RUN_LTHR_BPM = "run_lthr_bpm"


class ZoneScaleDirection(str, Enum):
    """Numeric direction in which training intensity rises."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class ZoneReviewReason(str, Enum):
    """Soft-range outcome for an otherwise valid athlete-supplied metric."""

    WITHIN_SOFT_RANGE = "within_soft_range"
    OUTSIDE_SOFT_RANGE = "outside_soft_range"
    SOFT_RANGE_NOT_CONFIGURED = "soft_range_not_configured"


class ZoneProfileSource(str, Enum):
    """Explicit provenance without implying clinical validation."""

    ATHLETE_ENTERED = "athlete_entered"
    FIELD_TEST = "field_test"
    WEARABLE_IMPORT = "wearable_import"
    ESTIMATED = "estimated"


class ZoneValidationState(str, Enum):
    """Who, if anyone, has confirmed the supplied zone profile."""

    UNREVIEWED = "unreviewed"
    CONFIRMED_BY_ATHLETE = "confirmed_by_athlete"
    PROTOCOL_VALIDATED = "protocol_validated"


_METRIC_DISCIPLINE = {
    ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M: Discipline.SWIM,
    ZoneMetricKind.BIKE_FTP_WATTS: Discipline.BIKE,
    ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM: Discipline.BIKE,
    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM: Discipline.RUN,
    ZoneMetricKind.RUN_LTHR_BPM: Discipline.RUN,
}
_METRIC_DIRECTION = {
    ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M: ZoneScaleDirection.DESCENDING,
    ZoneMetricKind.BIKE_FTP_WATTS: ZoneScaleDirection.ASCENDING,
    ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM: ZoneScaleDirection.ASCENDING,
    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM: (ZoneScaleDirection.DESCENDING),
    ZoneMetricKind.RUN_LTHR_BPM: ZoneScaleDirection.ASCENDING,
}
_PACE_METRICS = {
    ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
}
_TANAKA_BASE = Decimal("208")
_TANAKA_AGE_FACTOR = Decimal("0.7")
_AGE_220_BASE = Decimal("220")
_KARVONEN_BANDS = (
    (TrainingZone.ZONE_1, Decimal("0.50"), Decimal("0.60")),
    (TrainingZone.ZONE_2, Decimal("0.60"), Decimal("0.70")),
    (TrainingZone.ZONE_3, Decimal("0.70"), Decimal("0.80")),
    (TrainingZone.ZONE_4, Decimal("0.80"), Decimal("0.90")),
    (TrainingZone.ZONE_5, Decimal("0.90"), Decimal("1.00")),
)


@dataclass(frozen=True, slots=True)
class ZoneMetric:
    """One positive threshold metric in its canonical storage unit."""

    discipline: Discipline
    kind: ZoneMetricKind
    value: Decimal

    def __post_init__(self) -> None:
        if self.discipline is not _METRIC_DISCIPLINE[self.kind]:
            raise ValueError("Zone metric does not belong to this discipline.")
        if not self.value.is_finite() or self.value <= 0:
            raise ValueError("Zone metric must be finite and positive.")
        if self.kind in _PACE_METRICS and self.value != self.value.to_integral_value():
            raise ValueError("Pace metrics must use whole seconds.")


@dataclass(frozen=True, slots=True)
class ClinicalRange:
    """Inclusive soft review range; values outside it are not rejected."""

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
class ZoneMetricAssessment:
    """Soft-range assessment for a structurally valid metric."""

    ruleset_version: RulesetVersion
    requires_review: bool
    reason: ZoneReviewReason
    soft_range_rule: "ZoneSoftRangeRule | None" = None


@dataclass(frozen=True, slots=True)
class ZoneBoundary:
    """One numeric interval with an inclusive lower bound."""

    zone: TrainingZone
    lower: Decimal
    upper: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.zone, TrainingZone):
            raise ValueError("Zone must be a TrainingZone value.")
        if (
            not self.lower.is_finite()
            or not self.upper.is_finite()
            or self.lower < 0
            or self.upper <= self.lower
        ):
            raise ValueError("Zone boundary must be finite and increasing.")


@dataclass(frozen=True, slots=True)
class ZoneSoftRangeRule:
    """Versioned, attributable soft-review configuration; never a hard limit."""

    metric: ZoneMetricKind
    discipline: Discipline
    unit: str
    limits: ClinicalRange
    applicability: str
    evidence_reference: str
    reviewer: str
    valid_from: date
    valid_until: date
    ruleset_version: RulesetVersion

    def __post_init__(self) -> None:
        if self.discipline is not _METRIC_DISCIPLINE[self.metric]:
            raise ValueError("Soft range metric and discipline must agree.")
        if not all(
            value.strip()
            for value in (
                self.unit,
                self.applicability,
                self.evidence_reference,
                self.reviewer,
            )
        ):
            raise ValueError("Soft range provenance fields are required.")
        if self.valid_until < self.valid_from:
            raise ValueError("Soft range validity dates must be ordered.")


@dataclass(frozen=True, slots=True)
class KarvonenFallbackResult:
    """Explicitly estimated, unreviewed heart-rate zones from biometrics."""

    ruleset_version: RulesetVersion
    source: ZoneProfileSource
    validation_state: ZoneValidationState
    requires_confirmation: bool
    estimated_max_heart_rate_bpm: Decimal
    boundaries: tuple[ZoneBoundary, ...]


def _karvonen_result(
    *,
    age_years: int,
    resting_heart_rate_bpm: Decimal,
    estimated_max: Decimal,
    ruleset_version: RulesetVersion,
    specification: PhysiologySpecification,
) -> KarvonenFallbackResult:
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    if isinstance(age_years, bool) or age_years <= 0:
        raise ValueError("Age must be a positive whole number.")
    if not resting_heart_rate_bpm.is_finite() or resting_heart_rate_bpm <= 0:
        raise ValueError("Resting heart rate must be finite and positive.")
    if estimated_max <= resting_heart_rate_bpm:
        raise ValueError("Estimated maximum heart rate must exceed resting heart rate.")
    reserve = estimated_max - resting_heart_rate_bpm
    boundaries = tuple(
        ZoneBoundary(
            zone=zone,
            lower=resting_heart_rate_bpm + reserve * lower_fraction,
            upper=resting_heart_rate_bpm + reserve * upper_fraction,
        )
        for zone, lower_fraction, upper_fraction in _KARVONEN_BANDS
    )
    validate_zone_boundaries(
        boundaries,
        direction=ZoneScaleDirection.ASCENDING,
        specification=specification,
    )
    return KarvonenFallbackResult(
        ruleset_version=ruleset_version,
        source=ZoneProfileSource.ESTIMATED,
        validation_state=ZoneValidationState.UNREVIEWED,
        requires_confirmation=True,
        estimated_max_heart_rate_bpm=estimated_max,
        boundaries=boundaries,
    )


def metric_direction(kind: ZoneMetricKind) -> ZoneScaleDirection:
    """Return whether intensity rises with or against the numeric value."""
    return _METRIC_DIRECTION[kind]


def assess_metric_with_soft_limits(
    metric: ZoneMetric,
    limits: Mapping[ZoneMetricKind, ZoneSoftRangeRule],
    *,
    as_of: date | None = None,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> ZoneMetricAssessment:
    """Accept valid values while flagging missing or exceeded soft ranges."""
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    rule = limits.get(metric.kind)
    if (
        rule is None
        or as_of is None
        or not rule.valid_from <= as_of <= rule.valid_until
    ):
        return ZoneMetricAssessment(
            ruleset_version=specification.version,
            requires_review=True,
            reason=ZoneReviewReason.SOFT_RANGE_NOT_CONFIGURED,
        )
    if rule.metric is not metric.kind or rule.ruleset_version != specification.version:
        raise ValueError("Soft range provenance does not match the active ruleset.")
    if rule.limits.minimum <= metric.value <= rule.limits.maximum:
        return ZoneMetricAssessment(
            ruleset_version=specification.version,
            requires_review=False,
            reason=ZoneReviewReason.WITHIN_SOFT_RANGE,
            soft_range_rule=rule,
        )
    return ZoneMetricAssessment(
        ruleset_version=specification.version,
        requires_review=True,
        reason=ZoneReviewReason.OUTSIDE_SOFT_RANGE,
        soft_range_rule=rule,
    )


def validate_zone_boundaries(
    boundaries: tuple[ZoneBoundary, ...],
    *,
    direction: ZoneScaleDirection,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> None:
    """Require five contiguous zones in the metric's intensity direction."""
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    if [boundary.zone for boundary in boundaries] != list(TrainingZone):
        raise ValueError("Zone boundaries must contain consecutive Zones 1 through 5.")

    for previous, current in zip(boundaries, boundaries[1:], strict=False):
        if (
            direction is ZoneScaleDirection.ASCENDING
            and previous.upper != current.lower
        ):
            raise ValueError("Ascending zone boundaries must be contiguous.")
        if (
            direction is ZoneScaleDirection.DESCENDING
            and previous.lower != current.upper
        ):
            raise ValueError("Descending zone boundaries must be contiguous.")


def validate_zone_profile(
    *,
    metric_kind: ZoneMetricKind,
    boundaries: tuple[ZoneBoundary, ...],
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> None:
    """Validate a manual/test-derived profile in its canonical direction."""
    if metric_kind in _PACE_METRICS and any(
        boundary.lower != boundary.lower.to_integral_value()
        or boundary.upper != boundary.upper.to_integral_value()
        for boundary in boundaries
    ):
        raise ValueError("Pace zone boundaries must use whole seconds.")
    validate_zone_boundaries(
        boundaries,
        direction=metric_direction(metric_kind),
        specification=specification,
    )


def classify_zone_value(
    *,
    metric_kind: ZoneMetricKind,
    value: Decimal,
    boundaries: tuple[ZoneBoundary, ...],
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> TrainingZone:
    """Assign every shared boundary to the physiologically higher zone."""
    if not value.is_finite() or value < 0:
        raise ValueError("Zone classification value must be finite and non-negative.")
    validate_zone_profile(
        metric_kind=metric_kind,
        boundaries=boundaries,
        specification=specification,
    )
    direction = metric_direction(metric_kind)
    minimum_lower = min(boundary.lower for boundary in boundaries)
    maximum_upper = max(boundary.upper for boundary in boundaries)
    for boundary in boundaries:
        if direction is ZoneScaleDirection.ASCENDING:
            if boundary.lower <= value and (
                value < boundary.upper or value == boundary.upper == maximum_upper
            ):
                return boundary.zone
        elif (boundary.lower < value <= boundary.upper) or (
            value == boundary.lower == minimum_lower
        ):
            return boundary.zone
    raise ValueError("Value falls outside the supplied zone boundaries.")


def parse_pace_metric(
    *,
    kind: ZoneMetricKind,
    text: str,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> ZoneMetric:
    """Parse strict minutes:seconds pace into canonical whole seconds."""
    specification.require_approved(frozenset({RuleId.DISCIPLINE_ZONES}))
    if kind not in _PACE_METRICS:
        raise ValueError("Only swim CSS and run threshold pace use pace input.")
    match = fullmatch(r"(?P<minutes>[0-9]+):(?P<seconds>[0-5][0-9])", text)
    if match is None:
        raise ValueError("Pace must use minutes:seconds with two second digits.")
    value = Decimal(match.group("minutes")) * Decimal(60) + Decimal(
        match.group("seconds")
    )
    return ZoneMetric(
        discipline=_METRIC_DISCIPLINE[kind],
        kind=kind,
        value=value,
    )


def format_pace_metric(metric: ZoneMetric) -> str:
    """Format canonical whole seconds as minutes:seconds."""
    if metric.kind not in _PACE_METRICS:
        raise ValueError("Only swim CSS and run threshold pace use pace output.")
    integral = metric.value.to_integral_value()
    if metric.value != integral:
        raise ValueError("Pace display precision is whole seconds.")
    minutes, seconds = divmod(int(integral), 60)
    return f"{minutes}:{seconds:02d}"


def calculate_karvonen_fallback(
    *,
    age_years: int,
    resting_heart_rate_bpm: Decimal,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> KarvonenFallbackResult:
    """Generate unvalidated 50%-100% HRR zones using Tanaka HRmax."""
    estimated_max = _TANAKA_BASE - _TANAKA_AGE_FACTOR * Decimal(age_years)
    return _karvonen_result(
        age_years=age_years,
        resting_heart_rate_bpm=resting_heart_rate_bpm,
        estimated_max=estimated_max,
        ruleset_version=specification.version,
        specification=specification,
    )


def calculate_age_220_karvonen_fallback(
    *,
    age_years: int,
    resting_heart_rate_bpm: Decimal,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> KarvonenFallbackResult:
    """Generate an explicitly unreviewed `(220-age)` Karvonen alternative.

    This deterministic option is not the active onboarding default and carries
    no FTP, CSS, threshold-pace, or clinical-validation implication.
    """
    estimated_max = _AGE_220_BASE - Decimal(age_years)
    return _karvonen_result(
        age_years=age_years,
        resting_heart_rate_bpm=resting_heart_rate_bpm,
        estimated_max=estimated_max,
        ruleset_version=RulesetVersion("start23-age-220-karvonen-v1"),
        specification=specification,
    )
