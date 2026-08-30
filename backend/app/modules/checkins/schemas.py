"""Strict public contracts for structured weekly check-ins."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.coach.context import CheckInContextCandidate
from app.modules.physiology.injury import RestrictionStatus
from app.modules.physiology.models import Discipline

from .domain import AthletePlanChoice


class PublicCheckInModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FatigueLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class MissedWorkoutReason(str, Enum):
    TIME_CONSTRAINT = "time_constraint"
    FATIGUE = "fatigue"
    INJURY = "injury"
    ILLNESS = "illness"
    MOTIVATION = "motivation"
    WEATHER = "weather"
    OTHER = "other"


class CheckInStartRequest(PublicCheckInModel):
    week_start: date

    @model_validator(mode="after")
    def require_monday(self) -> "CheckInStartRequest":
        if self.week_start.weekday() != 0:
            raise ValueError("week_start must be a Monday.")
        return self


class ExternalActivityInput(PublicCheckInModel):
    name: str = Field(min_length=1, max_length=120)
    discipline: Discipline
    scheduled_at: datetime
    duration_minutes: Decimal = Field(gt=0, le=1440)
    strenuous: bool = True
    recurring: bool = False

    @model_validator(mode="after")
    def require_aware_start(self) -> "ExternalActivityInput":
        if self.scheduled_at.tzinfo is None or self.scheduled_at.utcoffset() is None:
            raise ValueError("scheduled_at must be timezone-aware.")
        return self


class RestrictionDecisionInput(PublicCheckInModel):
    discipline: Discipline
    status: RestrictionStatus
    source: Literal["athlete", "physician", "physiotherapist", "other_professional"]
    athlete_plan_choice: AthletePlanChoice
    professional_advice: str | None = Field(default=None, max_length=500)
    professional_advice_at: datetime | None = None


class CheckInContextUpdate(PublicCheckInModel):
    expected_revision: int = Field(ge=0)
    blocked_dates: frozenset[date] = Field(default_factory=frozenset, max_length=7)
    fatigue_level: FatigueLevel = FatigueLevel.NONE
    missed_workout_reasons: frozenset[MissedWorkoutReason] = Field(
        default_factory=frozenset,
        max_length=7,
    )
    recurring_activities_confirmed: bool
    external_activities: tuple[ExternalActivityInput, ...] = Field(
        default=(),
        max_length=14,
    )
    restrictions: tuple[RestrictionDecisionInput, ...] = Field(
        default=(),
        max_length=3,
    )
    alarm_symptoms_acknowledged: bool = False


class CheckInContextResponse(PublicCheckInModel):
    revision: int = Field(ge=1)
    state: Literal["draft", "confirmed", "superseded"]
    source: Literal["structured_form"]
    expires_at: datetime
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    blocked_dates: frozenset[date]
    fatigue_level: FatigueLevel
    missed_workout_reasons: frozenset[MissedWorkoutReason]
    recurring_activities_confirmed: bool
    external_activities: tuple[ExternalActivityInput, ...]
    restrictions: tuple[RestrictionDecisionInput, ...]
    alarm_symptoms_acknowledged: bool
    confirmed_at: datetime | None = None


class WeeklyCheckInResponse(PublicCheckInModel):
    id: UUID
    week_start: date
    timezone: str
    status: Literal["open", "completed"]
    context_revision: int = Field(ge=0)
    plan_proposal_id: UUID | None = None
    started_at: datetime
    completed_at: datetime | None = None
    context: CheckInContextResponse | None = None


class CheckInContextConfirmation(PublicCheckInModel):
    expected_revision: int = Field(ge=1)
    context_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class CheckInContextExtractionRequest(PublicCheckInModel):
    """Bounded free text that can produce only an inert candidate."""

    athlete_text: str = Field(min_length=1, max_length=1000)


class CheckInContextCandidateResponse(PublicCheckInModel):
    """Schema-validated suggestion that still requires structured confirmation."""

    source: Literal["llm", "deterministic_fallback"]
    candidate: CheckInContextCandidate
    requires_structured_confirmation: Literal[True] = True


class InjuryRestrictionResponse(PublicCheckInModel):
    id: UUID
    discipline: Discipline
    status: RestrictionStatus
    allowed_intensity: Literal["none", "low_only", "unrestricted"]
    source: str
    start_at: datetime
    review_at: datetime
    professional_advice: str | None = None
    professional_advice_at: datetime | None = None
    athlete_plan_choice: AthletePlanChoice
    confirmed_at: datetime
    cleared_at: datetime | None = None

    @property
    def review_due(self) -> bool:
        return self.cleared_at is None and self.review_at <= datetime.now(
            self.review_at.tzinfo
        )


class PlannedExternalActivityResponse(PublicCheckInModel):
    id: UUID
    week_start: date
    name: str
    discipline: Discipline
    scheduled_at: datetime
    duration_minutes: Decimal
    strenuous: bool
    recurring: bool
    status: Literal["planned", "completed", "cancelled"]
    completed_activity_id: UUID | None = None
    created_at: datetime


class GoalAchievementRequest(PublicCheckInModel):
    achieved_at: date

    @model_validator(mode="after")
    def achievement_is_not_future(self) -> "GoalAchievementRequest":
        if self.achieved_at > date.today():
            raise ValueError("achieved_at cannot be in the future")
        return self


class GoalMaintenanceResponse(PublicCheckInModel):
    goal_id: UUID
    status: Literal["active"]
    achieved_at: date
    confirmed_at: datetime
