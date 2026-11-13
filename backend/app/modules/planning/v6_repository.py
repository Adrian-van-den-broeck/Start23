"""Explicitly injected inactive V6 adapter; startup never constructs this class.

All identity, discovery, draft CAS, confirmation and cancellation operations use
the established repository. Only frozen V6 reads/writes use the successor RPCs.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx

from app.core.config import Settings
from app.modules.workouts.catalog import WorkoutTemplate
from app.modules.workouts.repository import PlanningCatalogUnavailableError
from app.modules.workouts.v6_storage import parse_catalog_document

from .repository import (
    JsonObject,
    PlanningRepositoryUnavailableError,
    SupabasePlanningRepository,
)


class InactiveSupabaseV6Repository(SupabasePlanningRepository):
    supports_frozen_v6_snapshots = True
    supports_frequency_policy = True

    async def fetch_v6_swipe_receipt(
        self, access_token: str, draft_id: UUID
    ) -> JsonObject | None:
        result = await self._request(
            "POST",
            "rpc/get_v6_frequency_swipe_receipt",
            access_token=access_token,
            json={"p_draft_id": str(draft_id)},
        )
        if result is not None and not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result) if result is not None else None

    async def fetch_frequency_context(
        self, athlete_id: UUID, week_start: date, timezone_name: str
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_v6_frequency_context",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_week_start": week_start.isoformat(),
                "p_timezone": timezone_name,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def create_swipe_draft(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        if "v6_frequency_context" not in payload:
            return await super().create_swipe_draft(athlete_id, payload)
        result = await self._request(
            "POST",
            "rpc/create_v6_frequency_swipe_draft",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def update_swipe_draft(
        self,
        athlete_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        payload: JsonObject,
    ) -> JsonObject:
        if "v6_frequency_context" not in payload:
            return await super().update_swipe_draft(
                athlete_id, draft_id, expected_revision, payload
            )
        result = await self._request(
            "POST",
            "rpc/update_v6_frequency_swipe_draft",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_draft_id": str(draft_id),
                "p_expected_revision": expected_revision,
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    def __init__(
        self, settings: Settings, *, client: httpx.AsyncClient | None = None
    ) -> None:
        super().__init__(settings, client=client)
        # Explicit inactive adapter requires the complete local V2 migration set.
        self._v2_ready = True

    @staticmethod
    def _response_payload(response: httpx.Response) -> Any:
        return response.json(parse_float=Decimal)

    async def create_plan_proposal(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/create_v6_frequency_swipe_proposal"
            if "v6_swipe_draft" in payload
            else "rpc/create_v6_weekly_plan_proposal",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_payload": {"weekly_registration_evidence": [], **payload},
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def fetch_v6_edit_retry(
        self, athlete_id: UUID, operation_key: str
    ) -> JsonObject | None:
        result = await self._request(
            "POST",
            "rpc/get_v6_mobile_edit_retry",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_operation_key": operation_key,
            },
        )
        if result is not None and not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result) if result is not None else None

    async def fetch_workout_context(
        self, access_token: str, workout_id: UUID
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_v6_move_workout_context",
            access_token=access_token,
            json={"p_workout_id": str(workout_id)},
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def move_v6_workout(
        self, athlete_id: UUID, payload: JsonObject
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/move_v6_planned_workout",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def fetch_plan(
        self, access_token: str, plan_id: UUID, revision: int | None = None
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_v6_mobile_weekly_plan",
            access_token=access_token,
            json={"p_plan_id": str(plan_id), "p_revision": revision},
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def fetch_calendar(
        self, access_token: str, from_date: date, to_date: date
    ) -> tuple[JsonObject, ...]:
        result = await self._request(
            "POST",
            "rpc/get_v6_mobile_calendar",
            access_token=access_token,
            json={
                "p_from_date": from_date.isoformat(),
                "p_to_date": to_date.isoformat(),
            },
        )
        if not isinstance(result, list):
            raise PlanningRepositoryUnavailableError
        return tuple(dict(row) for row in result)

    async def _v6_context(
        self, athlete_id: UUID, plan_id: UUID, revision: int | None
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_v6_plan_context_for_planning",
            service=True,
            json={
                "p_athlete_id": str(await self._rpc_athlete_id(athlete_id)),
                "p_plan_id": str(plan_id),
                "p_revision": revision,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        eligibility = await self._planning_eligibility_context(athlete_id)
        return {**result, **eligibility}

    async def fetch_plan_context(self, athlete_id: UUID, plan_id: UUID) -> JsonObject:
        return await self._v6_context(athlete_id, plan_id, None)

    async def fetch_plan_revision_context(
        self, athlete_id: UUID, plan_id: UUID, revision: int
    ) -> JsonObject:
        return await self._v6_context(athlete_id, plan_id, revision)


class InactiveSupabaseV6CatalogProvider:
    """Read immutable database revisions without workbook dependencies or a cache."""

    def __init__(self, repository: InactiveSupabaseV6Repository) -> None:
        self._repository = repository

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        rows = await self._repository._request(
            "POST", "rpc/get_inactive_v6_catalog_for_planning", service=True, json={}
        )
        try:
            if not isinstance(rows, list) or len(rows) != 77:
                raise ValueError("incomplete_v6_catalog")
            catalog = tuple(parse_catalog_document(row) for row in rows)
            if (
                len({t.id for t in catalog}) != 77
                or len({t.template_key for t in catalog}) != 77
            ):
                raise ValueError("ambiguous_v6_catalog")
            return catalog
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            raise PlanningCatalogUnavailableError from error

    async def aclose(self) -> None:
        # The application owns the shared planning repository/client.
        return None
