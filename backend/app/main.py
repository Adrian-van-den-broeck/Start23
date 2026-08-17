"""FastAPI application entrypoint."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import configure_error_handling
from app.core.logging import configure_logging
from app.core.security import AccessTokenVerifier, SupabaseAccessTokenVerifier
from app.modules.activities.repository import (
    ActivityRepository,
    SupabaseActivityRepository,
)
from app.modules.calibration.repository import (
    CalibrationRepository,
    SupabaseCalibrationRepository,
)
from app.modules.checkins.repository import (
    CheckInRepository,
    SupabaseCheckInRepository,
)
from app.modules.health.router import router as health_router
from app.modules.integrations.polar import PolarAccessLinkClient, PolarProvider
from app.modules.integrations.repository import (
    IntegrationRepository,
    SupabaseIntegrationRepository,
)
from app.modules.onboarding.repository import (
    OnboardingRepository,
    SupabaseOnboardingRepository,
)
from app.modules.planning.repository import (
    PlanningRepository,
    SupabasePlanningRepository,
)
from app.modules.planning.service import (
    PlanningCatalogProvider,
    SupabasePlanningCatalogProvider,
)
from app.modules.workouts.repository import SupabaseWorkoutCatalogRepository


def _lifespan(
    settings: Settings,
    onboarding_repository: OnboardingRepository,
    planning_repository: PlanningRepository,
    planning_catalog_provider: PlanningCatalogProvider,
    activity_repository: ActivityRepository,
    checkin_repository: CheckInRepository,
    calibration_repository: CalibrationRepository,
    integration_repository: IntegrationRepository,
    polar_provider: PolarProvider,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger = logging.getLogger(__name__)
        logger.info(
            "Application started",
            extra={
                "event": "application_started",
                "environment": settings.environment,
                "version": settings.app_version,
            },
        )
        yield
        await asyncio.gather(
            onboarding_repository.aclose(),
            planning_repository.aclose(),
            planning_catalog_provider.aclose(),
            activity_repository.aclose(),
            checkin_repository.aclose(),
            calibration_repository.aclose(),
            integration_repository.aclose(),
            polar_provider.aclose(),
        )
        logger.info(
            "Application stopped",
            extra={
                "event": "application_stopped",
                "environment": settings.environment,
                "version": settings.app_version,
            },
        )

    return lifespan


def create_app(
    settings: Settings | None = None,
    access_token_verifier: AccessTokenVerifier | None = None,
    onboarding_repository: OnboardingRepository | None = None,
    planning_repository: PlanningRepository | None = None,
    planning_catalog_provider: PlanningCatalogProvider | None = None,
    activity_repository: ActivityRepository | None = None,
    checkin_repository: CheckInRepository | None = None,
    calibration_repository: CalibrationRepository | None = None,
    integration_repository: IntegrationRepository | None = None,
    polar_provider: PolarProvider | None = None,
) -> FastAPI:
    """Create and configure the Start23 FastAPI application."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    repository = onboarding_repository or SupabaseOnboardingRepository(app_settings)
    weekly_planning_repository = planning_repository or SupabasePlanningRepository(
        app_settings
    )
    catalog_provider = planning_catalog_provider or SupabasePlanningCatalogProvider(
        SupabaseWorkoutCatalogRepository(app_settings)
    )
    completed_activity_repository = activity_repository or SupabaseActivityRepository(
        app_settings
    )
    weekly_checkin_repository = checkin_repository or SupabaseCheckInRepository(
        app_settings
    )
    zone_calibration_repository = (
        calibration_repository or SupabaseCalibrationRepository(app_settings)
    )
    wearable_integration_repository = (
        integration_repository or SupabaseIntegrationRepository(app_settings)
    )
    polar_client = polar_provider or PolarAccessLinkClient(app_settings)
    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=_lifespan(
            app_settings,
            repository,
            weekly_planning_repository,
            catalog_provider,
            completed_activity_repository,
            weekly_checkin_repository,
            zone_calibration_repository,
            wearable_integration_repository,
            polar_client,
        ),
    )
    application.state.settings = app_settings
    application.state.access_token_verifier = (
        access_token_verifier or SupabaseAccessTokenVerifier(app_settings)
    )
    application.state.onboarding_repository = repository
    application.state.planning_repository = weekly_planning_repository
    application.state.planning_catalog_provider = catalog_provider
    application.state.activity_repository = completed_activity_repository
    application.state.checkin_repository = weekly_checkin_repository
    application.state.calibration_repository = zone_calibration_repository
    application.state.integration_repository = wearable_integration_repository
    application.state.polar_provider = polar_client
    configure_error_handling(application)
    application.include_router(health_router)
    application.include_router(
        api_router,
        prefix=app_settings.api_v1_prefix,
    )
    return application


app = create_app()
