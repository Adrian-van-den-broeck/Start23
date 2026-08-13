"""Supabase Data API adapter for canonical Phase 7 activities."""

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class ActivityRepositoryError(Exception):
    """Base persistence error hidden behind public API messages."""


class ActivityRepositoryNotFoundError(ActivityRepositoryError):
    """An owner-scoped activity or planned workout was not found."""


class ActivityRepositoryConflictError(ActivityRepositoryError):
    """Idempotency or immutable-RPE state conflicts with the request."""

    def __init__(self, code: str = "activity_state_conflict") -> None:
        super().__init__(code)
        self.code = code


class ActivityRepositoryUnavailableError(ActivityRepositoryError):
    """Persistence is temporarily unavailable."""


class ActivityRepository(Protocol):
    """Persistence boundary used by the activity application service."""

    async def create_activity(
        self,
        access_token: str,
        idempotency_key: UUID,
        request_fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject: ...

    async def fetch_activity(
        self, access_token: str, activity_id: UUID
    ) -> JsonObject: ...

    async def list_activities(
        self,
        access_token: str,
        *,
        pending_rpe: bool,
    ) -> tuple[JsonObject, ...]: ...

    async def fetch_processing_context(
        self,
        athlete_id: UUID,
        activity_id: UUID,
    ) -> JsonObject: ...

    async def complete_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject: ...

    async def revise_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject: ...

    async def aclose(self) -> None: ...


class SupabaseActivityRepository:
    """Use caller RLS for public writes and narrow secret RPCs for hidden load."""

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
        self, access_token: str = "", *, service: bool = False
    ) -> dict[str, str]:
        key = self._secret_key if service else self._publishable_key
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
            raise ActivityRepositoryUnavailableError from error
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
            raise ActivityRepositoryNotFoundError
        conflicts = {
            "activity idempotency key reused": "idempotency_key_reused",
            "activity rpe is immutable": "activity_rpe_immutable",
            "planned workout already matched": "planned_workout_already_matched",
            "rpe correction window closed": "activity_rpe_window_closed",
            "planned external activity already completed": (
                "planned_external_activity_already_completed"
            ),
        }
        if response.status_code in {400, 409, 422} or code in {
            "23505",
            "23514",
            "40001",
            "P0001",
        }:
            raise ActivityRepositoryConflictError(
                conflicts.get(message, "activity_state_conflict")
            )
        raise ActivityRepositoryUnavailableError

    async def create_activity(
        self,
        access_token: str,
        idempotency_key: UUID,
        request_fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        external_activity_id = payload.get("planned_external_activity_id")
        rpc_name = (
            "create_external_activity_summary"
            if external_activity_id is not None
            else "create_activity_summary"
        )
        result = await self._request(
            "POST",
            f"rpc/{rpc_name}",
            access_token=access_token,
            json={
                "p_idempotency_key": str(idempotency_key),
                "p_request_fingerprint": request_fingerprint,
                "p_payload": payload,
                **(
                    {"p_external_activity_id": str(external_activity_id)}
                    if external_activity_id is not None
                    else {}
                ),
            },
        )
        if not isinstance(result, dict):
            raise ActivityRepositoryUnavailableError
        return dict(result)

    async def fetch_activity(self, access_token: str, activity_id: UUID) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_activity",
            access_token=access_token,
            json={"p_activity_id": str(activity_id)},
        )
        if not isinstance(result, dict):
            raise ActivityRepositoryNotFoundError
        return dict(result)

    async def list_activities(
        self,
        access_token: str,
        *,
        pending_rpe: bool,
    ) -> tuple[JsonObject, ...]:
        result = await self._request(
            "POST",
            "rpc/list_activities",
            access_token=access_token,
            json={"p_pending_rpe": pending_rpe},
        )
        if not isinstance(result, list):
            raise ActivityRepositoryUnavailableError
        return tuple(dict(row) for row in result if isinstance(row, dict))

    async def fetch_processing_context(
        self,
        athlete_id: UUID,
        activity_id: UUID,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/get_activity_processing_context",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_activity_id": str(activity_id),
            },
        )
        if not isinstance(result, dict):
            raise ActivityRepositoryNotFoundError
        return dict(result)

    async def complete_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/complete_activity_rpe",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_activity_id": str(activity_id),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise ActivityRepositoryUnavailableError
        return dict(result)

    async def revise_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/revise_activity_rpe",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_activity_id": str(activity_id),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise ActivityRepositoryUnavailableError
        return dict(result)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
