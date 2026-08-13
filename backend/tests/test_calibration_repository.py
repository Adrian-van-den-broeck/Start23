"""HTTP boundary tests for calibration persistence."""

import asyncio
from uuid import uuid4

import httpx
from pydantic import SecretStr

from app.core.config import Settings
from app.modules.calibration.repository import SupabaseCalibrationRepository


def test_setup_and_observation_rpcs_preserve_athlete_rls_context() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("save_discipline_zone_setup"):
            return httpx.Response(200, json={"discipline": "run"})
        return httpx.Response(200, json={"id": str(uuid4())})

    settings = Settings(
        environment="test",
        supabase_publishable_key="publishable",
        supabase_secret_key=SecretStr("secret"),
    )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseCalibrationRepository(settings, client=client)
            await repository.save_setup(
                "athlete-token",
                {"discipline": "run", "setup_route": "rpe_only"},
            )
            await repository.save_observation(
                "athlete-token",
                {"activity_id": str(uuid4())},
                "a" * 64,
            )

    asyncio.run(exercise())

    assert len(requests) == 2
    assert all(
        request.headers["Authorization"] == "Bearer athlete-token"
        for request in requests
    )
    assert all(request.headers["apikey"] == "publishable" for request in requests)
    assert b"athlete_id" not in requests[0].content
    assert b"athlete_id" not in requests[1].content


def test_generated_evaluation_uses_only_the_service_rpc() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json={"id": str(uuid4())})

    athlete_id = uuid4()
    settings = Settings(
        environment="test",
        supabase_publishable_key="publishable",
        supabase_secret_key=SecretStr("server-secret"),
    )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseCalibrationRepository(settings, client=client)
            await repository.save_evaluation(
                athlete_id,
                {"status": "insufficient_data"},
                "b" * 64,
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.path.endswith("/rest/v1/rpc/save_calibration_evaluation")
    assert captured.headers["apikey"] == "server-secret"
    assert "Authorization" not in captured.headers
    assert str(athlete_id).encode() in captured.content


def test_observation_read_keeps_explicit_owner_protocol_activity_filters() -> None:
    captured: httpx.Request | None = None
    observation_id = uuid4()
    athlete_id = uuid4()
    activity_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json=[
                {
                    "id": str(observation_id),
                    "fingerprint": "c" * 32,
                    "created_at": "2026-08-13T15:00:00Z",
                    "payload": {
                        "activity_id": str(activity_id),
                        "protocol_id": "start23_run_threshold_30min_v1",
                    },
                }
            ],
        )

    settings = Settings(
        environment="test",
        supabase_publishable_key="publishable",
    )
    rows: list[dict[str, object]] = []

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabaseCalibrationRepository(settings, client=client)
            rows.extend(
                await repository.list_observations(
                    "athlete-token",
                    athlete_id,
                    "start23_run_threshold_30min_v1",
                    activity_id,
                )
            )

    asyncio.run(exercise())

    assert captured is not None
    assert captured.url.params["athlete_id"] == f"eq.{athlete_id}"
    assert captured.url.params["activity_id"] == f"eq.{activity_id}"
    assert captured.url.params["protocol_id"] == ("eq.start23_run_threshold_30min_v1")
    assert rows[0]["id"] == str(observation_id)
    assert rows[0]["activity_id"] == str(activity_id)
