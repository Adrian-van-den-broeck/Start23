"""Supabase persistence adapter for Pioneer beta access."""

from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class PioneerRepositoryError(Exception):
    """Base error for hidden Pioneer persistence failures."""


class PioneerRepositoryUnavailableError(PioneerRepositoryError):
    """The Pioneer persistence boundary could not be reached."""


class PioneerRepository(Protocol):
    async def redeem(
        self,
        athlete_id: UUID,
        code_digest: str,
        idempotency_key: UUID,
        request_fingerprint: str,
    ) -> JsonObject: ...

    async def fetch_current(
        self,
        access_token: str,
    ) -> JsonObject | None: ...

    async def aclose(self) -> None: ...


class SupabasePioneerRepository:
    """Use one service RPC to redeem and caller RLS to read enrollment."""

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

    async def _request(
        self,
        method: str,
        path: str,
        *,
        key: str,
        access_token: str | None = None,
        params: dict[str, str] | None = None,
        json: JsonObject | None = None,
    ) -> Any:
        headers = {
            "apikey": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }
        if access_token is not None:
            headers["Authorization"] = f"Bearer {access_token}"
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}/{path}",
                headers=headers,
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PioneerRepositoryUnavailableError from error
        if not response.is_success:
            raise PioneerRepositoryUnavailableError
        try:
            return response.json() if response.content else None
        except ValueError as error:
            raise PioneerRepositoryUnavailableError from error

    async def redeem(
        self,
        athlete_id: UUID,
        code_digest: str,
        idempotency_key: UUID,
        request_fingerprint: str,
    ) -> JsonObject:
        if not self._secret_key:
            raise PioneerRepositoryUnavailableError
        payload = await self._request(
            "POST",
            "rpc/redeem_pioneer_access_code",
            key=self._secret_key,
            json={
                "p_athlete_id": str(athlete_id),
                "p_code_digest": code_digest,
                "p_idempotency_key": str(idempotency_key),
                "p_request_fingerprint": request_fingerprint,
            },
        )
        if not isinstance(payload, dict):
            raise PioneerRepositoryUnavailableError
        return payload

    async def fetch_current(self, access_token: str) -> JsonObject | None:
        if not self._publishable_key:
            raise PioneerRepositoryUnavailableError
        payload = await self._request(
            "GET",
            "pioneer_access_redemptions",
            key=self._publishable_key,
            access_token=access_token,
            params={
                "select": "program,status,redeemed_at",
                "limit": "1",
            },
        )
        if not isinstance(payload, list):
            raise PioneerRepositoryUnavailableError
        if not payload:
            return None
        row = payload[0]
        if not isinstance(row, dict):
            raise PioneerRepositoryUnavailableError
        return row

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
