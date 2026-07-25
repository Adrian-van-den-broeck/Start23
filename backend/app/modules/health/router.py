"""Health-check HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_app_settings
from app.core.config import Settings
from app.modules.health.schemas import HealthResponse, ReadinessResponse
from app.modules.health.service import build_health_response, build_readiness_response

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Report application health",
)
def get_health(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> HealthResponse:
    """Return dependency-free application health."""
    return build_health_response(settings)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Report application readiness",
)
def get_readiness(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ReadinessResponse:
    """Return readiness for the application's configured dependencies."""
    return build_readiness_response(settings)
