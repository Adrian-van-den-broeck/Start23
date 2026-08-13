"""Supabase persistence boundary for Phase 8 weekly check-ins."""

from collections.abc import Mapping
from datetime import date
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class CheckInRepositoryError(Exception):
    """Base error hidden behind public check-in messages."""


class CheckInRepositoryNotFoundError(CheckInRepositoryError):
    """An owner-scoped check-in does not exist."""


class CheckInRepositoryConflictError(CheckInRepositoryError):
    """A context or plan precondition is stale."""

    def __init__(self, code: str = "checkin_state_conflict") -> None:
        super().__init__(code)
        self.code = code


class CheckInRepositoryUnavailableError(CheckInRepositoryError):
    """The persistence dependency is temporarily unavailable."""


class CheckInRepository(Protocol):
    async def start_or_resume(
        self,
        access_token: str,
        week_start: date,
    ) -> JsonObject: ...

    async def fetch(self, access_token: str, checkin_id: UUID) -> JsonObject: ...

    async def save_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject: ...

    async def confirm_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
    ) -> JsonObject: ...

    async def fetch_planning_context(
        self,
        athlete_id: UUID,
        checkin_id: UUID,
    ) -> JsonObject: ...

    async def attach_plan_proposal(
        self,
        athlete_id: UUID,
        checkin_id: UUID,
        proposal_id: UUID,
    ) -> JsonObject: ...

    async def list_restrictions(
        self,
        access_token: str,
    ) -> tuple[JsonObject, ...]: ...

    async def list_external_activities(
        self,
        access_token: str,
        week_start: date | None,
    ) -> tuple[JsonObject, ...]: ...

    async def mark_goal_achieved(
        self,
        access_token: str,
        goal_id: UUID,
        achieved_at: date,
    ) -> JsonObject: ...

    async def aclose(self) -> None: ...


class SupabaseCheckInRepository:
    """Retain caller RLS for athlete actions and narrow trusted reads."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._publishable_key = settings.supabase_publishable_key
        self._secret_key = settings.supabase_secret_key.get_secret_value()
        self._client = client or httpx.AsyncClient(
            timeout=settings.supabase_data_api_timeout_seconds
        )
        self._owns_client = client is None

    def _headers(
        self,
        access_token: str = "",
        *,
        service: bool = False,
    ) -> dict[str, str]:
        key = self._secret_key if service else self._publishable_key
        if not key:
            raise CheckInRepositoryUnavailableError
        headers = {
            "apikey": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }
        if not service:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str = "",
        service: bool = False,
        params: Mapping[str, str] | None = None,
        json: Any = None,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}/{path}",
                headers=self._headers(access_token, service=service),
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise CheckInRepositoryUnavailableError from error
        if response.is_success:
            return response.json() if response.content else None
        code = ""
        message = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                code = str(body.get("code", ""))
                message = str(body.get("message", ""))
        except ValueError:
            pass
        if response.status_code == 404 or code == "P0002":
            raise CheckInRepositoryNotFoundError
        conflicts = {
            "check-in context is stale": "checkin_context_stale",
            "check-in context is not confirmed": "checkin_not_confirmed",
            "check-in is already completed": "checkin_already_completed",
            "active restriction review is missing": "restriction_review_required",
        }
        if response.status_code in {400, 409, 422} or code in {
            "23505",
            "23514",
            "40001",
            "P0001",
        }:
            raise CheckInRepositoryConflictError(
                conflicts.get(message, "checkin_state_conflict")
            )
        raise CheckInRepositoryUnavailableError

    async def start_or_resume(
        self,
        access_token: str,
        week_start: date,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/start_weekly_checkin",
            access_token=access_token,
            json={"p_week_start": week_start.isoformat()},
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryUnavailableError
        return dict(result)

    async def fetch(self, access_token: str, checkin_id: UUID) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_weekly_checkin",
            access_token=access_token,
            json={"p_checkin_id": str(checkin_id)},
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryNotFoundError
        return dict(result)

    async def save_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_weekly_checkin_context",
            access_token=access_token,
            json={
                "p_checkin_id": str(checkin_id),
                "p_expected_revision": expected_revision,
                "p_fingerprint": fingerprint,
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryUnavailableError
        return dict(result)

    async def confirm_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/confirm_weekly_checkin_context",
            access_token=access_token,
            json={
                "p_checkin_id": str(checkin_id),
                "p_expected_revision": expected_revision,
                "p_fingerprint": fingerprint,
            },
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryUnavailableError
        return dict(result)

    async def fetch_planning_context(
        self,
        athlete_id: UUID,
        checkin_id: UUID,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_checkin_context_for_planning",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_checkin_id": str(checkin_id),
            },
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryNotFoundError
        return dict(result)

    async def attach_plan_proposal(
        self,
        athlete_id: UUID,
        checkin_id: UUID,
        proposal_id: UUID,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/attach_checkin_plan_proposal",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_checkin_id": str(checkin_id),
                "p_proposal_id": str(proposal_id),
            },
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryUnavailableError
        return dict(result)

    async def list_restrictions(
        self,
        access_token: str,
    ) -> tuple[JsonObject, ...]:
        result = await self._request(
            "GET",
            "injury_restrictions",
            access_token=access_token,
            params={
                "select": (
                    "id,discipline,status,allowed_intensity,source,start_at,review_at,"
                    "professional_advice,professional_advice_at,athlete_plan_choice,"
                    "confirmed_at,cleared_at"
                ),
                "cleared_at": "is.null",
                "order": "discipline.asc",
            },
        )
        if not isinstance(result, list):
            raise CheckInRepositoryUnavailableError
        return tuple(dict(row) for row in result if isinstance(row, dict))

    async def list_external_activities(
        self,
        access_token: str,
        week_start: date | None,
    ) -> tuple[JsonObject, ...]:
        params = {
            "select": (
                "id,week_start,name,discipline,scheduled_at,duration_minutes,"
                "strenuous,recurring,status,completed_activity_id,created_at"
            ),
            "order": "scheduled_at.asc",
        }
        if week_start is not None:
            params["week_start"] = f"eq.{week_start.isoformat()}"
        result = await self._request(
            "GET",
            "planned_external_activities",
            access_token=access_token,
            params=params,
        )
        if not isinstance(result, list):
            raise CheckInRepositoryUnavailableError
        return tuple(dict(row) for row in result if isinstance(row, dict))

    async def mark_goal_achieved(
        self,
        access_token: str,
        goal_id: UUID,
        achieved_at: date,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/mark_goal_achieved",
            access_token=access_token,
            json={
                "p_goal_id": str(goal_id),
                "p_achieved_at": achieved_at.isoformat(),
            },
        )
        if not isinstance(result, dict):
            raise CheckInRepositoryUnavailableError
        return dict(result)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
