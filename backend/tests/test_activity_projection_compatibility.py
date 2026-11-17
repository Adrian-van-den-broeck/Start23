"""Explicit metadata opt-in preserves strict historical activity operations."""

import asyncio
import json
from typing import Any
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.modules.activities.repository import (
    ActivityRepositoryNotFoundError,
    ActivityRepositoryUnavailableError,
    SupabaseActivityRepository,
)


@pytest.mark.parametrize(
    "method", ["create", "get", "list", "match", "complete", "revise"]
)
@pytest.mark.parametrize("versioned", [False, True])
def test_all_activity_consumers_opt_in_only_after_owner_operation(
    method: str, versioned: bool
) -> None:
    activity, athlete, auth = uuid4(), uuid4(), uuid4()
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("resolve_legacy_auth_user_id"):
            return httpx.Response(200, json=str(auth))
        if request.url.path.endswith("get_activity_presentation_v2"):
            assert json.loads(request.content) == {"p_activity_id": str(activity)}
            assert request.headers["apikey"] == "sb_secret_local"
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"session_rpe_version": "2"})
        return httpx.Response(
            200,
            json=[{"id": str(activity)}] if method == "list" else {"id": str(activity)},
        )

    async def exercise() -> Any:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            repo = SupabaseActivityRepository(
                Settings(
                    environment="test",
                    _env_file=None,
                    realized_v2_storage_ready=versioned,
                    supabase_publishable_key="public",
                    supabase_secret_key="sb_secret_local",
                ),
                client=client,
            )
            if method == "create":
                return await repo.create_activity(
                    "caller", uuid4(), "f" * 64, {"discipline": "run"}
                )
            if method == "get":
                return await repo.fetch_activity("caller", activity)
            if method == "list":
                return (await repo.list_activities("caller", pending_rpe=False))[0]
            if method == "match":
                return await repo.confirm_planned_workout_match(
                    "caller", activity, uuid4()
                )
            if method == "complete":
                return await repo.complete_activity_rpe(athlete, activity, {})
            return await repo.revise_activity_rpe(athlete, activity, {})

    value = asyncio.run(exercise())
    assert value == {
        "id": str(activity),
        **({"session_rpe_version": "2"} if versioned else {}),
    }
    assert sum(
        r.url.path.endswith("get_activity_presentation_v2") for r in calls
    ) == int(versioned)


def test_foreign_activity_never_reaches_privileged_metadata() -> None:
    calls: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(404, json={"code": "P0002"})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            repo = SupabaseActivityRepository(
                Settings(
                    environment="test", _env_file=None, realized_v2_storage_ready=True
                ),
                client=client,
            )
            with pytest.raises(ActivityRepositoryNotFoundError):
                await repo.fetch_activity("caller", uuid4())

    asyncio.run(exercise())
    assert len(calls) == 1 and calls[0].endswith("get_activity")


@pytest.mark.parametrize(
    "metadata",
    [
        {"session_rpe_version": "3"},
        {"session_rpe_version": {}},
        {"session_rpe_version": "2", "planned_tss": 123},
        {},
    ],
)
def test_metadata_contract_is_closed(metadata: dict[str, Any]) -> None:
    async def exercise() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=metadata))
        ) as client:
            repo = SupabaseActivityRepository(
                Settings(
                    environment="test", _env_file=None, realized_v2_storage_ready=True
                ),
                client=client,
            )
            with pytest.raises(ActivityRepositoryUnavailableError):
                await repo._presentation({"id": str(uuid4())})

    asyncio.run(exercise())
