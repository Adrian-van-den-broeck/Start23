"""Minimal HTTP adapter for the approved Polar AccessLink v3 surface."""

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class PolarProviderError(Exception):
    """Provider failure that must not leak provider payloads to clients."""


class PolarAuthorizationError(PolarProviderError):
    """The provider token or grant is invalid or revoked."""


@dataclass(frozen=True)
class PolarToken:
    access_token: str
    provider_user_id: str
    expires_at: datetime | None


class PolarProvider(Protocol):
    def authorization_url(self, state: str) -> str: ...
    async def exchange_code(self, code: str) -> PolarToken: ...
    async def register_user(self, token: str, member_id: str) -> str: ...
    async def list_exercises(self, token: str) -> tuple[JsonObject, ...]: ...
    async def get_exercise(self, token: str, exercise_id: str) -> JsonObject: ...
    async def get_fit(self, token: str, exercise_id: str) -> bytes | None: ...
    async def revoke(self, token: str, provider_user_id: str) -> None: ...
    async def aclose(self) -> None: ...


class PolarAccessLinkClient:
    """Strict, bounded calls to Polar; no provider SDK enters domain modules."""

    _AUTH_URL = "https://flow.polar.com/oauth2/authorization"
    _TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
    _API_URL = "https://www.polaraccesslink.com/v3"

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client_id = settings.polar_client_id
        self._client_secret = settings.polar_client_secret.get_secret_value()
        self._redirect_uri = str(settings.polar_oauth_redirect_url)
        self._max_file_bytes = settings.polar_max_activity_file_bytes
        self._client = client or httpx.AsyncClient(
            timeout=settings.polar_api_timeout_seconds
        )
        self._owns_client = client is None

    def _configured(self) -> None:
        if not self._client_id or not self._client_secret:
            raise PolarProviderError("Polar integration is not configured.")

    def authorization_url(self, state: str) -> str:
        self._configured()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "scope": "accesslink.read_all",
                "state": state,
            }
        )
        return f"{self._AUTH_URL}?{query}"

    def _basic(self) -> str:
        credentials = f"{self._client_id}:{self._client_secret}".encode()
        encoded = base64.b64encode(credentials).decode()
        return f"Basic {encoded}"

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise PolarAuthorizationError
        if not response.is_success:
            raise PolarProviderError

    async def exchange_code(self, code: str) -> PolarToken:
        self._configured()
        try:
            response = await self._client.post(
                self._TOKEN_URL,
                headers={"Authorization": self._basic(), "Accept": "application/json"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                },
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        self._check(response)
        try:
            body = response.json()
            expires_in = int(body.get("expires_in", 0))
            return PolarToken(
                access_token=str(body["access_token"]),
                provider_user_id=str(body["x_user_id"]),
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    if expires_in > 0
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise PolarProviderError from error

    async def register_user(self, token: str, member_id: str) -> str:
        try:
            response = await self._client.post(
                f"{self._API_URL}/users",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                json={"member-id": member_id},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        if response.status_code == 409:
            return ""
        self._check(response)
        try:
            return str(response.json()["polar-user-id"])
        except (KeyError, TypeError, ValueError) as error:
            raise PolarProviderError from error

    async def list_exercises(self, token: str) -> tuple[JsonObject, ...]:
        try:
            response = await self._client.get(
                f"{self._API_URL}/exercises",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"samples": "false", "zones": "false", "route": "false"},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        self._check(response)
        body = response.json()
        if not isinstance(body, list):
            raise PolarProviderError
        return tuple(dict(item) for item in body if isinstance(item, dict))

    async def get_exercise(self, token: str, exercise_id: str) -> JsonObject:
        try:
            response = await self._client.get(
                f"{self._API_URL}/exercises/{exercise_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        self._check(response)
        body = response.json()
        if not isinstance(body, dict):
            raise PolarProviderError
        return dict(body)

    async def get_fit(self, token: str, exercise_id: str) -> bytes | None:
        try:
            response = await self._client.get(
                f"{self._API_URL}/exercises/{exercise_id}/fit",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/octet-stream",
                },
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        if response.status_code in {204, 404}:
            return None
        self._check(response)
        if len(response.content) > self._max_file_bytes:
            raise PolarProviderError
        return bytes(response.content)

    async def revoke(self, token: str, provider_user_id: str) -> None:
        try:
            response = await self._client.delete(
                f"{self._API_URL}/users/{provider_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PolarProviderError from error
        if response.status_code not in {204, 404}:
            self._check(response)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
