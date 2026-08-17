"""Supabase transport tests for trusted and athlete-scoped onboarding calls."""

import asyncio
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.modules.onboarding.repository import (
    RepositorySchemaMismatchError,
    SupabaseOnboardingRepository,
)


def _settings() -> Settings:
    return Settings(
        environment="test",
        supabase_publishable_key="sb_publishable_test",
        supabase_secret_key="sb_secret_test",
    )


def test_fetch_state_allows_missing_forward_zone_setup_table() -> None:
    athlete_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/rest/v1/discipline_zone_setups"):
            return httpx.Response(
                404,
                json={
                    "code": "PGRST205",
                    "message": "Could not find the table in the schema cache",
                },
            )
        return httpx.Response(200, json=[])

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabaseOnboardingRepository(_settings(), client=client)
            state = await repository.fetch_state("athlete-token", athlete_id)

        assert state["profile"] is None
        assert state["discipline_setups"] == []

    asyncio.run(exercise())


def test_fetch_state_does_not_hide_missing_required_table() -> None:
    athlete_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/rest/v1/athlete_profiles"):
            return httpx.Response(
                404,
                json={
                    "code": "PGRST205",
                    "message": "Could not find the table in the schema cache",
                },
            )
        return httpx.Response(200, json=[])

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabaseOnboardingRepository(_settings(), client=client)
            with pytest.raises(RepositorySchemaMismatchError):
                await repository.fetch_state("athlete-token", athlete_id)

    asyncio.run(exercise())


def test_fallback_rpc_uses_only_the_server_secret_key() -> None:
    athlete_id = uuid4()
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json={
                "profile_id": str(uuid4()),
                "version": 1,
                "status": "active",
                "proposal_id": None,
            },
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            repository = SupabaseOnboardingRepository(
                _settings(),
                client=client,
            )
            await repository.save_fallback_zone_profile(
                athlete_id,
                {
                    "discipline": "bike",
                    "boundaries": [
                        {
                            "zone_number": zone_number,
                            "lower_value": str(90 + zone_number * 10),
                            "upper_value": str(100 + zone_number * 10),
                        }
                        for zone_number in range(1, 6)
                    ],
                },
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/save_fallback_zone_profile")
    assert captured.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in captured.headers
    assert b"p_athlete_id" in captured.content
