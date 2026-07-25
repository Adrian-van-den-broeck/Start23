"""Supabase authentication and current-user endpoint tests."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt import PyJWK, PyJWKClient
from jwt.algorithms import ECAlgorithm

from app.core.config import Settings
from app.core.security import SupabaseAccessTokenVerifier
from app.main import create_app

_KEY_ID = "test-signing-key"


class StaticJWKClient(PyJWKClient):
    """Return one in-memory signing key without a network request."""

    def __init__(self, signing_key: PyJWK) -> None:
        self._signing_key = signing_key

    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        """Return the configured key for deterministic verifier tests."""
        return self._signing_key


@dataclass(frozen=True, slots=True)
class AuthenticationTestContext:
    """Objects required to create and verify local test tokens."""

    client: TestClient
    settings: Settings
    private_key: ec.EllipticCurvePrivateKey
    user_id: UUID


def _to_pyjwk(
    public_key: ec.EllipticCurvePublicKey,
) -> PyJWK:
    jwk_data = ECAlgorithm.to_jwk(public_key, as_dict=True)
    if not isinstance(jwk_data, dict):
        raise TypeError("Expected an EC JWK dictionary")

    jwk_data.update(
        {
            "alg": "ES256",
            "kid": _KEY_ID,
            "use": "sig",
        }
    )
    return PyJWK.from_dict(jwk_data)


@pytest.fixture
def auth_context() -> Iterator[AuthenticationTestContext]:
    """Create an application using a local ES256 verification key."""
    settings = Settings(
        environment="test",
        supabase_url="https://test-project.supabase.co",
    )
    private_key = ec.generate_private_key(ec.SECP256R1())
    verifier = SupabaseAccessTokenVerifier(
        settings,
        jwks_client=StaticJWKClient(_to_pyjwk(private_key.public_key())),
    )
    user_id = uuid4()

    with TestClient(
        create_app(settings, access_token_verifier=verifier)
    ) as test_client:
        yield AuthenticationTestContext(
            client=test_client,
            settings=settings,
            private_key=private_key,
            user_id=user_id,
        )


def _create_token(
    context: AuthenticationTestContext,
    *,
    expires_in: timedelta = timedelta(minutes=15),
    private_key: ec.EllipticCurvePrivateKey | None = None,
    role: str = "authenticated",
) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "aud": context.settings.supabase_jwt_audience,
        "exp": now + expires_in,
        "iat": now,
        "iss": context.settings.supabase_jwt_issuer,
        "role": role,
        "sub": str(context.user_id),
    }
    return jwt.encode(
        claims,
        private_key or context.private_key,
        algorithm="ES256",
        headers={"kid": _KEY_ID, "typ": "JWT"},
    )


def test_missing_token_is_rejected(
    auth_context: AuthenticationTestContext,
) -> None:
    """The current-user endpoint requires a bearer token."""
    response = auth_context.client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {
            "code": "authentication_required",
            "message": "Invalid authentication credentials",
            "details": None,
            "request_id": response.headers["x-request-id"],
        }
    }


def test_malformed_token_is_rejected(
    auth_context: AuthenticationTestContext,
) -> None:
    """A publishable key or arbitrary string is not a user access token."""
    response = auth_context.client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer sb_publishable_not-a-user-jwt"},
    )

    assert response.status_code == 401


def test_expired_token_is_rejected(
    auth_context: AuthenticationTestContext,
) -> None:
    """A correctly signed but expired access token is not accepted."""
    token = _create_token(auth_context, expires_in=timedelta(seconds=-1))

    response = auth_context.client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_invalid_signature_is_rejected(
    auth_context: AuthenticationTestContext,
) -> None:
    """A token signed by an unknown private key is not accepted."""
    token = _create_token(
        auth_context,
        private_key=ec.generate_private_key(ec.SECP256R1()),
    )

    response = auth_context.client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_non_authenticated_role_is_rejected(
    auth_context: AuthenticationTestContext,
) -> None:
    """Service-role and anonymous-role tokens cannot identify a mobile user."""
    token = _create_token(auth_context, role="service_role")

    response = auth_context.client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_valid_token_returns_verified_identity(
    auth_context: AuthenticationTestContext,
) -> None:
    """A valid access token returns its verified subject."""
    token = _create_token(auth_context)

    response = auth_context.client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(auth_context.user_id),
        "role": "authenticated",
    }


def test_request_input_cannot_override_verified_identity(
    auth_context: AuthenticationTestContext,
) -> None:
    """Query, header, and body user IDs never override the token subject."""
    token = _create_token(auth_context)
    attacker_id = uuid4()

    response = auth_context.client.request(
        "GET",
        "/api/v1/me",
        params={"user_id": str(attacker_id)},
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-Id": str(attacker_id),
        },
        json={"user_id": str(attacker_id)},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(auth_context.user_id)
    assert response.json()["id"] != str(attacker_id)
