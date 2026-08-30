"""Authenticated Polar lifecycle routes and signed public webhook callback."""

from typing import Annotated, Any, NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)

from app.api.dependencies import (
    get_access_token,
    get_app_settings,
    get_authenticated_identity,
)
from app.core.config import Settings
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity

from .domain import IntegrationPayloadError
from .polar import PolarProvider, PolarProviderError
from .repository import (
    IntegrationConflictError,
    IntegrationNotFoundError,
    IntegrationRepository,
    IntegrationRepositoryError,
)
from .schemas import (
    HistoricalImportRequest,
    ImportRunResponse,
    OAuthCallbackResponse,
    OAuthStartResponse,
    ProviderConnectionResponse,
    WebhookReceiptResponse,
)
from .service import IntegrationService

router = APIRouter(tags=["integrations"])
errors: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def get_integration_repository(request: Request) -> IntegrationRepository:
    repository: IntegrationRepository = request.app.state.integration_repository
    return repository


def get_polar_provider(request: Request) -> PolarProvider:
    provider: PolarProvider = request.app.state.polar_provider
    return provider


def get_integration_service(
    repository: Annotated[IntegrationRepository, Depends(get_integration_repository)],
    provider: Annotated[PolarProvider, Depends(get_polar_provider)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> IntegrationService:
    return IntegrationService(repository, provider, settings)


def _raise(error: Exception) -> NoReturn:
    if isinstance(error, IntegrationNotFoundError):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Polar connection was not found.",
        ) from error
    if isinstance(error, IntegrationConflictError):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The integration state changed. Try again.",
        ) from error
    if isinstance(error, IntegrationPayloadError):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(error),
        ) from error
    if isinstance(error, PolarProviderError | IntegrationRepositoryError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Polar is temporarily unavailable.",
        ) from error
    raise error


@router.post(
    "/integrations/polar/oauth/start",
    response_model=OAuthStartResponse,
    status_code=status.HTTP_201_CREATED,
    responses=errors,
)
async def start_polar_oauth(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> OAuthStartResponse:
    try:
        return await service.start_oauth(access_token)
    except Exception as error:
        _raise(error)


@router.get(
    "/integrations/polar/oauth/callback",
    response_model=OAuthCallbackResponse,
    responses=errors,
)
async def complete_polar_oauth(
    code: Annotated[str, Query(min_length=1, max_length=500)],
    state_value: Annotated[str, Query(alias="state", min_length=1, max_length=500)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> OAuthCallbackResponse:
    try:
        return await service.complete_oauth(code, state_value)
    except Exception as error:
        _raise(error)


@router.get(
    "/integrations/polar",
    response_model=ProviderConnectionResponse,
    responses=errors,
)
async def get_polar_connection(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ProviderConnectionResponse:
    try:
        return await service.get_connection(access_token)
    except Exception as error:
        _raise(error)


@router.delete(
    "/integrations/polar",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=errors,
)
async def disconnect_polar(
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> Response:
    try:
        await service.disconnect(identity.user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        _raise(error)


@router.post(
    "/integrations/polar/imports",
    response_model=ImportRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses=errors,
)
async def import_polar_history(
    payload: HistoricalImportRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ImportRunResponse:
    try:
        return await service.import_historical(
            identity.user_id, idempotency_key, payload.days
        )
    except Exception as error:
        _raise(error)


@router.get(
    "/integrations/polar/imports",
    response_model=tuple[ImportRunResponse, ...],
    responses=errors,
)
async def list_polar_imports(
    access_token: Annotated[str, Depends(get_access_token)],
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> tuple[ImportRunResponse, ...]:
    try:
        return await service.list_imports(access_token)
    except Exception as error:
        _raise(error)


@router.post(
    "/integrations/polar/imports/{import_id}/retry",
    response_model=ImportRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses=errors,
)
async def retry_polar_import(
    import_id: UUID,
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ImportRunResponse:
    """Retry one owned failed import after an explicit athlete action."""
    try:
        return await service.retry_historical(identity.user_id, import_id)
    except Exception as error:
        _raise(error)


@router.post(
    "/webhooks/polar",
    response_model=WebhookReceiptResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
async def polar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    signature: Annotated[str, Header(alias="Polar-Webhook-Signature")],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> WebhookReceiptResponse:
    try:
        result, receipt_id = await service.receive_webhook(
            await request.body(), signature
        )
        if receipt_id is not None:
            background_tasks.add_task(service.process_webhook, receipt_id)
        return result
    except IntegrationPayloadError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook.") from error
    except Exception as error:
        _raise(error)
