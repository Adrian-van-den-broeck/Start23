"""Strict TSS-free transport models for weekly planning."""

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.schemas import (
    RpeZoneResponse,
    WorkoutSegmentResponse,
    rpe_zone_responses,
)


class PublicPlanningModel(BaseModel):
    """Forbid accidental persistence or internal-load fields in public DTOs."""

    model_config = ConfigDict(extra="forbid")


class FixedWorkoutDate(PublicPlanningModel):
    """One exact athlete-local date for an explicitly selected template."""

    template_id: UUID
    scheduled_date: date


class WeeklyPlanProposalRequest(PublicPlanningModel):
    """Structured inputs for deterministic selection and auto-scheduling."""

    week_start: date
    available_dates: tuple[date, ...] = Field(default=(), max_length=7)
    reuse_previous_week: bool = False
    confirmed_injuries: frozenset[Discipline] = frozenset()
    low_only_disciplines: frozenset[Discipline] = frozenset()
    selected_template_ids: tuple[UUID, ...] | None = Field(
        default=None,
        max_length=24,
    )
    fixed_workout_dates: tuple[FixedWorkoutDate, ...] = Field(
        default=(),
        max_length=3,
    )

    @model_validator(mode="after")
    def validate_week_and_selection(self) -> "WeeklyPlanProposalRequest":
        if self.week_start.weekday() != 0:
            raise ValueError("week_start must be a Monday.")
        if bool(self.available_dates) == self.reuse_previous_week:
            raise ValueError(
                "Provide available_dates or explicitly reuse the previous week."
            )
        if len(set(self.available_dates)) != len(self.available_dates):
            raise ValueError("available_dates must be unique.")
        if self.selected_template_ids is not None and len(
            set(self.selected_template_ids)
        ) != len(self.selected_template_ids):
            raise ValueError("selected_template_ids must be unique.")
        fixed_ids = tuple(item.template_id for item in self.fixed_workout_dates)
        if len(set(fixed_ids)) != len(fixed_ids):
            raise ValueError("fixed workout templates must be unique.")
        if self.fixed_workout_dates and (
            self.selected_template_ids is None
            or not set(fixed_ids) <= set(self.selected_template_ids)
        ):
            raise ValueError("fixed workout dates require selected templates.")
        if any(
            item.scheduled_date not in self.available_dates
            for item in self.fixed_workout_dates
        ):
            raise ValueError("fixed workout dates must be available dates.")
        if self.confirmed_injuries & self.low_only_disciplines:
            raise ValueError("A discipline cannot be blocked and low-only.")
        return self


class ScheduleProposalRequest(PublicPlanningModel):
    """Explicit deck selection for a new pending schedule revision."""

    expected_base_revision: int = Field(ge=0)
    available_dates: tuple[date, ...] = Field(min_length=1, max_length=7)
    confirmed_injuries: frozenset[Discipline] = frozenset()
    low_only_disciplines: frozenset[Discipline] = frozenset()
    selected_template_ids: tuple[UUID, ...] = Field(
        min_length=1,
        max_length=24,
    )
    fixed_workout_dates: tuple[FixedWorkoutDate, ...] = Field(
        default=(),
        max_length=3,
    )

    @model_validator(mode="after")
    def validate_selection(self) -> "ScheduleProposalRequest":
        if len(set(self.selected_template_ids)) != len(self.selected_template_ids):
            raise ValueError("selected_template_ids must be unique.")
        if len(set(self.available_dates)) != len(self.available_dates):
            raise ValueError("available_dates must be unique.")
        if self.confirmed_injuries & self.low_only_disciplines:
            raise ValueError("A discipline cannot be blocked and low-only.")
        fixed_ids = tuple(item.template_id for item in self.fixed_workout_dates)
        if len(set(fixed_ids)) != len(fixed_ids):
            raise ValueError("fixed workout templates must be unique.")
        if not set(fixed_ids) <= set(self.selected_template_ids):
            raise ValueError("fixed workout dates require selected templates.")
        if any(
            item.scheduled_date not in self.available_dates
            for item in self.fixed_workout_dates
        ):
            raise ValueError("fixed workout dates must be available dates.")
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
    rpe_zones: tuple[RpeZoneResponse, ...] = ()
    scheduled_date: date
    source: Literal[
        "auto_planned",
        "athlete_selected",
        "athlete_moved",
        "system_adjusted",
    ]
    status: Literal["scheduled", "completed", "cancelled"]
    warnings: tuple[PlanWarningResponse, ...] = ()

    @model_validator(mode="after")
    def derive_rpe_zones(self) -> "PlannedWorkoutResponse":
        self.rpe_zones = rpe_zone_responses(self.discipline, self.segments)
        return self


class ChangeProposalSummaryResponse(PublicPlanningModel):
    """Common, typed public proposal envelope."""

    id: UUID
    kind: Literal["zone_update", "plan_revision", "validation_test"]
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
    target_test_assignment_id: UUID | None = None


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
    available_dates: tuple[date, ...]
    availability_source: Literal["explicit", "previous_week", "checkin"]
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
        week_start = date.fromisoformat(str(result["week_start"]))
        workout_dates = {
            date.fromisoformat(str(workout["scheduled_date"]))
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
    rpe_zones: tuple[RpeZoneResponse, ...] = ()

    @model_validator(mode="after")
    def derive_rpe_zones(self) -> "WorkoutDeckItemResponse":
        self.rpe_zones = rpe_zone_responses(self.discipline, self.segments)
        return self


class SwipeDraftCreateRequest(PublicPlanningModel):
    """Start a TSS-free draft from exact confirmed planning context."""

    week_start: date
    available_dates: tuple[date, ...] = Field(default=(), max_length=7)
    reuse_previous_week: bool = False
    confirmed_injuries: frozenset[Discipline] = frozenset()
    low_only_disciplines: frozenset[Discipline] = frozenset()
    plan_id: UUID | None = None
    expected_base_revision: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_draft_context(self) -> "SwipeDraftCreateRequest":
        if self.week_start.weekday() != 0:
            raise ValueError("week_start must be a Monday.")
        if bool(self.available_dates) == self.reuse_previous_week:
            raise ValueError(
                "Provide available_dates or explicitly reuse the previous week."
            )
        if len(set(self.available_dates)) != len(self.available_dates):
            raise ValueError("available_dates must be unique.")
        if self.confirmed_injuries & self.low_only_disciplines:
            raise ValueError("A discipline cannot be blocked and low-only.")
        if self.plan_id is None and self.expected_base_revision != 0:
            raise ValueError("A new week draft must use base revision zero.")
        return self


class SwipeDraftTransitionRequest(PublicPlanningModel):
    """One stale-safe swipe, undo, or passed-card reset."""

    expected_revision: int = Field(ge=1)
    action: Literal["accept", "pass", "undo", "reset_passed"]
    candidate_template_id: UUID | None = None

    @model_validator(mode="after")
    def validate_candidate_binding(self) -> "SwipeDraftTransitionRequest":
        requires_candidate = self.action in {"accept", "pass"}
        if requires_candidate != (self.candidate_template_id is not None):
            raise ValueError(
                "Accept/pass requires exactly one current candidate template."
            )
        return self


class SwipeDraftPlacementRequest(PublicPlanningModel):
    """Place one accepted card on an exact athlete-local available date."""

    expected_revision: int = Field(ge=1)
    scheduled_date: date


class SwipeDraftSubmitRequest(PublicPlanningModel):
    """Create a pending proposal through automatic or complete manual placement."""

    expected_revision: int = Field(ge=1)
    placement_mode: Literal["automatic", "manual"]


class SwipeTargetComposition(PublicPlanningModel):
    """Fixed public workout counts without exposing private load."""

    swim: int = Field(ge=0, le=24)
    bike: int = Field(ge=0, le=24)
    run: int = Field(ge=0, le=24)


class SwipeWeekDraftResponse(PublicPlanningModel):
    """Owner-visible draft projection with one current candidate at a time."""

    id: UUID
    revision: int = Field(ge=1)
    state: Literal["collecting", "placement", "submitted"]
    week_start: date
    available_dates: tuple[date, ...]
    availability_source: Literal["explicit", "previous_week"]
    target_workout_count: int = Field(ge=0, le=24)
    target_composition: SwipeTargetComposition
    accepted_workouts: tuple[WorkoutDeckItemResponse, ...]
    current_candidate: WorkoutDeckItemResponse | None
    placements: tuple[FixedWorkoutDate, ...]
    warnings: tuple[PlanWarningResponse, ...] = ()
    passed_count: int = Field(ge=0)
    exhausted: bool
    can_undo: bool
    ruleset_version: str
    plan_id: UUID | None = None
    proposal_id: UUID | None = None


class PlanValidationWorkoutInput(PublicPlanningModel):
    """One existing workout position to validate qualitatively."""

    workout_id: UUID
    scheduled_date: date


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
    scheduled_date: date


class CalendarResponse(PublicPlanningModel):
    """Owned public calendar events in the requested interval."""

    from_date: date
    to_date: date
    workouts: tuple[PlannedWorkoutResponse, ...]
    rest_days: tuple[RestDayResponse, ...] = ()


class PendingWorkoutAlternativesResponse(PublicPlanningModel):
    """Server-authoritative alternatives for one exact pending workout."""

    plan_id: UUID
    revision: int = Field(ge=1)
    proposal_id: UUID
    workout_id: UUID
    can_remove: bool
    alternatives: tuple[WorkoutDeckItemResponse, ...]


class PendingWorkoutEditRequest(PublicPlanningModel):
    """Replace or remove one workout from an exact pending revision."""

    expected_revision: int = Field(ge=1)
    expected_proposal_id: UUID
    replacement_template_id: UUID | None = None


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
