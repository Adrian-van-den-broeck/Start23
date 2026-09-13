"""Opaque identity and bounded legacy-owner adapter transport tests."""

import asyncio
from uuid import uuid4

import httpx

from app.core.config import Settings
from app.modules.identity.repository import (
    LegacyAthleteOwnerAdapter,
    SupabaseAthleteIdentityRepository,
)


def _settings() -> Settings:
    return Settings(
        environment="test",
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="publishable",
        supabase_secret_key="secret",
    )


def test_current_token_resolves_to_opaque_id_not_auth_subject() -> None:
    athlete_id = uuid4()
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json=str(athlete_id))

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseAthleteIdentityRepository(_settings(), client=client)
            assert await repository.resolve_current_athlete_id("jwt") == athlete_id

    asyncio.run(exercise())
    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/get_current_athlete_id")
    assert captured.headers["authorization"] == "Bearer jwt"


def test_legacy_adapter_maps_distinct_ids_and_caches_the_boundary() -> None:
    athlete_id = uuid4()
    auth_user_id = uuid4()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=str(auth_user_id))

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = LegacyAthleteOwnerAdapter(_settings(), client)
            assert await adapter.legacy_id(athlete_id) == auth_user_id
            assert await adapter.legacy_id(athlete_id) == auth_user_id

    asyncio.run(exercise())
    assert athlete_id != auth_user_id
    assert len(requests) == 1
    assert requests[0].headers["apikey"] == "secret"
    assert "authorization" not in requests[0].headers
