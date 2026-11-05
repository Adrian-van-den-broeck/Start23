"""Inactive adapter to existing pending, swipe, approval and repository contracts.

Never installed by application startup or settings. A repository must explicitly
support frozen V6 snapshots; the current Supabase writer does not and rejects.
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

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.physiology.planned_v6 import METHOD
from app.modules.workouts.catalog import WorkoutTemplate
from app.modules.workouts.joren_v6_official import V6Template, official_catalog

from .domain import PlanningConstraintError, PlanningTarget, PlanningTargetBasis
from .repository import (
    JsonObject,
    PlanningRepository,
    PlanningRepositoryUnavailableError,
)
from .schemas import (
    ChangeProposalSummaryResponse,
    PendingWorkoutAlternativesResponse,
    PendingWorkoutEditRequest,
    WeeklyPlanProposalResponse,
    WeeklyPlanResponse,
)
from .service import PlanningService, _SwipePlanningContext
from .swipe import SwipeSelectionState
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


class FrozenV6Repository(PlanningRepository, Protocol):
    supports_frozen_v6_snapshots: bool

    async def fetch_v6_edit_retry(
        self, athlete_id: UUID, operation_key: str
    ) -> JsonObject | None:
        """Owner-scoped immutable idempotent edit result, before stale checks."""


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
        self._bind_occurrences(kwargs["athlete_id"], kwargs["week_start"])
        context = await super()._prepare_swipe_context(**kwargs)
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
        self._bind_occurrences(kwargs["athlete_id"], kwargs["week_start"])
        return await super()._build_and_persist(**kwargs)

    def _bind_occurrences(self, athlete_id: UUID, week_start: date) -> None:
        scoped = replace(
            self._controls,
            occurrence_namespace=uuid5(athlete_id, f"{VERSION}:{week_start}"),
        )
        self._plan_builder = partial(build_v6_plan, controls=scoped)

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
        payload["planning_ruleset_version"] = VERSION
        payload["v6_frozen_snapshot"] = json.loads(
            private_json(
                {
                    "policy": VERSION,
                    "planned_method": METHOD,
                    "input_fingerprint": payload["input_fingerprint"],
                    "estimated_sports": sorted(s.value for s in draft.estimated_sports),
                    "controls": json.loads(controls_json(draft.controls)),
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
            discipline_caps={
                Discipline(s): InternalLoad(Decimal(v["value"]))
                for s, v in stored["discipline_caps"].items()
            },
        )
        timezone_name, race_date, goals, capabilities = self._context_values(snapshot)
        ids = tuple(
            (replacement if w.id == workout_id else w.template_id)
            for w in plan.workouts
            if w.id != workout_id or replacement is not None
        )
        occurrences = tuple(
            w.id for w in plan.workouts if w.id != workout_id or replacement is not None
        )
        fixed = {
            w.id: w.scheduled_date
            for w in plan.workouts
            if w.id != workout_id or replacement is not None
        }
        result = await self._computation.run(
            self._plan_builder,
            controls=replace(self._controls, authorized_target=frozen_target),
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
        deck = self._eligible_workouts(
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
            return WeeklyPlanProposalResponse.model_validate(retry)
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
            goal_disciplines=self._context_values(self._planning_input(context))[2],
            draft=draft,
            workout_source="athlete_selected",
        )
        payload["expected_pending_revision"] = request.expected_revision
        payload["expected_proposal_id"] = str(request.expected_proposal_id)
        payload["v6_edit_operation_key"] = operation_key
        retained = {str(w.id): w for w in plan.workouts if w.id != workout_id}
        for row in payload["workouts"]:
            if row["occurrence_id"] in retained:
                row["source"] = retained[row["occurrence_id"]].source
        result = await self._repository.create_plan_proposal(athlete_id, payload)
        return WeeklyPlanProposalResponse(
            proposal=ChangeProposalSummaryResponse.model_validate(
                await self._repository.fetch_proposal(
                    access_token, UUID(result["proposal_id"])
                )
            ),
            plan=WeeklyPlanResponse.model_validate(
                await self._repository.fetch_plan(
                    access_token, plan_id, int(result["revision"])
                )
            ),
        )
