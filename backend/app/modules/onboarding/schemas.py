"""Public TSS-free schemas for Phase 4 onboarding."""

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.modules.calibration.schemas import (
    CalculatedZoneBoundaryResponse,
    CalculatedZoneMetricProfileResponse,
    DisciplineSetupResponse,
    KnownThresholdInput,
    KnownZoneProfileInput,
)
from app.modules.physiology.models import Discipline
from app.modules.physiology.zones import ZoneMetricKind

TrimmedText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
OnboardingStep = Literal[
    "profile",
    "history",
    "goal",
    "zones",
    "review",
    "completed",
]


class PublicModel(BaseModel):
    """Base public model with accidental-field rejection."""

    model_config = ConfigDict(extra="forbid")


class AthleteProfileUpdate(PublicModel):
    """Confirmed profile and biometrics supplied by the athlete."""

    date_of_birth: date | None = None
    height_cm: Decimal | None = Field(default=None, gt=0, max_digits=5)
    weight_kg: Decimal | None = Field(default=None, gt=0, max_digits=5)
    resting_heart_rate_bpm: int | None = Field(default=None, gt=0, le=32767)
    motivation_text: TrimmedText | None = Field(default=None, max_length=1000)
    motivation_tag: TrimmedText | None = Field(default=None, max_length=50)
    timezone: TrimmedText | None = Field(default=None, max_length=100)

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_must_be_past(cls, value: date | None) -> date | None:
        """A future or same-day birth date is structurally invalid."""
        if value is not None and value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    @model_validator(mode="after")
    def at_least_one_field(self) -> "AthleteProfileUpdate":
        """PATCH requests must carry at least one explicit field."""
        if not self.model_fields_set:
            raise ValueError("at least one profile field is required")
        return self


class AthleteProfileResponse(PublicModel):
    """Owner-scoped athlete profile."""

    athlete_id: UUID
    date_of_birth: date | None
    height_cm: Decimal | None
    weight_kg: Decimal | None
    resting_heart_rate_bpm: int | None
    motivation_text: str | None
    motivation_tag: str | None
    timezone: str
    onboarding_status: Literal["not_started", "in_progress", "completed"]
    revision: int
    created_at: datetime
    updated_at: datetime


class TrainingHistoryEntryInput(PublicModel):
    """Canonical weekly history for one triathlon discipline."""

    discipline: Discipline
    weekly_minutes: int = Field(ge=0, le=10080)
    experience_years: Decimal = Field(ge=0, le=100, max_digits=4)


class TrainingHistoryReplace(PublicModel):
    """Complete swim/bike/run history replacement."""

    entries: tuple[TrainingHistoryEntryInput, ...] = Field(min_length=3, max_length=3)

    @field_validator("entries")
    @classmethod
    def require_all_disciplines(
        cls,
        entries: tuple[TrainingHistoryEntryInput, ...],
    ) -> tuple[TrainingHistoryEntryInput, ...]:
        """Exactly one entry for swim, bike, and run is required."""
        if {entry.discipline for entry in entries} != set(Discipline):
            raise ValueError("swim, bike, and run history are required")
        return entries


class TrainingHistoryEntryResponse(TrainingHistoryEntryInput):
    """Persisted athlete-confirmed training history."""

    confirmed_at: datetime
    updated_at: datetime


class PrimaryRaceGoalInput(PublicModel):
    """The single active race-oriented A goal in the MVP."""

    title: TrimmedText = Field(max_length=120)
    specific_description: TrimmedText = Field(max_length=1000)
    measurable_outcome: TrimmedText = Field(max_length=500)
    feasibility_score: int = Field(ge=1, le=10)
    target_date: date
    race_discipline_profile: tuple[Discipline, ...] = Field(
        min_length=1,
        max_length=3,
    )

    @field_validator("target_date")
    @classmethod
    def race_date_must_be_future(cls, value: date) -> date:
        """The primary onboarding race is still upcoming."""
        if value <= date.today():
            raise ValueError("target_date must be in the future")
        return value

    @field_validator("race_discipline_profile")
    @classmethod
    def disciplines_must_be_unique(
        cls,
        value: tuple[Discipline, ...],
    ) -> tuple[Discipline, ...]:
        """A race cannot list a discipline twice."""
        if len(set(value)) != len(value):
            raise ValueError("race disciplines must be unique")
        return value


class PrimaryRaceGoalResponse(PrimaryRaceGoalInput):
    """Persisted primary goal without internal periodization values."""

    id: UUID
    priority: Literal["A"]
    goal_type: Literal["race"]
    status: Literal["active", "superseded"]
    revision: int
    created_at: datetime
    updated_at: datetime


class ZoneBoundaryInput(PublicModel):
    """One canonical lower-inclusive zone interval."""

    zone_number: int = Field(ge=1, le=5)
    lower_value: Decimal = Field(ge=0)
    upper_value: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def upper_exceeds_lower(self) -> "ZoneBoundaryInput":
        """Every interval has positive width."""
        if self.upper_value <= self.lower_value:
            raise ValueError("upper_value must exceed lower_value")
        return self


class ManualZoneSubmission(PublicModel):
    """Explicit athlete-confirmed manual zone profile."""

    setup_method: Literal["manual"]
    confirmed: Literal[True]
    metric_kind: ZoneMetricKind
    metric_value: Decimal = Field(gt=0)
    boundaries: tuple[ZoneBoundaryInput, ...] = Field(
        min_length=5,
        max_length=5,
    )


class FallbackZoneSubmission(PublicModel):
    """Explicit request for approved unvalidated Karvonen fallback zones."""

    setup_method: Literal["fallback"]
    confirmed: Literal[True]


class CalculatedZoneSubmission(PublicModel):
    """Confirmed known thresholds with optional athlete-entered boundary overrides."""

    setup_method: Literal["calculated"]
    confirmed: Literal[True]
    thresholds: tuple[KnownThresholdInput, ...] = Field(min_length=1, max_length=2)
    boundary_overrides: tuple[KnownZoneProfileInput, ...] = Field(
        default=(),
        max_length=2,
    )


ZoneSubmission = Annotated[
    ManualZoneSubmission | FallbackZoneSubmission | CalculatedZoneSubmission,
    Field(discriminator="setup_method"),
]


class ZoneMetricResponse(PublicModel):
    """Canonical threshold metric for a manual zone profile."""

    metric_kind: ZoneMetricKind
    value: Decimal


class ZoneProfileResponse(PublicModel):
    """Public zone version; generated replacements remain pending."""

    id: UUID
    discipline: Discipline
    version: int
    setup_method: Literal["manual", "fallback", "calculated"]
    status: Literal["pending", "active", "superseded", "rejected", "expired"]
    source: Literal[
        "athlete_entered",
        "estimated",
        "reviewed_field_threshold",
    ]
    validation_status: Literal[
        "confirmed_by_athlete",
        "unreviewed",
        "pending_athlete_confirmation",
        "rejected_by_athlete",
    ]
    fallback_active: bool
    needs_testing: bool
    requires_review: bool
    review_reason: Literal[
        "within_soft_range",
        "outside_soft_range",
        "soft_range_not_configured",
        "fallback_unvalidated",
        "athlete_confirmation_required",
    ]
    ruleset_version: str
    zone_model_version: str | None = None
    source_method: str | None = None
    source_quality: str | None = None
    calculated_at: datetime | None = None
    review_status: str | None = None
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    evidence_version: str | None = None
    effective_from: datetime | None
    created_at: datetime
    metric: ZoneMetricResponse | None
    boundaries: tuple[CalculatedZoneBoundaryResponse, ...]
    metric_profiles: tuple[CalculatedZoneMetricProfileResponse, ...] = ()
    proposal_id: UUID | None = None
    base_zone_profile_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def expose_unambiguous_provenance(cls, value: Any) -> Any:
        """Replace the legacy structural flag with explicit public semantics."""
        if not isinstance(value, Mapping):
            return value
        result = dict(value)
        setup_method = result.get("setup_method")
        source_quality = result.get("source_quality")
        result.setdefault(
            "source",
            (
                source_quality
                if setup_method == "calculated"
                else "athlete_entered"
                if setup_method == "manual"
                else "estimated"
            ),
        )
        result.setdefault(
            "validation_status",
            (
                result.get("review_status")
                if setup_method == "calculated"
                else "confirmed_by_athlete"
                if setup_method == "manual"
                else "unreviewed"
            ),
        )
        result.pop("validated", None)
        return result


class ZoneSubmissionResponse(PublicModel):
    """Outcome of an initial or replacement zone submission."""

    profile: ZoneProfileResponse
    proposal_id: UUID | None


class ZoneProposalApproval(PublicModel):
    """Stale-safe precondition for applying one zone replacement."""

    expected_base_zone_profile_id: UUID | None


class ZoneProposalDecisionResponse(PublicModel):
    """Atomic public result of a zone proposal decision."""

    proposal_id: UUID
    state: Literal["applied", "rejected"]
    active_zone_profile_id: UUID | None
    superseded_zone_profile_id: UUID | None


class OnboardingStateResponse(PublicModel):
    """Resumable, derived onboarding state."""

    status: Literal["not_started", "in_progress", "completed"]
    current_step: OnboardingStep
    completed_steps: tuple[OnboardingStep, ...]
    profile: AthleteProfileResponse | None
    training_history: tuple[TrainingHistoryEntryResponse, ...]
    primary_goal: PrimaryRaceGoalResponse | None
    zones: tuple[ZoneProfileResponse, ...]
    discipline_setups: tuple[DisciplineSetupResponse, ...]
    can_complete: bool
    initial_plan_request_id: UUID | None


class OnboardingCompleteResponse(PublicModel):
    """Completed onboarding and the pending Phase 6 planning trigger."""

    onboarding: OnboardingStateResponse
    initial_plan_request_id: UUID
    initial_plan_request_status: Literal["pending"] = "pending"
