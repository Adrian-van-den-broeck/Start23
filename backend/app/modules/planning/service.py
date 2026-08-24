"""Application orchestration for deterministic weekly planning."""

import hashlib
import json
import logging
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

from app.modules.coach.weekly_plan import (
    CoachProviderError,
    CoachWorkoutFacts,
    WeeklyPlanCoach,
    WeeklyPlanCoachFacts,
    deterministic_weekly_plan_explanation,
)
from app.modules.physiology.anti_stack import ScheduledWorkout
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    InternalLoad,
    RuleId,
)
from app.modules.physiology.specification import PHASE_3_RULESET_V3
from app.modules.workouts.catalog import (
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
    active_catalog,
)
from app.modules.workouts.repository import (
    SupabaseWorkoutCatalogRepository,
    parse_planning_catalog,
)

from .domain import (
    AvailabilityWindow,
    PlanLoadSample,
    PlanningConstraintError,
    PlanningTargetBasis,
    PlanningWarning,
    ZoneCapability,
    build_weekly_plan,
    eligible_workouts,
    remaining_workout_deck,
    validate_manual_schedule,
)
from .repository import JsonObject, PlanningRepository, PlanningRepositoryError
from .schemas import (
    CalendarResponse,
    ChangeProposalSummaryResponse,
    PlannedWorkoutMoveRequest,
    PlannedWorkoutResponse,
    PlanProposalDecisionResponse,
    PlanValidationRequest,
    PlanValidationResponse,
    PlanWarningResponse,
    RestDayResponse,
    ScheduleProposalRequest,
    WeeklyPlanProposalRequest,
    WeeklyPlanProposalResponse,
    WeeklyPlanResponse,
    WorkoutDeckItemResponse,
    WorkoutDeckResponse,
)


class PlanningDomainError(ValueError):
    """Persisted or submitted planning input is incomplete or inconsistent."""


class PlanningCatalogProvider(Protocol):
    """Validated source for the TSS-bearing immutable catalog."""

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        """Return validated catalog versions."""

    async def aclose(self) -> None:
        """Release provider resources."""


class SupabasePlanningCatalogProvider:
    """Adapt the Phase 5 service-only RPC to validated catalog domain objects."""

    def __init__(self, repository: SupabaseWorkoutCatalogRepository) -> None:
        self._repository = repository

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        return parse_planning_catalog(await self._repository.fetch_for_planning())

    async def aclose(self) -> None:
        await self._repository.aclose()


_ZONE_REQUIREMENT_BY_METRIC = {
    "swim_css_seconds_per_100m": ZoneRequirement.PACE,
    "bike_ftp_watts": ZoneRequirement.POWER,
    "bike_threshold_heart_rate_bpm": ZoneRequirement.HEART_RATE,
    "run_threshold_pace_seconds_per_km": ZoneRequirement.PACE,
    "run_lthr_bpm": ZoneRequirement.HEART_RATE,
}


class PlanningService:
    """Coordinate trusted inputs, pure decisions, and typed persistence."""

    def __init__(
        self,
        repository: PlanningRepository,
        catalog_provider: PlanningCatalogProvider,
        weekly_plan_coach: WeeklyPlanCoach,
    ) -> None:
        self._repository = repository
        self._catalog_provider = catalog_provider
        self._weekly_plan_coach = weekly_plan_coach

    @staticmethod
    def _coach_facts(
        *,
        week_start: date,
        timezone_name: str,
        draft: Any,
    ) -> WeeklyPlanCoachFacts:
        athlete_timezone = ZoneInfo(timezone_name)
        workout_dates = {
            workout.scheduled_at.astimezone(athlete_timezone).date()
            for workout in draft.workouts
        }
        return WeeklyPlanCoachFacts(
            week_start=week_start,
            timezone=timezone_name,
            phase=draft.target.phase,
            workouts=tuple(
                CoachWorkoutFacts(
                    discipline=workout.discipline,
                    name=workout.snapshot.name,
                    scheduled_at=workout.scheduled_at,
                    duration_minutes=workout.snapshot.duration_minutes,
                    intensity=workout.snapshot.intensity_bucket,
                )
                for workout in draft.workouts
            ),
            rest_days=tuple(
                current
                for offset in range(7)
                if (current := week_start + timedelta(days=offset)) not in workout_dates
            ),
        )

    @staticmethod
    def _planning_input(source: Mapping[str, Any]) -> JsonObject:
        snapshot = source.get("input_snapshot")
        if not isinstance(snapshot, dict):
            raise PlanningDomainError("The planning input snapshot is unavailable.")
        required = {"profile", "training_history", "goal", "zones", "ruleset_version"}
        if not required.issubset(snapshot):
            raise PlanningDomainError("The planning input snapshot is incomplete.")
        return dict(snapshot)

    @staticmethod
    def _context_values(
        snapshot: Mapping[str, Any],
    ) -> tuple[
        str,
        date,
        frozenset[Discipline],
        dict[Discipline, ZoneCapability],
    ]:
        profile = snapshot.get("profile")
        goal = snapshot.get("goal")
        zones = snapshot.get("zones")
        if not isinstance(profile, dict) or not isinstance(goal, dict):
            raise PlanningDomainError("Profile and goal inputs are required.")
        if not isinstance(zones, list):
            raise PlanningDomainError("Active discipline zones are required.")
        try:
            timezone_name = str(profile["timezone"])
            ZoneInfo(timezone_name)
            race_date = date.fromisoformat(str(goal["target_date"]))
            goal_disciplines = frozenset(
                Discipline(str(value)) for value in goal["race_discipline_profile"]
            )
        except (KeyError, TypeError, ValueError) as error:
            raise PlanningDomainError("The race planning input is invalid.") from error
        capabilities: dict[Discipline, ZoneCapability] = {}
        for zone in zones:
            if not isinstance(zone, dict):
                raise PlanningDomainError("A zone input is invalid.")
            try:
                discipline = Discipline(str(zone["discipline"]))
                fallback_active = bool(zone["fallback_active"])
                metric = zone.get("metric")
                requirement = (
                    ZoneRequirement.HEART_RATE
                    if fallback_active
                    else _ZONE_REQUIREMENT_BY_METRIC[
                        str(metric["kind"]) if isinstance(metric, dict) else ""
                    ]
                )
            except (KeyError, ValueError) as error:
                raise PlanningDomainError(
                    "An active zone cannot drive the workout catalog."
                ) from error
            capabilities[discipline] = ZoneCapability(
                requirements=frozenset({requirement}),
                fallback_active=fallback_active,
            )
        if not goal_disciplines:
            raise PlanningDomainError("The primary race requires a discipline.")
        return timezone_name, race_date, goal_disciplines, capabilities

    @staticmethod
    def _availability(
        values: tuple[Any, ...],
    ) -> tuple[AvailabilityWindow, ...]:
        return tuple(
            AvailabilityWindow(
                starts_at=value.starts_at,
                ends_at=value.ends_at,
            )
            for value in values
        )

    @staticmethod
    def _load_samples(rows: tuple[JsonObject, ...]) -> tuple[PlanLoadSample, ...]:
        try:
            return tuple(
                PlanLoadSample(
                    week_start=date.fromisoformat(str(row["week_start"])),
                    load=InternalLoad(Decimal(str(row["planned_tss"]))),
                    phase=TrainingPhase(str(row["phase"])),
                    realized_load=(
                        InternalLoad(Decimal(str(row["realized_tss"])))
                        if row.get("realized_tss") is not None
                        else None
                    ),
                    target_basis=(
                        PlanningTargetBasis(str(row["target_basis"]))
                        if row.get("target_basis") is not None
                        else None
                    ),
                    planned_high_minutes=(
                        DurationMinutes(Decimal(str(row["planned_high_minutes"])))
                        if row.get("planned_high_minutes") is not None
                        else None
                    ),
                    planned_total_minutes=(
                        DurationMinutes(Decimal(str(row["planned_total_minutes"])))
                        if row.get("planned_total_minutes") is not None
                        else None
                    ),
                    realized_high_minutes=(
                        DurationMinutes(Decimal(str(row["realized_high_minutes"])))
                        if row.get("realized_high_minutes") is not None
                        else None
                    ),
                    realized_classified_minutes=(
                        DurationMinutes(
                            Decimal(str(row["realized_classified_minutes"]))
                        )
                        if row.get("realized_classified_minutes") is not None
                        else None
                    ),
                    realized_total_minutes=(
                        DurationMinutes(Decimal(str(row["realized_total_minutes"])))
                        if row.get("realized_total_minutes") is not None
                        else None
                    ),
                    completed_activity_count=(
                        int(row["completed_activity_count"])
                        if row.get("completed_activity_count") is not None
                        else None
                    ),
                )
                for row in rows
            )
        except (KeyError, ValueError) as error:
            raise PlanningDomainError("Stored plan load history is invalid.") from error

    @staticmethod
    def _generation_fingerprint(
        *,
        input_fingerprint: str,
        week_start: date,
        availability: tuple[AvailabilityWindow, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selected_template_ids: tuple[UUID, ...] | None,
        checkin_id: UUID | None = None,
    ) -> str:
        canonical = {
            "input_fingerprint": input_fingerprint,
            "week_start": week_start.isoformat(),
            "availability": [
                {
                    "starts_at": window.starts_at.isoformat(),
                    "ends_at": window.ends_at.isoformat(),
                }
                for window in availability
            ],
            "confirmed_injuries": sorted(item.value for item in injuries),
            "low_only_disciplines": sorted(item.value for item in low_only_disciplines),
            "checkin_id": str(checkin_id) if checkin_id is not None else None,
            "selected_template_ids": (
                sorted(str(value) for value in selected_template_ids)
                if selected_template_ids is not None
                else None
            ),
        }
        return hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _proposal_payload(
        *,
        request_id: UUID | None,
        input_fingerprint: str,
        generation_fingerprint: str,
        plan_id: UUID | None,
        expected_base_revision: int,
        week_start: date,
        timezone_name: str,
        availability: tuple[AvailabilityWindow, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        goal_disciplines: frozenset[Discipline],
        draft: Any,
        workout_source: str,
        checkin_id: UUID | None = None,
    ) -> JsonObject:
        return {
            "initial_plan_request_id": (
                str(request_id) if request_id is not None else None
            ),
            "input_fingerprint": input_fingerprint,
            "generation_fingerprint": generation_fingerprint,
            "plan_id": str(plan_id) if plan_id is not None else None,
            "expected_base_revision": expected_base_revision,
            "week_start": week_start.isoformat(),
            "timezone": timezone_name,
            "phase": draft.target.phase.value,
            "target_basis": draft.target.basis.value,
            "target_tss": str(draft.target.target.value),
            "taper_period": (
                draft.target.taper_period.value
                if draft.target.taper_period is not None
                else None
            ),
            "total_duration_minutes": str(draft.total_duration_minutes),
            "low_intensity_percent": str(draft.low_intensity_percent),
            "high_intensity_percent": str(draft.high_intensity_percent),
            "confirmed_injuries": sorted(item.value for item in injuries),
            "low_only_disciplines": sorted(item.value for item in low_only_disciplines),
            "goal_disciplines": sorted(item.value for item in goal_disciplines),
            "checkin_id": str(checkin_id) if checkin_id is not None else None,
            "availability": [
                {
                    "starts_at": window.starts_at.isoformat(),
                    "ends_at": window.ends_at.isoformat(),
                }
                for window in availability
            ],
            "workouts": [
                {
                    "template_id": str(workout.snapshot.template_id),
                    "discipline": workout.discipline.value,
                    "scheduled_at": workout.scheduled_at.isoformat(),
                    "source": workout_source,
                }
                for workout in draft.workouts
            ],
            "warnings": [
                {
                    "rule_id": warning.rule_id.value,
                    "code": warning.code,
                    "severity": warning.severity,
                    "message": warning.message,
                    "affected_template_id": (
                        str(warning.affected_template_id)
                        if warning.affected_template_id is not None
                        else None
                    ),
                }
                for warning in draft.warnings
            ],
            "planned_tss": str(draft.planned_load.value),
            "ruleset_version": PHASE_3_RULESET_V3.version.value,
        }

    async def _build_and_persist(
        self,
        *,
        athlete_id: UUID,
        input_source: Mapping[str, Any],
        request_id: UUID | None,
        plan_id: UUID | None,
        expected_base_revision: int,
        week_start: date,
        availability: tuple[AvailabilityWindow, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selected_template_ids: tuple[UUID, ...] | None,
        checkin_id: UUID | None = None,
    ) -> JsonObject:
        snapshot = self._planning_input(input_source)
        timezone_name, race_date, disciplines, capabilities = self._context_values(
            snapshot
        )
        catalog = active_catalog(await self._catalog_provider.fetch_catalog())
        prior_loads = self._load_samples(
            await self._repository.fetch_load_history(athlete_id, week_start)
        )
        draft = build_weekly_plan(
            week_start=week_start,
            timezone_name=timezone_name,
            race_date=race_date,
            catalog=catalog,
            prior_loads=prior_loads,
            goal_disciplines=disciplines,
            confirmed_injuries=injuries,
            low_only_disciplines=low_only_disciplines,
            zone_capabilities=capabilities,
            availability=availability,
            selected_template_ids=selected_template_ids,
            maintenance_active=bool(input_source.get("maintenance_active", False)),
        )
        try:
            input_fingerprint = str(input_source["input_fingerprint"])
        except KeyError as error:
            raise PlanningDomainError(
                "The planning input fingerprint is missing."
            ) from error
        generation_fingerprint = self._generation_fingerprint(
            input_fingerprint=input_fingerprint,
            week_start=week_start,
            availability=availability,
            injuries=injuries,
            low_only_disciplines=low_only_disciplines,
            selected_template_ids=selected_template_ids,
            checkin_id=checkin_id,
        )
        result = await self._repository.create_plan_proposal(
            athlete_id,
            self._proposal_payload(
                request_id=request_id,
                input_fingerprint=input_fingerprint,
                generation_fingerprint=generation_fingerprint,
                plan_id=plan_id,
                expected_base_revision=expected_base_revision,
                week_start=week_start,
                timezone_name=timezone_name,
                availability=availability,
                injuries=injuries,
                low_only_disciplines=low_only_disciplines,
                goal_disciplines=disciplines,
                draft=draft,
                workout_source=(
                    "athlete_selected"
                    if selected_template_ids is not None
                    else "auto_planned"
                ),
                checkin_id=checkin_id,
            ),
        )
        proposal_id = UUID(str(result["proposal_id"]))
        coach_facts = self._coach_facts(
            week_start=week_start,
            timezone_name=timezone_name,
            draft=draft,
        )
        try:
            explanation = await self._weekly_plan_coach.explain(coach_facts)
        except CoachProviderError:
            logging.getLogger(__name__).warning(
                "Weekly-plan coach unavailable; using deterministic explanation",
                extra={
                    "event": "weekly_plan_coach_fallback",
                    "proposal_id": str(proposal_id),
                },
            )
            explanation = deterministic_weekly_plan_explanation(coach_facts)
        try:
            await self._repository.set_plan_proposal_explanation(
                athlete_id,
                proposal_id,
                explanation.public_explanation,
            )
        except PlanningRepositoryError:
            # The plan is already safely pending. A missing explanation migration or
            # transient metadata write must not turn an idempotent plan into an error.
            logging.getLogger(__name__).warning(
                "Weekly-plan explanation could not be persisted",
                extra={
                    "event": "weekly_plan_explanation_persistence_skipped",
                    "proposal_id": str(proposal_id),
                },
            )
        return result

    async def generate_initial_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        request: WeeklyPlanProposalRequest,
    ) -> WeeklyPlanProposalResponse:
        source = await self._repository.fetch_initial_request(
            access_token,
            athlete_id,
        )
        if source is None:
            raise PlanningDomainError(
                "Complete onboarding before generating the first weekly plan."
            )
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=source,
            request_id=UUID(str(source["id"])),
            plan_id=None,
            expected_base_revision=0,
            week_start=request.week_start,
            availability=self._availability(request.availability),
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
            selected_template_ids=request.selected_template_ids,
        )
        proposal_id = UUID(str(result["proposal_id"]))
        plan_id = UUID(str(result["plan_id"]))
        revision = int(result["revision"])
        plan = await self._repository.fetch_plan(
            access_token,
            plan_id,
            revision,
        )
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=WeeklyPlanResponse.model_validate(plan),
        )

    async def generate_schedule_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        request: ScheduleProposalRequest,
    ) -> WeeklyPlanProposalResponse:
        context = await self._repository.fetch_plan_context(athlete_id, plan_id)
        active_revision = context.get("active_revision")
        current_base = int(active_revision) if active_revision is not None else 0
        if current_base != request.expected_base_revision:
            raise PlanningConstraintError(
                "proposal_stale",
                "The plan changed after this schedule request was prepared.",
            )
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=context,
            request_id=(
                UUID(str(context["initial_plan_request_id"]))
                if context.get("initial_plan_request_id") is not None
                else None
            ),
            plan_id=plan_id,
            expected_base_revision=request.expected_base_revision,
            week_start=date.fromisoformat(str(context["week_start"])),
            availability=self._availability(request.availability),
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
            selected_template_ids=request.selected_template_ids,
        )
        proposal_id = UUID(str(result["proposal_id"]))
        revision = int(result["revision"])
        plan = await self._repository.fetch_plan(access_token, plan_id, revision)
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=WeeklyPlanResponse.model_validate(plan),
        )

    async def generate_checkin_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        *,
        checkin_id: UUID,
        input_source: Mapping[str, Any],
        week_start: date,
        availability: tuple[AvailabilityWindow, ...],
        blocked_disciplines: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
    ) -> WeeklyPlanProposalResponse:
        """Generate the idempotent pending plan for confirmed weekly context."""
        plan_id = (
            UUID(str(input_source["plan_id"]))
            if input_source.get("plan_id") is not None
            else None
        )
        expected_base_revision = int(input_source.get("active_revision") or 0)
        request_id = (
            UUID(str(input_source["initial_plan_request_id"]))
            if input_source.get("initial_plan_request_id") is not None
            else None
        )
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=input_source,
            request_id=request_id,
            plan_id=plan_id,
            expected_base_revision=expected_base_revision,
            week_start=week_start,
            availability=availability,
            injuries=blocked_disciplines,
            low_only_disciplines=low_only_disciplines,
            selected_template_ids=None,
            checkin_id=checkin_id,
        )
        proposal_id = UUID(str(result["proposal_id"]))
        persisted_plan_id = UUID(str(result["plan_id"]))
        revision = int(result["revision"])
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=WeeklyPlanResponse.model_validate(
                await self._repository.fetch_plan(
                    access_token,
                    persisted_plan_id,
                    revision,
                )
            ),
        )

    async def get_plan(
        self,
        access_token: str,
        plan_id: UUID,
        revision: int | None,
    ) -> WeeklyPlanResponse:
        return WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(access_token, plan_id, revision)
        )

    async def get_deck(
        self,
        athlete_id: UUID,
        plan_id: UUID,
        *,
        expected_revision: int | None = None,
        selected_template_ids: tuple[UUID, ...] = (),
    ) -> WorkoutDeckResponse:
        context = await self._repository.fetch_plan_context(athlete_id, plan_id)
        snapshot = self._planning_input(context)
        _, _, disciplines, capabilities = self._context_values(snapshot)
        try:
            phase = TrainingPhase(str(context["phase"]))
            revision = int(context["revision"])
            injuries = frozenset(
                Discipline(str(value))
                for value in context.get("confirmed_injuries", [])
            )
        except (KeyError, ValueError) as error:
            raise PlanningDomainError("Stored plan context is invalid.") from error
        if expected_revision is not None and revision != expected_revision:
            raise PlanningConstraintError(
                "plan_revision_stale",
                "The plan changed after this deck request was prepared.",
            )
        deck = eligible_workouts(
            catalog=active_catalog(await self._catalog_provider.fetch_catalog()),
            phase=phase,
            goal_disciplines=disciplines,
            confirmed_injuries=injuries,
            low_only_disciplines=frozenset(
                Discipline(str(value))
                for value in context.get("low_only_disciplines", [])
            ),
            zone_capabilities=capabilities,
        )
        if selected_template_ids:
            try:
                target = InternalLoad(Decimal(str(context["target_tss"])))
            except (KeyError, ValueError) as error:
                raise PlanningDomainError(
                    "Stored plan target is unavailable for deck recalculation."
                ) from error
            deck = remaining_workout_deck(
                deck=deck,
                target=target,
                selected_template_ids=selected_template_ids,
            )
        return WorkoutDeckResponse(
            plan_id=plan_id,
            revision=revision,
            phase=phase,
            templates=tuple(
                WorkoutDeckItemResponse(
                    id=template.id,
                    template_key=template.template_key,
                    version=template.version,
                    discipline=template.discipline,
                    name=template.name,
                    description=template.description,
                    duration_minutes=template.duration_minutes,
                    distance_meters=template.distance_meters,
                    intensity_bucket=template.intensity_bucket,
                    expected_rpe_min=template.expected_rpe_min,
                    expected_rpe_max=template.expected_rpe_max,
                    segments=tuple(
                        {
                            "sequence": segment.sequence,
                            "name": segment.name,
                            "instructions": segment.instructions,
                            "duration_minutes": segment.duration_minutes,
                            "distance_meters": segment.distance_meters,
                            "zone": segment.zone,
                            "expected_rpe": segment.expected_rpe,
                            "is_swim_technique": segment.is_swim_technique,
                        }
                        for segment in template.segments
                    ),
                )
                for template in deck
            ),
        )

    async def validate_layout(
        self,
        access_token: str,
        plan_id: UUID,
        request: PlanValidationRequest,
    ) -> PlanValidationResponse:
        plan = WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(access_token, plan_id)
        )
        if plan.revision != request.expected_revision:
            raise PlanningConstraintError(
                "plan_revision_stale",
                "The plan changed after this layout was prepared.",
            )
        persisted = {workout.id: workout for workout in plan.workouts}
        submitted = {workout.workout_id for workout in request.workouts}
        if submitted != set(persisted):
            raise PlanningDomainError(
                "A validation layout must contain every workout in the selected "
                "revision."
            )
        warnings = validate_manual_schedule(
            workouts=tuple(
                ScheduledWorkout(
                    workout_id=str(workout.workout_id),
                    disciplines=frozenset({persisted[workout.workout_id].discipline}),
                    intensity=persisted[workout.workout_id].intensity_bucket,
                    starts_at=workout.scheduled_at,
                )
                for workout in request.workouts
            ),
            moved_workout_id=None,
        )
        public_warnings = tuple(
            PlanWarningResponse(
                rule_id=warning.rule_id.value,
                code=warning.code,
                severity="warning",
                message=warning.message,
            )
            for warning in warnings
        )
        return PlanValidationResponse(
            valid_for_generated_schedule=not public_warnings,
            warnings=public_warnings,
        )

    async def move_workout(
        self,
        access_token: str,
        athlete_id: UUID,
        workout_id: UUID,
        request: PlannedWorkoutMoveRequest,
    ) -> WeeklyPlanResponse:
        context = await self._repository.fetch_workout_context(
            access_token,
            workout_id,
        )
        plan = WeeklyPlanResponse.model_validate(context["plan"])
        if plan.revision != request.expected_revision:
            raise PlanningConstraintError(
                "plan_revision_stale",
                "The plan changed after this calendar edit was prepared.",
            )
        moved = next(
            (workout for workout in plan.workouts if workout.id == workout_id),
            None,
        )
        if moved is None:
            raise PlanningDomainError("The planned workout is not active.")
        if moved.discipline in plan.confirmed_injuries:
            raise PlanningConstraintError(
                "injury_exclusion",
                "A confirmed injured discipline cannot be scheduled.",
            )
        athlete_timezone = ZoneInfo(plan.timezone)
        local_date = request.scheduled_at.astimezone(athlete_timezone).date()
        if not plan.week_start <= local_date <= plan.week_start + timedelta(days=6):
            raise PlanningConstraintError(
                "schedule_outside_week",
                "A workout move must remain inside its training week.",
            )
        scheduled = tuple(
            ScheduledWorkout(
                workout_id=str(workout.id),
                disciplines=frozenset({workout.discipline}),
                intensity=workout.intensity_bucket,
                starts_at=(
                    request.scheduled_at
                    if workout.id == workout_id
                    else workout.scheduled_at
                ),
            )
            for workout in plan.workouts
        )
        warnings = list(
            validate_manual_schedule(
                workouts=scheduled,
                moved_workout_id=str(workout_id),
            )
        )
        availability = context.get("availability")
        if isinstance(availability, list):
            duration = timedelta(minutes=float(moved.duration_minutes))
            fits = any(
                datetime.fromisoformat(str(window["starts_at"])) <= request.scheduled_at
                and request.scheduled_at + duration
                <= datetime.fromisoformat(str(window["ends_at"]))
                for window in availability
                if isinstance(window, dict)
            )
            if not fits:
                warnings.append(
                    PlanningWarning(
                        rule_id=RuleId.SOFT_BOUNDARIES,
                        code="outside_confirmed_availability",
                        message=(
                            "This athlete move falls outside the availability "
                            "confirmed for the plan."
                        ),
                    )
                )
        result = await self._repository.move_planned_workout(
            athlete_id,
            workout_id,
            request.expected_revision,
            request.scheduled_at,
            [
                {
                    "rule_id": warning.rule_id.value,
                    "code": warning.code,
                    "severity": warning.severity,
                    "message": warning.message,
                }
                for warning in warnings
            ],
        )
        return WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(
                access_token,
                UUID(str(result["plan_id"])),
                int(result["revision"]),
            )
        )

    async def get_calendar(
        self,
        access_token: str,
        from_datetime: datetime,
        to_datetime: datetime,
    ) -> CalendarResponse:
        if (
            from_datetime.tzinfo is None
            or from_datetime.utcoffset() is None
            or to_datetime.tzinfo is None
            or to_datetime.utcoffset() is None
        ):
            raise PlanningDomainError("Calendar boundaries must be timezone-aware.")
        if to_datetime <= from_datetime:
            raise PlanningDomainError("Calendar end must follow its start.")
        if to_datetime - from_datetime > timedelta(days=93):
            raise PlanningDomainError("Calendar ranges are limited to 93 days.")
        return CalendarResponse(
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            workouts=tuple(
                PlannedWorkoutResponse.model_validate(row)
                for row in await self._repository.fetch_calendar(
                    access_token,
                    from_datetime,
                    to_datetime,
                )
            ),
            rest_days=tuple(
                RestDayResponse.model_validate(row)
                for row in await self._repository.fetch_calendar_rest_days(
                    access_token,
                    from_datetime,
                    to_datetime,
                )
            ),
        )

    async def proposal_kind(self, access_token: str, proposal_id: UUID) -> str:
        return str(
            (await self._repository.fetch_proposal(access_token, proposal_id))["kind"]
        )

    async def list_proposals(
        self,
        access_token: str,
        state: str | None,
    ) -> tuple[ChangeProposalSummaryResponse, ...]:
        return tuple(
            ChangeProposalSummaryResponse.model_validate(row)
            for row in await self._repository.list_proposals(access_token, state)
        )

    async def get_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> ChangeProposalSummaryResponse:
        return ChangeProposalSummaryResponse.model_validate(
            await self._repository.fetch_proposal(access_token, proposal_id)
        )

    async def approve_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_revision: int,
    ) -> PlanProposalDecisionResponse:
        return PlanProposalDecisionResponse.model_validate(
            await self._repository.approve_plan_proposal(
                access_token,
                proposal_id,
                expected_base_revision,
            )
        )

    async def reject_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> PlanProposalDecisionResponse:
        return PlanProposalDecisionResponse.model_validate(
            await self._repository.reject_plan_proposal(
                access_token,
                proposal_id,
            )
        )
