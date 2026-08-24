"""Authenticated zone-intake, field-test, and calibration routes."""

from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_access_token, get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity
from app.modules.calibration.repository import (
    CalibrationRepository,
    CalibrationRepositoryConflictError,
    CalibrationRepositoryError,
    CalibrationRepositoryNotFoundError,
    CalibrationRepositoryUnavailableError,
)
from app.modules.calibration.schemas import (
    CalibrationEvaluationRequest,
    CalibrationEvaluationResponse,
    CalibrationObservationCreate,
    CalibrationObservationResponse,
    CalibrationProtocolResponse,
    CalibrationStatusResponse,
    DisciplineSetupInput,
    DisciplineSetupResponse,
    ThresholdConfirmationRequest,
    ThresholdDecisionResponse,
    ZoneOptionResponse,
)
from app.modules.calibration.service import (
    CalibrationDomainError,
    CalibrationService,
)
from app.modules.physiology.models import Discipline

router = APIRouter(tags=["calibration"])
error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_calibration_repository(request: Request) -> CalibrationRepository:
    repository: CalibrationRepository = request.app.state.calibration_repository
    return repository


def get_calibration_service(
    repository: Annotated[
        CalibrationRepository,
        Depends(get_calibration_repository),
    ],
) -> CalibrationService:
    return CalibrationService(repository)


def _raise_public_error(error: Exception) -> NoReturn:
    if isinstance(error, CalibrationRepositoryNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The calibration resource was not found.",
        ) from error
    if isinstance(error, CalibrationRepositoryConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The calibration change conflicts with stored state.",
        ) from error
    if isinstance(error, CalibrationRepositoryUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Calibration persistence is temporarily unavailable.",
        ) from error
    if isinstance(error, (CalibrationDomainError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, CalibrationRepositoryError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Calibration persistence is temporarily unavailable.",
        ) from error
    raise error


@router.get(
    "/onboarding/zone-options",
    response_model=tuple[ZoneOptionResponse, ...],
    responses=error_responses,
)
async def get_zone_options(
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> tuple[ZoneOptionResponse, ...]:
    """Return the four explicit setup choices."""
    return service.zone_options()


@router.put(
    "/onboarding/disciplines/{discipline}/setup",
    response_model=DisciplineSetupResponse,
    responses=error_responses,
)
async def save_discipline_setup(
    discipline: Discipline,
    setup: DisciplineSetupInput,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> DisciplineSetupResponse:
    """Persist a resumable owner-derived setup route."""
    try:
        return await service.save_setup(access_token, discipline, setup)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/calibration/protocols/{discipline}",
    response_model=tuple[CalibrationProtocolResponse, ...],
    responses=error_responses,
)
async def get_calibration_protocols(
    discipline: Discipline,
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> tuple[CalibrationProtocolResponse, ...]:
    """Return reviewed protocol definitions for one discipline."""
    return service.protocols(discipline)


@router.post(
    "/calibration/observations",
    response_model=CalibrationObservationResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def save_calibration_observation(
    observation: CalibrationObservationCreate,
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> CalibrationObservationResponse:
    """Persist one immutable and retry-idempotent segment observation."""
    try:
        return await service.save_observation(access_token, observation)
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/calibration/evaluate",
    response_model=CalibrationEvaluationResponse,
    responses=error_responses,
)
async def evaluate_calibration(
    evaluation: CalibrationEvaluationRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> CalibrationEvaluationResponse:
    """Evaluate owned observations with deterministic reviewed formulas."""
    try:
        return await service.evaluate(
            access_token,
            identity.user_id,
            evaluation,
        )
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/calibration/evaluations/{evaluation_id}/threshold/confirm",
    response_model=ThresholdDecisionResponse,
    responses=error_responses,
)
async def confirm_calibration_threshold(
    evaluation_id: UUID,
    confirmation: ThresholdConfirmationRequest,
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> ThresholdDecisionResponse:
    """Confirm a threshold and create a separate pending zone proposal."""
    del confirmation
    try:
        return await service.confirm_threshold(
            access_token,
            identity.user_id,
            evaluation_id,
        )
    except Exception as error:
        _raise_public_error(error)


@router.post(
    "/calibration/evaluations/{evaluation_id}/threshold/reject",
    response_model=ThresholdDecisionResponse,
    responses=error_responses,
)
async def reject_calibration_threshold(
    evaluation_id: UUID,
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> ThresholdDecisionResponse:
    """Reject a threshold without creating or changing a zone profile."""
    try:
        return await service.reject_threshold(identity.user_id, evaluation_id)
    except Exception as error:
        _raise_public_error(error)


@router.get(
    "/calibration/status",
    response_model=CalibrationStatusResponse,
    responses=error_responses,
)
async def get_calibration_status(
    access_token: Annotated[str, Depends(get_access_token)],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[CalibrationService, Depends(get_calibration_service)],
) -> CalibrationStatusResponse:
    """Return only the verified athlete's setup and evaluation state."""
    try:
        return await service.status(access_token, identity.user_id)
    except Exception as error:
        _raise_public_error(error)
