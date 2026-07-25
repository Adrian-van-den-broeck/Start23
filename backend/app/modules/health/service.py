"""Health-check application service."""

from app.core.config import Settings
from app.modules.health.schemas import HealthResponse, ReadinessResponse


def build_health_response(settings: Settings) -> HealthResponse:
    """Build the public dependency-free health response."""
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


def build_readiness_response(settings: Settings) -> ReadinessResponse:
    """Build readiness while the application has no external dependencies."""
    return ReadinessResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
