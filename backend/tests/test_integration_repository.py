"""Transport tests for owner-RLS, secret RPC, and private file boundaries."""

import asyncio
from uuid import uuid4

import httpx

from app.core.config import Settings
from app.modules.integrations.repository import SupabaseIntegrationRepository


def _settings() -> Settings:
    return Settings(
        environment="test",
        supabase_publishable_key="sb_publishable_test",
        supabase_secret_key="sb_secret_test",
    )


def test_oauth_state_uses_owner_token_but_callback_storage_is_service_only() -> None:
    requests: list[httpx.Request] = []
    athlete_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("consume_polar_oauth_state"):
            return httpx.Response(200, json=str(athlete_id))
        return httpx.Response(200, json={"id": str(uuid4())})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseIntegrationRepository(_settings(), client=client)
            await repository.create_oauth_state(
                "athlete-token",
                "a" * 64,
                "2026-08-17T10:10:00Z",
            )
            assert await repository.consume_oauth_state("a" * 64) == athlete_id
            await repository.save_connection(
                athlete_id,
                "475",
                "provider-access-token-value",
                None,
            )

    asyncio.run(exercise())

    assert requests[0].headers["apikey"] == "sb_publishable_test"
    assert requests[0].headers["authorization"] == "Bearer athlete-token"
    assert all(
        request.headers["apikey"] == "sb_secret_test" for request in requests[1:]
    )
    assert all("authorization" not in request.headers for request in requests[1:])


def test_raw_fit_upload_is_private_and_metadata_uses_bounded_rpc() -> None:
    requests: list[httpx.Request] = []
    athlete_id = uuid4()
    activity_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201 if "/storage/v1/object/" in request.url.path else 200)

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseIntegrationRepository(_settings(), client=client)
            await repository.upload_activity_file(
                athlete_id,
                activity_id,
                "2AC312F",
                b"FIT-fixture",
                "b" * 64,
            )

    asyncio.run(exercise())

    upload, metadata = requests
    assert upload.url.path.endswith(
        f"/storage/v1/object/activity-files/{athlete_id}/{activity_id}/2AC312F.fit"
    )
    assert upload.headers["authorization"] == "Bearer sb_secret_test"
    assert upload.headers["x-upsert"] == "false"
    assert upload.content == b"FIT-fixture"
    assert metadata.url.path.endswith("/rest/v1/rpc/save_polar_activity_file")
    assert metadata.headers["apikey"] == "sb_secret_test"
    assert "authorization" not in metadata.headers
