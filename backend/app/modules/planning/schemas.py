"""Strict TSS-free transport models for weekly planning."""

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.schemas import WorkoutSegmentResponse


class PublicPlanningModel(BaseModel):
    """Forbid accidental persistence or internal-load fields in public DTOs."""

    model_config = ConfigDict(extra="forbid")


class AvailabilityWindowInput(PublicPlanningModel):
    """One explicit athlete availability interval."""

    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> "AvailabilityWindowInput":
        if (
            self.starts_at.tzinfo is None
            or self.starts_at.utcoffset() is None
            or self.ends_at.tzinfo is None
            or self.ends_at.utcoffset() is None
        ):
            raise ValueError("Availability windows must be timezone-aware.")
        if self.ends_at <= self.starts_at:
            raise ValueError("Availability window end must follow its start.")
        return self


class WeeklyPlanProposalRequest(PublicPlanningModel):
    """Structured inputs for deterministic selection and auto-scheduling."""

    week_start: date
    availability: tuple[AvailabilityWindowInput, ...] = Field(
        min_length=1,
        max_length=28,
    )
    confirmed_injuries: frozenset[Discipline] = frozenset()
    low_only_disciplines: frozenset[Discipline] = frozenset()
    selected_template_ids: tuple[UUID, ...] | None = Field(
        default=None,
        max_length=24,
    )

    @model_validator(mode="after")
    def validate_week_and_selection(self) -> "WeeklyPlanProposalRequest":
        if self.week_start.weekday() != 0:
            raise ValueError("week_start must be a Monday.")
        if self.selected_template_ids is not None and len(
            set(self.selected_template_ids)
        ) != len(self.selected_template_ids):
            raise ValueError("selected_template_ids must be unique.")
        if self.confirmed_injuries & self.low_only_disciplines:
            raise ValueError("A discipline cannot be blocked and low-only.")
        return self


class ScheduleProposalRequest(PublicPlanningModel):
    """Explicit deck selection for a new pending schedule revision."""

    expected_base_revision: int = Field(ge=0)
    availability: tuple[AvailabilityWindowInput, ...] = Field(
        min_length=1,
        max_length=28,
    )
    confirmed_injuries: frozenset[Discipline] = frozenset()
    low_only_disciplines: frozenset[Discipline] = frozenset()
    selected_template_ids: tuple[UUID, ...] = Field(
        min_length=1,
        max_length=24,
    )

    @model_validator(mode="after")
    def validate_selection(self) -> "ScheduleProposalRequest":
        if len(set(self.selected_template_ids)) != len(self.selected_template_ids):
            raise ValueError("selected_template_ids must be unique.")
        if self.confirmed_injuries & self.low_only_disciplines:
            raise ValueError("A discipline cannot be blocked and low-only.")
        return self


class PlanWarningResponse(PublicPlanningModel):
    """Qualitative rule result with no hidden calculation values."""

    id: UUID | None = None
    rule_id: str
    code: str
    severity: Literal["info", "warning", "conflict"]
    message: str
    planned_workout_id: UUID | None = None


class PlannedWorkoutResponse(PublicPlanningModel):
    """Immutable public workout snapshot within a plan revision."""

    id: UUID
    template_id: UUID
    template_key: UUID
    template_version: int = Field(ge=1)
    discipline: Discipline
    name: str
    description: str
    duration_minutes: Decimal = Field(gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    intensity_bucket: IntensityBucket
    expected_rpe_min: int = Field(ge=1, le=10)
    expected_rpe_max: int = Field(ge=1, le=10)
    segments: tuple[WorkoutSegmentResponse, ...]
    scheduled_at: datetime
    timezone: str
    source: Literal[
        "auto_planned",
        "athlete_selected",
        "athlete_moved",
        "system_adjusted",
    ]
    status: Literal["scheduled", "completed", "cancelled"]
    warnings: tuple[PlanWarningResponse, ...] = ()


class ChangeProposalSummaryResponse(PublicPlanningModel):
    """Common, typed public proposal envelope."""

    id: UUID
    kind: Literal["zone_update", "plan_revision"]
    state: Literal["pending", "approved", "rejected", "expired", "applied"]
    reason_codes: tuple[str, ...]
    public_explanation: str
    ruleset_version: str
    created_at: datetime
    decided_at: datetime | None = None
    applied_at: datetime | None = None
    decision_actor: UUID | None = None
    target_plan_revision_id: UUID | None = None
    base_plan_revision: int | None = None
    target_zone_profile_id: UUID | None = None
    base_zone_profile_id: UUID | None = None


class WeeklyPlanResponse(PublicPlanningModel):
    """One explicitly selected active or pending weekly plan revision."""

    id: UUID
    week_start: date
    timezone: str
    state: Literal["pending_approval", "active", "superseded", "rejected", "expired"]
    active_revision: int | None
    revision_id: UUID
    revision: int = Field(ge=1)
    revision_state: Literal[
        "draft",
        "pending_approval",
        "active",
        "rejected",
        "superseded",
        "expired",
    ]
    phase: TrainingPhase
    target_basis: Literal[
        "initial_catalog_baseline",
        "prior_planned_hold",
        "realized_progression",
        "realized_baseline",
        "inactive_restart",
        "maintenance_hold",
        "physiological_debt",
        "manual_review_recovery",
        "activity_correction",
        "recovery_factor",
        "taper_factor",
        "injury_rest_only",
    ]
    taper_period: Literal["a_t_minus_2", "a_t_minus_1"] | None = None
    total_duration_minutes: Decimal = Field(ge=0)
    low_intensity_percent: Decimal = Field(ge=0, le=100)
    high_intensity_percent: Decimal = Field(ge=0, le=100)
    display_low_intensity_percent: int = Field(ge=0, le=100)
    display_high_intensity_percent: int = Field(ge=0, le=100)
    low_intensity_minutes: Decimal = Field(ge=0)
    high_intensity_minutes: Decimal = Field(ge=0)
    confirmed_injuries: frozenset[Discipline]
    low_only_disciplines: frozenset[Discipline] = frozenset()
    workouts: tuple[PlannedWorkoutResponse, ...]
    rest_days: tuple["RestDayResponse", ...] = ()
    warnings: tuple[PlanWarningResponse, ...]
    proposal: ChangeProposalSummaryResponse | None

    @model_validator(mode="before")
    @classmethod
    def add_stable_intensity_display(cls, value: Any) -> Any:
        """Derive complementary whole percentages and exact detail minutes."""
        if not isinstance(value, Mapping):
            return value
        result = dict(value)
        total = Decimal(str(result["total_duration_minutes"]))
        low_percent = Decimal(str(result["low_intensity_percent"]))
        high_percent = Decimal(str(result["high_intensity_percent"]))
        display_low = int(low_percent.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        result.setdefault("display_low_intensity_percent", display_low)
        result.setdefault("display_high_intensity_percent", 100 - display_low)
        result.setdefault("low_intensity_minutes", total * low_percent / Decimal(100))
        result.setdefault("high_intensity_minutes", total * high_percent / Decimal(100))
        timezone_name = str(result["timezone"])
        athlete_timezone = ZoneInfo(timezone_name)
        week_start = date.fromisoformat(str(result["week_start"]))
        workout_dates = {
            datetime.fromisoformat(str(workout["scheduled_at"]))
            .astimezone(athlete_timezone)
            .date()
            for workout in result.get("workouts", [])
            if isinstance(workout, Mapping)
        }
        rest_reason = (
            "restriction_rest"
            if result.get("target_basis") == "injury_rest_only"
            else "planned_rest"
        )
        result.setdefault(
            "rest_days",
            [
                {"date": current, "reason": rest_reason}
                for offset in range(7)
                if (current := week_start + timedelta(days=offset)) not in workout_dates
            ],
        )
        return result


class RestDayResponse(PublicPlanningModel):
    """Intentional empty plan date, distinct from missing plan data."""

    date: date
    reason: Literal["planned_rest", "restriction_rest"]


class WeeklyPlanProposalResponse(PublicPlanningModel):
    """New pending proposal plus its complete visible target."""

    proposal: ChangeProposalSummaryResponse
    plan: WeeklyPlanResponse


class WorkoutDeckResponse(PublicPlanningModel):
    """Eligible current catalog cards for one plan context."""

    plan_id: UUID
    revision: int = Field(ge=1)
    phase: TrainingPhase
    templates: tuple["WorkoutDeckItemResponse", ...]


class WorkoutDeckItemResponse(PublicPlanningModel):
    """TSS-free eligible catalog item."""

    id: UUID
    template_key: UUID
    version: int = Field(ge=1)
    discipline: Discipline
    name: str
    description: str
    duration_minutes: Decimal = Field(gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    intensity_bucket: IntensityBucket
    expected_rpe_min: int = Field(ge=1, le=10)
    expected_rpe_max: int = Field(ge=1, le=10)
    segments: tuple[WorkoutSegmentResponse, ...]


class PlanValidationWorkoutInput(PublicPlanningModel):
    """One existing workout position to validate qualitatively."""

    workout_id: UUID
    scheduled_at: datetime

    @model_validator(mode="after")
    def require_timezone(self) -> "PlanValidationWorkoutInput":
        if self.scheduled_at.tzinfo is None or self.scheduled_at.utcoffset() is None:
            raise ValueError("scheduled_at must be timezone-aware.")
        return self


class PlanValidationRequest(PublicPlanningModel):
    """Explicit schedule layout for qualitative validation."""

    expected_revision: int = Field(ge=1)
    workouts: tuple[PlanValidationWorkoutInput, ...] = Field(
        min_length=1,
        max_length=24,
    )

    @model_validator(mode="after")
    def require_unique_workouts(self) -> "PlanValidationRequest":
        workout_ids = tuple(workout.workout_id for workout in self.workouts)
        if len(set(workout_ids)) != len(workout_ids):
            raise ValueError("workout_id values must be unique.")
        return self


class PlanValidationResponse(PublicPlanningModel):
    """TSS-free validation result."""

    valid_for_generated_schedule: bool
    warnings: tuple[PlanWarningResponse, ...]


class PlannedWorkoutMoveRequest(PublicPlanningModel):
    """Revision-preconditioned direct athlete calendar move."""

    expected_revision: int = Field(ge=1)
    scheduled_at: datetime

    @model_validator(mode="after")
    def require_timezone(self) -> "PlannedWorkoutMoveRequest":
        if self.scheduled_at.tzinfo is None or self.scheduled_at.utcoffset() is None:
            raise ValueError("scheduled_at must be timezone-aware.")
        return self


class CalendarResponse(PublicPlanningModel):
    """Owned public calendar events in the requested interval."""

    from_datetime: datetime
    to_datetime: datetime
    workouts: tuple[PlannedWorkoutResponse, ...]
    rest_days: tuple[RestDayResponse, ...] = ()


class ProposalApprovalRequest(PublicPlanningModel):
    """Exactly one typed stale-safety precondition."""

    expected_base_revision: int | None = Field(default=None, ge=0)
    expected_base_zone_profile_id: UUID | None = None

    @model_validator(mode="after")
    def require_one_precondition(self) -> "ProposalApprovalRequest":
        supplied = (
            "expected_base_revision" in self.model_fields_set,
            "expected_base_zone_profile_id" in self.model_fields_set,
        )
        if sum(supplied) != 1:
            raise ValueError("Exactly one proposal precondition is required.")
        if supplied[0] and self.expected_base_revision is None:
            raise ValueError("A plan proposal requires a numeric base revision.")
        return self


class PlanProposalDecisionResponse(PublicPlanningModel):
    """Atomic public result for a plan proposal."""

    proposal_id: UUID
    state: Literal["applied", "rejected"]
    plan_id: UUID
    active_revision: int | None
    target_revision_id: UUID
