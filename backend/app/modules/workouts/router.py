"""Authenticated Phase 5 workout catalog routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_authenticated_identity
from app.core.errors import ErrorResponse
from app.core.security import AuthenticatedIdentity
from app.modules.workouts.catalog import active_catalog
from app.modules.workouts.schemas import WorkoutCatalogResponse, WorkoutTemplateResponse

router = APIRouter(tags=["workouts"])


@router.get(
    "/workout-catalog",
    response_model=WorkoutCatalogResponse,
    responses={401: {"model": ErrorResponse}},
)
def get_workout_catalog(
    _: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
) -> WorkoutCatalogResponse:
    """Return only the latest reviewed, TSS-free catalog versions."""
    return WorkoutCatalogResponse(
        templates=tuple(
            WorkoutTemplateResponse.from_domain(template)
            for template in active_catalog()
        )
    )
