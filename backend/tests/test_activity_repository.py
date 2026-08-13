"""Transport tests for caller-RLS and narrow Phase 7 activity RPCs."""

import asyncio
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.modules.activities.repository import (
    ActivityRepositoryConflictError,
    SupabaseActivityRepository,
)


def _settings() -> Settings:
    return Settings(
        environment="test",
        supabase_publishable_key="sb_publishable_test",
        supabase_secret_key="sb_secret_test",
    )


def test_activity_creation_preserves_caller_rls_and_idempotency() -> None:
    captured: httpx.Request | None = None
    activity_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json={"id": str(activity_id)})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseActivityRepository(_settings(), client=client)
            await repository.create_activity(
                "athlete-token",
                uuid4(),
                "a" * 64,
                {"discipline": "run"},
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/create_activity_summary")
    assert captured.headers["apikey"] == "sb_publishable_test"
    assert captured.headers["authorization"] == "Bearer athlete-token"
    assert b"p_idempotency_key" in captured.content
    assert b"p_request_fingerprint" in captured.content


def test_planned_external_activity_creation_uses_atomic_caller_rpc() -> None:
    captured: httpx.Request | None = None
    external_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json={"id": str(uuid4())})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseActivityRepository(_settings(), client=client)
            await repository.create_activity(
                "athlete-token",
                uuid4(),
                "a" * 64,
                {
                    "discipline": "run",
                    "planned_external_activity_id": str(external_id),
                },
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/create_external_activity_summary")
    assert str(external_id).encode() in captured.content
    assert captured.headers["authorization"] == "Bearer athlete-token"


def test_hidden_load_context_and_rpe_completion_use_only_server_secret() -> None:
    requests: list[httpx.Request] = []
    athlete_id = uuid4()
    activity_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("get_activity_processing_context"):
            return httpx.Response(200, json={"duration_minutes": "60"})
        return httpx.Response(200, json={"id": str(activity_id)})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseActivityRepository(_settings(), client=client)
            await repository.fetch_processing_context(athlete_id, activity_id)
            await repository.complete_activity_rpe(
                athlete_id,
                activity_id,
                {"rpe": 4, "realized_tss": "4"},
            )
            await repository.revise_activity_rpe(
                athlete_id,
                activity_id,
                {"rpe": 5, "realized_tss": "5"},
            )

    asyncio.run(exercise())

    assert len(requests) == 3
    assert all(request.headers["apikey"] == "sb_secret_test" for request in requests)
    assert all("authorization" not in request.headers for request in requests)
    assert all(str(athlete_id).encode() in request.content for request in requests)


def test_rpe_correction_window_conflict_maps_to_stable_code() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"code": "40001", "message": "rpe correction window closed"},
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseActivityRepository(_settings(), client=client)
            with pytest.raises(ActivityRepositoryConflictError) as captured:
                await repository.revise_activity_rpe(
                    uuid4(),
                    uuid4(),
                    {"rpe": 7},
                )
            assert captured.value.code == "activity_rpe_window_closed"

    asyncio.run(exercise())
