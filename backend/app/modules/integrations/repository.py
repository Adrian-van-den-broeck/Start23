"""Supabase persistence and private Storage adapter for wearable imports."""

from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class IntegrationRepositoryError(Exception):
    """Persistence failure hidden behind a stable integration error."""


class IntegrationNotFoundError(IntegrationRepositoryError):
    """The owner connection or import resource does not exist."""


class IntegrationConflictError(IntegrationRepositoryError):
    """One-time state or provider ownership conflicts with stored state."""


class IntegrationRepository(Protocol):
    async def create_oauth_state(
        self, access_token: str, state_hash: str, expires_at: str
    ) -> None: ...
    async def consume_oauth_state(self, state_hash: str) -> UUID: ...
    async def save_connection(
        self,
        athlete_id: UUID,
        provider_user_id: str,
        access_token: str,
        expires_at: str | None,
    ) -> JsonObject: ...
    async def get_connection(self, access_token: str) -> JsonObject: ...
    async def get_credentials(self, athlete_id: UUID) -> JsonObject: ...
    async def disconnect(self, athlete_id: UUID, status: str) -> None: ...
    async def start_import(
        self, athlete_id: UUID, idempotency_key: UUID, payload: JsonObject
    ) -> JsonObject: ...
    async def finish_import(
        self, athlete_id: UUID, import_id: UUID, payload: JsonObject
    ) -> JsonObject: ...
    async def list_imports(self, access_token: str) -> tuple[JsonObject, ...]: ...
    async def import_activity(
        self,
        athlete_id: UUID,
        import_id: UUID,
        provider_entity_id: str,
        idempotency_key: UUID,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject: ...
    async def upload_activity_file(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        provider_entity_id: str,
        content: bytes,
        checksum: str,
    ) -> None: ...
    async def record_webhook(
        self, event_key: str, payload_fingerprint: str, payload: JsonObject
    ) -> JsonObject: ...
    async def get_webhook_context(self, receipt_id: UUID) -> JsonObject: ...
    async def finish_webhook(
        self, receipt_id: UUID, *, status: str, failure_code: str | None = None
    ) -> None: ...
    async def aclose(self) -> None: ...


class SupabaseIntegrationRepository:
    """Use caller RLS for reads and bounded secret-only integration RPCs."""

    _BUCKET = "activity-files"

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        root = str(settings.supabase_url).rstrip("/")
        self._rest_url = f"{root}/rest/v1"
        self._storage_url = f"{root}/storage/v1/object"
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

    async def _rpc(
        self,
        name: str,
        payload: JsonObject,
        *,
        access_token: str = "",
        service: bool = False,
    ) -> Any:
        try:
            response = await self._client.post(
                f"{self._rest_url}/rpc/{name}",
                headers=self._headers(access_token, service=service),
                json=payload,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise IntegrationRepositoryError from error
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
            raise IntegrationNotFoundError
        if response.status_code in {400, 409, 422} or code in {
            "23505",
            "23514",
            "40001",
            "P0001",
        }:
            raise IntegrationConflictError(message)
        raise IntegrationRepositoryError

    async def create_oauth_state(
        self, access_token: str, state_hash: str, expires_at: str
    ) -> None:
        await self._rpc(
            "start_polar_oauth",
            {"p_state_hash": state_hash, "p_expires_at": expires_at},
            access_token=access_token,
        )

    async def consume_oauth_state(self, state_hash: str) -> UUID:
        result = await self._rpc(
            "consume_polar_oauth_state",
            {"p_state_hash": state_hash},
            service=True,
        )
        try:
            return UUID(str(result))
        except (TypeError, ValueError) as error:
            raise IntegrationRepositoryError from error

    async def save_connection(
        self,
        athlete_id: UUID,
        provider_user_id: str,
        access_token: str,
        expires_at: str | None,
    ) -> JsonObject:
        result = await self._rpc(
            "save_polar_connection",
            {
                "p_athlete_id": str(athlete_id),
                "p_provider_user_id": provider_user_id,
                "p_access_token": access_token,
                "p_token_expires_at": expires_at,
            },
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationRepositoryError
        return dict(result)

    async def get_connection(self, access_token: str) -> JsonObject:
        result = await self._rpc("get_polar_connection", {}, access_token=access_token)
        if not isinstance(result, dict):
            raise IntegrationNotFoundError
        return dict(result)

    async def get_credentials(self, athlete_id: UUID) -> JsonObject:
        result = await self._rpc(
            "get_polar_credentials",
            {"p_athlete_id": str(athlete_id)},
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationNotFoundError
        return dict(result)

    async def disconnect(self, athlete_id: UUID, status: str) -> None:
        await self._rpc(
            "disconnect_polar_connection",
            {"p_athlete_id": str(athlete_id), "p_status": status},
            service=True,
        )

    async def start_import(
        self, athlete_id: UUID, idempotency_key: UUID, payload: JsonObject
    ) -> JsonObject:
        result = await self._rpc(
            "start_polar_import",
            {
                "p_athlete_id": str(athlete_id),
                "p_idempotency_key": str(idempotency_key),
                "p_payload": payload,
            },
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationRepositoryError
        return dict(result)

    async def finish_import(
        self, athlete_id: UUID, import_id: UUID, payload: JsonObject
    ) -> JsonObject:
        result = await self._rpc(
            "finish_polar_import",
            {
                "p_athlete_id": str(athlete_id),
                "p_import_id": str(import_id),
                "p_payload": payload,
            },
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationRepositoryError
        return dict(result)

    async def list_imports(self, access_token: str) -> tuple[JsonObject, ...]:
        result = await self._rpc("list_polar_imports", {}, access_token=access_token)
        if not isinstance(result, list):
            raise IntegrationRepositoryError
        return tuple(dict(row) for row in result if isinstance(row, dict))

    async def import_activity(
        self,
        athlete_id: UUID,
        import_id: UUID,
        provider_entity_id: str,
        idempotency_key: UUID,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._rpc(
            "import_polar_activity",
            {
                "p_athlete_id": str(athlete_id),
                "p_import_id": str(import_id),
                "p_provider_entity_id": provider_entity_id,
                "p_idempotency_key": str(idempotency_key),
                "p_request_fingerprint": fingerprint,
                "p_payload": payload,
            },
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationRepositoryError
        return dict(result)

    async def upload_activity_file(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        provider_entity_id: str,
        content: bytes,
        checksum: str,
    ) -> None:
        object_name = f"{athlete_id}/{activity_id}/{provider_entity_id}.fit"
        headers = {
            "apikey": self._secret_key,
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/octet-stream",
            "x-upsert": "false",
        }
        try:
            response = await self._client.post(
                f"{self._storage_url}/{self._BUCKET}/{object_name}",
                headers=headers,
                content=content,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise IntegrationRepositoryError from error
        if response.status_code not in {200, 201, 409}:
            raise IntegrationRepositoryError
        await self._rpc(
            "save_polar_activity_file",
            {
                "p_athlete_id": str(athlete_id),
                "p_activity_id": str(activity_id),
                "p_object_name": object_name,
                "p_checksum": checksum,
                "p_size_bytes": len(content),
            },
            service=True,
        )

    async def record_webhook(
        self, event_key: str, payload_fingerprint: str, payload: JsonObject
    ) -> JsonObject:
        result = await self._rpc(
            "record_polar_webhook",
            {
                "p_event_key": event_key,
                "p_payload_fingerprint": payload_fingerprint,
                "p_payload": payload,
            },
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationRepositoryError
        return dict(result)

    async def get_webhook_context(self, receipt_id: UUID) -> JsonObject:
        result = await self._rpc(
            "get_polar_webhook_context",
            {"p_receipt_id": str(receipt_id)},
            service=True,
        )
        if not isinstance(result, dict):
            raise IntegrationNotFoundError
        return dict(result)

    async def finish_webhook(
        self, receipt_id: UUID, *, status: str, failure_code: str | None = None
    ) -> None:
        await self._rpc(
            "finish_polar_webhook",
            {
                "p_receipt_id": str(receipt_id),
                "p_status": status,
                "p_failure_code": failure_code,
            },
            service=True,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
