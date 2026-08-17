"""Versioned API router composition."""

from fastapi import APIRouter

from app.modules.activities.router import router as activities_router
from app.modules.calibration.router import router as calibration_router
from app.modules.checkins.router import router as checkins_router
from app.modules.health.router import router as health_router
from app.modules.identity.router import router as identity_router
from app.modules.integrations.router import router as integrations_router
from app.modules.onboarding.router import router as onboarding_router
from app.modules.planning.router import router as planning_router
from app.modules.workouts.router import router as workouts_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(identity_router)
api_router.include_router(onboarding_router)
api_router.include_router(workouts_router)
api_router.include_router(planning_router)
api_router.include_router(activities_router)
api_router.include_router(checkins_router)
api_router.include_router(calibration_router)
api_router.include_router(integrations_router)
