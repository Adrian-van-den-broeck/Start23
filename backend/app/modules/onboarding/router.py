"""Authenticated Phase 4 onboarding routes."""

from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_access_token, get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity
from app.modules.onboarding.repository import (
    OnboardingRepository,
    RepositoryConflictError,
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryUnavailableError,
)
from app.modules.onboarding.schemas import (
    AthleteProfileResponse,
    AthleteProfileUpdate,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
    PrimaryRaceGoalInput,
    PrimaryRaceGoalResponse,
    TrainingHistoryEntryResponse,
    TrainingHistoryReplace,
    ZoneProposalDecisionResponse,
    ZoneSubmission,
    ZoneSubmissionResponse,
)
from app.modules.onboarding.service import OnboardingDomainError, OnboardingService
from app.modules.physiology.models import Discipline
from app.modules.planning.router import get_planning_service, raise_planning_error
from app.modules.planning.schemas import (
    PlanProposalDecisionResponse,
    ProposalApprovalRequest,
)
from app.modules.planning.service import PlanningService

router = APIRouter(tags=["onboarding"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_onboarding_repository(request: Request) -> OnboardingRepository:
    """Return the process-wide owner-scoped repository."""
    repository: OnboardingRepository = request.app.state.onboarding_repository
    return repository


def get_onboarding_service(
    repository: Annotated[
        OnboardingRepository,
        Depends(get_onboarding_repository),
    ],
) -> OnboardingService:
    """Build a request-scoped application service."""
    return OnboardingService(repository)


def _raise_public_error(error: Exception) -> NoReturn:
    if isinstance(error, RepositoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested onboarding resource was not found.",
        ) from error
    if isinstance(error, RepositoryConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The onboarding change conflicts with current state.",
        ) from error
    if isinstance(error, RepositoryUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Onboarding persistence is temporarily unavailable.",
        ) from error
    if isinstance(error, (OnboardingDomainError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, RepositoryError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Onboarding persistence is temporarily unavailable.",
        ) from error
    raise error


@router.get(
    "/me/profile",
    response_model=AthleteProfileResponse,
    responses=error_responses,
)
async def get_profile(
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> AthleteProfileResponse:
    """Return the verified athlete's profile."""
    try:
        profile = await service.get_profile(access_token, identity.user_id)
        if profile is None:
            raise RepositoryNotFoundError
        return profile
    except Exception as error:
        _raise_public_error(error)


@router.patch(
    "/me/profile",
    response_model=AthleteProfileResponse,
    responses=error_responses,
)
async def update_profile(
    update: AthleteProfileUpdate,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> AthleteProfileResponse:
    """Create or patch confirmed profile and biometric fields."""
    try:
        return await service.update_profile(access_token, identity.user_id, update)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/onboarding",
    response_model=OnboardingStateResponse,
    responses=error_responses,
)
async def get_onboarding(
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingStateResponse:
    """Return the athlete's resumable onboarding state."""
    try:
        return await service.get_state(access_token, identity.user_id)
    except Exception as error:
        _raise_public_error(error)


@router.put(
    "/me/training-history",
    response_model=tuple[TrainingHistoryEntryResponse, ...],
    responses=error_responses,
)
async def replace_training_history(
    replacement: TrainingHistoryReplace,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> tuple[TrainingHistoryEntryResponse, ...]:
    """Replace all athlete-confirmed triathlon history atomically."""
    try:
        return await service.replace_training_history(access_token, replacement)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/me/goals",
    response_model=PrimaryRaceGoalResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def create_primary_goal(
    goal: PrimaryRaceGoalInput,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> PrimaryRaceGoalResponse:
    """Create the one active race-oriented A goal."""
    try:
        return await service.save_primary_goal(access_token, goal)
    except Exception as error:
        _raise_public_error(error)


@router.put(
    "/me/goals/{goal_id}",
    response_model=PrimaryRaceGoalResponse,
    responses=error_responses,
)
async def update_primary_goal(
    goal_id: UUID,
    goal: PrimaryRaceGoalInput,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> PrimaryRaceGoalResponse:
    """Update the owned active primary race goal."""
    try:
        return await service.save_primary_goal(
            access_token,
            goal,
            goal_id=goal_id,
        )
    except Exception as error:
        _raise_public_error(error)


@router.put(
    "/me/zones/{discipline}",
    response_model=ZoneSubmissionResponse,
    responses=error_responses,
)
async def save_zone_profile(
    discipline: Discipline,
    submission: ZoneSubmission,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ZoneSubmissionResponse:
    """Persist first active zones or a pending replacement proposal."""
    try:
        return await service.save_zone_profile(
            access_token,
            identity.user_id,
            discipline,
            submission,
        )
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    responses=error_responses,
)
async def complete_onboarding(
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingCompleteResponse:
    """Complete valid onboarding and create an initial planning request."""
    try:
        return await service.complete(access_token, identity.user_id)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/change-proposals/{proposal_id}/approve",
    response_model=ZoneProposalDecisionResponse | PlanProposalDecisionResponse,
    responses=error_responses,
)
async def approve_change_proposal(
    proposal_id: UUID,
    approval: ProposalApprovalRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    onboarding_service: Annotated[
        OnboardingService,
        Depends(get_onboarding_service),
    ],
    planning_service: Annotated[
        PlanningService,
        Depends(get_planning_service),
    ],
) -> ZoneProposalDecisionResponse | PlanProposalDecisionResponse:
    """Atomically approve one typed owner proposal against its exact base."""
    try:
        if approval.expected_base_revision is not None:
            return await planning_service.approve_plan_proposal(
                access_token,
                proposal_id,
                approval.expected_base_revision,
            )
        return await onboarding_service.approve_zone_proposal(
            access_token,
            proposal_id,
            approval.expected_base_zone_profile_id,
        )
    except Exception as error:
        if approval.expected_base_revision is not None:
            raise_planning_error(error)
        _raise_public_error(error)


@router.post(
    "/change-proposals/{proposal_id}/reject",
    response_model=ZoneProposalDecisionResponse | PlanProposalDecisionResponse,
    responses=error_responses,
)
async def reject_change_proposal(
    proposal_id: UUID,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    onboarding_service: Annotated[
        OnboardingService,
        Depends(get_onboarding_service),
    ],
    planning_service: Annotated[
        PlanningService,
        Depends(get_planning_service),
    ],
) -> ZoneProposalDecisionResponse | PlanProposalDecisionResponse:
    """Reject one typed owned proposal without changing its active target."""
    try:
        try:
            return await onboarding_service.reject_zone_proposal(
                access_token,
                proposal_id,
            )
        except RepositoryNotFoundError:
            return await planning_service.reject_plan_proposal(
                access_token,
                proposal_id,
            )
    except Exception as error:
        if not isinstance(error, (RepositoryError, OnboardingDomainError, ValueError)):
            raise_planning_error(error)
        _raise_public_error(error)
