"""Inactive adapter to existing pending, swipe, approval and repository contracts.

Never installed by application startup or settings. A repository must explicitly
support frozen V6 snapshots; the historical Supabase writer still rejects.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, replace
from datetime import date
from decimal import Decimal
from functools import partial
from typing import Any, Protocol
from uuid import UUID, uuid5

from app.modules.physiology.models import Discipline, Fraction, InternalLoad
from app.modules.physiology.planned_v6 import METHOD
from app.modules.physiology.taper import TaperPeriod
from app.modules.workouts.catalog import WorkoutTemplate
from app.modules.workouts.joren_v6_official import V6Template, official_catalog

from .domain import PlanningConstraintError, PlanningTarget, PlanningTargetBasis
from .repository import (
    JsonObject,
    PlanningRepository,
    PlanningRepositoryUnavailableError,
)
from .schemas import (
    CalendarResponse,
    PendingWorkoutAlternativesResponse,
    PendingWorkoutEditRequest,
    PlannedWorkoutMoveRequest,
    PlannedWorkoutResponse,
    SwipeDraftSubmitRequest,
    SwipeWeekDraftResponse,
    WeeklyPlanProposalRequest,
    WeeklyPlanProposalResponse,
    WeeklyPlanResponse,
    WorkoutDeckItemResponse,
)
from .service import PlanningService, _SwipePlanningContext
from .swipe import SwipeSelectionState
from .v6_presentation import source_prescription
from .v6_selection import VERSION, V6Controls, V6Plan, build_v6_plan, eligible_v6


def private_json(value: object) -> str:
    def encode(item: object) -> object:
        if isinstance(item, Decimal | UUID | date):
            return str(item)
        if isinstance(item, frozenset):
            return sorted(item)
        raise TypeError("unsupported_v6_snapshot_value")

    return json.dumps(value, default=encode, ensure_ascii=False, sort_keys=True)


def controls_json(controls: V6Controls) -> str:
    data = asdict(controls)
    data["week_scope"] = (
        controls.week_scope.isoformat() if controls.week_scope else None
    )
    return private_json(data)


def frozen_controls(data: JsonObject) -> V6Controls:
    """Restore trusted revision-bound evidence after a worker/service restart."""
    return V6Controls(
        estimate_swim_for_preview=data["estimate_swim_for_preview"],
        occurrence_namespace=UUID(data["occurrence_namespace"])
        if data["occurrence_namespace"]
        else None,
        athlete_scope=UUID(data["athlete_scope"]) if data["athlete_scope"] else None,
        week_scope=date.fromisoformat(data["week_scope"])
        if data["week_scope"]
        else None,
        duration_evidence=tuple((UUID(k), v) for k, v in data["duration_evidence"]),
        maximum_uses=tuple((UUID(k), n) for k, n in data["maximum_uses"]),
        prescribed_swim_seconds=tuple(
            (UUID(k), tuple(Decimal(s) for s in seconds), ref)
            for k, seconds, ref in data["prescribed_swim_seconds"]
        ),
        maximum_combinations=data["maximum_combinations"],
    )


def effective_controls(data: JsonObject, current: V6Controls) -> V6Controls:
    """Keep stored evidence; current restrictions may tighten, never expand it."""
    stored = frozen_controls(data)
    limits = dict(stored.maximum_uses)
    for key, limit in current.maximum_uses:
        limits[key] = min(limits.get(key, limit), limit)
    return replace(
        stored,
        maximum_uses=tuple(sorted(limits.items(), key=lambda row: str(row[0]))),
        estimate_swim_for_preview=(
            stored.estimate_swim_for_preview and current.estimate_swim_for_preview
        ),
        maximum_combinations=min(
            stored.maximum_combinations, current.maximum_combinations
        ),
    )


class FrozenV6Repository(PlanningRepository, Protocol):
    supports_frozen_v6_snapshots: bool

    async def fetch_v6_edit_retry(
        self, athlete_id: UUID, operation_key: str
    ) -> JsonObject | None:
        """Owner-scoped immutable idempotent edit result, before stale checks."""

    async def move_v6_workout(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        """Atomic immutable confirmed revision move and existing edit receipt."""


class InactiveV6CatalogProvider:
    def __init__(self) -> None:
        self._catalog = official_catalog()

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        return self._catalog

    async def aclose(self) -> None:
        return None


def v6_catalog_view(
    catalog: tuple[WorkoutTemplate, ...] = (),
) -> tuple[WorkoutTemplate, ...]:
    if not catalog or any(not isinstance(t, V6Template) for t in catalog):
        raise ValueError("v6_official_catalog_required")
    if len({t.id for t in catalog}) != len(catalog):
        raise ValueError("ambiguous_v6_catalog")
    return catalog


class V6PlanningService(PlanningService):
    """Use only through explicit local dependency injection; no production flag."""

    _catalog_view = staticmethod(v6_catalog_view)
    _planning_policy_version = VERSION

    @staticmethod
    def _swipe_response(
        row: Mapping[str, Any], context: _SwipePlanningContext
    ) -> SwipeWeekDraftResponse:
        response = PlanningService._swipe_response(row, context)
        catalog = {t.id: t for t in context.eligible_deck}
        cards = response.accepted_workouts + (
            (response.current_candidate,) if response.current_candidate else ()
        )
        for card in cards:
            template = catalog[card.id]
            if isinstance(template, V6Template):
                card.source_prescription = source_prescription(template)
        return response

    @staticmethod
    def _deck_item(
        template: WorkoutTemplate, *, contributes_to_zone_calibration: bool = False
    ) -> WorkoutDeckItemResponse:
        item = PlanningService._deck_item(
            template, contributes_to_zone_calibration=contributes_to_zone_calibration
        )
        if isinstance(template, V6Template):
            item.source_prescription = source_prescription(template)
        return item

    async def _present_workouts(
        self, workouts: tuple[PlannedWorkoutResponse, ...]
    ) -> tuple[PlannedWorkoutResponse, ...]:
        catalog = {t.id: t for t in await self._catalog_provider.fetch_catalog()}
        for workout in workouts:
            template = catalog.get(workout.template_id)
            if isinstance(template, V6Template):
                if (
                    template.template_key != workout.template_key
                    or template.version != workout.template_version
                ):
                    raise PlanningRepositoryUnavailableError(
                        "The exact source revision is unavailable."
                    )
                workout.source_prescription = source_prescription(template)
        return workouts

    async def generate_initial_proposal(
        self, access_token: str, athlete_id: UUID, request: WeeklyPlanProposalRequest
    ) -> WeeklyPlanProposalResponse:
        response = await super().generate_initial_proposal(
            access_token, athlete_id, request
        )
        response.plan.workouts = await self._present_workouts(response.plan.workouts)
        return response

    async def submit_swipe_draft(
        self,
        access_token: str,
        athlete_id: UUID,
        draft_id: UUID,
        request: SwipeDraftSubmitRequest,
    ) -> WeeklyPlanProposalResponse:
        response = await super().submit_swipe_draft(
            access_token, athlete_id, draft_id, request
        )
        response.plan.workouts = await self._present_workouts(response.plan.workouts)
        return response

    async def get_plan(
        self, access_token: str, plan_id: UUID, revision: int | None
    ) -> WeeklyPlanResponse:
        plan = await super().get_plan(access_token, plan_id, revision)
        plan.workouts = await self._present_workouts(plan.workouts)
        return plan

    async def get_calendar(
        self, access_token: str, from_date: date, to_date: date
    ) -> CalendarResponse:
        calendar = await super().get_calendar(access_token, from_date, to_date)
        calendar.workouts = await self._present_workouts(calendar.workouts)
        return calendar

    async def move_workout(
        self,
        access_token: str,
        athlete_id: UUID,
        workout_id: UUID,
        request: PlannedWorkoutMoveRequest,
    ) -> WeeklyPlanResponse:
        operation_key = hashlib.sha256(
            f"v6-move:{athlete_id}:{workout_id}:{request.expected_revision}:{request.scheduled_date}".encode()
        ).hexdigest()
        retry = await self._v6_repository.fetch_v6_edit_retry(athlete_id, operation_key)
        if retry is not None:
            plan = WeeklyPlanResponse.model_validate(retry["plan"])
            plan.workouts = await self._present_workouts(plan.workouts)
            return plan
        public_context = await self._repository.fetch_workout_context(
            access_token, workout_id
        )
        plan = WeeklyPlanResponse.model_validate(public_context["plan"])
        if not any(w.physical_workout_id for w in plan.workouts):
            return await super().move_workout(
                access_token, athlete_id, workout_id, request
            )
        if (
            plan.revision != request.expected_revision
            or plan.active_revision != request.expected_revision
            or plan.revision_state != "active"
        ):
            raise PlanningConstraintError(
                "plan_revision_stale", "The plan changed. Reload the training week."
            )
        moved = next(
            (w for w in plan.workouts if workout_id in {w.id, w.physical_workout_id}),
            None,
        )
        if moved is None or moved.status != "scheduled":
            raise PlanningConstraintError(
                "recorded_workout_move_unsupported",
                "Recorded training cannot be moved. Reload the training week.",
            )
        context = await self._repository.fetch_plan_revision_context(
            athlete_id, plan.id, plan.revision
        )
        # Reuse complete-week validation with ALL source identities/dates fixed.
        await self._replacement_plan(
            athlete_id=athlete_id,
            context=context,
            plan=plan,
            workout_id=moved.id,
            replacement=moved.template_id,
            moved_date=request.scheduled_date,
        )
        result = await self._v6_repository.move_v6_workout(
            athlete_id,
            {
                "operation_key": operation_key,
                "plan_id": str(plan.id),
                "revision_id": str(plan.revision_id),
                "expected_revision": request.expected_revision,
                "occurrence_id": str(moved.id),
                "physical_workout_id": str(moved.physical_workout_id),
                "scheduled_date": request.scheduled_date.isoformat(),
            },
        )
        plan = WeeklyPlanResponse.model_validate(result["plan"])
        plan.workouts = await self._present_workouts(plan.workouts)
        return plan

    @staticmethod
    def _transition_placements(
        row: Mapping[str, Any], selection: SwipeSelectionState
    ) -> dict[UUID, date]:
        return {
            UUID(k): date.fromisoformat(v)
            for k, v in row.get("placements", {}).items()
            if UUID(k) in selection.accepted_occurrence_ids
        }

    async def _load_swipe_draft_context(
        self, access_token: str, athlete_id: UUID, draft_id: UUID
    ) -> tuple[JsonObject, _SwipePlanningContext]:
        row, context = await super()._load_swipe_draft_context(
            access_token, athlete_id, draft_id
        )
        # Retained dates are passed through the existing complete-week scheduler.
        # Bind by template within this at-most-one-new-per-sport draft scope.
        selection = self._swipe_history(row)
        fixed = {
            template: date.fromisoformat(row["placements"][str(occurrence)])
            for template, occurrence in zip(
                selection.accepted_template_ids, selection.accepted_occurrence_ids
            )
            if str(occurrence) in row.get("placements", {})
        }
        source = dict(context.source)
        source["_v6_retained_dates"] = fixed
        return row, replace(context, source=source)

    def __init__(
        self,
        repository: FrozenV6Repository,
        catalog_provider: Any,
        weekly_plan_coach: Any,
        computation: Any,
        *,
        controls: V6Controls = V6Controls(),
    ) -> None:
        if getattr(repository, "supports_frozen_v6_snapshots", False) is not True:
            raise PlanningRepositoryUnavailableError(
                "V6 snapshot storage is not available."
            )
        super().__init__(repository, catalog_provider, weekly_plan_coach, computation)
        self._v6_repository = repository
        self._controls = controls
        self._plan_builder = partial(build_v6_plan, controls=controls)
        self._eligible_workouts = partial(eligible_v6, controls=controls)

    @staticmethod
    def _generation_fingerprint(**kwargs: Any) -> str:
        return hashlib.sha256(
            (
                PlanningService._generation_fingerprint(**kwargs) + VERSION + METHOD
            ).encode()
        ).hexdigest()

    async def _prepare_swipe_context(self, **kwargs: Any) -> _SwipePlanningContext:
        self._assert_individual_scope(kwargs["athlete_id"], kwargs["week_start"])
        context = await PlanningService._prepare_swipe_context(
            self._scoped_service(kwargs["athlete_id"], kwargs["week_start"]), **kwargs
        )
        fingerprint = hashlib.sha256(
            (
                context.context_fingerprint + controls_json(self._controls) + VERSION
            ).encode()
        ).hexdigest()
        return replace(context, context_fingerprint=fingerprint)

    def _assert_individual_scope(self, athlete_id: UUID, week_start: date) -> None:
        if (
            self._controls.athlete_scope is not None
            and self._controls.athlete_scope != athlete_id
            or self._controls.week_scope is not None
            and self._controls.week_scope != week_start
        ):
            raise PlanningConstraintError(
                "v6_evidence_scope_mismatch",
                "Individual evidence belongs to another athlete or week.",
            )

    async def _build_and_persist(self, **kwargs: Any) -> JsonObject:
        self._assert_individual_scope(kwargs["athlete_id"], kwargs["week_start"])
        return await PlanningService._build_and_persist(
            self._scoped_service(kwargs["athlete_id"], kwargs["week_start"]), **kwargs
        )

    def _scoped_service(
        self, athlete_id: UUID, week_start: date
    ) -> "V6PlanningService":
        """Request-local adapter; never mutate a shared planner across awaits."""
        scoped = replace(
            self._controls,
            occurrence_namespace=uuid5(athlete_id, f"{VERSION}:{week_start}"),
        )
        return type(self)(
            self._v6_repository,
            self._catalog_provider,
            self._weekly_plan_coach,
            self._computation,
            controls=scoped,
        )

    @staticmethod
    def _selection_has_completion(
        *,
        context: _SwipePlanningContext,
        week_start: date,
        available_dates: tuple[date, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        accepted_template_ids: tuple[UUID, ...],
        passed_template_ids: tuple[UUID, ...],
    ) -> tuple[UUID, ...] | None:
        try:
            plan = context.plan_builder(
                week_start=week_start,
                timezone_name=context.timezone_name,
                race_date=context.race_date,
                catalog=context.catalog,
                prior_loads=context.prior_loads,
                goal_disciplines=context.goal_disciplines,
                confirmed_injuries=injuries,
                low_only_disciplines=low_only_disciplines,
                cross_training_opt_ins=context.cross_training_opt_ins,
                zone_capabilities=context.capabilities,
                available_dates=available_dates,
                onboarding_baseline=PlanningService._onboarding_baseline(
                    PlanningService._planning_input(context.source)
                ),
                maintenance_active=bool(
                    context.source.get("maintenance_active", False)
                ),
                prefix=accepted_template_ids,
                excluded=frozenset(passed_template_ids),
                required_composition=context.target_composition,
                fixed_template_dates={
                    k: v
                    for k, v in context.source.get("_v6_retained_dates", {}).items()
                    if k in accepted_template_ids
                },
            )
        except PlanningConstraintError as error:
            if error.code == "v6_search_incomplete":
                raise
            return None
        assert isinstance(plan, V6Plan)
        return tuple(t.id for t in plan.templates)

    @staticmethod
    def _next_swipe_candidate(
        *,
        context: _SwipePlanningContext,
        week_start: date,
        available_dates: tuple[date, ...],
        injuries: frozenset[Discipline],
        low_only_disciplines: frozenset[Discipline],
        selection: SwipeSelectionState,
    ) -> UUID | None:
        completion = V6PlanningService._selection_has_completion(
            context=context,
            week_start=week_start,
            available_dates=available_dates,
            injuries=injuries,
            low_only_disciplines=low_only_disciplines,
            accepted_template_ids=selection.accepted_template_ids,
            passed_template_ids=selection.passed_template_ids,
        )
        count = len(selection.accepted_template_ids)
        return completion[count] if completion and len(completion) > count else None

    @staticmethod
    def _proposal_payload(**kwargs: Any) -> JsonObject:
        draft = kwargs["draft"]
        if not isinstance(draft, V6Plan):
            raise ValueError("v6_snapshot_required")
        payload = PlanningService._proposal_payload(**kwargs)
        if kwargs.get("checkin_id") is not None:
            context = kwargs["input_source"]
            payload["v6_checkin_context"] = {
                "revision": context["checkin_context_revision"],
                "fingerprint": context["checkin_context_fingerprint"],
                "payload": context["confirmed_context"],
            }
        payload["planning_ruleset_version"] = VERSION
        payload["v6_frozen_snapshot"] = json.loads(
            private_json(
                {
                    "policy": VERSION,
                    "planned_method": METHOD,
                    "input_fingerprint": payload["input_fingerprint"],
                    "estimated_sports": sorted(s.value for s in draft.estimated_sports),
                    "controls": json.loads(
                        controls_json(replace(draft.controls, authorized_target=None))
                    ),
                    "target": asdict(draft.target),
                    "optimality": draft.optimality,
                    "examined": draft.examined,
                    "templates": [asdict(t) for t in draft.templates],
                    "activation": "INACTIVE_PREVIEW",
                }
            )
        )
        payload["generation_fingerprint"] = hashlib.sha256(
            (
                payload["generation_fingerprint"]
                + private_json(payload["v6_frozen_snapshot"])
            ).encode()
        ).hexdigest()
        by_id = {t.id: t for t in draft.templates}
        for row in payload["workouts"]:
            template = by_id[UUID(row["template_id"])]
            row["planned_method"] = METHOD
            row["planned_method_version"] = METHOD
            row["source_revision_sha256"] = template.source_revision.source_sha256
        return payload

    async def _replacement_plan(
        self,
        *,
        athlete_id: UUID,
        context: JsonObject,
        plan: WeeklyPlanResponse,
        workout_id: UUID,
        replacement: UUID | None,
        moved_date: date | None = None,
    ) -> V6Plan:
        self._assert_individual_scope(athlete_id, plan.week_start)
        target = next((w for w in plan.workouts if w.id == workout_id), None)
        if target is None:
            raise PlanningConstraintError(
                "pending_workout_stale",
                "The workout is not part of this pending revision.",
            )
        snapshot = self._planning_input(context)
        frozen = context["v6_frozen_snapshot"]
        if frozen["input_fingerprint"] != context["input_fingerprint"]:
            raise PlanningConstraintError(
                "v6_pending_context_stale", "The confirmed planning context changed."
            )
        stored = frozen["target"]
        frozen_target = PlanningTarget(
            phase=plan.phase,
            basis=PlanningTargetBasis(plan.target_basis),
            target=InternalLoad(Decimal(stored["target"]["value"])),
            build_week=stored["build_week"],
            taper_period=TaperPeriod(stored["taper_period"])
            if stored["taper_period"]
            else None,
            desired_high_fraction=Fraction(
                Decimal(stored["desired_high_fraction"]["value"])
            ),
            manual_review_required=stored["manual_review_required"],
            replacement_disciplines=frozenset(
                Discipline(s) for s in stored["replacement_disciplines"]
            ),
            injury_load_unallocated=stored["injury_load_unallocated"],
            cross_training_consent_required=stored["cross_training_consent_required"],
            discipline_caps={
                Discipline(s): InternalLoad(Decimal(v["value"]))
                for s, v in stored["discipline_caps"].items()
            },
        )
        timezone_name, race_date, goals, capabilities = self._context_values(snapshot)
        ids = tuple(
            (
                replacement
                if w.id == workout_id and replacement is not None
                else w.template_id
            )
            for w in plan.workouts
            if w.id != workout_id or replacement is not None
        )
        occurrences = tuple(
            w.id for w in plan.workouts if w.id != workout_id or replacement is not None
        )
        fixed = {
            w.id: moved_date if w.id == workout_id and moved_date else w.scheduled_date
            for w in plan.workouts
            if w.id != workout_id or replacement is not None
        }
        controls = effective_controls(frozen["controls"], self._controls)
        if (
            controls.athlete_scope is not None
            and controls.athlete_scope != athlete_id
            or controls.week_scope is not None
            and controls.week_scope != plan.week_start
        ):
            raise PlanningConstraintError(
                "v6_evidence_scope_mismatch",
                "Individual evidence belongs to another athlete or week.",
            )
        result = await self._computation.run(
            build_v6_plan,
            controls=replace(controls, authorized_target=frozen_target),
            week_start=plan.week_start,
            timezone_name=timezone_name,
            race_date=race_date,
            catalog=self._catalog_view(await self._catalog_provider.fetch_catalog()),
            prior_loads=self._load_samples(
                await self._repository.fetch_load_history(athlete_id, plan.week_start)
            ),
            goal_disciplines=goals,
            confirmed_injuries=frozenset(
                Discipline(s) for s in context.get("confirmed_injuries", [])
            ),
            low_only_disciplines=frozenset(
                Discipline(s) for s in context.get("low_only_disciplines", [])
            ),
            cross_training_opt_ins=frozenset(
                Discipline(s) for s in context.get("cross_training_opt_ins", [])
            ),
            zone_capabilities=capabilities,
            available_dates=tuple(
                date.fromisoformat(d) for d in context["available_dates"]
            ),
            onboarding_baseline=self._onboarding_baseline(snapshot),
            selected_template_ids=ids,
            selected_occurrence_ids=occurrences,
            fixed_occurrence_dates=fixed,
        )
        assert isinstance(result, V6Plan)
        return result

    async def _pending_revision_edit_state(
        self, access_token: str, athlete_id: UUID, plan_id: UUID, revision: int
    ) -> tuple[JsonObject, WeeklyPlanResponse, tuple[WorkoutTemplate, ...]]:
        context, plan, _ = await super()._pending_revision_edit_state(
            access_token, athlete_id, plan_id, revision
        )
        _, _, goals, capabilities = self._context_values(self._planning_input(context))
        deck = eligible_v6(
            controls=effective_controls(
                context["v6_frozen_snapshot"]["controls"], self._controls
            ),
            catalog=self._catalog_view(await self._catalog_provider.fetch_catalog()),
            phase=plan.phase,
            goal_disciplines=goals,
            confirmed_injuries=plan.confirmed_injuries,
            low_only_disciplines=plan.low_only_disciplines,
            zone_capabilities=capabilities,
            build_week=context["v6_frozen_snapshot"]["target"]["build_week"],
        )
        return context, plan, deck

    async def get_pending_workout_alternatives(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        workout_id: UUID,
        expected_revision: int,
    ) -> PendingWorkoutAlternativesResponse:
        context, plan, deck = await self._pending_revision_edit_state(
            access_token, athlete_id, plan_id, expected_revision
        )
        target = next((w for w in plan.workouts if w.id == workout_id), None)
        if target is None:
            raise PlanningConstraintError(
                "pending_workout_stale",
                "The workout is not part of this pending revision.",
            )
        alternatives = []
        for candidate in sorted(deck, key=lambda t: str(t.id)):
            if (
                candidate.discipline is not target.discipline
                or candidate.id == target.template_id
            ):
                continue
            try:
                result = await self._replacement_plan(
                    athlete_id=athlete_id,
                    context=context,
                    plan=plan,
                    workout_id=workout_id,
                    replacement=candidate.id,
                )
            except PlanningConstraintError:
                continue
            alternatives.append((candidate, result))
        from .v6_selection import ranking

        _, _, goals, _ = self._context_values(self._planning_input(context))
        alternatives.sort(key=lambda r: ranking(r[1].templates, goals))
        assert plan.proposal is not None
        try:
            await self._replacement_plan(
                athlete_id=athlete_id,
                context=context,
                plan=plan,
                workout_id=workout_id,
                replacement=None,
            )
            can_remove = True
        except PlanningConstraintError:
            can_remove = False
        return PendingWorkoutAlternativesResponse(
            plan_id=plan_id,
            revision=expected_revision,
            proposal_id=plan.proposal.id,
            workout_id=workout_id,
            can_remove=can_remove,
            alternatives=tuple(self._deck_item(t) for t, _ in alternatives),
        )

    async def edit_pending_workout(
        self,
        access_token: str,
        athlete_id: UUID,
        plan_id: UUID,
        workout_id: UUID,
        request: PendingWorkoutEditRequest,
    ) -> WeeklyPlanProposalResponse:
        operation_key = hashlib.sha256(
            f"{VERSION}:{athlete_id}:{plan_id}:{request.expected_revision}:{request.expected_proposal_id}:{workout_id}:{request.replacement_template_id}".encode()
        ).hexdigest()
        retry = await self._v6_repository.fetch_v6_edit_retry(athlete_id, operation_key)
        if retry is not None:
            response = WeeklyPlanProposalResponse.model_validate(retry)
            response.plan.workouts = await self._present_workouts(
                response.plan.workouts
            )
            return response
        context, plan, _ = await self._pending_revision_edit_state(
            access_token, athlete_id, plan_id, request.expected_revision
        )
        assert plan.proposal is not None
        if plan.proposal.id != request.expected_proposal_id:
            raise PlanningConstraintError(
                "proposal_stale", "The pending proposal changed."
            )
        draft = await self._replacement_plan(
            athlete_id=athlete_id,
            context=context,
            plan=plan,
            workout_id=workout_id,
            replacement=request.replacement_template_id,
        )
        # Bind the pending revision as well as the active base; a compatible V6
        # repository must perform this compare-and-swap atomically with expiry.
        fingerprint = hashlib.sha256(
            f"{VERSION}:{athlete_id}:{plan_id}:{request.expected_revision}:{workout_id}:{request.replacement_template_id}".encode()
        ).hexdigest()
        payload = self._proposal_payload(
            request_id=UUID(context["initial_plan_request_id"]),
            input_fingerprint=context["input_fingerprint"],
            generation_fingerprint=fingerprint,
            plan_id=plan_id,
            expected_base_revision=int(context.get("active_revision") or 0),
            week_start=plan.week_start,
            timezone_name=plan.timezone,
            available_dates=plan.available_dates,
            availability_source=plan.availability_source,
            injuries=plan.confirmed_injuries,
            low_only_disciplines=plan.low_only_disciplines,
            cross_training_opt_ins=frozenset(
                Discipline(s) for s in context.get("cross_training_opt_ins", [])
            ),
            goal_disciplines=self._context_values(self._planning_input(context))[2],
            draft=draft,
            workout_source="athlete_selected",
        )
        payload["expected_pending_revision"] = request.expected_revision
        payload["expected_proposal_id"] = str(request.expected_proposal_id)
        payload["v6_edit_operation_key"] = operation_key
        payload["weekly_registration_evidence"] = context.get(
            "weekly_registration_evidence", []
        )
        retained = {str(w.id): w for w in plan.workouts if w.id != workout_id}
        for row in payload["workouts"]:
            if row["occurrence_id"] in retained:
                row["source"] = retained[row["occurrence_id"]].source
        await self._repository.create_plan_proposal(athlete_id, payload)
        immutable_result = await self._v6_repository.fetch_v6_edit_retry(
            athlete_id, operation_key
        )
        if immutable_result is None:
            raise PlanningRepositoryUnavailableError(
                "The immutable edit receipt is unavailable."
            )
        response = WeeklyPlanProposalResponse.model_validate(immutable_result)
        response.plan.workouts = await self._present_workouts(response.plan.workouts)
        return response
