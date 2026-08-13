"""Owner-scoped Supabase persistence for calibration setup and observations."""

import asyncio
import logging
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]
logger = logging.getLogger(__name__)


class CalibrationRepositoryError(Exception):
    """Base persistence failure without client-sensitive details."""


class CalibrationRepositoryConflictError(CalibrationRepositoryError):
    """A stable idempotency or lifecycle constraint was violated."""


class CalibrationRepositoryNotFoundError(CalibrationRepositoryError):
    """The owner-scoped resource does not exist."""


class CalibrationRepositoryUnavailableError(CalibrationRepositoryError):
    """Supabase could not complete the operation."""


class CalibrationRepository(Protocol):
    """Persistence surface used by the calibration application service."""

    async def save_setup(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        """Upsert one owner-derived discipline setup choice."""

    async def save_observation(
        self,
        access_token: str,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        """Insert or return one identical immutable observation."""

    async def list_observations(
        self,
        access_token: str,
        athlete_id: UUID,
        protocol_id: str,
        activity_id: UUID,
    ) -> list[JsonObject]:
        """Read exact owner/protocol/activity observations."""

    async def save_evaluation(
        self,
        athlete_id: UUID,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        """Persist a server-calculated evaluation through a service-only RPC."""

    async def fetch_status(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject:
        """Fetch owner-scoped setup and evaluation history."""

    async def aclose(self) -> None:
        """Release owned network resources."""


class SupabaseCalibrationRepository:
    """Use caller JWTs for RLS and a narrow secret-key evaluation RPC."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._publishable_key = settings.supabase_publishable_key
        self._secret_key = settings.supabase_secret_key.get_secret_value()
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.supabase_data_api_timeout_seconds,
        )

    def _headers(self, access_token: str) -> dict[str, str]:
        if not self._publishable_key:
            raise CalibrationRepositoryUnavailableError
        return {
            "apikey": self._publishable_key,
            "Authorization": f"Bearer {access_token}",
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }

    def _service_headers(self) -> dict[str, str]:
        if not self._secret_key:
            raise CalibrationRepositoryUnavailableError
        return {
            "apikey": self._secret_key,
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }

    async def _request(
        self,
        method: str,
        path: str,
        access_token: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Any = None,
        service: bool = False,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}/{path}",
                headers=(
                    self._service_headers() if service else self._headers(access_token)
                ),
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise CalibrationRepositoryUnavailableError from error
        if response.is_success:
            return response.json() if response.content else None

        error_code: str | None = None
        try:
            body = response.json()
            if isinstance(body, dict):
                error_code = str(body.get("code"))
        except ValueError:
            pass
        logger.warning(
            "Supabase calibration request failed",
            extra={
                "event": "supabase_calibration_request_failed",
                "path": path,
                "status_code": response.status_code,
                "error_code": error_code,
            },
        )
        if response.status_code == 404 or error_code == "P0002":
            raise CalibrationRepositoryNotFoundError
        if response.status_code in {400, 409, 422} or error_code in {
            "23505",
            "23514",
            "40001",
        }:
            raise CalibrationRepositoryConflictError
        raise CalibrationRepositoryUnavailableError

    async def _select(
        self,
        table: str,
        access_token: str,
        athlete_id: UUID,
        *,
        extra_params: Mapping[str, str] | None = None,
    ) -> list[JsonObject]:
        result = await self._request(
            "GET",
            table,
            access_token,
            params={
                "athlete_id": f"eq.{athlete_id}",
                **dict(extra_params or {}),
            },
        )
        if not isinstance(result, list):
            raise CalibrationRepositoryUnavailableError
        return [dict(row) for row in result]

    async def save_setup(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_discipline_zone_setup",
            access_token,
            json={"p_setup": values},
        )
        if not isinstance(result, dict):
            raise CalibrationRepositoryUnavailableError
        return dict(result)

    async def save_observation(
        self,
        access_token: str,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_calibration_observation",
            access_token,
            json={"p_observation": values, "p_fingerprint": fingerprint},
        )
        if not isinstance(result, dict):
            raise CalibrationRepositoryUnavailableError
        return dict(result)

    async def list_observations(
        self,
        access_token: str,
        athlete_id: UUID,
        protocol_id: str,
        activity_id: UUID,
    ) -> list[JsonObject]:
        rows = await self._select(
            "calibration_observations",
            access_token,
            athlete_id,
            extra_params={
                "protocol_id": f"eq.{protocol_id}",
                "activity_id": f"eq.{activity_id}",
                "order": "performed_at.asc,created_at.asc",
            },
        )
        return [
            {
                **dict(row["payload"]),
                "id": row["id"],
                "fingerprint": row["fingerprint"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def save_evaluation(
        self,
        athlete_id: UUID,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_calibration_evaluation",
            "",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_evaluation": values,
                "p_fingerprint": fingerprint,
            },
        )
        if not isinstance(result, dict):
            raise CalibrationRepositoryUnavailableError
        return dict(result)

    async def fetch_status(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject:
        setups, evaluations = await asyncio.gather(
            self._select(
                "discipline_zone_setups",
                access_token,
                athlete_id,
                extra_params={"order": "discipline.asc"},
            ),
            self._select(
                "calibration_evaluations",
                access_token,
                athlete_id,
                extra_params={"order": "created_at.desc"},
            ),
        )
        return {"setups": setups, "evaluations": evaluations}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
