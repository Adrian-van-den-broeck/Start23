"""Authenticated weekly-planning, deck, calendar, and proposal routes."""

from datetime import date
from typing import Annotated, Any, Literal, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_access_token, get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity
from app.modules.coach.weekly_plan import WeeklyPlanCoach
from app.modules.workouts.repository import PlanningCatalogUnavailableError

from .domain import PlanningConstraintError
from .repository import (
    PlanningRepository,
    PlanningRepositoryConflictError,
    PlanningRepositoryError,
    PlanningRepositoryNotFoundError,
    PlanningRepositoryUnavailableError,
)
from .schemas import (
    CalendarResponse,
    ChangeProposalSummaryResponse,
    PendingWorkoutAlternativesResponse,
    PendingWorkoutEditRequest,
    PlannedWorkoutMoveRequest,
    PlanValidationRequest,
    PlanValidationResponse,
    ScheduleProposalRequest,
    WeeklyPlanProposalRequest,
    WeeklyPlanProposalResponse,
    WeeklyPlanResponse,
    WorkoutDeckResponse,
)
from .service import (
    PlanningCatalogProvider,
    PlanningDomainError,
    PlanningService,
)

router = APIRouter(tags=["planning"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_planning_repository(request: Request) -> PlanningRepository:
    """Return the process-wide Phase 6 persistence adapter."""
    repository: PlanningRepository = request.app.state.planning_repository
    return repository


def get_planning_catalog_provider(request: Request) -> PlanningCatalogProvider:
    """Return the validated private catalog provider."""
    provider: PlanningCatalogProvider = request.app.state.planning_catalog_provider
    return provider


def get_weekly_plan_coach(request: Request) -> WeeklyPlanCoach:
    """Return the process-wide constrained qualitative coach."""
    coach: WeeklyPlanCoach = request.app.state.weekly_plan_coach
    return coach


def get_planning_service(
    repository: Annotated[PlanningRepository, Depends(get_planning_repository)],
    catalog_provider: Annotated[
        PlanningCatalogProvider,
        Depends(get_planning_catalog_provider),
    ],
    weekly_plan_coach: Annotated[
        WeeklyPlanCoach,
        Depends(get_weekly_plan_coach),
    ],
) -> PlanningService:
    """Build one request-scoped planning application service."""
    return PlanningService(repository, catalog_provider, weekly_plan_coach)


def raise_planning_error(error: Exception) -> NoReturn:
    """Map internal planning failures to stable, TSS-free HTTP errors."""
    if isinstance(error, PlanningRepositoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested planning resource was not found.",
        ) from error
    if isinstance(error, (PlanningRepositoryConflictError, PlanningConstraintError)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": error.code,
                "message": str(error),
            },
        ) from error
    if isinstance(
        error,
        (
            PlanningRepositoryUnavailableError,
            PlanningCatalogUnavailableError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly planning is temporarily unavailable.",
        ) from error
    if isinstance(error, (PlanningDomainError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, PlanningRepositoryError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly planning is temporarily unavailable.",
        ) from error
    raise error


@router.post(
    "/weekly-plans/proposals",
    response_model=WeeklyPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def create_initial_weekly_plan_proposal(
    proposal: WeeklyPlanProposalRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> WeeklyPlanProposalResponse:
    """Consume confirmed onboarding input into a pending auto-scheduled plan."""
    try:
        return await service.generate_initial_proposal(
            access_token,
            identity.user_id,
            proposal,
        )
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/weekly-plans/{plan_id}",
    response_model=WeeklyPlanResponse,
    responses=error_responses,
)
async def get_weekly_plan(
    plan_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
    revision: Annotated[int | None, Query(ge=1)] = None,
) -> WeeklyPlanResponse:
    """Read one owner-visible active or explicitly selected revision."""
    try:
        return await service.get_plan(access_token, plan_id, revision)
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/weekly-plans/{plan_id}/deck",
    response_model=WorkoutDeckResponse,
    responses=error_responses,
)
async def get_weekly_plan_deck(
    plan_id: UUID,
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
    expected_revision: int | None = None,
    selected_template_ids: list[UUID] | None = Query(default=None),
) -> WorkoutDeckResponse:
    """Return current eligible workout cards without hidden load."""
    try:
        return await service.get_deck(
            identity.user_id,
            plan_id,
            expected_revision=expected_revision,
            selected_template_ids=tuple(selected_template_ids or ()),
        )
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/weekly-plans/{plan_id}/schedule-proposals",
    response_model=WeeklyPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def create_schedule_proposal(
    plan_id: UUID,
    proposal: ScheduleProposalRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> WeeklyPlanProposalResponse:
    """Create a new pending revision from an explicit eligible deck selection."""
    try:
        return await service.generate_schedule_proposal(
            access_token,
            identity.user_id,
            plan_id,
            proposal,
        )
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/weekly-plans/{plan_id}/pending-workouts/{workout_id}/alternatives",
    response_model=PendingWorkoutAlternativesResponse,
    responses=error_responses,
)
async def get_pending_workout_alternatives(
    plan_id: UUID,
    workout_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
    expected_revision: Annotated[int, Query(ge=1)],
) -> PendingWorkoutAlternativesResponse:
    """Return valid removal/replacement choices for one exact pending revision."""
    try:
        return await service.get_pending_workout_alternatives(
            access_token,
            identity.user_id,
            plan_id,
            workout_id,
            expected_revision,
        )
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/weekly-plans/{plan_id}/pending-workouts/{workout_id}/edit-proposals",
    response_model=WeeklyPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def edit_pending_workout(
    plan_id: UUID,
    workout_id: UUID,
    edit: PendingWorkoutEditRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> WeeklyPlanProposalResponse:
    """Create a new pending revision after one server-authoritative edit."""
    try:
        return await service.edit_pending_workout(
            access_token,
            identity.user_id,
            plan_id,
            workout_id,
            edit,
        )
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/weekly-plans/{plan_id}/validate",
    response_model=PlanValidationResponse,
    responses=error_responses,
)
async def validate_weekly_plan(
    plan_id: UUID,
    layout: PlanValidationRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PlanValidationResponse:
    """Return qualitative soft-boundary warnings for an explicit layout."""
    try:
        return await service.validate_layout(access_token, plan_id, layout)
    except Exception as error:
        raise_planning_error(error)


@router.patch(
    "/planned-workouts/{workout_id}",
    response_model=WeeklyPlanResponse,
    responses=error_responses,
)
async def move_planned_workout(
    workout_id: UUID,
    move: PlannedWorkoutMoveRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> WeeklyPlanResponse:
    """Apply an explicit owner move as a new active revision with warnings."""
    try:
        return await service.move_workout(
            access_token,
            identity.user_id,
            workout_id,
            move,
        )
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/calendar",
    response_model=CalendarResponse,
    responses=error_responses,
)
async def get_calendar(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
) -> CalendarResponse:
    """Read active owner calendar events in a bounded timezone-aware range."""
    try:
        return await service.get_calendar(
            access_token,
            from_date,
            to_date,
        )
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/change-proposals",
    response_model=tuple[ChangeProposalSummaryResponse, ...],
    responses=error_responses,
)
async def list_change_proposals(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
    proposal_state: Annotated[
        Literal["pending", "approved", "rejected", "expired", "applied"] | None,
        Query(alias="state"),
    ] = None,
) -> tuple[ChangeProposalSummaryResponse, ...]:
    """List typed athlete-owned zone and plan proposals."""
    try:
        return await service.list_proposals(access_token, proposal_state)
    except Exception as error:
        raise_planning_error(error)


@router.get(
    "/change-proposals/{proposal_id}",
    response_model=ChangeProposalSummaryResponse,
    responses=error_responses,
)
async def get_change_proposal(
    proposal_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> ChangeProposalSummaryResponse:
    """Read one typed athlete-owned proposal envelope."""
    try:
        return await service.get_proposal(access_token, proposal_id)
    except Exception as error:
        raise_planning_error(error)
