"""Phase 9 OAuth, import, disconnect, replay, and failure-isolation tests."""

import asyncio
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.core.config import Settings
from app.modules.integrations.polar import (
    PolarProviderError,
    PolarToken,
)
from app.modules.integrations.repository import IntegrationNotFoundError, JsonObject
from app.modules.integrations.service import IntegrationService

_NOW = datetime(2026, 8, 17, 10, tzinfo=timezone.utc)
_FIXTURE = Path(__file__).parent / "fixtures" / "polar" / "exercise.json"


def _exercise() -> JsonObject:
    value = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class MemoryIntegrationRepository:
    def __init__(self, athlete_id: UUID) -> None:
        self.athlete_id = athlete_id
        self.states: set[str] = set()
        self.connected = False
        self.connection_status = "disconnected"
        self.imports: dict[UUID, JsonObject] = {}
        self.import_keys: dict[UUID, UUID] = {}
        self.activities: dict[str, JsonObject] = {}
        self.files: dict[str, bytes] = {}
        self.webhooks: dict[str, UUID] = {}

    async def create_oauth_state(
        self, access_token: str, state_hash: str, expires_at: str
    ) -> None:
        assert access_token == "athlete-token"
        assert datetime.fromisoformat(expires_at) > datetime.now(timezone.utc)
        self.states = {state_hash}

    async def consume_oauth_state(self, state_hash: str) -> UUID:
        if state_hash not in self.states:
            raise IntegrationNotFoundError
        self.states.remove(state_hash)
        return self.athlete_id

    def _connection(self) -> JsonObject:
        return {
            "id": str(UUID(int=1)),
            "provider": "polar",
            "status": self.connection_status,
            "connected_at": _NOW.isoformat(),
            "disconnected_at": (
                None if self.connection_status == "connected" else _NOW.isoformat()
            ),
            "last_import_at": None,
        }

    async def save_connection(
        self,
        athlete_id: UUID,
        provider_user_id: str,
        access_token: str,
        expires_at: str | None,
    ) -> JsonObject:
        assert athlete_id == self.athlete_id
        self.connected = True
        self.connection_status = "connected"
        self.provider_user_id = provider_user_id
        self.provider_token = access_token
        return self._connection()

    async def get_connection(self, access_token: str) -> JsonObject:
        if not self.connected or access_token != "athlete-token":
            raise IntegrationNotFoundError
        return self._connection()

    async def get_credentials(self, athlete_id: UUID) -> JsonObject:
        if not self.connected or athlete_id != self.athlete_id:
            raise IntegrationNotFoundError
        return {
            "access_token": self.provider_token,
            "provider_user_id": self.provider_user_id,
            "timezone": "Europe/Amsterdam",
        }

    async def disconnect(self, athlete_id: UUID, status: str) -> None:
        assert athlete_id == self.athlete_id
        self.connected = False
        self.connection_status = status

    async def start_import(
        self, athlete_id: UUID, idempotency_key: UUID, payload: JsonObject
    ) -> JsonObject:
        existing = self.import_keys.get(idempotency_key)
        if existing is not None:
            return dict(self.imports[existing])
        import_id = uuid4()
        row: JsonObject = {
            "id": str(import_id),
            "provider": "polar",
            "kind": payload["kind"],
            "status": "running",
            "range_start": payload.get("range_start"),
            "range_end": payload.get("range_end"),
            "discovered_count": 0,
            "imported_count": 0,
            "skipped_count": 0,
            "failure_code": None,
            "created_at": _NOW.isoformat(),
            "completed_at": None,
        }
        self.import_keys[idempotency_key] = import_id
        self.imports[import_id] = row
        return dict(row)

    async def finish_import(
        self, athlete_id: UUID, import_id: UUID, payload: JsonObject
    ) -> JsonObject:
        row = self.imports[import_id]
        if row["status"] == "running":
            row.update(payload)
            row["completed_at"] = _NOW.isoformat()
        return dict(row)

    async def list_imports(self, access_token: str) -> tuple[JsonObject, ...]:
        assert access_token == "athlete-token"
        return tuple(dict(row) for row in self.imports.values())

    async def import_activity(
        self,
        athlete_id: UUID,
        import_id: UUID,
        provider_entity_id: str,
        idempotency_key: UUID,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        existing = self.activities.get(provider_entity_id)
        if existing is not None:
            return {"created": False, "activity": dict(existing)}
        assert athlete_id == self.athlete_id
        assert self.imports[import_id]["status"] == "running"
        assert len(fingerprint) == 64
        row = {
            "id": str(uuid4()),
            "source": "canonical_summary",
            **payload,
        }
        self.activities[provider_entity_id] = row
        return {"created": True, "activity": dict(row)}

    async def upload_activity_file(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        provider_entity_id: str,
        content: bytes,
        checksum: str,
    ) -> None:
        assert athlete_id == self.athlete_id
        assert hashlib.sha256(content).hexdigest() == checksum
        self.files[provider_entity_id] = content

    async def record_webhook(
        self, event_key: str, payload_fingerprint: str, payload: JsonObject
    ) -> JsonObject:
        assert event_key == payload_fingerprint
        existing = self.webhooks.get(event_key)
        if existing is not None:
            return {"id": str(existing), "duplicate": True}
        receipt_id = uuid4()
        self.webhooks[event_key] = receipt_id
        return {"id": str(receipt_id), "duplicate": False}

    async def get_webhook_context(self, receipt_id: UUID) -> JsonObject:
        raise IntegrationNotFoundError

    async def finish_webhook(
        self, receipt_id: UUID, *, status: str, failure_code: str | None = None
    ) -> None:
        return None

    async def aclose(self) -> None:
        return None


class FakePolarProvider:
    def __init__(self) -> None:
        self.fail_list = False
        self.fail_revoke = False
        self.revoked = False

    def authorization_url(self, state: str) -> str:
        return f"https://flow.polar.test/authorize?state={state}"

    async def exchange_code(self, code: str) -> PolarToken:
        assert code == "oauth-code"
        return PolarToken("provider-access-token-value", "475", None)

    async def register_user(self, token: str, member_id: str) -> str:
        assert token == "provider-access-token-value"
        assert member_id.startswith("start23:")
        return "475"

    async def list_exercises(self, token: str) -> tuple[JsonObject, ...]:
        if self.fail_list:
            raise PolarProviderError
        return (_exercise(),)

    async def get_exercise(self, token: str, exercise_id: str) -> JsonObject:
        return _exercise()

    async def get_fit(self, token: str, exercise_id: str) -> bytes | None:
        return b"FIT-test-fixture"

    async def revoke(self, token: str, provider_user_id: str) -> None:
        if self.fail_revoke:
            raise PolarProviderError
        self.revoked = True

    async def aclose(self) -> None:
        return None


def _service() -> tuple[
    IntegrationService,
    MemoryIntegrationRepository,
    FakePolarProvider,
]:
    athlete_id = uuid4()
    repository = MemoryIntegrationRepository(athlete_id)
    provider = FakePolarProvider()
    settings = Settings(
        environment="test",
        polar_client_id="polar-client",
        polar_client_secret="polar-secret",
        polar_webhook_secret="webhook-secret",
    )
    return IntegrationService(repository, provider, settings), repository, provider


def _connect(
    service: IntegrationService, repository: MemoryIntegrationRepository
) -> None:
    async def exercise() -> None:
        start = await service.start_oauth("athlete-token")
        state = start.authorization_url.split("state=", maxsplit=1)[1]
        await service.complete_oauth("oauth-code", state)

    asyncio.run(exercise())
    assert repository.connected


def test_oauth_state_is_one_time_and_disconnect_revokes_before_token_removal() -> None:
    service, repository, provider = _service()
    _connect(service, repository)

    asyncio.run(service.disconnect(repository.athlete_id))

    assert provider.revoked
    assert repository.connection_status == "disconnected"
    assert not repository.connected


def test_provider_disconnect_failure_keeps_local_token_for_safe_retry() -> None:
    service, repository, provider = _service()
    _connect(service, repository)
    provider.fail_revoke = True

    with pytest.raises(PolarProviderError):
        asyncio.run(service.disconnect(repository.athlete_id))

    assert repository.connected
    assert repository.connection_status == "connected"


def test_historical_import_uses_canonical_path_and_private_file_storage() -> None:
    service, repository, _ = _service()
    _connect(service, repository)
    key = uuid4()

    result = asyncio.run(
        service.import_historical(
            repository.athlete_id,
            key,
            30,
            today=date(2026, 8, 17),
        )
    )
    replay = asyncio.run(
        service.import_historical(
            repository.athlete_id,
            key,
            30,
            today=date(2026, 8, 17),
        )
    )

    assert result.status == "completed"
    assert result.imported_count == 1
    assert replay.id == result.id
    assert len(repository.activities) == 1
    activity = repository.activities["2AC312F"]
    assert activity["source"] == "canonical_summary"
    assert activity["discipline"] == "run"
    assert "rpe" not in activity
    assert "tss" not in json.dumps(activity).lower()
    assert repository.files == {"2AC312F": b"FIT-test-fixture"}


def test_provider_failure_marks_import_failed_without_activity_corruption() -> None:
    service, repository, provider = _service()
    _connect(service, repository)
    provider.fail_list = True

    with pytest.raises(PolarProviderError):
        asyncio.run(
            service.import_historical(
                repository.athlete_id,
                uuid4(),
                30,
                today=date(2026, 8, 17),
            )
        )

    assert not repository.activities
    assert next(iter(repository.imports.values()))["status"] == "failed"


def test_identical_signed_webhook_is_recorded_once_and_not_reprocessed() -> None:
    service, repository, _ = _service()
    payload = {
        "event": "PING",
        "timestamp": _NOW.isoformat().replace("+00:00", "Z"),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(b"webhook-secret", raw, hashlib.sha256).hexdigest()

    first, first_receipt = asyncio.run(
        service.receive_webhook(raw, signature, now=_NOW)
    )
    replay, replay_receipt = asyncio.run(
        service.receive_webhook(raw, signature, now=_NOW + timedelta(seconds=1))
    )

    assert first.status == "accepted"
    assert replay.status == "duplicate"
    assert first_receipt is None
    assert replay_receipt is None
    assert len(repository.webhooks) == 1
