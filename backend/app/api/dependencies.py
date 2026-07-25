"""Shared FastAPI dependencies."""

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings
from app.core.security import (
    AccessTokenVerifier,
    AuthenticatedIdentity,
    InvalidAccessTokenError,
)

_bearer_scheme = HTTPBearer(auto_error=False)
_authentication_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_app_settings(request: Request) -> Settings:
    """Return the settings attached to the current application."""
    return cast(Settings, request.app.state.settings)


def get_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(_bearer_scheme),
    ],
) -> str:
    """Extract a non-empty bearer token without logging its value."""
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise _authentication_error
    return credentials.credentials


def get_access_token_verifier(request: Request) -> AccessTokenVerifier:
    """Return the process-wide Supabase access-token verifier."""
    return cast(AccessTokenVerifier, request.app.state.access_token_verifier)


def get_authenticated_identity(
    access_token: Annotated[str, Depends(get_access_token)],
    verifier: Annotated[AccessTokenVerifier, Depends(get_access_token_verifier)],
) -> AuthenticatedIdentity:
    """Return the identity derived exclusively from a verified access token."""
    try:
        return verifier.verify(access_token)
    except InvalidAccessTokenError:
        raise _authentication_error from None
