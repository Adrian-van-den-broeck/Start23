"""Opaque athlete-identity resolution at the Supabase authentication boundary."""

from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings


class AthleteIdentityResolutionError(Exception):
    """The authenticated account could not be mapped to one athlete."""


class AthleteIdentityRepository(Protocol):
    """Resolve the current token without exposing the private identity map."""

    async def resolve_current_athlete_id(self, access_token: str) -> UUID:
        """Return the one opaque athlete ID mapped to the caller token."""

    async def aclose(self) -> None:
        """Release repository resources."""


class SupabaseAthleteIdentityRepository:
    """Call the narrowly scoped owner RPC with the verified caller token."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._publishable_key = settings.supabase_publishable_key
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.supabase_data_api_timeout_seconds,
        )

    async def resolve_current_athlete_id(self, access_token: str) -> UUID:
        if not self._publishable_key:
            raise AthleteIdentityResolutionError
        try:
            response = await self._client.post(
                f"{self._base_url}/rpc/get_current_athlete_id",
                headers={
                    "apikey": self._publishable_key,
                    "Authorization": f"Bearer {access_token}",
                    "Accept-Profile": "public",
                    "Content-Profile": "public",
                },
                json={},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise AthleteIdentityResolutionError from error
        if not response.is_success:
            raise AthleteIdentityResolutionError
        try:
            payload: Any = response.json()
            return UUID(str(payload))
        except (TypeError, ValueError) as error:
            raise AthleteIdentityResolutionError from error

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class LegacyAthleteOwnerAdapter:
    """Bounded R3 adapter for stored procedures still keyed by auth UUID."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._secret_key = settings.supabase_secret_key.get_secret_value()
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._client = client
        self._legacy_by_opaque: dict[UUID, UUID] = {}
        self._opaque_by_legacy: dict[UUID, UUID] = {}

    def _headers(self) -> dict[str, str]:
        if not self._secret_key:
            raise AthleteIdentityResolutionError
        return {
            "apikey": self._secret_key,
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }

    async def legacy_id(self, athlete_id: UUID) -> UUID:
        """Resolve opaque domain ownership only at an old-RPC boundary."""
        cached = self._legacy_by_opaque.get(athlete_id)
        if cached is not None:
            return cached
        resolved = await self._resolve(
            "resolve_legacy_auth_user_id",
            {"p_athlete_id": str(athlete_id)},
        )
        self._legacy_by_opaque[athlete_id] = resolved
        self._opaque_by_legacy[resolved] = athlete_id
        return resolved

    async def opaque_id(self, auth_user_id: UUID) -> UUID:
        """Normalize legacy owners returned by background/service RPCs."""
        cached = self._opaque_by_legacy.get(auth_user_id)
        if cached is not None:
            return cached
        resolved = await self._resolve(
            "resolve_opaque_athlete_id_for_auth_user",
            {"p_auth_user_id": str(auth_user_id)},
        )
        self._opaque_by_legacy[auth_user_id] = resolved
        self._legacy_by_opaque[resolved] = auth_user_id
        return resolved

    async def _resolve(self, rpc: str, payload: dict[str, str]) -> UUID:
        try:
            response = await self._client.post(
                f"{self._base_url}/rpc/{rpc}",
                headers=self._headers(),
                json=payload,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise AthleteIdentityResolutionError from error
        if not response.is_success:
            raise AthleteIdentityResolutionError
        try:
            return UUID(str(response.json()))
        except (TypeError, ValueError) as error:
            raise AthleteIdentityResolutionError from error
