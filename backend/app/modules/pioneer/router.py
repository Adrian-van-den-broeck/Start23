"""Authenticated Pioneer beta access routes."""

from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import get_access_token, get_authenticated_athlete
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedAthlete

from .repository import (
    PioneerRepository,
    PioneerRepositoryError,
    PioneerRepositoryUnavailableError,
)
from .schemas import PioneerRedemptionRequest, PioneerRedemptionResponse
from .service import PioneerDomainError, PioneerService

router = APIRouter(prefix="/pioneer-access", tags=["pioneer-access"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_pioneer_repository(request: Request) -> PioneerRepository:
    repository: PioneerRepository = request.app.state.pioneer_repository
    return repository


def get_pioneer_service(
    repository: Annotated[PioneerRepository, Depends(get_pioneer_repository)],
) -> PioneerService:
    return PioneerService(repository)


def _raise_public_error(error: Exception) -> NoReturn:
    if isinstance(error, PioneerDomainError):
        if error.code == "pioneer_rate_limited":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif error.code in {"pioneer_code_reused", "pioneer_idempotency_conflict"}:
            status_code = status.HTTP_409_CONFLICT
        elif error.code.startswith("pioneer_code_"):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(
            status_code=status_code,
            detail={"code": error.code, "message": str(error)},
        ) from error
    if isinstance(error, (PioneerRepositoryUnavailableError, PioneerRepositoryError)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pioneer access is temporarily unavailable.",
        ) from error
    raise error


@router.get(
    "/redemption",
    response_model=PioneerRedemptionResponse | None,
    responses=error_responses,
)
async def get_pioneer_redemption(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedAthlete, Depends(get_authenticated_athlete)],
    service: Annotated[PioneerService, Depends(get_pioneer_service)],
) -> PioneerRedemptionResponse | None:
    """Return only the authenticated athlete's current enrollment."""
    try:
        return await service.current(access_token)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/redemptions",
    response_model=PioneerRedemptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def redeem_pioneer_access(
    redemption: PioneerRedemptionRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    athlete: Annotated[AuthenticatedAthlete, Depends(get_authenticated_athlete)],
    service: Annotated[PioneerService, Depends(get_pioneer_service)],
) -> PioneerRedemptionResponse:
    """Redeem one code against token-derived opaque athlete ownership."""
    try:
        return await service.redeem(
            athlete.athlete_id,
            idempotency_key,
            redemption,
        )
    except Exception as error:
        _raise_public_error(error)
