"""BR-009 deterministic zone parsing, validation, and fallback calculations."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
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


class ZoneSourceQuality(str, Enum):
    """Evidence quality stored with a generated zone version."""

    MEASURED_LAB = "measured_lab"
    REVIEWED_FIELD_THRESHOLD = "reviewed_field_threshold"
    ATHLETE_ENTERED = "athlete_entered"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class HeartRateToleranceStatus(str, Enum):
    """Deterministic comparison against an applicable reviewed BPM reference."""

    WITHIN_TOLERANCE = "within_tolerance"
    OUTSIDE_TOLERANCE = "outside_tolerance"


@dataclass(frozen=True, slots=True)
class HeartRateToleranceResult:
    """TSS-free observation result that cannot manufacture a threshold or zone."""

    observed_bpm: int
    reference_bpm: int
    lower_inclusive_bpm: int
    upper_inclusive_bpm: int
    status: HeartRateToleranceStatus


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
ZONE_MODEL_VERSION = RulesetVersion("start23-zone-model-1.0")
ZONE_MODEL_EVIDENCE_VERSION = "voorstel-start23-zone-1-5-rekenmodel-v1.0"
_ZONE_MODEL_RATIOS = {
    ZoneMetricKind.BIKE_FTP_WATTS: (
        Decimal("0.56"),
        Decimal("0.76"),
        Decimal("0.91"),
        Decimal("1.06"),
    ),
    ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM: (
        Decimal("0.85"),
        Decimal("0.90"),
        Decimal("0.95"),
        Decimal("1.03"),
    ),
    ZoneMetricKind.RUN_LTHR_BPM: (
        Decimal("0.85"),
        Decimal("0.90"),
        Decimal("0.95"),
        Decimal("1.03"),
    ),
    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM: (
        Decimal("0.78"),
        Decimal("0.88"),
        Decimal("0.95"),
        Decimal("1.02"),
    ),
    ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M: (
        Decimal("0.78"),
        Decimal("0.88"),
        Decimal("0.95"),
        Decimal("1.02"),
    ),
}
_PRIMARY_METRIC_ORDER = {
    Discipline.SWIM: (ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,),
    Discipline.BIKE: (
        ZoneMetricKind.BIKE_FTP_WATTS,
        ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM,
    ),
    Discipline.RUN: (
        ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
        ZoneMetricKind.RUN_LTHR_BPM,
    ),
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


def assess_heart_rate_tolerance(
    *,
    observed_bpm: int,
    reference_bpm: int,
    tolerance_bpm: int = 10,
) -> HeartRateToleranceResult:
    """Apply the approved inclusive ``+/-10 bpm`` observation boundary.

    The result is observation context only. It deliberately returns no zone,
    threshold, or plan decision and must be called only with a reviewed session
    or protocol reference supplied by trusted backend context.
    """

    if isinstance(observed_bpm, bool) or not 20 <= observed_bpm <= 260:
        raise ValueError("Observed heart rate must be between 20 and 260 bpm.")
    if isinstance(reference_bpm, bool) or not 20 <= reference_bpm <= 260:
        raise ValueError("Reference heart rate must be between 20 and 260 bpm.")
    if isinstance(tolerance_bpm, bool) or tolerance_bpm != 10:
        raise ValueError("The reviewed heart-rate tolerance is exactly 10 bpm.")
    lower = reference_bpm - tolerance_bpm
    upper = reference_bpm + tolerance_bpm
    return HeartRateToleranceResult(
        observed_bpm=observed_bpm,
        reference_bpm=reference_bpm,
        lower_inclusive_bpm=lower,
        upper_inclusive_bpm=upper,
        status=(
            HeartRateToleranceStatus.WITHIN_TOLERANCE
            if lower <= observed_bpm <= upper
            else HeartRateToleranceStatus.OUTSIDE_TOLERANCE
        ),
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
class CalculatedZoneBoundary:
    """One model-derived interval; ``None`` represents an open outer edge."""

    zone: TrainingZone
    lower: Decimal | None
    upper: Decimal | None

    def __post_init__(self) -> None:
        if not isinstance(self.zone, TrainingZone):
            raise ValueError("Zone must be a TrainingZone value.")
        if self.lower is None and self.upper is None:
            raise ValueError("A calculated zone needs at least one boundary.")
        if self.lower is not None and (not self.lower.is_finite() or self.lower < 0):
            raise ValueError("Calculated lower boundaries must be non-negative.")
        if self.upper is not None and (not self.upper.is_finite() or self.upper <= 0):
            raise ValueError("Calculated upper boundaries must be positive.")
        if (
            self.lower is not None
            and self.upper is not None
            and self.upper <= self.lower
        ):
            raise ValueError("Calculated zone boundaries must be increasing.")


@dataclass(frozen=True, slots=True)
class CalculatedZoneMetricProfile:
    """Five rounded ranges derived from one canonical threshold metric."""

    metric: ZoneMetric
    boundaries: tuple[CalculatedZoneBoundary, ...]
    is_primary: bool
    zone_model_version: RulesetVersion = ZONE_MODEL_VERSION


@dataclass(frozen=True, slots=True)
class CalculatedZoneClassification:
    """Classification result including the FTP-only supramaximal marker."""

    zone: TrainingZone
    relative_intensity: Decimal
    supramaximal: bool


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


def round_zone_boundary(value: Decimal) -> Decimal:
    """Round one generated boundary once to its canonical whole-unit value."""
    if not value.is_finite() or value < 0:
        raise ValueError("Zone boundary input must be finite and non-negative.")
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def validate_calculated_zone_profile(
    profile: CalculatedZoneMetricProfile,
) -> None:
    """Validate five gap-free model ranges with open outer edges."""
    boundaries = profile.boundaries
    if [boundary.zone for boundary in boundaries] != list(TrainingZone):
        raise ValueError("Zone boundaries must contain consecutive Zones 1 through 5.")
    direction = metric_direction(profile.metric.kind)
    if direction is ZoneScaleDirection.ASCENDING:
        if boundaries[0].lower != 0 or boundaries[-1].upper is not None:
            raise ValueError("Ascending calculated zones need open-ended Zone 5.")
        if any(
            previous.upper != current.lower
            for previous, current in zip(boundaries, boundaries[1:], strict=False)
        ):
            raise ValueError("Ascending zone boundaries must be contiguous.")
    else:
        if boundaries[0].upper is not None or boundaries[-1].lower != 0:
            raise ValueError("Descending calculated zones need open-ended Zone 1.")
        if any(
            previous.lower != current.upper
            for previous, current in zip(boundaries, boundaries[1:], strict=False)
        ):
            raise ValueError("Descending zone boundaries must be contiguous.")
    if profile.metric.kind in _PACE_METRICS and any(
        value != value.to_integral_value()
        for boundary in boundaries
        for value in (boundary.lower, boundary.upper)
        if value is not None
    ):
        raise ValueError("Pace zone boundaries must use whole seconds.")


def calculate_zone_profile(
    metric: ZoneMetric | None,
    *,
    zone_model_version: RulesetVersion = ZONE_MODEL_VERSION,
    is_primary: bool = True,
) -> CalculatedZoneMetricProfile:
    """Convert one approved threshold to five canonical Start23 ranges."""
    if metric is None:
        raise ValueError("A threshold metric is required to calculate zones.")
    if zone_model_version != ZONE_MODEL_VERSION:
        raise ValueError("The requested zone model version is not active.")
    ratios = _ZONE_MODEL_RATIOS[metric.kind]
    if metric.kind in _PACE_METRICS:
        cutoffs = tuple(round_zone_boundary(metric.value / ratio) for ratio in ratios)
        if any(
            previous <= current
            for previous, current in zip(cutoffs, cutoffs[1:], strict=False)
        ):
            raise ValueError(
                "Threshold is too low to produce distinct whole-second pace zones."
            )
        boundaries = (
            CalculatedZoneBoundary(TrainingZone.ZONE_1, cutoffs[0], None),
            CalculatedZoneBoundary(TrainingZone.ZONE_2, cutoffs[1], cutoffs[0]),
            CalculatedZoneBoundary(TrainingZone.ZONE_3, cutoffs[2], cutoffs[1]),
            CalculatedZoneBoundary(TrainingZone.ZONE_4, cutoffs[3], cutoffs[2]),
            CalculatedZoneBoundary(TrainingZone.ZONE_5, Decimal(0), cutoffs[3]),
        )
    else:
        cutoffs = tuple(round_zone_boundary(metric.value * ratio) for ratio in ratios)
        if any(
            previous >= current
            for previous, current in zip(cutoffs, cutoffs[1:], strict=False)
        ):
            raise ValueError(
                "Threshold is too low to produce distinct whole-unit zones."
            )
        boundaries = (
            CalculatedZoneBoundary(TrainingZone.ZONE_1, Decimal(0), cutoffs[0]),
            CalculatedZoneBoundary(TrainingZone.ZONE_2, cutoffs[0], cutoffs[1]),
            CalculatedZoneBoundary(TrainingZone.ZONE_3, cutoffs[1], cutoffs[2]),
            CalculatedZoneBoundary(TrainingZone.ZONE_4, cutoffs[2], cutoffs[3]),
            CalculatedZoneBoundary(TrainingZone.ZONE_5, cutoffs[3], None),
        )
    profile = CalculatedZoneMetricProfile(
        metric=metric,
        boundaries=boundaries,
        is_primary=is_primary,
        zone_model_version=zone_model_version,
    )
    validate_calculated_zone_profile(profile)
    return profile


def calculate_zone_profiles(
    metrics: tuple[ZoneMetric, ...],
    *,
    zone_model_version: RulesetVersion = ZONE_MODEL_VERSION,
) -> tuple[CalculatedZoneMetricProfile, ...]:
    """Calculate one multi-metric discipline profile in primary-first order."""
    if not metrics:
        raise ValueError("At least one threshold metric is required.")
    disciplines = {metric.discipline for metric in metrics}
    kinds = {metric.kind for metric in metrics}
    if len(disciplines) != 1:
        raise ValueError("Zone profile metrics must belong to one discipline.")
    if len(kinds) != len(metrics):
        raise ValueError("Zone profile metrics must be unique.")
    discipline = next(iter(disciplines))
    order = _PRIMARY_METRIC_ORDER[discipline]
    ordered = tuple(sorted(metrics, key=lambda metric: order.index(metric.kind)))
    return tuple(
        calculate_zone_profile(
            metric,
            zone_model_version=zone_model_version,
            is_primary=index == 0,
        )
        for index, metric in enumerate(ordered)
    )


def classify_calculated_zone_value(
    *,
    profile: CalculatedZoneMetricProfile,
    value: Decimal,
) -> CalculatedZoneClassification:
    """Classify one value with rounded ranges and higher-intensity ownership."""
    if not value.is_finite() or value <= 0:
        raise ValueError("Zone classification value must be finite and positive.")
    validate_calculated_zone_profile(profile)
    direction = metric_direction(profile.metric.kind)
    for boundary in profile.boundaries:
        if direction is ZoneScaleDirection.ASCENDING:
            lower_matches = boundary.lower is None or boundary.lower <= value
            upper_matches = boundary.upper is None or value < boundary.upper
        else:
            lower_matches = boundary.lower is None or boundary.lower < value
            upper_matches = boundary.upper is None or value <= boundary.upper
        if lower_matches and upper_matches:
            relative_intensity = (
                value / profile.metric.value
                if direction is ZoneScaleDirection.ASCENDING
                else profile.metric.value / value
            )
            return CalculatedZoneClassification(
                zone=boundary.zone,
                relative_intensity=relative_intensity,
                supramaximal=(
                    profile.metric.kind is ZoneMetricKind.BIKE_FTP_WATTS
                    and relative_intensity > Decimal("1.20")
                ),
            )
    raise ValueError("Value falls outside the calculated zone profile.")


def classify_calculated_zone_speed(
    *,
    profile: CalculatedZoneMetricProfile,
    speed_meters_per_second: Decimal,
) -> CalculatedZoneClassification:
    """Classify pace/CSS from speed through the same canonical pace ranges."""
    if profile.metric.kind not in _PACE_METRICS:
        raise ValueError("Speed classification requires a pace or CSS profile.")
    if not speed_meters_per_second.is_finite() or speed_meters_per_second <= 0:
        raise ValueError("Speed must be finite and positive.")
    distance_meters = (
        Decimal(1000)
        if profile.metric.kind is ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM
        else Decimal(100)
    )
    return classify_calculated_zone_value(
        profile=profile,
        value=round_zone_boundary(distance_meters / speed_meters_per_second),
    )


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
