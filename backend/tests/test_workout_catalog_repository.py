"""Transport tests for the server-private durable workout catalog."""

import asyncio
from decimal import Decimal

import httpx

from app.core.config import Settings
from app.modules.workouts.repository import SupabaseWorkoutCatalogRepository


def test_planning_catalog_uses_only_the_server_secret_key() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json=[
                {
                    "id": "51000000-0000-0000-0000-000000000001",
                    "planned_tss": 1.6666666666666667,
                }
            ],
        )

    async def exercise() -> tuple[dict[str, object], ...]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabaseWorkoutCatalogRepository(
                Settings(
                    environment="test",
                    supabase_secret_key="sb_secret_test",
                ),
                client=client,
            )
            return await repository.fetch_for_planning()

    rows = asyncio.run(exercise())

    assert rows[0]["planned_tss"] == Decimal("1.6666666666666667")
    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/get_workout_catalog_for_planning")
    assert captured.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in captured.headers


def test_planning_catalog_preserves_exact_numeric_load_precision() -> None:
    async def exercise() -> tuple[dict[str, object], ...]:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=(
                    b'[{"id":"51000000-0000-0000-0000-000000000001",'
                    b'"planned_tss":4.166666666666666666666666667}]'
                ),
                headers={"Content-Type": "application/json"},
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabaseWorkoutCatalogRepository(
                Settings(
                    environment="test",
                    supabase_secret_key="sb_secret_test",
                ),
                client=client,
            )
            return await repository.fetch_for_planning()

    rows = asyncio.run(exercise())

    assert rows[0]["planned_tss"] == Decimal("4.166666666666666666666666667")
