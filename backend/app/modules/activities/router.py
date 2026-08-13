"""Authenticated canonical activity and RPE routes."""

from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import get_access_token, get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity

from .repository import (
    ActivityRepository,
    ActivityRepositoryConflictError,
    ActivityRepositoryError,
    ActivityRepositoryNotFoundError,
    ActivityRepositoryUnavailableError,
)
from .schemas import ActivityResponse, ActivityRpeSubmission, ActivitySummaryInput
from .service import ActivityDomainError, ActivityService

router = APIRouter(tags=["activities"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_activity_repository(request: Request) -> ActivityRepository:
    repository: ActivityRepository = request.app.state.activity_repository
    return repository


def get_activity_service(
    repository: Annotated[ActivityRepository, Depends(get_activity_repository)],
) -> ActivityService:
    return ActivityService(repository)


def _raise_public_error(error: Exception) -> NoReturn:
    if isinstance(error, ActivityRepositoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested activity resource was not found.",
        ) from error
    if isinstance(error, ActivityRepositoryConflictError):
        messages = {
            "idempotency_key_reused": (
                "This idempotency key was already used for another activity."
            ),
            "activity_rpe_immutable": "RPE was already submitted for this activity.",
            "activity_rpe_window_closed": (
                "RPE can be corrected only during the current local training week."
            ),
            "planned_workout_already_matched": (
                "This planned workout already has a completed activity."
            ),
            "activity_state_conflict": (
                "The activity state changed. Refresh and try again."
            ),
        }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error.code, "message": messages[error.code]},
        ) from error
    if isinstance(error, ActivityRepositoryUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Activity persistence is temporarily unavailable.",
        ) from error
    if isinstance(error, (ActivityDomainError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, ActivityRepositoryError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Activity persistence is temporarily unavailable.",
        ) from error
    raise error


@router.post(
    "/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def create_activity(
    summary: ActivitySummaryInput,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> ActivityResponse:
    """Create or replay one validated canonical activity summary."""
    try:
        return await service.create(access_token, idempotency_key, summary)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/activities",
    response_model=tuple[ActivityResponse, ...],
    responses=error_responses,
)
async def list_activities(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> tuple[ActivityResponse, ...]:
    try:
        return await service.list(access_token)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/activities/pending-rpe",
    response_model=tuple[ActivityResponse, ...],
    responses=error_responses,
)
async def list_pending_rpe(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> tuple[ActivityResponse, ...]:
    try:
        return await service.list(access_token, pending_rpe=True)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityResponse,
    responses=error_responses,
)
async def get_activity(
    activity_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> ActivityResponse:
    try:
        return await service.get(access_token, activity_id)
    except Exception as error:
        _raise_public_error(error)


@router.put(
    "/activities/{activity_id}/rpe",
    response_model=ActivityResponse,
    responses=error_responses,
)
async def submit_activity_rpe(
    activity_id: UUID,
    submission: ActivityRpeSubmission,
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[ActivityService, Depends(get_activity_service)],
) -> ActivityResponse:
    try:
        return await service.submit_rpe(identity.user_id, activity_id, submission)
    except Exception as error:
        _raise_public_error(error)
