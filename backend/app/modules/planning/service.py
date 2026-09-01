"""Application orchestration for deterministic weekly planning."""

import hashlib
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import combinations
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

from app.modules.calibration.domain import TestSchedulingMode, validate_test_schedule
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
from app.modules.physiology.specification import PHASE_10_RULESET_V1
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
    PlanLoadSample,
    PlanningConstraintError,
    PlanningTargetBasis,
    PlanningWarning,
    ZoneCapability,
    build_weekly_plan,
    canonical_schedule_instant,
    eligible_workouts,
    remaining_workout_deck,
    validate_manual_schedule,
)
from .repository import JsonObject, PlanningRepository, PlanningRepositoryError
from .schemas import (
    CalendarResponse,
    ChangeProposalSummaryResponse,
    PendingWorkoutAlternativesResponse,
    PendingWorkoutEditRequest,
    PlannedWorkoutMoveRequest,
    PlannedWorkoutResponse,
    PlanProposalDecisionResponse,
    PlanValidationRequest,
    PlanValidationResponse,
    PlanWarningResponse,
    RestDayResponse,
    ScheduleProposalRequest,
    SwipeDraftCreateRequest,
    SwipeDraftPlacementRequest,
    SwipeDraftSubmitRequest,
    SwipeDraftTransitionRequest,
    SwipeTargetComposition,
    SwipeWeekDraftResponse,
    WeeklyPlanProposalRequest,
    WeeklyPlanProposalResponse,
    WeeklyPlanResponse,
    WorkoutDeckItemResponse,
    WorkoutDeckResponse,
)
from .swipe import (
    SwipeDecision,
    SwipeDecisionKind,
    SwipeSelectionState,
    apply_swipe_decision,
    composition_can_extend,
    composition_is_complete,
    discipline_composition,
    reset_passed_cards,
    undo_last_swipe,
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
_RPE_GUIDANCE_PROTOCOL_BY_DISCIPLINE = {
    Discipline.SWIM: "start23_week1_swim_calibration_v1",
    Discipline.BIKE: "start23_week1_bike_calibration_v1",
    Discipline.RUN: "start23_week1_run_calibration_v1",
}


@dataclass(frozen=True, slots=True)
class _SwipePlanningContext:
    """Exact private context used to recalculate every public draft transition."""

    source: JsonObject
    timezone_name: str
    race_date: date
    goal_disciplines: frozenset[Discipline]
    capabilities: dict[Discipline, ZoneCapability]
    catalog: tuple[WorkoutTemplate, ...]
    prior_loads: tuple[PlanLoadSample, ...]
    eligible_deck: tuple[WorkoutTemplate, ...]
    target_workout_count: int
    target_composition: dict[Discipline, int]
    context_fingerprint: str


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
    def _deck_item(template: WorkoutTemplate) -> WorkoutDeckItemResponse:
        return WorkoutDeckItemResponse(
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
                    "zone_target": segment.zone_target,
                    "protocol_target": (
                        {
                            "protocol_id": segment.protocol_target.protocol_id,
                            "segment_id": segment.protocol_target.segment_id,
                            "target_rpe_min": segment.protocol_target.target_rpe_min,
                            "target_rpe_max": segment.protocol_target.target_rpe_max,
                            "intensity_bucket": (
                                segment.protocol_target.intensity_bucket
                            ),
                            "optional": segment.protocol_target.optional,
                        }
                        if segment.protocol_target is not None
                        else None
                    ),
                    "rpe_target": (
                        {
                            "target_rpe_min": segment.rpe_target.target_rpe_min,
                            "target_rpe_max": segment.rpe_target.target_rpe_max,
                            "intensity_bucket": segment.rpe_target.intensity_bucket,
                            "heart_rate_observation_required": (
                                segment.rpe_target.heart_rate_observation_required
                            ),
                        }
                        if segment.rpe_target is not None
                        else None
                    ),
                    "expected_rpe": segment.expected_rpe,
                    "is_swim_technique": segment.is_swim_technique,
                }
                for segment in template.segments
            ),
        )

    @staticmethod
    def _coach_facts(
        *,
        week_start: date,
        timezone_name: str,
        draft: Any,
    ) -> WeeklyPlanCoachFacts:
        workout_dates = {workout.scheduled_date for workout in draft.workouts}
        return WeeklyPlanCoachFacts(
            week_start=week_start,
            timezone=timezone_name,
            phase=draft.target.phase,
            workouts=tuple(
                CoachWorkoutFacts(
                    discipline=workout.discipline,
                    name=workout.snapshot.name,
                    scheduled_date=workout.scheduled_date,
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
        setups = snapshot.get("discipline_setups", [])
        if not isinstance(setups, list):
            raise PlanningDomainError("Discipline setup inputs are invalid.")
        for setup in setups:
            if not isinstance(setup, dict):
                raise PlanningDomainError("A discipline setup input is invalid.")
            try:
                discipline = Discipline(str(setup["discipline"]))
            except (KeyError, ValueError) as error:
                raise PlanningDomainError(
                    "A pending protocol setup is invalid."
                ) from error
            current = capabilities.get(discipline, ZoneCapability(frozenset()))
            protocol_ids = current.protocol_ids
            protocol_id = setup.get("protocol_id")
            if setup.get("setup_status") in {"test_pending", "calibration_pending"}:
                if not isinstance(protocol_id, str) or not protocol_id:
                    raise PlanningDomainError("A pending protocol setup is invalid.")
                protocol_ids |= frozenset({protocol_id})
            route = str(setup.get("setup_route", ""))
            rpe_guided = current.rpe_guided or (
                discipline not in capabilities
                and route in {"field_test", "calibration_week", "rpe_only"}
            )
            if rpe_guided:
                protocol_ids |= frozenset(
                    {_RPE_GUIDANCE_PROTOCOL_BY_DISCIPLINE[discipline]}
                )
            capabilities[discipline] = ZoneCapability(
                requirements=current.requirements,
                fallback_active=current.fallback_active,
                protocol_ids=protocol_ids,
                rpe_guided=rpe_guided,
            )
        if not goal_disciplines:
            raise PlanningDomainError("The primary race requires a discipline.")
        return timezone_name, race_date, goal_disciplines, capabilities

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

    async def _prepare_swipe_context(
        self,
        *,
        athlete_id: UUID,
        input_source: Mapping[str, Any],
        initial_plan_request_id: UUID,
        plan_id: UUID | None,
        base_plan_revision: int,
        context_plan_revision: int | None,
        week_start: date,
        available_dates: tuple[date, ...],
        availability_source: str,
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
    ) -> _SwipePlanningContext:
        """Rebuild the exact deterministic context and its non-sensitive hash."""

        snapshot = self._planning_input(input_source)
        timezone_name, race_date, disciplines, capabilities = self._context_values(
            snapshot
        )
        catalog = active_catalog(await self._catalog_provider.fetch_catalog())
        history_rows = await self._repository.fetch_load_history(athlete_id, week_start)
        prior_loads = self._load_samples(history_rows)
        automatic = build_weekly_plan(
            week_start=week_start,
            timezone_name=timezone_name,
            race_date=race_date,
            catalog=catalog,
            prior_loads=prior_loads,
            goal_disciplines=disciplines,
            confirmed_injuries=injuries,
            low_only_disciplines=low_only_disciplines,
            zone_capabilities=capabilities,
            available_dates=available_dates,
            maintenance_active=bool(input_source.get("maintenance_active", False)),
        )
        eligible = tuple(
            template
            for template in eligible_workouts(
                catalog=catalog,
                phase=automatic.target.phase,
                goal_disciplines=disciplines,
                confirmed_injuries=injuries,
                low_only_disciplines=low_only_disciplines,
                zone_capabilities=capabilities,
            )
            if not template.explicit_scheduling_only
        )
        composition = discipline_composition(
            tuple(workout.discipline for workout in automatic.workouts)
        )
        try:
            input_fingerprint = str(input_source["input_fingerprint"])
        except KeyError as error:
            raise PlanningDomainError(
                "The planning input fingerprint is missing."
            ) from error
        canonical = {
            "athlete_id": str(athlete_id),
            "initial_plan_request_id": str(initial_plan_request_id),
            "input_fingerprint": input_fingerprint,
            "plan_id": str(plan_id) if plan_id is not None else None,
            "base_plan_revision": base_plan_revision,
            "context_plan_revision": context_plan_revision,
            "week_start": week_start.isoformat(),
            "available_dates": sorted(value.isoformat() for value in available_dates),
            "availability_source": availability_source,
            "confirmed_injuries": sorted(item.value for item in injuries),
            "low_only_disciplines": sorted(item.value for item in low_only_disciplines),
            "maintenance_active": bool(input_source.get("maintenance_active", False)),
            "ruleset_version": PHASE_10_RULESET_V1.version.value,
            "history": history_rows,
            "catalog": [
                {"id": str(template.id), "version": template.version}
                for template in eligible
            ],
            "target_workout_count": len(automatic.workouts),
            "target_composition": {
                discipline.value: composition[discipline] for discipline in Discipline
            },
        }
        context_fingerprint = hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode()
        ).hexdigest()
        return _SwipePlanningContext(
            source=dict(input_source),
            timezone_name=timezone_name,
            race_date=race_date,
            goal_disciplines=disciplines,
            capabilities=capabilities,
            catalog=catalog,
            prior_loads=prior_loads,
            eligible_deck=eligible,
            target_workout_count=len(automatic.workouts),
            target_composition=composition,
            context_fingerprint=context_fingerprint,
        )

    @staticmethod
    def _swipe_history(row: Mapping[str, Any]) -> SwipeSelectionState:
        raw = row.get("decision_history", [])
        if not isinstance(raw, list):
            raise PlanningDomainError("Stored swipe decision history is invalid.")
        try:
            return SwipeSelectionState(
                history=tuple(
                    SwipeDecision(
                        action=SwipeDecisionKind(str(entry["action"])),
                        template_id=UUID(str(entry["template_id"])),
                    )
                    for entry in raw
                    if isinstance(entry, dict)
                )
            )
        except (KeyError, ValueError) as error:
            raise PlanningDomainError(
                "Stored swipe decision history is invalid."
            ) from error

    def _selection_has_completion(
        self,
        *,
        context: _SwipePlanningContext,
        week_start: date,
        available_dates: tuple[date, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        accepted_template_ids: tuple[UUID, ...],
        passed_template_ids: frozenset[UUID],
    ) -> bool:
        by_id = {template.id: template for template in context.eligible_deck}
        if not set(accepted_template_ids) <= set(by_id):
            return False
        remaining_slots = context.target_workout_count - len(accepted_template_ids)
        if remaining_slots < 0:
            return False
        pool = tuple(
            template
            for template in context.eligible_deck
            if template.id not in accepted_template_ids
            and template.id not in passed_template_ids
        )
        candidate_sets = (
            (accepted_template_ids,)
            if remaining_slots == 0
            else tuple(
                accepted_template_ids + tuple(template.id for template in choice)
                for choice in combinations(pool, remaining_slots)
            )
        )
        for selected_ids in candidate_sets:
            selected_disciplines = tuple(
                by_id[value].discipline for value in selected_ids
            )
            if not composition_is_complete(
                accepted_disciplines=selected_disciplines,
                target_composition=context.target_composition,
            ):
                continue
            try:
                build_weekly_plan(
                    week_start=week_start,
                    timezone_name=context.timezone_name,
                    race_date=context.race_date,
                    catalog=context.catalog,
                    prior_loads=context.prior_loads,
                    goal_disciplines=context.goal_disciplines,
                    confirmed_injuries=injuries,
                    low_only_disciplines=low_only_disciplines,
                    zone_capabilities=context.capabilities,
                    available_dates=available_dates,
                    selected_template_ids=selected_ids,
                    maintenance_active=bool(
                        context.source.get("maintenance_active", False)
                    ),
                )
            except PlanningConstraintError:
                continue
            return True
        return False

    def _next_swipe_candidate(
        self,
        *,
        context: _SwipePlanningContext,
        week_start: date,
        available_dates: tuple[date, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selection: SwipeSelectionState,
    ) -> UUID | None:
        accepted = selection.accepted_template_ids
        passed = selection.passed_template_ids
        by_id = {template.id: template for template in context.eligible_deck}
        accepted_disciplines = tuple(by_id[value].discipline for value in accepted)
        for template in context.eligible_deck:
            if template.id in accepted or template.id in passed:
                continue
            if not composition_can_extend(
                accepted_disciplines=accepted_disciplines,
                candidate_discipline=template.discipline,
                target_composition=context.target_composition,
            ):
                continue
            if self._selection_has_completion(
                context=context,
                week_start=week_start,
                available_dates=available_dates,
                injuries=injuries,
                low_only_disciplines=low_only_disciplines,
                accepted_template_ids=accepted + (template.id,),
                passed_template_ids=passed,
            ):
                return template.id
        return None

    @staticmethod
    def _swipe_update_payload(
        *,
        context_fingerprint: str,
        selection: SwipeSelectionState,
        current_template_id: UUID | None,
        placements: Mapping[UUID, date],
        state: str,
        plan_id: UUID | None = None,
        proposal_id: UUID | None = None,
    ) -> JsonObject:
        return {
            "context_fingerprint": context_fingerprint,
            "accepted_template_ids": [
                str(value) for value in selection.accepted_template_ids
            ],
            "passed_template_ids": [
                str(value) for value in sorted(selection.passed_template_ids, key=str)
            ],
            "current_template_id": (
                str(current_template_id) if current_template_id is not None else None
            ),
            "decision_history": [
                {
                    "action": decision.action.value,
                    "template_id": str(decision.template_id),
                }
                for decision in selection.history
            ],
            "placements": {
                str(template_id): scheduled_date.isoformat()
                for template_id, scheduled_date in placements.items()
            },
            "state": state,
            "plan_id": str(plan_id) if plan_id is not None else None,
            "proposal_id": str(proposal_id) if proposal_id is not None else None,
        }

    def _swipe_response(
        self,
        row: Mapping[str, Any],
        context: _SwipePlanningContext,
    ) -> SwipeWeekDraftResponse:
        if row.get("state") == "cancelled":
            raise PlanningConstraintError(
                "swipe_draft_closed",
                "This swipe draft was replaced by a newer draft.",
            )
        selection = self._swipe_history(row)
        by_id = {template.id: template for template in context.eligible_deck}
        try:
            accepted = tuple(
                self._deck_item(by_id[template_id])
                for template_id in selection.accepted_template_ids
            )
            current_id = (
                UUID(str(row["current_template_id"]))
                if row.get("current_template_id") is not None
                else None
            )
            current = self._deck_item(by_id[current_id]) if current_id else None
            raw_placements = row.get("placements", {})
            if not isinstance(raw_placements, dict):
                raise ValueError
            placements = tuple(
                {
                    "template_id": template_id,
                    "scheduled_date": date.fromisoformat(
                        str(raw_placements[str(template_id)])
                    ),
                }
                for template_id in selection.accepted_template_ids
                if str(template_id) in raw_placements
            )
            composition = SwipeTargetComposition(
                **{
                    discipline.value: context.target_composition[discipline]
                    for discipline in Discipline
                }
            )
            state = str(row["state"])
            public_warnings: tuple[PlanWarningResponse, ...] = ()
            if state == "placement":
                available_dates = tuple(
                    date.fromisoformat(str(value))
                    for value in row.get("available_dates", [])
                )
                preview = build_weekly_plan(
                    week_start=date.fromisoformat(str(row["week_start"])),
                    timezone_name=context.timezone_name,
                    race_date=context.race_date,
                    catalog=context.catalog,
                    prior_loads=context.prior_loads,
                    goal_disciplines=context.goal_disciplines,
                    confirmed_injuries=frozenset(
                        Discipline(str(value))
                        for value in row.get("confirmed_injuries", [])
                    ),
                    low_only_disciplines=frozenset(
                        Discipline(str(value))
                        for value in row.get("low_only_disciplines", [])
                    ),
                    zone_capabilities=context.capabilities,
                    available_dates=available_dates,
                    selected_template_ids=selection.accepted_template_ids,
                    fixed_template_dates={
                        UUID(str(key)): date.fromisoformat(str(value))
                        for key, value in raw_placements.items()
                    },
                    maintenance_active=bool(
                        context.source.get("maintenance_active", False)
                    ),
                )
                public_warnings = tuple(
                    PlanWarningResponse(
                        rule_id=warning.rule_id.value,
                        code=warning.code,
                        severity=(
                            warning.severity
                            if warning.severity in {"info", "warning", "conflict"}
                            else "warning"
                        ),
                        message=warning.message,
                    )
                    for warning in preview.warnings
                )
            return SwipeWeekDraftResponse(
                id=UUID(str(row["id"])),
                revision=int(row["revision"]),
                state=state,
                week_start=date.fromisoformat(str(row["week_start"])),
                available_dates=tuple(
                    date.fromisoformat(str(value))
                    for value in row.get("available_dates", [])
                ),
                availability_source=str(row["availability_source"]),
                target_workout_count=context.target_workout_count,
                target_composition=composition,
                accepted_workouts=accepted,
                current_candidate=current,
                placements=placements,
                warnings=public_warnings,
                passed_count=len(selection.passed_template_ids),
                exhausted=state == "collecting" and current is None,
                can_undo=bool(selection.history),
                ruleset_version=str(row["ruleset_version"]),
                plan_id=(
                    UUID(str(row["plan_id"]))
                    if row.get("plan_id") is not None
                    else None
                ),
                proposal_id=(
                    UUID(str(row["proposal_id"]))
                    if row.get("proposal_id") is not None
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise PlanningDomainError("Stored swipe draft state is invalid.") from error

    @staticmethod
    def _generation_fingerprint(
        *,
        input_fingerprint: str,
        week_start: date,
        available_dates: tuple[date, ...],
        availability_source: str,
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selected_template_ids: tuple[UUID, ...] | None,
        fixed_template_dates: Mapping[UUID, date] | None = None,
        checkin_id: UUID | None = None,
    ) -> str:
        canonical = {
            "input_fingerprint": input_fingerprint,
            "week_start": week_start.isoformat(),
            "available_dates": sorted(value.isoformat() for value in available_dates),
            "availability_source": availability_source,
            "confirmed_injuries": sorted(item.value for item in injuries),
            "low_only_disciplines": sorted(item.value for item in low_only_disciplines),
            "checkin_id": str(checkin_id) if checkin_id is not None else None,
            "selected_template_ids": (
                sorted(str(value) for value in selected_template_ids)
                if selected_template_ids is not None
                else None
            ),
            "fixed_template_dates": {
                str(template_id): scheduled_date.isoformat()
                for template_id, scheduled_date in sorted(
                    (fixed_template_dates or {}).items(),
                    key=lambda item: str(item[0]),
                )
            },
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
        available_dates: tuple[date, ...],
        availability_source: str,
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
            # The legacy column keeps only date strings from Phase 10 onward.
            "availability": sorted(value.isoformat() for value in available_dates),
            "available_dates": sorted(value.isoformat() for value in available_dates),
            "availability_source": availability_source,
            "workouts": [
                {
                    "template_id": str(workout.snapshot.template_id),
                    "discipline": workout.discipline.value,
                    "scheduled_date": workout.scheduled_date.isoformat(),
                    # Internal compatibility projection for pre-Phase-10 activity
                    # RPCs. It is never returned in the public plan/calendar DTO.
                    "scheduled_at": canonical_schedule_instant(
                        workout.scheduled_date,
                        timezone_name=timezone_name,
                    ).isoformat(),
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
            "ruleset_version": PHASE_10_RULESET_V1.version.value,
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
        available_dates: tuple[date, ...],
        availability_source: str,
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selected_template_ids: tuple[UUID, ...] | None,
        fixed_template_dates: Mapping[UUID, date] | None = None,
        checkin_id: UUID | None = None,
        allow_explicit_test_selection: bool = False,
    ) -> JsonObject:
        snapshot = self._planning_input(input_source)
        timezone_name, race_date, disciplines, capabilities = self._context_values(
            snapshot
        )
        catalog = active_catalog(await self._catalog_provider.fetch_catalog())
        if selected_template_ids is not None and not allow_explicit_test_selection:
            selected_ids = set(selected_template_ids)
            if any(
                template.id in selected_ids and template.explicit_scheduling_only
                for template in catalog
            ):
                raise PlanningConstraintError(
                    "field_test_assignment_required",
                    "Field-test workouts must use the typed test-assignment flow.",
                )
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
            available_dates=available_dates,
            selected_template_ids=selected_template_ids,
            fixed_template_dates=fixed_template_dates,
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
            available_dates=available_dates,
            availability_source=availability_source,
            injuries=injuries,
            low_only_disciplines=low_only_disciplines,
            selected_template_ids=selected_template_ids,
            fixed_template_dates=fixed_template_dates,
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
                available_dates=available_dates,
                availability_source=availability_source,
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
        if request.reuse_previous_week:
            available_dates = await self._repository.fetch_previous_available_dates(
                athlete_id,
                request.week_start,
            )
            if not available_dates:
                raise PlanningConstraintError(
                    "previous_week_availability_unavailable",
                    "No approved previous-week availability is available to copy.",
                )
            availability_source = "previous_week"
        else:
            available_dates = request.available_dates
            availability_source = "explicit"
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=source,
            request_id=UUID(str(source["id"])),
            plan_id=None,
            expected_base_revision=0,
            week_start=request.week_start,
            available_dates=available_dates,
            availability_source=availability_source,
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
            selected_template_ids=request.selected_template_ids,
            fixed_template_dates={
                item.template_id: item.scheduled_date
                for item in request.fixed_workout_dates
            },
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

    async def _load_swipe_draft_context(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
    ) -> tuple[JsonObject, _SwipePlanningContext]:
        row = await self._repository.fetch_swipe_draft(access_token, draft_id)
        if UUID(str(row["athlete_id"])) != athlete_id:
            raise PlanningConstraintError(
                "swipe_draft_owner_mismatch",
                "The swipe draft does not belong to the authenticated athlete.",
            )
        try:
            initial_request_id = UUID(str(row["initial_plan_request_id"]))
            context_revision = (
                int(row["context_plan_revision"])
                if row.get("context_plan_revision") is not None
                else None
            )
            plan_id = (
                UUID(str(row["plan_id"])) if row.get("plan_id") is not None else None
            )
            week_start = date.fromisoformat(str(row["week_start"]))
            available_dates = tuple(
                date.fromisoformat(str(value))
                for value in row.get("available_dates", [])
            )
            injuries = frozenset(
                Discipline(str(value)) for value in row.get("confirmed_injuries", [])
            )
            low_only = frozenset(
                Discipline(str(value)) for value in row.get("low_only_disciplines", [])
            )
        except (KeyError, TypeError, ValueError) as error:
            raise PlanningDomainError(
                "Stored swipe draft context is invalid."
            ) from error

        source: JsonObject
        if context_revision is not None:
            if plan_id is None:
                raise PlanningDomainError("Stored swipe draft plan binding is invalid.")
            source = await self._repository.fetch_plan_context(athlete_id, plan_id)
            current_base = int(source.get("active_revision") or 0)
            if (
                current_base != int(row["base_plan_revision"])
                or int(source.get("revision") or 0) != context_revision
                or date.fromisoformat(str(source["week_start"])) != week_start
            ):
                raise PlanningConstraintError(
                    "swipe_draft_context_stale",
                    "The bound plan revision changed. Start a new swipe draft.",
                )
        else:
            initial_source = await self._repository.fetch_initial_request(
                access_token,
                athlete_id,
            )
            if (
                initial_source is None
                or UUID(str(initial_source["id"])) != initial_request_id
            ):
                raise PlanningConstraintError(
                    "swipe_draft_context_stale",
                    "The confirmed planning input changed. Start a new swipe draft.",
                )
            source = initial_source
            plan_id = None

        if (
            str(source.get("input_fingerprint")) != str(row["input_fingerprint"])
            or UUID(str(source.get("initial_plan_request_id", source.get("id"))))
            != initial_request_id
        ):
            raise PlanningConstraintError(
                "swipe_draft_context_stale",
                "The confirmed planning input changed. Start a new swipe draft.",
            )
        context = await self._prepare_swipe_context(
            athlete_id=athlete_id,
            input_source=source,
            initial_plan_request_id=initial_request_id,
            plan_id=plan_id,
            base_plan_revision=int(row["base_plan_revision"]),
            context_plan_revision=context_revision,
            week_start=week_start,
            available_dates=available_dates,
            availability_source=str(row["availability_source"]),
            injuries=injuries,
            low_only_disciplines=low_only,
        )
        if context.context_fingerprint != str(row["context_fingerprint"]):
            raise PlanningConstraintError(
                "swipe_draft_context_stale",
                "Planning history or catalog context changed. Start a new swipe draft.",
            )
        return row, context

    async def create_swipe_draft(
        self,
        access_token: str,
        athlete_id: UUID,
        request: SwipeDraftCreateRequest,
    ) -> SwipeWeekDraftResponse:
        """Create or resume one exact server-authoritative swipe draft."""

        if request.plan_id is None:
            source = await self._repository.fetch_initial_request(
                access_token,
                athlete_id,
            )
            if source is None:
                raise PlanningDomainError(
                    "Complete onboarding before starting a swipe week."
                )
            initial_request_id = UUID(str(source["id"]))
            context_revision = None
        else:
            source = await self._repository.fetch_plan_context(
                athlete_id,
                request.plan_id,
            )
            current_base = int(source.get("active_revision") or 0)
            if current_base != request.expected_base_revision:
                raise PlanningConstraintError(
                    "swipe_draft_base_stale",
                    "The plan changed before this swipe draft was started.",
                )
            if date.fromisoformat(str(source["week_start"])) != request.week_start:
                raise PlanningConstraintError(
                    "swipe_draft_week_mismatch",
                    "The selected plan does not belong to this local week.",
                )
            initial_request_id = UUID(str(source["initial_plan_request_id"]))
            context_revision = int(source["revision"])

        if request.reuse_previous_week:
            available_dates = await self._repository.fetch_previous_available_dates(
                athlete_id,
                request.week_start,
            )
            if not available_dates:
                raise PlanningConstraintError(
                    "previous_week_availability_unavailable",
                    "No approved previous-week availability is available to copy.",
                )
            availability_source = "previous_week"
        else:
            available_dates = request.available_dates
            availability_source = "explicit"

        context = await self._prepare_swipe_context(
            athlete_id=athlete_id,
            input_source=source,
            initial_plan_request_id=initial_request_id,
            plan_id=request.plan_id,
            base_plan_revision=request.expected_base_revision,
            context_plan_revision=context_revision,
            week_start=request.week_start,
            available_dates=available_dates,
            availability_source=availability_source,
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
        )
        selection = SwipeSelectionState()
        current = self._next_swipe_candidate(
            context=context,
            week_start=request.week_start,
            available_dates=available_dates,
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
            selection=selection,
        )
        if current is None and context.target_workout_count > 0:
            raise PlanningConstraintError(
                "swipe_draft_no_completion",
                "No eligible card sequence can complete this weekly target.",
            )
        row = await self._repository.create_swipe_draft(
            athlete_id,
            {
                "plan_id": str(request.plan_id) if request.plan_id else None,
                "initial_plan_request_id": str(initial_request_id),
                "base_plan_revision": request.expected_base_revision,
                "context_plan_revision": context_revision,
                "week_start": request.week_start.isoformat(),
                "timezone": context.timezone_name,
                "available_dates": [value.isoformat() for value in available_dates],
                "availability_source": availability_source,
                "confirmed_injuries": sorted(
                    value.value for value in request.confirmed_injuries
                ),
                "low_only_disciplines": sorted(
                    value.value for value in request.low_only_disciplines
                ),
                "input_fingerprint": str(source["input_fingerprint"]),
                "context_fingerprint": context.context_fingerprint,
                "ruleset_version": PHASE_10_RULESET_V1.version.value,
                "target_workout_count": context.target_workout_count,
                "target_composition": {
                    discipline.value: context.target_composition[discipline]
                    for discipline in Discipline
                },
                "current_template_id": str(current) if current is not None else None,
                "state": (
                    "placement" if context.target_workout_count == 0 else "collecting"
                ),
            },
        )
        return self._swipe_response(row, context)

    async def get_swipe_draft(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
    ) -> SwipeWeekDraftResponse:
        row, context = await self._load_swipe_draft_context(
            access_token,
            athlete_id,
            draft_id,
        )
        return self._swipe_response(row, context)

    async def transition_swipe_draft(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
        request: SwipeDraftTransitionRequest,
    ) -> SwipeWeekDraftResponse:
        """Recalculate and persist exactly one stale-safe swipe transition."""

        row, context = await self._load_swipe_draft_context(
            access_token,
            athlete_id,
            draft_id,
        )
        selection = self._swipe_history(row)
        stored_revision = int(row["revision"])
        if request.expected_revision != stored_revision:
            if (
                request.action in {"accept", "pass"}
                and request.candidate_template_id is not None
                and request.expected_revision == stored_revision - 1
                and selection.history
                and selection.history[-1]
                == SwipeDecision(
                    action=SwipeDecisionKind(request.action),
                    template_id=request.candidate_template_id,
                )
            ):
                return self._swipe_response(row, context)
            raise PlanningConstraintError(
                "swipe_draft_stale",
                "The swipe draft changed after this action was prepared.",
            )
        state = str(row["state"])
        if state not in {"collecting", "placement"}:
            raise PlanningConstraintError(
                "swipe_draft_closed",
                "This swipe draft can no longer be changed.",
            )
        week_start = date.fromisoformat(str(row["week_start"]))
        available_dates = tuple(
            date.fromisoformat(str(value)) for value in row["available_dates"]
        )
        injuries = frozenset(
            Discipline(str(value)) for value in row["confirmed_injuries"]
        )
        low_only = frozenset(
            Discipline(str(value)) for value in row["low_only_disciplines"]
        )
        placements: dict[UUID, date] = {}

        if request.action == "undo":
            selection = undo_last_swipe(selection)
        elif request.action == "reset_passed":
            if state != "collecting":
                raise PlanningConstraintError(
                    "swipe_selection_complete",
                    "Passed cards can be reset only during workout selection.",
                )
            selection = reset_passed_cards(selection)
        else:
            if state != "collecting":
                raise PlanningConstraintError(
                    "swipe_selection_complete",
                    "Workout selection is already complete.",
                )
            recomputed_current = self._next_swipe_candidate(
                context=context,
                week_start=week_start,
                available_dates=available_dates,
                injuries=injuries,
                low_only_disciplines=low_only,
                selection=selection,
            )
            stored_current = (
                UUID(str(row["current_template_id"]))
                if row.get("current_template_id") is not None
                else None
            )
            if recomputed_current is None or recomputed_current != stored_current:
                raise PlanningConstraintError(
                    "swipe_draft_context_stale",
                    "The current workout card can no longer be validated.",
                )
            assert request.candidate_template_id is not None
            selection = apply_swipe_decision(
                selection,
                action=SwipeDecisionKind(request.action),
                current_template_id=recomputed_current,
                expected_template_id=request.candidate_template_id,
                target_workout_count=context.target_workout_count,
            )

        selection_complete = (
            len(selection.accepted_template_ids) == context.target_workout_count
        )
        by_id = {template.id: template for template in context.eligible_deck}
        if selection_complete:
            if not composition_is_complete(
                accepted_disciplines=tuple(
                    by_id[value].discipline for value in selection.accepted_template_ids
                ),
                target_composition=context.target_composition,
            ) or not self._selection_has_completion(
                context=context,
                week_start=week_start,
                available_dates=available_dates,
                injuries=injuries,
                low_only_disciplines=low_only,
                accepted_template_ids=selection.accepted_template_ids,
                passed_template_ids=frozenset(),
            ):
                raise PlanningConstraintError(
                    "swipe_selection_invalid",
                    "The accepted cards do not complete the deterministic target.",
                )
            next_state = "placement"
            current = None
        else:
            next_state = "collecting"
            current = self._next_swipe_candidate(
                context=context,
                week_start=week_start,
                available_dates=available_dates,
                injuries=injuries,
                low_only_disciplines=low_only,
                selection=selection,
            )
        updated = await self._repository.update_swipe_draft(
            athlete_id,
            draft_id,
            stored_revision,
            self._swipe_update_payload(
                context_fingerprint=context.context_fingerprint,
                selection=selection,
                current_template_id=current,
                placements=placements,
                state=next_state,
            ),
        )
        return self._swipe_response(updated, context)

    async def place_swipe_workout(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
        template_id: UUID,
        request: SwipeDraftPlacementRequest,
    ) -> SwipeWeekDraftResponse:
        """Validate the complete layout after one exact manual date placement."""

        row, context = await self._load_swipe_draft_context(
            access_token,
            athlete_id,
            draft_id,
        )
        if int(row["revision"]) != request.expected_revision:
            raise PlanningConstraintError(
                "swipe_draft_stale",
                "The swipe draft changed after this placement was prepared.",
            )
        if row["state"] != "placement":
            raise PlanningConstraintError(
                "swipe_selection_incomplete",
                "Complete workout selection before placing cards.",
            )
        selection = self._swipe_history(row)
        if template_id not in selection.accepted_template_ids:
            raise PlanningConstraintError(
                "swipe_template_not_accepted",
                "Only an accepted workout card can be placed.",
            )
        week_start = date.fromisoformat(str(row["week_start"]))
        available_dates = tuple(
            date.fromisoformat(str(value)) for value in row["available_dates"]
        )
        if request.scheduled_date not in available_dates:
            raise PlanningConstraintError(
                "swipe_date_unavailable",
                "The selected date is not in confirmed availability.",
            )
        raw_placements = row.get("placements", {})
        if not isinstance(raw_placements, dict):
            raise PlanningDomainError("Stored swipe placements are invalid.")
        placements = {
            UUID(str(key)): date.fromisoformat(str(value))
            for key, value in raw_placements.items()
        }
        placements[template_id] = request.scheduled_date
        injuries = frozenset(
            Discipline(str(value)) for value in row["confirmed_injuries"]
        )
        low_only = frozenset(
            Discipline(str(value)) for value in row["low_only_disciplines"]
        )
        build_weekly_plan(
            week_start=week_start,
            timezone_name=context.timezone_name,
            race_date=context.race_date,
            catalog=context.catalog,
            prior_loads=context.prior_loads,
            goal_disciplines=context.goal_disciplines,
            confirmed_injuries=injuries,
            low_only_disciplines=low_only,
            zone_capabilities=context.capabilities,
            available_dates=available_dates,
            selected_template_ids=selection.accepted_template_ids,
            fixed_template_dates=placements,
            maintenance_active=bool(context.source.get("maintenance_active", False)),
        )
        updated = await self._repository.update_swipe_draft(
            athlete_id,
            draft_id,
            request.expected_revision,
            self._swipe_update_payload(
                context_fingerprint=context.context_fingerprint,
                selection=selection,
                current_template_id=None,
                placements=placements,
                state="placement",
            ),
        )
        return self._swipe_response(updated, context)

    async def submit_swipe_draft(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
        request: SwipeDraftSubmitRequest,
    ) -> WeeklyPlanProposalResponse:
        """Create only a pending immutable proposal from a complete swipe draft."""

        row, context = await self._load_swipe_draft_context(
            access_token,
            athlete_id,
            draft_id,
        )
        if row["state"] == "submitted":
            plan_id = UUID(str(row["plan_id"]))
            proposal_id = UUID(str(row["proposal_id"]))
            plan = WeeklyPlanResponse.model_validate(
                await self._repository.fetch_plan(access_token, plan_id)
            )
            return WeeklyPlanProposalResponse(
                proposal=ChangeProposalSummaryResponse.model_validate(
                    await self._repository.fetch_proposal(access_token, proposal_id)
                ),
                plan=plan,
            )
        if int(row["revision"]) != request.expected_revision:
            raise PlanningConstraintError(
                "swipe_draft_stale",
                "The swipe draft changed after submit was prepared.",
            )
        if row["state"] != "placement":
            raise PlanningConstraintError(
                "swipe_selection_incomplete",
                "Complete workout selection before submitting the week.",
            )
        selection = self._swipe_history(row)
        raw_placements = row.get("placements", {})
        if not isinstance(raw_placements, dict):
            raise PlanningDomainError("Stored swipe placements are invalid.")
        placements = {
            UUID(str(key)): date.fromisoformat(str(value))
            for key, value in raw_placements.items()
        }
        if request.placement_mode == "manual" and set(placements) != set(
            selection.accepted_template_ids
        ):
            raise PlanningConstraintError(
                "swipe_layout_incomplete",
                "Place every accepted workout before manual submit.",
            )
        fixed_dates = placements if request.placement_mode == "manual" else {}
        week_start = date.fromisoformat(str(row["week_start"]))
        available_dates = tuple(
            date.fromisoformat(str(value)) for value in row["available_dates"]
        )
        injuries = frozenset(
            Discipline(str(value)) for value in row["confirmed_injuries"]
        )
        low_only = frozenset(
            Discipline(str(value)) for value in row["low_only_disciplines"]
        )
        bound_plan_id = (
            UUID(str(row["plan_id"]))
            if row.get("context_plan_revision") is not None
            else None
        )
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=context.source,
            request_id=UUID(str(row["initial_plan_request_id"])),
            plan_id=bound_plan_id,
            expected_base_revision=int(row["base_plan_revision"]),
            week_start=week_start,
            available_dates=available_dates,
            availability_source=str(row["availability_source"]),
            injuries=injuries,
            low_only_disciplines=low_only,
            selected_template_ids=selection.accepted_template_ids,
            fixed_template_dates=fixed_dates,
        )
        plan_id = UUID(str(result["plan_id"]))
        proposal_id = UUID(str(result["proposal_id"]))
        revision = int(result["revision"])
        plan = WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(access_token, plan_id, revision)
        )
        final_placements = {
            workout.template_id: workout.scheduled_date for workout in plan.workouts
        }
        await self._repository.update_swipe_draft(
            athlete_id,
            draft_id,
            request.expected_revision,
            self._swipe_update_payload(
                context_fingerprint=context.context_fingerprint,
                selection=selection,
                current_template_id=None,
                placements=final_placements,
                state="submitted",
                plan_id=plan_id,
                proposal_id=proposal_id,
            ),
        )
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=plan,
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
            available_dates=request.available_dates,
            availability_source="explicit",
            injuries=request.confirmed_injuries,
            low_only_disciplines=request.low_only_disciplines,
            selected_template_ids=request.selected_template_ids,
            fixed_template_dates={
                item.template_id: item.scheduled_date
                for item in request.fixed_workout_dates
            },
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

    async def generate_integrated_field_test_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        *,
        plan_id: UUID,
        expected_revision: int,
        discipline: Discipline,
        protocol_id: str,
        scheduled_date: date,
    ) -> WeeklyPlanProposalResponse:
        """Replace one same-discipline workout with an exact-date field test."""
        context = await self._repository.fetch_plan_context(athlete_id, plan_id)
        active_revision = context.get("active_revision")
        if active_revision is None or int(active_revision) != expected_revision:
            raise PlanningConstraintError(
                "proposal_stale",
                "The plan changed after this test request was prepared.",
            )
        snapshot = self._planning_input(context)
        timezone_name, _, _, _ = self._context_values(snapshot)
        week_start = date.fromisoformat(str(context["week_start"]))
        validate_test_schedule(
            protocol_id=protocol_id,
            discipline=discipline,
            scheduling_mode=TestSchedulingMode.WEEKLY_PLAN,
            scheduled_date=scheduled_date,
            athlete_today=datetime.now(ZoneInfo(timezone_name)).date(),
            plan_week_start=week_start,
        )
        current = WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(
                access_token,
                plan_id,
                expected_revision,
            )
        )
        if scheduled_date not in current.available_dates:
            raise PlanningConstraintError(
                "test_date_unavailable",
                "The selected test date is not an available plan date.",
            )
        catalog = active_catalog(await self._catalog_provider.fetch_catalog())
        test_templates = tuple(
            template
            for template in catalog
            if template.discipline is discipline
            and template.explicit_scheduling_only
            and any(
                segment.protocol_target is not None
                and segment.protocol_target.protocol_id == protocol_id
                for segment in template.segments
            )
        )
        if len(test_templates) != 1:
            raise PlanningDomainError(
                "The reviewed field test has no unique plannable template."
            )
        replaceable = sorted(
            (
                workout
                for workout in current.workouts
                if workout.discipline is discipline and workout.status == "scheduled"
            ),
            key=lambda workout: (workout.scheduled_date, str(workout.id)),
        )
        if not replaceable:
            raise PlanningConstraintError(
                "test_discipline_missing",
                "The active plan has no same-discipline workout to replace.",
            )
        replaced = replaceable[0]
        test_template = test_templates[0]
        selected_template_ids = tuple(
            workout.template_id
            for workout in current.workouts
            if workout.id != replaced.id and workout.status == "scheduled"
        ) + (test_template.id,)
        result = await self._build_and_persist(
            athlete_id=athlete_id,
            input_source=context,
            request_id=(
                UUID(str(context["initial_plan_request_id"]))
                if context.get("initial_plan_request_id") is not None
                else None
            ),
            plan_id=plan_id,
            expected_base_revision=expected_revision,
            week_start=week_start,
            available_dates=current.available_dates,
            availability_source=current.availability_source,
            injuries=current.confirmed_injuries,
            low_only_disciplines=current.low_only_disciplines,
            selected_template_ids=selected_template_ids,
            fixed_template_dates={test_template.id: scheduled_date},
            allow_explicit_test_selection=True,
        )
        proposal_id = UUID(str(result["proposal_id"]))
        revision = int(result["revision"])
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=WeeklyPlanResponse.model_validate(
                await self._repository.fetch_plan(access_token, plan_id, revision)
            ),
        )

    async def generate_checkin_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        *,
        checkin_id: UUID,
        input_source: Mapping[str, Any],
        week_start: date,
        available_dates: tuple[date, ...],
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
            available_dates=available_dates,
            availability_source="checkin",
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
        deck = tuple(
            template for template in deck if not template.explicit_scheduling_only
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
            templates=tuple(self._deck_item(template) for template in deck),
        )

    async def _pending_revision_edit_state(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        revision: int,
    ) -> tuple[JsonObject, WeeklyPlanResponse, tuple[WorkoutTemplate, ...]]:
        context = await self._repository.fetch_plan_revision_context(
            athlete_id,
            plan_id,
            revision,
        )
        plan = WeeklyPlanResponse.model_validate(
            await self._repository.fetch_plan(access_token, plan_id, revision)
        )
        if plan.revision_state != "pending_approval" or plan.proposal is None:
            raise PlanningConstraintError(
                "pending_revision_required",
                "Only an exact pending weekly-plan revision can be edited.",
            )
        if plan.proposal.state != "pending":
            raise PlanningConstraintError(
                "proposal_stale",
                "The pending proposal has already been decided or replaced.",
            )
        snapshot = self._planning_input(context)
        _, _, disciplines, capabilities = self._context_values(snapshot)
        try:
            phase = TrainingPhase(str(context["phase"]))
            injuries = frozenset(
                Discipline(str(value))
                for value in context.get("confirmed_injuries", [])
            )
            low_only = frozenset(
                Discipline(str(value))
                for value in context.get("low_only_disciplines", [])
            )
        except (KeyError, ValueError) as error:
            raise PlanningDomainError(
                "Stored pending plan context is invalid."
            ) from error
        deck = eligible_workouts(
            catalog=active_catalog(await self._catalog_provider.fetch_catalog()),
            phase=phase,
            goal_disciplines=disciplines,
            confirmed_injuries=injuries,
            low_only_disciplines=low_only,
            zone_capabilities=capabilities,
        )
        deck = tuple(
            template for template in deck if not template.explicit_scheduling_only
        )
        return context, plan, deck

    async def _candidate_edit_is_valid(
        self,
        *,
        athlete_id: UUID,
        context: Mapping[str, Any],
        selected_template_ids: tuple[UUID, ...],
    ) -> bool:
        try:
            snapshot = self._planning_input(context)
            timezone_name, race_date, disciplines, capabilities = self._context_values(
                snapshot
            )
            week_start = date.fromisoformat(str(context["week_start"]))
            build_weekly_plan(
                week_start=week_start,
                timezone_name=timezone_name,
                race_date=race_date,
                catalog=active_catalog(await self._catalog_provider.fetch_catalog()),
                prior_loads=self._load_samples(
                    await self._repository.fetch_load_history(athlete_id, week_start)
                ),
                goal_disciplines=disciplines,
                confirmed_injuries=frozenset(
                    Discipline(str(value))
                    for value in context.get("confirmed_injuries", [])
                ),
                low_only_disciplines=frozenset(
                    Discipline(str(value))
                    for value in context.get("low_only_disciplines", [])
                ),
                zone_capabilities=capabilities,
                available_dates=tuple(
                    date.fromisoformat(str(value))
                    for value in context.get("available_dates", [])
                ),
                selected_template_ids=selected_template_ids,
                maintenance_active=bool(context.get("maintenance_active", False)),
            )
        except (PlanningConstraintError, PlanningDomainError, KeyError, ValueError):
            return False
        return True

    async def get_pending_workout_alternatives(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        workout_id: UUID,
        expected_revision: int,
    ) -> PendingWorkoutAlternativesResponse:
        context, plan, deck = await self._pending_revision_edit_state(
            access_token,
            athlete_id,
            plan_id,
            expected_revision,
        )
        target = next(
            (workout for workout in plan.workouts if workout.id == workout_id),
            None,
        )
        if target is None:
            raise PlanningConstraintError(
                "pending_workout_stale",
                "The workout is not part of the exact pending revision.",
            )
        current_ids = tuple(workout.template_id for workout in plan.workouts)
        without_target = tuple(
            template_id
            for template_id in current_ids
            if template_id != target.template_id
        )
        can_remove = await self._candidate_edit_is_valid(
            athlete_id=athlete_id,
            context=context,
            selected_template_ids=without_target,
        )
        alternatives: list[WorkoutTemplate] = []
        for candidate in deck:
            if (
                candidate.id in current_ids
                or candidate.discipline is not target.discipline
            ):
                continue
            if await self._candidate_edit_is_valid(
                athlete_id=athlete_id,
                context=context,
                selected_template_ids=without_target + (candidate.id,),
            ):
                alternatives.append(candidate)
        assert plan.proposal is not None
        return PendingWorkoutAlternativesResponse(
            plan_id=plan_id,
            revision=expected_revision,
            proposal_id=plan.proposal.id,
            workout_id=workout_id,
            can_remove=can_remove,
            alternatives=tuple(self._deck_item(template) for template in alternatives),
        )

    async def edit_pending_workout(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        workout_id: UUID,
        request: PendingWorkoutEditRequest,
    ) -> WeeklyPlanProposalResponse:
        context, plan, _ = await self._pending_revision_edit_state(
            access_token,
            athlete_id,
            plan_id,
            request.expected_revision,
        )
        assert plan.proposal is not None
        if plan.proposal.id != request.expected_proposal_id:
            raise PlanningConstraintError(
                "proposal_stale",
                "The proposal changed after this edit was prepared.",
            )
        target = next(
            (workout for workout in plan.workouts if workout.id == workout_id),
            None,
        )
        if target is None:
            raise PlanningConstraintError(
                "pending_workout_stale",
                "The workout is not part of the exact pending revision.",
            )
        selected_ids = tuple(
            workout.template_id for workout in plan.workouts if workout.id != workout_id
        )
        if request.replacement_template_id is not None:
            selected_ids += (request.replacement_template_id,)
        if not await self._candidate_edit_is_valid(
            athlete_id=athlete_id,
            context=context,
            selected_template_ids=selected_ids,
        ):
            raise PlanningConstraintError(
                "replacement_not_eligible",
                "The requested removal or replacement is not eligible for this "
                "pending revision.",
            )
        available_dates = tuple(
            date.fromisoformat(str(value))
            for value in context.get("available_dates", [])
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
            expected_base_revision=int(context.get("active_revision") or 0),
            week_start=date.fromisoformat(str(context["week_start"])),
            available_dates=available_dates,
            availability_source=str(context.get("availability_source", "explicit")),
            injuries=frozenset(
                Discipline(str(value))
                for value in context.get("confirmed_injuries", [])
            ),
            low_only_disciplines=frozenset(
                Discipline(str(value))
                for value in context.get("low_only_disciplines", [])
            ),
            selected_template_ids=selected_ids,
        )
        proposal_id = UUID(str(result["proposal_id"]))
        revision = int(result["revision"])
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(access_token, proposal_id)
            ),
            plan=WeeklyPlanResponse.model_validate(
                await self._repository.fetch_plan(access_token, plan_id, revision)
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
                    starts_at=canonical_schedule_instant(
                        workout.scheduled_date,
                        timezone_name=plan.timezone,
                    ),
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
        if not (
            plan.week_start
            <= request.scheduled_date
            <= plan.week_start + timedelta(days=6)
        ):
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
                    canonical_schedule_instant(
                        request.scheduled_date,
                        timezone_name=plan.timezone,
                    )
                    if workout.id == workout_id
                    else canonical_schedule_instant(
                        workout.scheduled_date,
                        timezone_name=plan.timezone,
                    )
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
        available_dates = context.get("available_dates")
        if isinstance(available_dates, list):
            if request.scheduled_date.isoformat() not in {
                str(value) for value in available_dates
            }:
                warnings.append(
                    PlanningWarning(
                        rule_id=RuleId.SOFT_BOUNDARIES,
                        code="outside_confirmed_availability",
                        message=(
                            "This athlete move falls outside the available dates "
                            "confirmed for the plan."
                        ),
                    )
                )
        result = await self._repository.move_planned_workout(
            athlete_id,
            workout_id,
            request.expected_revision,
            request.scheduled_date,
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
        from_date: date,
        to_date: date,
    ) -> CalendarResponse:
        if to_date <= from_date:
            raise PlanningDomainError("Calendar end must follow its start.")
        if to_date - from_date > timedelta(days=93):
            raise PlanningDomainError("Calendar ranges are limited to 93 days.")
        return CalendarResponse(
            from_date=from_date,
            to_date=to_date,
            workouts=tuple(
                PlannedWorkoutResponse.model_validate(row)
                for row in await self._repository.fetch_calendar(
                    access_token,
                    from_date,
                    to_date,
                )
            ),
            rest_days=tuple(
                RestDayResponse.model_validate(row)
                for row in await self._repository.fetch_calendar_rest_days(
                    access_token,
                    from_date,
                    to_date,
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
