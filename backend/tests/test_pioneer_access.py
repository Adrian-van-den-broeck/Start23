"""Phase 16 Pioneer access-code API and transport regressions."""

import asyncio
from collections.abc import Iterator
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.pioneer.repository import SupabasePioneerRepository

_NOW = datetime(2026, 9, 23, 8, tzinfo=timezone.utc)


class PioneerTokenVerifier:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            owner = self._owners[access_token]
        except KeyError as error:
            raise InvalidAccessTokenError from error
        return AuthenticatedIdentity(
            user_id=owner,
            athlete_id=owner,
            role="authenticated",
        )


class MemoryPioneerRepository:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners
        athlete_a = owners["athlete-a"]
        self._codes = {
            self._digest("VALID-CODE"): ("valid", None),
            self._digest("EXPIRED1"): ("expired", None),
            self._digest("REVOKED1"): ("revoked", None),
            self._digest("BOUND-A1"): ("valid", athlete_a),
        }
        self._used_codes: set[str] = set()
        self._attempts: dict[tuple[UUID, UUID], tuple[str, dict[str, Any]]] = {}
        self._redemptions: dict[UUID, dict[str, Any]] = {}

    @staticmethod
    def _digest(code: str) -> str:
        return sha256(code.encode("ascii")).hexdigest()

    async def redeem(
        self,
        athlete_id: UUID,
        code_digest: str,
        idempotency_key: UUID,
        request_fingerprint: str,
    ) -> dict[str, Any]:
        attempt_key = (athlete_id, idempotency_key)
        previous = self._attempts.get(attempt_key)
        if previous is not None:
            fingerprint, previous_result = previous
            if fingerprint != request_fingerprint:
                return {"status": "idempotency_conflict"}
            return previous_result

        code = self._codes.get(code_digest)
        result: dict[str, Any]
        if code is None:
            result = {"status": "invalid"}
        elif code[0] != "valid":
            result = {"status": code[0]}
        elif code[1] is not None and code[1] != athlete_id:
            result = {"status": "unauthorized"}
        elif code_digest in self._used_codes or athlete_id in self._redemptions:
            result = {"status": "reused"}
        else:
            redemption = {
                "id": str(uuid4()),
                "program": "pioneer",
                "status": "active",
                "redeemed_at": _NOW.isoformat(),
            }
            self._used_codes.add(code_digest)
            self._redemptions[athlete_id] = redemption
            result = {"status": "success", "redemption": redemption}
        self._attempts[attempt_key] = (request_fingerprint, result)
        return result

    async def fetch_current(self, access_token: str) -> dict[str, Any] | None:
        redemption = self._redemptions.get(self._owners[access_token])
        return dict(redemption) if redemption else None

    async def aclose(self) -> None:
        return None


@pytest.fixture
def pioneer_client() -> Iterator[tuple[TestClient, dict[str, UUID]]]:
    owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
    repository = MemoryPioneerRepository(owners)
    with TestClient(
        create_app(
            Settings(environment="test"),
            access_token_verifier=PioneerTokenVerifier(owners),
            pioneer_repository=repository,
        )
    ) as client:
        yield client, owners


def _headers(token: str = "athlete-a", key: UUID | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(key or uuid4()),
    }


@pytest.mark.parametrize(
    ("code", "error_code"),
    [
        ("UNKNOWN1", "pioneer_code_invalid"),
        ("EXPIRED1", "pioneer_code_expired"),
        ("REVOKED1", "pioneer_code_revoked"),
    ],
)
def test_invalid_expired_and_revoked_codes_fail(
    pioneer_client: tuple[TestClient, dict[str, UUID]],
    code: str,
    error_code: str,
) -> None:
    client, _ = pioneer_client
    response = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(),
        json={"code": code},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == error_code
    assert code not in response.text


def test_valid_code_succeeds_and_exact_retry_is_idempotent(
    pioneer_client: tuple[TestClient, dict[str, UUID]],
) -> None:
    client, _ = pioneer_client
    key = uuid4()
    first = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(key=key),
        json={"code": " valid-code "},
    )
    replay = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(key=key),
        json={"code": "VALID-CODE"},
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert set(first.json()) == {"program", "status", "redeemed_at"}
    assert "code" not in first.text.lower()
    assert "athlete" not in first.text.lower()


def test_code_reuse_and_idempotency_key_reuse_are_rejected(
    pioneer_client: tuple[TestClient, dict[str, UUID]],
) -> None:
    client, _ = pioneer_client
    key = uuid4()
    assert (
        client.post(
            "/api/v1/pioneer-access/redemptions",
            headers=_headers(key=key),
            json={"code": "VALID-CODE"},
        ).status_code
        == 201
    )

    reused = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(key=uuid4()),
        json={"code": "VALID-CODE"},
    )
    key_conflict = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(key=key),
        json={"code": "EXPIRED1"},
    )

    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "pioneer_code_reused"
    assert key_conflict.status_code == 409
    assert key_conflict.json()["error"]["code"] == "pioneer_idempotency_conflict"


def test_bound_code_and_cross_user_redemption_are_isolated(
    pioneer_client: tuple[TestClient, dict[str, UUID]],
) -> None:
    client, _ = pioneer_client
    unauthorized = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers("athlete-b"),
        json={"code": "BOUND-A1"},
    )
    accepted = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers("athlete-a"),
        json={"code": "BOUND-A1"},
    )
    other_view = client.get(
        "/api/v1/pioneer-access/redemption",
        headers={"Authorization": "Bearer athlete-b"},
    )

    assert unauthorized.status_code == 403
    assert unauthorized.json()["error"]["code"] == "pioneer_code_unauthorized"
    assert accepted.status_code == 201
    assert other_view.status_code == 200
    assert other_view.json() is None


def test_malformed_and_unauthenticated_redemptions_fail(
    pioneer_client: tuple[TestClient, dict[str, UUID]],
) -> None:
    client, _ = pioneer_client
    malformed = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers=_headers(),
        json={"code": "bad!"},
    )
    unauthenticated = client.post(
        "/api/v1/pioneer-access/redemptions",
        headers={"Idempotency-Key": str(uuid4())},
        json={"code": "VALID-CODE"},
    )

    assert malformed.status_code == 422
    assert unauthenticated.status_code == 401


def test_supabase_repository_uses_secret_only_for_redeem_and_user_rls_for_read() -> (
    None
):
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/rpc/redeem_pioneer_access_code"):
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "redemption": {
                        "id": str(uuid4()),
                        "program": "pioneer",
                        "status": "active",
                        "redeemed_at": _NOW.isoformat(),
                    },
                },
            )
        return httpx.Response(
            200,
            json=[
                {
                    "program": "pioneer",
                    "status": "active",
                    "redeemed_at": _NOW.isoformat(),
                }
            ],
        )

    async def exercise() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        repository = SupabasePioneerRepository(
            Settings(
                environment="test",
                supabase_publishable_key="publishable-test-key",
                supabase_secret_key="secret-test-key",
            ),
            client=client,
        )
        athlete_id = uuid4()
        await repository.redeem(
            athlete_id,
            "a" * 64,
            uuid4(),
            "b" * 64,
        )
        await repository.fetch_current("athlete-access-token")
        await client.aclose()

    asyncio.run(exercise())

    assert requests[0].headers["apikey"] == "secret-test-key"
    assert "authorization" not in requests[0].headers
    assert requests[1].headers["apikey"] == "publishable-test-key"
    assert requests[1].headers["authorization"] == "Bearer athlete-access-token"
    assert requests[1].url.params["select"] == "program,status,redeemed_at"
