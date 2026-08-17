"""Owner-scoped Supabase Data API repository for onboarding."""

import asyncio
import logging
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]
logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base persistence failure with no client-sensitive payload."""


class RepositoryConflictError(RepositoryError):
    """The requested state conflicts with persisted state."""


class RepositoryNotFoundError(RepositoryError):
    """The owner-scoped resource does not exist."""


class RepositoryUnavailableError(RepositoryError):
    """Supabase could not complete the request."""


class RepositorySchemaMismatchError(RepositoryUnavailableError):
    """The configured Data API schema is behind the running backend."""


class OnboardingRepository(Protocol):
    """Persistence surface used by the Phase 4 application service."""

    async def fetch_state(self, access_token: str, athlete_id: UUID) -> JsonObject:
        """Fetch all public onboarding records for one verified owner."""

    async def upsert_profile(
        self,
        access_token: str,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        """Create or patch the owner's profile."""

    async def replace_training_history(
        self,
        access_token: str,
        entries: list[JsonObject],
    ) -> list[JsonObject]:
        """Atomically replace the three discipline-history rows."""

    async def save_primary_goal(
        self,
        access_token: str,
        goal_id: UUID | None,
        values: JsonObject,
    ) -> JsonObject:
        """Create or update the one active A-race goal."""

    async def save_zone_profile(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        """Atomically persist explicit manual zones and an optional proposal."""

    async def save_fallback_zone_profile(
        self,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        """Persist server-generated fallback zones through the trusted RPC."""

    async def complete_onboarding(self, access_token: str) -> UUID:
        """Validate persisted state and create a pending planning request."""

    async def approve_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_zone_profile_id: UUID,
    ) -> JsonObject:
        """Atomically promote one stale-safe pending zone version."""

    async def reject_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        """Reject one pending zone version without changing active zones."""

    async def aclose(self) -> None:
        """Release repository resources."""


class SupabaseOnboardingRepository:
    """Call PostgREST with the verified user token so RLS retains auth.uid()."""

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

    def _headers(
        self,
        access_token: str,
        *,
        prefer: str | None = None,
    ) -> dict[str, str]:
        if not self._publishable_key:
            raise RepositoryUnavailableError("publishable key is not configured")
        headers = {
            "apikey": self._publishable_key,
            "Authorization": f"Bearer {access_token}",
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }
        if prefer is not None:
            headers["Prefer"] = prefer
        return headers

    def _service_headers(self) -> dict[str, str]:
        if not self._secret_key:
            raise RepositoryUnavailableError("secret key is not configured")
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
        prefer: str | None = None,
        service: bool = False,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}/{path}",
                headers=(
                    self._service_headers()
                    if service
                    else self._headers(access_token, prefer=prefer)
                ),
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise RepositoryUnavailableError from error

        if response.is_success:
            if response.status_code == 204 or not response.content:
                return None
            return response.json()

        error_code: str | None = None
        try:
            error_payload = response.json()
            if isinstance(error_payload, dict):
                error_code = str(error_payload.get("code"))
        except ValueError:
            pass

        logger.warning(
            "Supabase Data API request failed",
            extra={
                "event": "supabase_data_api_request_failed",
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "error_code": error_code,
            },
        )

        if error_code == "P0002":
            raise RepositoryNotFoundError
        if response.status_code == 404 and error_code == "PGRST205":
            raise RepositorySchemaMismatchError
        if response.status_code == 404:
            raise RepositoryNotFoundError
        if response.status_code in {400, 409, 422} or error_code in {
            "23505",
            "23514",
            "40001",
        }:
            raise RepositoryConflictError
        raise RepositoryUnavailableError

    async def _select(
        self,
        table: str,
        access_token: str,
        athlete_id: UUID,
        *,
        select: str = "*",
        extra_params: Mapping[str, str] | None = None,
    ) -> list[JsonObject]:
        params = {
            "select": select,
            "athlete_id": f"eq.{athlete_id}",
            **dict(extra_params or {}),
        }
        payload = await self._request(
            "GET",
            table,
            access_token,
            params=params,
        )
        if not isinstance(payload, list):
            raise RepositoryUnavailableError
        return [dict(row) for row in payload]

    async def _select_optional(
        self,
        table: str,
        access_token: str,
        athlete_id: UUID,
        *,
        extra_params: Mapping[str, str] | None = None,
    ) -> list[JsonObject]:
        """Read a forward-schema table without blocking the earlier flow."""
        try:
            return await self._select(
                table,
                access_token,
                athlete_id,
                extra_params=extra_params,
            )
        except RepositorySchemaMismatchError:
            logger.warning(
                "Optional Supabase Data API table is not deployed",
                extra={
                    "event": "optional_supabase_table_unavailable",
                    "table": table,
                },
            )
            return []

    async def fetch_state(self, access_token: str, athlete_id: UUID) -> JsonObject:
        """Fetch rows in parallel with an explicit owner filter on every query."""
        (
            profiles,
            sessions,
            history,
            goals,
            zone_profiles,
            metrics,
            boundaries,
            discipline_setups,
        ) = await asyncio.gather(
            self._select("athlete_profiles", access_token, athlete_id),
            self._select("onboarding_sessions", access_token, athlete_id),
            self._select(
                "training_history_entries",
                access_token,
                athlete_id,
                extra_params={"order": "discipline.asc"},
            ),
            self._select(
                "goals",
                access_token,
                athlete_id,
                extra_params={"status": "eq.active"},
            ),
            self._select(
                "zone_profile_versions",
                access_token,
                athlete_id,
                extra_params={
                    "status": "in.(active,pending)",
                    "order": "discipline.asc,version.desc",
                },
            ),
            self._select("zone_metrics", access_token, athlete_id),
            self._select(
                "zone_boundaries",
                access_token,
                athlete_id,
                extra_params={"order": "zone_number.asc"},
            ),
            self._select_optional(
                "discipline_zone_setups",
                access_token,
                athlete_id,
                extra_params={"order": "discipline.asc"},
            ),
        )
        return {
            "profile": profiles[0] if profiles else None,
            "session": sessions[0] if sessions else None,
            "training_history": history,
            "goals": goals,
            "zone_profiles": zone_profiles,
            "zone_metrics": metrics,
            "zone_boundaries": boundaries,
            "discipline_setups": discipline_setups,
        }

    async def upsert_profile(
        self,
        access_token: str,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        update_payload = {"onboarding_status": "in_progress", **values}
        result = await self._request(
            "PATCH",
            "athlete_profiles",
            access_token,
            params={"athlete_id": f"eq.{athlete_id}"},
            json=update_payload,
            prefer="return=representation",
        )
        if isinstance(result, list) and result:
            return dict(result[0])
        insert_payload = {
            "athlete_id": str(athlete_id),
            **update_payload,
        }
        result = await self._request(
            "POST",
            "athlete_profiles",
            access_token,
            json=insert_payload,
            prefer="return=representation",
        )
        if not isinstance(result, list) or not result:
            raise RepositoryUnavailableError
        return dict(result[0])

    async def replace_training_history(
        self,
        access_token: str,
        entries: list[JsonObject],
    ) -> list[JsonObject]:
        result = await self._request(
            "POST",
            "rpc/replace_training_history",
            access_token,
            json={"p_entries": entries},
        )
        if not isinstance(result, list):
            raise RepositoryUnavailableError
        return [dict(row) for row in result]

    async def save_primary_goal(
        self,
        access_token: str,
        goal_id: UUID | None,
        values: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_primary_race_goal",
            access_token,
            json={
                "p_goal_id": str(goal_id) if goal_id is not None else None,
                **{f"p_{key}": value for key, value in values.items()},
            },
        )
        if isinstance(result, list):
            if not result:
                raise RepositoryNotFoundError
            return dict(result[0])
        if not isinstance(result, dict):
            raise RepositoryUnavailableError
        return dict(result)

    async def save_fallback_zone_profile(
        self,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_fallback_zone_profile",
            "",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_discipline": values["discipline"],
                "p_boundaries": values["boundaries"],
            },
        )
        if not isinstance(result, dict):
            raise RepositoryUnavailableError
        return dict(result)

    async def save_zone_profile(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/save_zone_profile",
            access_token,
            json={f"p_{key}": value for key, value in values.items()},
        )
        if not isinstance(result, dict):
            raise RepositoryUnavailableError
        return dict(result)

    async def complete_onboarding(self, access_token: str) -> UUID:
        result = await self._request(
            "POST",
            "rpc/complete_onboarding",
            access_token,
            json={},
        )
        try:
            return UUID(str(result))
        except (TypeError, ValueError) as error:
            raise RepositoryUnavailableError from error

    async def approve_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_zone_profile_id: UUID,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/approve_zone_proposal",
            access_token,
            json={
                "p_proposal_id": str(proposal_id),
                "p_expected_base_zone_profile_id": str(expected_base_zone_profile_id),
            },
        )
        if not isinstance(result, dict):
            raise RepositoryUnavailableError
        return dict(result)

    async def reject_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/reject_zone_proposal",
            access_token,
            json={"p_proposal_id": str(proposal_id)},
        )
        if not isinstance(result, dict):
            raise RepositoryUnavailableError
        return dict(result)

    async def aclose(self) -> None:
        """Close only clients constructed by this repository."""
        if self._owns_client:
            await self._client.aclose()
