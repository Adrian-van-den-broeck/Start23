"""Explicit local integration seam. Never imported by application startup."""

from typing import cast
from urllib.parse import urlparse
from uuid import UUID

from fastapi import FastAPI, Request

from app.modules.checkins.router import get_checkin_service
from app.modules.checkins.service import CheckInService
from app.modules.planning.router import get_planning_service
from app.modules.planning.schemas import WeeklyPlanProposalResponse
from app.modules.planning.service import PlanningCatalogProvider
from app.modules.planning.v6_selection import V6Controls
from app.modules.planning.v6_service import FrozenV6Repository, V6PlanningService


def install_local_v6(
    app: FastAPI,
    repository: FrozenV6Repository,
    catalog: PlanningCatalogProvider,
    *,
    controls: V6Controls = V6Controls(),
) -> None:
    """Use existing routes/authentication against explicitly isolated dependencies.

    No endpoint, client flag, production setting or alternative approval flow.
    Caller supplies local/synthetic repositories and the existing token verifier.
    """
    settings = app.state.settings
    if settings.environment != "test" or (
        settings.supabase_url is not None
        and urlparse(str(settings.supabase_url)).hostname
        not in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError("V6 mobile integration requires an isolated test application.")

    def service(request: Request) -> V6PlanningService:
        return V6PlanningService(
            repository,
            catalog,
            app.state.weekly_plan_coach,
            request.app.state.planning_computation,
            controls=getattr(app.state, "v6_controls", controls),
            allow_test_frequency_controls=True,
        )

    app.dependency_overrides[get_planning_service] = service

    class LocalV6CheckInService(CheckInService):
        async def generate_plan_proposal(
            self, access_token: str, athlete_id: UUID, checkin_id: UUID
        ) -> WeeklyPlanProposalResponse:
            response = await super().generate_plan_proposal(
                access_token, athlete_id, checkin_id
            )
            response.plan.workouts = await cast(
                V6PlanningService, self._planning_service
            )._present_workouts(response.plan.workouts)
            return response

    def checkin_service(request: Request) -> CheckInService:
        return LocalV6CheckInService(
            request.app.state.checkin_repository,
            service(request),
            request.app.state.checkin_context_coach,
        )

    app.dependency_overrides[get_checkin_service] = checkin_service
