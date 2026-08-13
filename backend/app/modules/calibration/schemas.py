"""Strict TSS-free API contracts for zone setup and calibration."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.calibration.domain import (
    Confidence,
    DataQuality,
    EvaluationStatus,
    GuidanceMode,
    ProtocolReviewStatus,
    ProtocolType,
    SetupRoute,
    SteadyExecution,
    ThresholdStatus,
    ZoneStatus,
)
from app.modules.physiology.models import Discipline
from app.modules.physiology.zones import ZoneMetricKind


class CalibrationPublicModel(BaseModel):
    """Reject accidental private fields on every public contract."""

    model_config = ConfigDict(extra="forbid")


class KnownThresholdInput(CalibrationPublicModel):
    """One athlete-supplied threshold without a validation claim."""

    metric_kind: ZoneMetricKind
    value: Decimal = Field(gt=0)


class KnownBoundaryInput(CalibrationPublicModel):
    """One optional athlete-supplied canonical zone boundary."""

    zone_number: int = Field(ge=1, le=5)
    lower_value: Decimal = Field(ge=0)
    upper_value: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def validate_width(self) -> "KnownBoundaryInput":
        if self.upper_value <= self.lower_value:
            raise ValueError("upper_value must exceed lower_value")
        return self


class KnownZoneProfileInput(CalibrationPublicModel):
    """Optional complete athlete-supplied Zone 1-5 profile for one metric."""

    metric_kind: ZoneMetricKind
    boundaries: tuple[KnownBoundaryInput, ...] = Field(min_length=5, max_length=5)


class KnownValuesSetup(CalibrationPublicModel):
    """Partial known values; zone profiles are optional."""

    setup_route: Literal[SetupRoute.KNOWN_VALUES]
    guidance_mode: GuidanceMode
    thresholds: tuple[KnownThresholdInput, ...] = Field(default=(), max_length=2)
    zone_profiles: tuple[KnownZoneProfileInput, ...] = Field(default=(), max_length=2)
    pool_length_meters: Literal[25, 50] | None = None

    @model_validator(mode="after")
    def require_at_least_one_value(self) -> "KnownValuesSetup":
        if not self.thresholds and not self.zone_profiles:
            raise ValueError("known_values requires a threshold or zone profile")
        return self


class FieldTestSetup(CalibrationPublicModel):
    """Selection of one reviewed field-test protocol."""

    setup_route: Literal[SetupRoute.FIELD_TEST]
    guidance_mode: GuidanceMode
    protocol_id: str = Field(min_length=1, max_length=100)
    pool_length_meters: Literal[25, 50] | None = None


class CalibrationWeekSetup(CalibrationPublicModel):
    """Conservative reviewed Week-1 route."""

    setup_route: Literal[SetupRoute.CALIBRATION_WEEK]
    guidance_mode: GuidanceMode
    pool_length_meters: Literal[25, 50] | None = None


class RpeOnlySetup(CalibrationPublicModel):
    """Explicit zone-free onboarding route."""

    setup_route: Literal[SetupRoute.RPE_ONLY]
    guidance_mode: Literal[GuidanceMode.RPE_ONLY] = GuidanceMode.RPE_ONLY


DisciplineSetupInput = Annotated[
    KnownValuesSetup | FieldTestSetup | CalibrationWeekSetup | RpeOnlySetup,
    Field(discriminator="setup_route"),
]


class DisciplineSetupResponse(CalibrationPublicModel):
    """Resumable discipline setup state."""

    discipline: Discipline
    setup_route: SetupRoute
    guidance_mode: GuidanceMode
    setup_status: Literal[
        "configured",
        "test_pending",
        "calibration_pending",
    ]
    protocol_id: str | None
    pool_length_meters: Literal[25, 50] | None
    threshold_status: Literal["unknown", "user_provided"]
    zone_status: Literal["unknown", "user_provided", "pending_protocol"]
    source: Literal["user_provided", "field_test", "week1_calibration", "none"]
    validation_status: Literal["self_reported", "not_assessed"]
    confidence: Confidence
    known_thresholds: tuple[KnownThresholdInput, ...]
    known_zone_profiles: tuple[KnownZoneProfileInput, ...]
    revision: int
    created_at: datetime
    updated_at: datetime


class ZoneOptionResponse(CalibrationPublicModel):
    """One user-facing setup route."""

    setup_route: SetupRoute
    label: str
    creates_threshold: bool
    creates_zones: bool


class ProtocolSegmentResponse(CalibrationPublicModel):
    """Reviewed execution segment metadata."""

    order: int
    segment_id: str
    purpose: str
    duration_seconds: int | None
    distance_meters: int | None
    target_rpe_min: int
    target_rpe_max: int
    optional: bool


class CalibrationProtocolResponse(CalibrationPublicModel):
    """TSS-free protocol projection."""

    protocol_id: str
    discipline: Discipline
    protocol_type: ProtocolType
    version: int
    review_status: ProtocolReviewStatus
    result_status_on_success: EvaluationStatus
    guidance_modes: tuple[str, ...]
    segments: tuple[ProtocolSegmentResponse, ...]


class SwimRepetitionInput(CalibrationPublicModel):
    """One completed or attempted swim repetition."""

    distance_meters: int = Field(gt=0)
    elapsed_time_seconds: Decimal = Field(gt=0)
    rest_time_seconds: int = Field(ge=0)
    completed: bool


class CalibrationObservationCreate(CalibrationPublicModel):
    """Canonical metrics for one protocol segment; athlete identity is omitted."""

    activity_id: UUID
    planned_workout_id: UUID | None = None
    protocol_id: str = Field(min_length=1, max_length=100)
    discipline: Discipline
    segment_id: str = Field(min_length=1, max_length=100)
    performed_at: datetime
    completed: bool
    interrupted: bool = False
    quality_status: DataQuality = DataQuality.MISSING
    target_rpe: int = Field(ge=1, le=10)
    reported_block_rpe: int | None = Field(default=None, ge=1, le=10)
    reported_session_rpe: int | None = Field(default=None, ge=1, le=10)
    steady_execution: SteadyExecution | None = None
    duration_seconds: int | None = Field(default=None, gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    average_heart_rate_bpm: Decimal | None = Field(default=None, gt=0)
    ending_heart_rate_bpm: Decimal | None = Field(default=None, gt=0)
    average_heart_rate_last_20min_bpm: Decimal | None = Field(default=None, gt=0)
    average_power_watts: Decimal | None = Field(default=None, gt=0)
    average_power_last_20min_watts: Decimal | None = Field(default=None, gt=0)
    average_pace_seconds_per_km: Decimal | None = Field(default=None, gt=0)
    elapsed_time_seconds: Decimal | None = Field(default=None, gt=0)
    pool_length_meters: Literal[25, 50] | None = None
    stroke: Literal["freestyle"] | None = None
    equipment: Literal["none"] | None = None
    rest_time_seconds: int | None = Field(default=None, ge=0)
    data_completeness: Decimal | None = Field(default=None, ge=0, le=1)
    stable_segment: bool | None = None
    power_source_calibrated: bool | None = None
    repetitions: tuple[SwimRepetitionInput, ...] = Field(default=(), max_length=20)

    @field_validator("performed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("performed_at must include a timezone offset")
        return value


class CalibrationObservationResponse(CalibrationObservationCreate):
    """Persisted immutable observation."""

    id: UUID
    fingerprint: str
    created_at: datetime


class CalibrationEvaluationRequest(CalibrationPublicModel):
    """Evaluate observations for one activity and reviewed protocol."""

    activity_id: UUID
    protocol_id: str = Field(min_length=1, max_length=100)


class ThresholdEstimateResponse(CalibrationPublicModel):
    """One pending field-test estimate."""

    metric_kind: ZoneMetricKind
    value: Decimal


class CalibrationEvaluationResponse(CalibrationPublicModel):
    """Persisted fail-closed protocol outcome."""

    id: UUID
    activity_id: UUID
    protocol_id: str
    discipline: Discipline
    ruleset_version: str
    status: EvaluationStatus
    threshold_status: ThresholdStatus
    zone_status: ZoneStatus
    confidence: Confidence
    reason_codes: tuple[str, ...]
    thresholds: tuple[ThresholdEstimateResponse, ...]
    requires_athlete_confirmation: bool
    review_status: Literal["pending_athlete_confirmation", "not_applicable"]
    fingerprint: str
    created_at: datetime


class CalibrationStatusResponse(CalibrationPublicModel):
    """Owner-scoped setup and evaluation history."""

    setups: tuple[DisciplineSetupResponse, ...]
    evaluations: tuple[CalibrationEvaluationResponse, ...]
