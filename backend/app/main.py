"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import configure_error_handling
from app.core.logging import configure_logging
from app.core.security import AccessTokenVerifier, SupabaseAccessTokenVerifier
from app.modules.health.router import router as health_router


def _lifespan(
    settings: Settings,
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
) -> FastAPI:
    """Create and configure the Start23 FastAPI application."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=_lifespan(app_settings),
    )
    application.state.settings = app_settings
    application.state.access_token_verifier = (
        access_token_verifier or SupabaseAccessTokenVerifier(app_settings)
    )
    configure_error_handling(application)
    application.include_router(health_router)
    application.include_router(
        api_router,
        prefix=app_settings.api_v1_prefix,
    )
    return application


app = create_app()
