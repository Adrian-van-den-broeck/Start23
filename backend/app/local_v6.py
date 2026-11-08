"""Explicit local integration seam. Never imported by application startup."""

from urllib.parse import urlparse

from fastapi import FastAPI, Request

from app.modules.planning.router import get_planning_service
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
        )

    app.dependency_overrides[get_planning_service] = service
