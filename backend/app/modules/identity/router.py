"""Authenticated identity HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_authenticated_athlete
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedAthlete
from app.modules.identity.schemas import MeResponse
from app.modules.identity.service import build_me_response

router = APIRouter(tags=["identity"])


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Return the authenticated user identity",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing or invalid bearer token",
        }
    },
)
def get_me(
    identity: Annotated[AuthenticatedAthlete, Depends(get_authenticated_athlete)],
) -> MeResponse:
    """Return identity derived only from the verified bearer token."""
    return build_me_response(identity)
