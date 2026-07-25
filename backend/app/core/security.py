"""Supabase access-token verification and authenticated identity types."""

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError

from app.core.config import Settings


class InvalidAccessTokenError(Exception):
    """Raised when a Supabase access token cannot be trusted."""


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Identity derived from verified Supabase access-token claims."""

    user_id: UUID
    role: Literal["authenticated"]


class AccessTokenVerifier(Protocol):
    """Interface used by authentication dependencies and tests."""

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        """Verify an access token and return its trusted identity."""


class SupabaseAccessTokenVerifier:
    """Verify Supabase user access tokens against the project's public JWKS."""

    def __init__(
        self,
        settings: Settings,
        jwks_client: PyJWKClient | None = None,
    ) -> None:
        self._settings = settings
        self._jwks_client = jwks_client or PyJWKClient(
            settings.supabase_jwks_url,
            cache_keys=False,
            cache_jwk_set=True,
            lifespan=settings.supabase_jwks_cache_seconds,
            timeout=settings.supabase_jwks_timeout_seconds,
        )

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        """Validate signature and required claims, then return token identity."""
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(access_token)
            claims = jwt.decode(
                access_token,
                signing_key,
                algorithms=[self._settings.supabase_jwt_algorithm],
                audience=self._settings.supabase_jwt_audience,
                issuer=self._settings.supabase_jwt_issuer,
                options={
                    "require": ["aud", "exp", "iat", "iss", "role", "sub"],
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                },
            )

            if claims["role"] != "authenticated":
                raise InvalidAccessTokenError

            user_id = UUID(str(claims["sub"]))
        except InvalidAccessTokenError:
            raise
        except (KeyError, PyJWKClientError, PyJWTError, TypeError, ValueError):
            raise InvalidAccessTokenError from None

        return AuthenticatedIdentity(
            user_id=user_id,
            role="authenticated",
        )
