"""Transport tests for owner-scoped and trusted Phase 6 RPC calls."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.modules.planning.repository import (
    PlanningRepositoryConflictError,
    SupabasePlanningRepository,
)


def _settings() -> Settings:
    return Settings(
        environment="test",
        supabase_publishable_key="sb_publishable_test",
        supabase_secret_key="sb_secret_test",
    )


def test_generated_plan_persistence_uses_only_the_server_secret() -> None:
    athlete_id = uuid4()
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json={
                "plan_id": str(uuid4()),
                "proposal_id": str(uuid4()),
                "revision": 1,
            },
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabasePlanningRepository(_settings(), client=client)
            await repository.create_plan_proposal(
                athlete_id,
                {"generation_fingerprint": "a" * 64},
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/create_weekly_plan_proposal_v2")
    assert captured.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in captured.headers
    assert str(athlete_id).encode() in captured.content


def test_coach_explanation_write_uses_bounded_service_rpc() -> None:
    athlete_id = uuid4()
    proposal_id = uuid4()
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json="Veilig weekvoorstel ter controle.")

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabasePlanningRepository(_settings(), client=client)
            await repository.set_plan_proposal_explanation(
                athlete_id,
                proposal_id,
                "Veilig weekvoorstel ter controle.",
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith(
        "/rest/v1/rpc/set_weekly_plan_proposal_explanation"
    )
    assert captured.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in captured.headers
    assert str(proposal_id).encode() in captured.content


def test_plan_reads_and_approval_preserve_the_caller_rls_token() -> None:
    requests: list[httpx.Request] = []
    plan_id = uuid4()
    proposal_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/rpc/get_weekly_plan"):
            return httpx.Response(200, json={"id": str(plan_id)})
        return httpx.Response(
            200,
            json={
                "proposal_id": str(proposal_id),
                "state": "applied",
                "plan_id": str(plan_id),
                "active_revision": 1,
                "target_revision_id": str(uuid4()),
            },
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabasePlanningRepository(_settings(), client=client)
            await repository.fetch_plan("athlete-token", plan_id)
            await repository.approve_plan_proposal(
                "athlete-token",
                proposal_id,
                0,
            )

    asyncio.run(exercise())

    assert len(requests) == 2
    assert all(
        request.headers["apikey"] == "sb_publishable_test"
        and request.headers["authorization"] == "Bearer athlete-token"
        for request in requests
    )


def test_direct_move_is_persisted_only_through_the_trusted_backend_rpc() -> None:
    athlete_id = uuid4()
    workout_id = uuid4()
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json={"plan_id": str(uuid4()), "revision": 2},
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabasePlanningRepository(_settings(), client=client)
            await repository.move_planned_workout(
                athlete_id,
                workout_id,
                1,
                datetime(2026, 8, 5, 7, tzinfo=timezone.utc),
                [],
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/move_planned_workout")
    assert captured.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in captured.headers
    assert str(athlete_id).encode() in captured.content


def test_database_conflicts_map_to_stable_public_planning_codes() -> None:
    proposal_id = uuid4()

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"code": "40001", "message": "plan proposal is stale"},
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabasePlanningRepository(_settings(), client=client)
            with pytest.raises(PlanningRepositoryConflictError) as captured:
                await repository.approve_plan_proposal(
                    "athlete-token",
                    proposal_id,
                    1,
                )
            assert captured.value.code == "proposal_stale"
            assert str(captured.value) == (
                "This proposal is based on an older plan revision."
            )

    asyncio.run(exercise())
