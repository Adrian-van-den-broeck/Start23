"""Deterministic evaluation of reviewed Start23 calibration protocols.

Reviewed field-test thresholds are converted with the versioned Start23 Zone
1-5 model.  Both the threshold and generated profile remain pending athlete
confirmation; submaximal calibration still cannot manufacture a threshold.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Final

from app.modules.physiology.models import Discipline
from app.modules.physiology.rpe_zones import zone_for_rpe_range
from app.modules.physiology.zones import (
    CalculatedZoneMetricProfile,
    ZoneMetric,
    ZoneMetricKind,
    calculate_zone_profiles,
)

CALIBRATION_RULESET_VERSION: Final = "start23-calibration-ruleset-v2"


class SetupRoute(str, Enum):
    """The four explicit athlete choices for each discipline."""

    KNOWN_VALUES = "known_values"
    FIELD_TEST = "field_test"
    CALIBRATION_WEEK = "calibration_week"
    RPE_ONLY = "rpe_only"


class GuidanceMode(str, Enum):
    """Primary execution metric selected by the athlete."""

    POWER = "power"
    HEART_RATE = "heart_rate"
    COMBINED = "combined"
    PACE = "pace"
    RPE_ONLY = "rpe_only"


class ProtocolType(str, Enum):
    """Supported reviewed protocol families."""

    FIELD_TEST = "field_test"
    SUBMAXIMAL_CALIBRATION = "submaximal_calibration"


class TestSchedulingMode(str, Enum):
    """Athlete-selected placement for a reviewed field test."""

    STANDALONE = "standalone"
    WEEKLY_PLAN = "weekly_plan"


class NumericZoneVisibility(str, Enum):
    """Why numeric zones are visible or deliberately withheld."""

    VISIBLE = "visible"
    RPE_GUIDED = "rpe_guided"
    WEEK_2_EVALUATION_PENDING = "week_2_evaluation_pending"
    PROPOSAL_CONFIRMATION_PENDING = "proposal_confirmation_pending"


class ProtocolReviewStatus(str, Enum):
    """Only active protocols may be evaluated."""

    APPROVED_ACTIVE = "approved_active"


class EvaluationStatus(str, Enum):
    """Public, non-clinical outcome of a deterministic evaluation."""

    INSUFFICIENT_DATA = "insufficient_data"
    RPE_ONLY = "rpe_only"
    PROVISIONALLY_CALIBRATED = "provisionally_calibrated"
    THRESHOLD_ESTIMATED = "threshold_estimated"
    INSUFFICIENT_PROTOCOL = "insufficient_protocol"


class ThresholdStatus(str, Enum):
    """Whether a reviewed field-test threshold was produced."""

    UNKNOWN = "unknown"
    ESTIMATED = "threshold_estimated"


class ZoneStatus(str, Enum):
    """Zone state without activating a generated profile."""

    UNKNOWN = "unknown"
    PROVISIONAL = "provisionally_calibrated"
    PENDING_ATHLETE_CONFIRMATION = "pending_athlete_confirmation"
    # Retained so historical v1 evaluations remain readable.
    PENDING_PROTOCOL = "pending_protocol"


class Confidence(str, Enum):
    """Conservative confidence labels, without clinical meaning."""

    NOT_ASSESSED = "not_assessed"
    LOW = "low"
    MEDIUM = "medium"


class DataQuality(str, Enum):
    """Athlete/device supplied quality assessment."""

    MISSING = "missing"
    INSUFFICIENT = "insufficient"
    SUFFICIENT = "sufficient"


class SteadyExecution(str, Enum):
    """Whether the requested effort was held evenly."""

    YES = "yes"
    MOSTLY = "mostly"
    NO = "no"


@dataclass(frozen=True, slots=True)
class ProtocolSegment:
    """One immutable segment definition from an approved CSV fixture."""

    order: int
    segment_id: str
    purpose: str
    duration_seconds: int | None
    distance_meters: int | None
    target_rpe_min: int
    target_rpe_max: int
    optional: bool = False

    def __post_init__(self) -> None:
        zone_for_rpe_range(self.target_rpe_min, self.target_rpe_max)


@dataclass(frozen=True, slots=True)
class CalibrationProtocol:
    """Versioned protocol metadata needed by the backend evaluator."""

    protocol_id: str
    discipline: Discipline
    protocol_type: ProtocolType
    version: int
    review_status: ProtocolReviewStatus
    result_status_on_success: EvaluationStatus
    guidance_modes: tuple[str, ...]
    segments: tuple[ProtocolSegment, ...]


@dataclass(frozen=True, slots=True)
class SwimRepetition:
    """One equipment-free freestyle calibration repetition."""

    distance_meters: int
    elapsed_time_seconds: Decimal
    rest_time_seconds: int
    completed: bool

    def __post_init__(self) -> None:
        if self.distance_meters <= 0:
            raise ValueError("Swim repetition distance must be positive.")
        if not self.elapsed_time_seconds.is_finite() or self.elapsed_time_seconds <= 0:
            raise ValueError("Swim repetition time must be finite and positive.")
        if self.rest_time_seconds < 0:
            raise ValueError("Swim repetition rest must be non-negative.")


@dataclass(frozen=True, slots=True)
class CalibrationObservation:
    """Canonical immutable measurements for one protocol segment."""

    protocol_id: str
    discipline: Discipline
    segment_id: str
    completed: bool
    interrupted: bool
    quality_status: DataQuality
    target_rpe: int | None = None
    reported_block_rpe: int | None = None
    reported_session_rpe: int | None = None
    steady_execution: SteadyExecution | None = None
    duration_seconds: int | None = None
    distance_meters: int | None = None
    average_heart_rate_bpm: Decimal | None = None
    ending_heart_rate_bpm: Decimal | None = None
    average_heart_rate_last_20min_bpm: Decimal | None = None
    average_power_watts: Decimal | None = None
    average_power_last_20min_watts: Decimal | None = None
    average_pace_seconds_per_km: Decimal | None = None
    elapsed_time_seconds: Decimal | None = None
    pool_length_meters: int | None = None
    stroke: str | None = None
    equipment: str | None = None
    rest_time_seconds: int | None = None
    data_completeness: Decimal | None = None
    stable_segment: bool | None = None
    power_source_calibrated: bool | None = None
    repetitions: tuple[SwimRepetition, ...] = ()

    def __post_init__(self) -> None:
        for name, rpe in (
            ("target_rpe", self.target_rpe),
            ("reported_block_rpe", self.reported_block_rpe),
            ("reported_session_rpe", self.reported_session_rpe),
        ):
            if rpe is not None and (isinstance(rpe, bool) or not 1 <= rpe <= 10):
                raise ValueError(f"{name} must be an integer from 1 through 10.")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise ValueError("Duration must be positive when supplied.")
        if self.distance_meters is not None and self.distance_meters <= 0:
            raise ValueError("Distance must be positive when supplied.")
        if self.rest_time_seconds is not None and self.rest_time_seconds < 0:
            raise ValueError("Rest duration must be non-negative.")
        if self.data_completeness is not None and (
            not self.data_completeness.is_finite()
            or not Decimal(0) <= self.data_completeness <= Decimal(1)
        ):
            raise ValueError("Data completeness must be between zero and one.")
        for name, value in (
            ("average_heart_rate_bpm", self.average_heart_rate_bpm),
            ("ending_heart_rate_bpm", self.ending_heart_rate_bpm),
            (
                "average_heart_rate_last_20min_bpm",
                self.average_heart_rate_last_20min_bpm,
            ),
            ("average_power_watts", self.average_power_watts),
            ("average_power_last_20min_watts", self.average_power_last_20min_watts),
            ("average_pace_seconds_per_km", self.average_pace_seconds_per_km),
            ("elapsed_time_seconds", self.elapsed_time_seconds),
        ):
            if value is not None and (not value.is_finite() or value <= 0):
                raise ValueError(f"{name} must be finite and positive.")


@dataclass(frozen=True, slots=True)
class ThresholdEstimate:
    """One protocol-estimated threshold in its canonical unit."""

    metric_kind: ZoneMetricKind
    value: Decimal


@dataclass(frozen=True, slots=True)
class ProtocolEvaluation:
    """Deterministic, TSS-free evaluation result."""

    protocol_id: str
    discipline: Discipline
    ruleset_version: str
    status: EvaluationStatus
    threshold_status: ThresholdStatus
    zone_status: ZoneStatus
    confidence: Confidence
    reason_codes: tuple[str, ...]
    thresholds: tuple[ThresholdEstimate, ...] = ()
    zone_profiles: tuple[CalculatedZoneMetricProfile, ...] = ()
    requires_athlete_confirmation: bool = False


@dataclass(frozen=True, slots=True)
class TestScheduleDecision:
    """Validated date-only placement without prescribing a training hour."""

    protocol_id: str
    discipline: Discipline
    scheduling_mode: TestSchedulingMode
    scheduled_date: date


def numeric_zone_visibility(
    *,
    setup_route: SetupRoute,
    has_active_profile: bool,
    week_2_evaluation_completed: bool,
    has_pending_complete_proposal: bool,
) -> NumericZoneVisibility:
    """Fail closed for calibration-derived numeric profiles through Week 2."""

    if has_active_profile:
        return NumericZoneVisibility.VISIBLE
    if setup_route is not SetupRoute.CALIBRATION_WEEK:
        if has_pending_complete_proposal:
            return NumericZoneVisibility.PROPOSAL_CONFIRMATION_PENDING
        return NumericZoneVisibility.RPE_GUIDED
    if not week_2_evaluation_completed:
        return NumericZoneVisibility.WEEK_2_EVALUATION_PENDING
    if has_pending_complete_proposal:
        return NumericZoneVisibility.PROPOSAL_CONFIRMATION_PENDING
    return NumericZoneVisibility.RPE_GUIDED


def _segment(
    order: int,
    segment_id: str,
    purpose: str,
    duration: int | None,
    distance: int | None,
    rpe_min: int,
    rpe_max: int,
    *,
    optional: bool = False,
) -> ProtocolSegment:
    return ProtocolSegment(
        order=order,
        segment_id=segment_id,
        purpose=purpose,
        duration_seconds=duration,
        distance_meters=distance,
        target_rpe_min=rpe_min,
        target_rpe_max=rpe_max,
        optional=optional,
    )


PROTOCOLS: Final[dict[str, CalibrationProtocol]] = {
    "start23_run_threshold_30min_v1": CalibrationProtocol(
        protocol_id="start23_run_threshold_30min_v1",
        discipline=Discipline.RUN,
        protocol_type=ProtocolType.FIELD_TEST,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.THRESHOLD_ESTIMATED,
        guidance_modes=("heart_rate", "pace", "combined"),
        segments=(
            _segment(1, "warmup", "prepare", 900, None, 2, 3),
            _segment(2, "strides", "prepare", 300, None, 5, 6),
            _segment(3, "test_30min", "valid_test_segment", 1800, None, 7, 8),
            _segment(4, "cooldown", "recovery", 600, None, 2, 3),
        ),
    ),
    "start23_bike_ftp_30min_v1": CalibrationProtocol(
        protocol_id="start23_bike_ftp_30min_v1",
        discipline=Discipline.BIKE,
        protocol_type=ProtocolType.FIELD_TEST,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.THRESHOLD_ESTIMATED,
        guidance_modes=("power", "combined"),
        segments=(
            _segment(1, "warmup", "prepare", 1200, None, 2, 3),
            _segment(2, "test_30min", "valid_test_segment", 1800, None, 7, 8),
            _segment(3, "cooldown", "recovery", 600, None, 2, 3),
        ),
    ),
    "start23_bike_fthr_20min_v1": CalibrationProtocol(
        protocol_id="start23_bike_fthr_20min_v1",
        discipline=Discipline.BIKE,
        protocol_type=ProtocolType.FIELD_TEST,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.THRESHOLD_ESTIMATED,
        guidance_modes=("heart_rate",),
        segments=(
            _segment(1, "warmup", "prepare", 1200, None, 2, 3),
            _segment(2, "test_20min", "valid_test_segment", 1200, None, 7, 8),
            _segment(3, "cooldown", "recovery", 600, None, 2, 3),
        ),
    ),
    "start23_swim_css_400_200_v1": CalibrationProtocol(
        protocol_id="start23_swim_css_400_200_v1",
        discipline=Discipline.SWIM,
        protocol_type=ProtocolType.FIELD_TEST,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.THRESHOLD_ESTIMATED,
        guidance_modes=("pace",),
        segments=(
            _segment(1, "warmup", "prepare", None, 600, 2, 3),
            _segment(2, "tt_400m", "valid_test_segment", None, 400, 9, 10),
            _segment(3, "active_recovery", "recovery_between_tests", 420, None, 2, 3),
            _segment(4, "tt_200m", "valid_test_segment", None, 200, 9, 10),
            _segment(5, "cooldown", "recovery", None, 200, 2, 3),
        ),
    ),
    "start23_week1_run_calibration_v1": CalibrationProtocol(
        protocol_id="start23_week1_run_calibration_v1",
        discipline=Discipline.RUN,
        protocol_type=ProtocolType.SUBMAXIMAL_CALIBRATION,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.PROVISIONALLY_CALIBRATED,
        guidance_modes=("heart_rate", "pace", "rpe_only"),
        segments=(
            _segment(1, "warmup", "prepare", 600, None, 2, 3),
            _segment(
                2, "comfortable_20min", "calibration_observation", 1200, None, 4, 4
            ),
            _segment(
                3,
                "steady_8min_optional",
                "optional_calibration_observation",
                480,
                None,
                5,
                6,
                optional=True,
            ),
            _segment(4, "cooldown", "recovery", 600, None, 2, 3),
        ),
    ),
    "start23_week1_bike_calibration_v1": CalibrationProtocol(
        protocol_id="start23_week1_bike_calibration_v1",
        discipline=Discipline.BIKE,
        protocol_type=ProtocolType.SUBMAXIMAL_CALIBRATION,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.PROVISIONALLY_CALIBRATED,
        guidance_modes=("heart_rate", "power", "combined", "rpe_only"),
        segments=(
            _segment(1, "warmup", "prepare", 900, None, 2, 3),
            _segment(
                2, "comfortable_20min", "calibration_observation", 1200, None, 4, 4
            ),
            _segment(
                3,
                "steady_10min_optional",
                "optional_calibration_observation",
                600,
                None,
                5,
                6,
                optional=True,
            ),
            _segment(4, "cooldown", "recovery", 600, None, 2, 3),
        ),
    ),
    "start23_week1_swim_calibration_v1": CalibrationProtocol(
        protocol_id="start23_week1_swim_calibration_v1",
        discipline=Discipline.SWIM,
        protocol_type=ProtocolType.SUBMAXIMAL_CALIBRATION,
        version=1,
        review_status=ProtocolReviewStatus.APPROVED_ACTIVE,
        result_status_on_success=EvaluationStatus.PROVISIONALLY_CALIBRATED,
        guidance_modes=("pace", "rpe_only"),
        segments=(
            _segment(1, "warmup", "prepare", None, 300, 2, 3),
            _segment(
                2, "4x200_comfortable", "calibration_observation", None, 800, 4, 4
            ),
            _segment(3, "4x100_steady", "calibration_observation", None, 400, 5, 6),
            _segment(4, "cooldown", "recovery", None, 200, 2, 3),
        ),
    ),
}


def validate_test_schedule(
    *,
    protocol_id: str,
    discipline: Discipline,
    scheduling_mode: TestSchedulingMode,
    scheduled_date: date,
    athlete_today: date,
    plan_week_start: date | None = None,
) -> TestScheduleDecision:
    """Validate a reviewed field-test choice against athlete-local dates."""

    protocol = PROTOCOLS.get(protocol_id)
    if (
        protocol is None
        or protocol.protocol_type is not ProtocolType.FIELD_TEST
        or protocol.discipline is not discipline
    ):
        raise ValueError("The field-test protocol does not match the discipline.")
    if scheduled_date < athlete_today:
        raise ValueError("The athlete-local test date cannot be in the past.")
    if scheduling_mode is TestSchedulingMode.WEEKLY_PLAN:
        if discipline is Discipline.SWIM:
            raise ValueError(
                "The swim test has no approved planned-duration/load treatment."
            )
        if plan_week_start is None or plan_week_start.weekday() != 0:
            raise ValueError("An integrated test requires its plan week.")
        if not plan_week_start <= scheduled_date <= plan_week_start + timedelta(days=6):
            raise ValueError("The integrated test date must fall inside the plan week.")
    elif plan_week_start is not None:
        raise ValueError("A standalone test does not reference a weekly plan.")
    return TestScheduleDecision(
        protocol_id=protocol_id,
        discipline=discipline,
        scheduling_mode=scheduling_mode,
        scheduled_date=scheduled_date,
    )


def protocols_for_discipline(
    discipline: Discipline,
) -> tuple[CalibrationProtocol, ...]:
    """Return active protocols in stable field-test/calibration order."""
    return tuple(
        protocol
        for protocol in PROTOCOLS.values()
        if protocol.discipline is discipline
        and protocol.review_status is ProtocolReviewStatus.APPROVED_ACTIVE
    )


def pace_seconds_per_100m(
    *,
    elapsed_time_seconds: Decimal,
    distance_meters: int,
) -> Decimal:
    """Convert an exact swim repetition to canonical seconds per 100 metres."""
    if not elapsed_time_seconds.is_finite() or elapsed_time_seconds <= 0:
        raise ValueError("Elapsed time must be finite and positive.")
    if distance_meters <= 0:
        raise ValueError("Distance must be positive.")
    return elapsed_time_seconds / Decimal(distance_meters) * Decimal(100)


def _result(
    protocol: CalibrationProtocol,
    status: EvaluationStatus,
    reasons: tuple[str, ...],
    *,
    thresholds: tuple[ThresholdEstimate, ...] = (),
) -> ProtocolEvaluation:
    threshold_estimated = bool(thresholds)
    zone_profiles: tuple[CalculatedZoneMetricProfile, ...] = ()
    if threshold_estimated:
        zone_profiles = calculate_zone_profiles(
            tuple(
                ZoneMetric(
                    discipline=protocol.discipline,
                    kind=threshold.metric_kind,
                    value=threshold.value,
                )
                for threshold in thresholds
            )
        )
        zone_status = ZoneStatus.PENDING_ATHLETE_CONFIRMATION
        confidence = Confidence.MEDIUM
        reasons = tuple(
            dict.fromkeys(reasons + ("zone_profile_pending_athlete_confirmation",))
        )
    elif status is EvaluationStatus.PROVISIONALLY_CALIBRATED:
        zone_status = ZoneStatus.PROVISIONAL
        confidence = Confidence.LOW
    else:
        zone_status = ZoneStatus.UNKNOWN
        confidence = Confidence.NOT_ASSESSED
    return ProtocolEvaluation(
        protocol_id=protocol.protocol_id,
        discipline=protocol.discipline,
        ruleset_version=CALIBRATION_RULESET_VERSION,
        status=status,
        threshold_status=(
            ThresholdStatus.ESTIMATED
            if threshold_estimated
            else ThresholdStatus.UNKNOWN
        ),
        zone_status=zone_status,
        confidence=confidence,
        reason_codes=reasons,
        thresholds=thresholds,
        zone_profiles=zone_profiles,
        requires_athlete_confirmation=threshold_estimated,
    )


def _observation_map(
    protocol: CalibrationProtocol,
    observations: tuple[CalibrationObservation, ...],
) -> tuple[dict[str, CalibrationObservation], tuple[str, ...]]:
    allowed_segments = {segment.segment_id for segment in protocol.segments}
    mapped: dict[str, CalibrationObservation] = {}
    reasons: list[str] = []
    for observation in observations:
        if (
            observation.protocol_id != protocol.protocol_id
            or observation.discipline is not protocol.discipline
        ):
            reasons.append("protocol_observation_mismatch")
            continue
        if observation.segment_id not in allowed_segments:
            reasons.append("unknown_segment")
            continue
        if observation.segment_id in mapped:
            reasons.append("duplicate_segment_observation")
            continue
        mapped[observation.segment_id] = observation
    required = {
        segment.segment_id for segment in protocol.segments if not segment.optional
    }
    if not required.issubset(mapped):
        reasons.append("required_segment_missing")
    return mapped, tuple(dict.fromkeys(reasons))


def _common_reasons(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for definition in protocol.segments:
        observation = mapped.get(definition.segment_id)
        if observation is None or definition.optional:
            continue
        if not observation.completed:
            reasons.append("test_segment_incomplete")
        if observation.interrupted:
            reasons.append("interrupted")
        if observation.quality_status is DataQuality.INSUFFICIENT:
            reasons.append("sensor_quality_insufficient")
        if (
            protocol.protocol_type is ProtocolType.FIELD_TEST
            and definition.purpose == "valid_test_segment"
            and observation.quality_status is not DataQuality.SUFFICIENT
        ):
            reasons.append("sensor_quality_insufficient")
        if (
            definition.duration_seconds is not None
            and observation.duration_seconds != definition.duration_seconds
            and definition.purpose not in {"recovery_between_tests"}
        ):
            reasons.append("segment_duration_invalid")
        if (
            definition.distance_meters is not None
            and observation.distance_meters != definition.distance_meters
        ):
            reasons.append("segment_distance_invalid")
    cooldown = mapped.get("cooldown")
    if cooldown is None or cooldown.reported_session_rpe is None:
        reasons.append("missing_session_rpe")
    return tuple(dict.fromkeys(reasons))


def _whole_seconds(value: Decimal) -> Decimal:
    """Apply the approved canonical whole-second half-up rule once."""
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def _evaluate_run_test(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
    initial_reasons: tuple[str, ...],
) -> ProtocolEvaluation:
    reasons = list(initial_reasons) + list(_common_reasons(protocol, mapped))
    test = mapped.get("test_30min")
    thresholds: list[ThresholdEstimate] = []
    if test is not None:
        if test.reported_block_rpe is None:
            reasons.append("missing_block_rpe")
        elif not 8 <= test.reported_block_rpe <= 9:
            reasons.append("effort_below_protocol")
        if test.stable_segment is not True:
            reasons.append("pace_instability_excessive")
        if test.average_pace_seconds_per_km is None:
            reasons.append("pace_data_missing")
        elif test.stable_segment is True:
            thresholds.append(
                ThresholdEstimate(
                    ZoneMetricKind.RUN_THRESHOLD_PACE_SECONDS_PER_KM,
                    _whole_seconds(test.average_pace_seconds_per_km),
                )
            )
        if test.average_heart_rate_last_20min_bpm is not None:
            if test.data_completeness is None or test.data_completeness < Decimal(
                "0.95"
            ):
                reasons.append("heart_rate_quality_insufficient")
            else:
                thresholds.append(
                    ThresholdEstimate(
                        ZoneMetricKind.RUN_LTHR_BPM,
                        test.average_heart_rate_last_20min_bpm.quantize(
                            Decimal(1), rounding=ROUND_HALF_UP
                        ),
                    )
                )
    reasons = list(dict.fromkeys(reasons))
    blocking = {
        "protocol_observation_mismatch",
        "unknown_segment",
        "duplicate_segment_observation",
        "required_segment_missing",
        "test_segment_incomplete",
        "interrupted",
        "sensor_quality_insufficient",
        "segment_duration_invalid",
        "missing_session_rpe",
        "missing_block_rpe",
        "effort_below_protocol",
        "pace_instability_excessive",
        "pace_data_missing",
    }
    if blocking.intersection(reasons):
        return _result(protocol, EvaluationStatus.INSUFFICIENT_DATA, tuple(reasons))
    if not thresholds:
        return _result(
            protocol,
            EvaluationStatus.INSUFFICIENT_DATA,
            tuple(reasons + ["threshold_metric_missing"]),
        )
    return _result(
        protocol,
        EvaluationStatus.THRESHOLD_ESTIMATED,
        tuple(reasons),
        thresholds=tuple(thresholds),
    )


def _evaluate_bike_ftp_test(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
    initial_reasons: tuple[str, ...],
) -> ProtocolEvaluation:
    reasons = list(initial_reasons) + list(_common_reasons(protocol, mapped))
    test = mapped.get("test_30min")
    threshold: ThresholdEstimate | None = None
    if test is not None:
        if test.reported_block_rpe is None:
            reasons.append("missing_block_rpe")
        elif not 8 <= test.reported_block_rpe <= 9:
            reasons.append("effort_below_protocol")
        if test.power_source_calibrated is not True:
            reasons.append("power_source_not_calibrated")
        if test.data_completeness is None or test.data_completeness < Decimal("0.95"):
            reasons.append("power_quality_insufficient")
        if test.stable_segment is not True:
            reasons.append("power_variability_excessive")
        if test.average_power_last_20min_watts is None:
            reasons.append("power_data_missing")
        else:
            threshold = ThresholdEstimate(
                ZoneMetricKind.BIKE_FTP_WATTS,
                (test.average_power_last_20min_watts * Decimal("0.95")).quantize(
                    Decimal(1), rounding=ROUND_HALF_UP
                ),
            )
    reasons = list(dict.fromkeys(reasons))
    if reasons or threshold is None:
        return _result(
            protocol,
            EvaluationStatus.INSUFFICIENT_DATA,
            tuple(reasons or ["threshold_metric_missing"]),
        )
    return _result(
        protocol,
        EvaluationStatus.THRESHOLD_ESTIMATED,
        (),
        thresholds=(threshold,),
    )


def _evaluate_bike_hr_test(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
    initial_reasons: tuple[str, ...],
) -> ProtocolEvaluation:
    reasons = list(initial_reasons) + list(_common_reasons(protocol, mapped))
    test = mapped.get("test_20min")
    threshold: ThresholdEstimate | None = None
    if test is not None:
        if test.reported_block_rpe is None:
            reasons.append("missing_block_rpe")
        elif not 8 <= test.reported_block_rpe <= 9:
            reasons.append("effort_below_protocol")
        if test.data_completeness is None or test.data_completeness < Decimal("0.95"):
            reasons.append("heart_rate_quality_insufficient")
        if test.average_heart_rate_bpm is None:
            reasons.append("heart_rate_data_missing")
        else:
            threshold = ThresholdEstimate(
                ZoneMetricKind.BIKE_THRESHOLD_HEART_RATE_BPM,
                test.average_heart_rate_bpm.quantize(
                    Decimal(1), rounding=ROUND_HALF_UP
                ),
            )
    reasons = list(dict.fromkeys(reasons))
    if reasons or threshold is None:
        return _result(
            protocol,
            EvaluationStatus.INSUFFICIENT_DATA,
            tuple(reasons or ["threshold_metric_missing"]),
        )
    return _result(
        protocol,
        EvaluationStatus.THRESHOLD_ESTIMATED,
        (),
        thresholds=(threshold,),
    )


def _evaluate_swim_css_test(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
    initial_reasons: tuple[str, ...],
) -> ProtocolEvaluation:
    reasons = list(initial_reasons) + list(_common_reasons(protocol, mapped))
    first = mapped.get("tt_400m")
    second = mapped.get("tt_200m")
    recovery = mapped.get("active_recovery")
    threshold: ThresholdEstimate | None = None
    for effort in (first, second):
        if effort is None:
            continue
        if effort.reported_block_rpe is None:
            reasons.append("missing_block_rpe")
        elif not 9 <= effort.reported_block_rpe <= 10:
            reasons.append("effort_below_protocol")
        if effort.pool_length_meters not in {25, 50}:
            reasons.append("invalid_pool_length")
        if effort.stroke != "freestyle":
            reasons.append("stroke_not_freestyle")
        if effort.equipment != "none":
            reasons.append("equipment_used")
        if effort.elapsed_time_seconds is None:
            reasons.append("test_time_missing")
    if (
        first is not None
        and second is not None
        and first.pool_length_meters != second.pool_length_meters
    ):
        reasons.append("pool_length_mismatch")
    if (
        recovery is None
        or recovery.duration_seconds is None
        or not 300 <= recovery.duration_seconds <= 600
    ):
        reasons.append("recovery_duration_invalid")
    if (
        first is not None
        and second is not None
        and first.elapsed_time_seconds is not None
        and second.elapsed_time_seconds is not None
    ):
        time_400 = first.elapsed_time_seconds
        time_200 = second.elapsed_time_seconds
        if time_400 <= time_200 or time_200 * Decimal(2) >= time_400:
            reasons.append("pace_relationship_invalid")
        else:
            css = (time_400 - time_200) / Decimal(2)
            threshold = ThresholdEstimate(
                ZoneMetricKind.SWIM_CSS_SECONDS_PER_100M,
                _whole_seconds(css),
            )
    reasons = list(dict.fromkeys(reasons))
    if reasons or threshold is None:
        return _result(
            protocol,
            EvaluationStatus.INSUFFICIENT_DATA,
            tuple(reasons or ["threshold_metric_missing"]),
        )
    return _result(
        protocol,
        EvaluationStatus.THRESHOLD_ESTIMATED,
        (),
        thresholds=(threshold,),
    )


def _has_objective_metrics(observation: CalibrationObservation) -> bool:
    return any(
        value is not None
        for value in (
            observation.average_heart_rate_bpm,
            observation.average_power_watts,
            observation.average_pace_seconds_per_km,
            observation.elapsed_time_seconds,
        )
    ) or bool(observation.repetitions)


def _evaluate_submaximal_calibration(
    protocol: CalibrationProtocol,
    mapped: dict[str, CalibrationObservation],
    initial_reasons: tuple[str, ...],
) -> ProtocolEvaluation:
    reasons = list(initial_reasons) + list(_common_reasons(protocol, mapped))
    main_definitions = tuple(
        segment
        for segment in protocol.segments
        if segment.purpose
        in {"calibration_observation", "optional_calibration_observation"}
    )
    required_main = tuple(
        segment for segment in main_definitions if not segment.optional
    )
    main_observations = tuple(
        mapped[segment.segment_id]
        for segment in required_main
        if segment.segment_id in mapped
    )
    for observation in main_observations:
        if observation.reported_block_rpe is None:
            reasons.append("missing_block_rpe")
        if observation.steady_execution is SteadyExecution.NO:
            reasons.append("unstable_execution")
        if (
            _has_objective_metrics(observation)
            and observation.quality_status is not DataQuality.SUFFICIENT
        ):
            reasons.append("sensor_quality_insufficient")
        if protocol.discipline is Discipline.SWIM:
            expected_distance = (
                200 if observation.segment_id.startswith("4x200") else 100
            )
            if observation.pool_length_meters not in {25, 50}:
                reasons.append("invalid_pool_length")
            if observation.stroke != "freestyle":
                reasons.append("stroke_not_freestyle")
            if observation.equipment != "none":
                reasons.append("equipment_used")
            if len(observation.repetitions) != 4 or any(
                repetition.distance_meters != expected_distance
                or not repetition.completed
                for repetition in observation.repetitions
            ):
                reasons.append("set_incomplete")
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return _result(
            protocol,
            EvaluationStatus.INSUFFICIENT_DATA,
            tuple(reasons),
        )
    if not any(
        _has_objective_metrics(observation) for observation in main_observations
    ):
        return _result(protocol, EvaluationStatus.RPE_ONLY, ("sensor_data_missing",))
    return _result(
        protocol,
        EvaluationStatus.PROVISIONALLY_CALIBRATED,
        ("threshold_not_permitted_from_submaximal_calibration",),
    )


def evaluate_protocol(
    *,
    protocol_id: str,
    observations: tuple[CalibrationObservation, ...],
) -> ProtocolEvaluation:
    """Evaluate one reviewed protocol, failing closed on missing rules or data."""
    try:
        protocol = PROTOCOLS[protocol_id]
    except KeyError as error:
        raise ValueError("Unknown or inactive calibration protocol.") from error
    mapped, initial_reasons = _observation_map(protocol, observations)
    if protocol.protocol_type is ProtocolType.SUBMAXIMAL_CALIBRATION:
        return _evaluate_submaximal_calibration(
            protocol,
            mapped,
            initial_reasons,
        )
    if protocol_id == "start23_run_threshold_30min_v1":
        return _evaluate_run_test(protocol, mapped, initial_reasons)
    if protocol_id == "start23_bike_ftp_30min_v1":
        return _evaluate_bike_ftp_test(protocol, mapped, initial_reasons)
    if protocol_id == "start23_bike_fthr_20min_v1":
        return _evaluate_bike_hr_test(protocol, mapped, initial_reasons)
    if protocol_id == "start23_swim_css_400_200_v1":
        return _evaluate_swim_css_test(protocol, mapped, initial_reasons)
    return _result(
        protocol,
        EvaluationStatus.INSUFFICIENT_PROTOCOL,
        ("calculation_method_not_approved",),
    )
