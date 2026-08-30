"""Authenticated structured weekly check-in routes."""

from datetime import date
from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_access_token, get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity
from app.modules.coach.context import CheckInContextCoach
from app.modules.coach.weekly_plan import WeeklyPlanCoach
from app.modules.planning.repository import PlanningRepository
from app.modules.planning.schemas import WeeklyPlanProposalResponse
from app.modules.planning.service import PlanningCatalogProvider, PlanningService

from .repository import (
    CheckInRepository,
    CheckInRepositoryConflictError,
    CheckInRepositoryError,
    CheckInRepositoryNotFoundError,
    CheckInRepositoryUnavailableError,
)
from .schemas import (
    CheckInContextCandidateResponse,
    CheckInContextConfirmation,
    CheckInContextExtractionRequest,
    CheckInContextUpdate,
    CheckInStartRequest,
    GoalAchievementRequest,
    GoalMaintenanceResponse,
    InjuryRestrictionResponse,
    PlannedExternalActivityResponse,
    WeeklyCheckInResponse,
)
from .service import CheckInDomainError, CheckInService

router = APIRouter(tags=["check-ins"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_checkin_repository(request: Request) -> CheckInRepository:
    repository: CheckInRepository = request.app.state.checkin_repository
    return repository


def get_checkin_service(
    request: Request,
    repository: Annotated[CheckInRepository, Depends(get_checkin_repository)],
) -> CheckInService:
    planning_repository: PlanningRepository = request.app.state.planning_repository
    catalog_provider: PlanningCatalogProvider = (
        request.app.state.planning_catalog_provider
    )
    weekly_plan_coach: WeeklyPlanCoach = request.app.state.weekly_plan_coach
    context_coach: CheckInContextCoach = request.app.state.checkin_context_coach
    return CheckInService(
        repository,
        PlanningService(planning_repository, catalog_provider, weekly_plan_coach),
        context_coach,
    )


def _raise_public_error(error: Exception) -> NoReturn:
    if isinstance(error, CheckInRepositoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested weekly check-in was not found.",
        ) from error
    if isinstance(error, CheckInRepositoryConflictError):
        messages = {
            "checkin_context_stale": (
                "The check-in changed after this form was prepared."
            ),
            "checkin_not_confirmed": (
                "Confirm the structured context before generating a plan."
            ),
            "checkin_already_completed": "This check-in is already completed.",
            "restriction_review_required": (
                "Review every active restriction before completing this check-in."
            ),
            "checkin_state_conflict": (
                "The check-in state changed. Refresh and try again."
            ),
        }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error.code, "message": messages[error.code]},
        ) from error
    if isinstance(error, (CheckInDomainError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, (CheckInRepositoryUnavailableError, CheckInRepositoryError)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly check-in persistence is temporarily unavailable.",
        ) from error
    raise error


@router.post(
    "/checkins",
    response_model=WeeklyCheckInResponse,
    responses=error_responses,
)
async def start_weekly_checkin(
    payload: CheckInStartRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> WeeklyCheckInResponse:
    try:
        return await service.start(access_token, week_start=payload.week_start)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/checkins/{checkin_id}",
    response_model=WeeklyCheckInResponse,
    responses=error_responses,
)
async def get_weekly_checkin(
    checkin_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> WeeklyCheckInResponse:
    try:
        return await service.get(access_token, checkin_id)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/checkins/{checkin_id}/context-candidates",
    response_model=CheckInContextCandidateResponse,
    responses=error_responses,
)
async def extract_weekly_checkin_context_candidate(
    checkin_id: UUID,
    payload: CheckInContextExtractionRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> CheckInContextCandidateResponse:
    """Extract an inert candidate and optional clarifying questions."""
    try:
        return await service.extract_context_candidate(
            access_token,
            checkin_id,
            payload,
        )
    except Exception as error:
        _raise_public_error(error)


@router.put(
    "/checkins/{checkin_id}/context",
    response_model=WeeklyCheckInResponse,
    responses=error_responses,
)
async def save_weekly_checkin_context(
    checkin_id: UUID,
    payload: CheckInContextUpdate,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> WeeklyCheckInResponse:
    try:
        return await service.save_context(access_token, checkin_id, payload)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/checkins/{checkin_id}/context-confirmation",
    response_model=WeeklyCheckInResponse,
    responses=error_responses,
)
async def confirm_weekly_checkin_context(
    checkin_id: UUID,
    payload: CheckInContextConfirmation,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> WeeklyCheckInResponse:
    try:
        return await service.confirm_context(access_token, checkin_id, payload)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/checkins/{checkin_id}/plan-proposals",
    response_model=WeeklyPlanProposalResponse,
    responses=error_responses,
)
async def generate_checkin_plan_proposal(
    checkin_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> WeeklyPlanProposalResponse:
    try:
        return await service.generate_plan_proposal(
            access_token,
            identity.user_id,
            checkin_id,
        )
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/me/injury-restrictions",
    response_model=tuple[InjuryRestrictionResponse, ...],
    responses=error_responses,
)
async def list_injury_restrictions(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> tuple[InjuryRestrictionResponse, ...]:
    try:
        return await service.list_restrictions(access_token)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/planned-external-activities",
    response_model=tuple[PlannedExternalActivityResponse, ...],
    responses=error_responses,
)
async def list_planned_external_activities(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
    week_start: Annotated[date | None, Query()] = None,
) -> tuple[PlannedExternalActivityResponse, ...]:
    try:
        return await service.list_external_activities(access_token, week_start)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/me/goals/{goal_id}/achievement",
    response_model=GoalMaintenanceResponse,
    responses=error_responses,
)
async def mark_goal_achieved(
    goal_id: UUID,
    payload: GoalAchievementRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CheckInService, Depends(get_checkin_service)],
) -> GoalMaintenanceResponse:
    try:
        return await service.mark_goal_achieved(access_token, goal_id, payload)
    except Exception as error:
        _raise_public_error(error)
