"""A5 orchestration recovery; PostgreSQL proof lives in the SQL suite."""

import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import _create_proposal
from test_planning import planning_client as planning_client

from app.core.config import Settings
from app.modules.checkins.repository import (
    CheckInRepository,
    CheckInRepositoryConflictError,
    CheckInRepositoryNotFoundError,
    CheckInRepositoryUnavailableError,
    SupabaseCheckInRepository,
)
from app.modules.checkins.service import CheckInService
from app.modules.coach.context import DisabledCheckInContextCoach
from app.modules.planning.repository import PlanningRepositoryUnavailableError
from app.modules.planning.schemas import WeeklyPlanProposalResponse
from app.modules.planning.service import PlanningService


def test_committed_attachment_is_replayed_before_open_context(
    planning_client: TestClient,
) -> None:
    expected = _create_proposal(planning_client)
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = expected
    repository.fetch_planning_context.side_effect = CheckInRepositoryConflictError(
        "checkin_not_confirmed"
    )
    planner = AsyncMock()
    service = CheckInService(
        cast(CheckInRepository, repository),
        cast(PlanningService, planner),
        DisabledCheckInContextCoach(),
    )
    checkin_id, athlete_id = uuid4(), uuid4()
    for _ in range(3):
        result = asyncio.run(
            service.generate_plan_proposal("athlete-a", athlete_id, checkin_id)
        )
        assert result.model_dump(mode="json") == expected
    planner.generate_checkin_proposal.assert_not_awaited()
    repository.fetch_planning_context.assert_not_awaited()
    repository.attach_plan_proposal.assert_not_awaited()


@pytest.mark.parametrize(
    "state,revision_state",
    [
        ("pending", "pending_approval"),
        ("applied", "active"),
        ("rejected", "rejected"),
        ("expired", "expired"),
        ("applied", "superseded"),
    ],
)
def test_create_replays_current_state(
    planning_client: TestClient, state: str, revision_state: str
) -> None:
    expected = _create_proposal(planning_client)
    expected["proposal"]["state"] = state
    expected["plan"]["proposal"]["state"] = state
    expected["plan"]["revision_state"] = revision_state
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = expected
    cast(FastAPI, planning_client.app).state.checkin_repository = repository
    for _ in range(3):
        response = planning_client.post(
            f"/api/v1/checkins/{uuid4()}/plan-proposals",
            headers={"Authorization": "Bearer athlete-a"},
        )
        assert response.status_code == 200, response.text
        assert response.json() == expected
    repository.fetch_planning_context.assert_not_awaited()
    repository.attach_plan_proposal.assert_not_awaited()


def test_commit_race_before_open_guard_is_recovered(
    planning_client: TestClient,
) -> None:
    expected = _create_proposal(planning_client)
    repository = AsyncMock()
    repository.fetch_attached_proposal.side_effect = [None, expected]
    repository.fetch_planning_context.side_effect = CheckInRepositoryConflictError(
        "checkin_not_confirmed"
    )
    planner = AsyncMock()
    service = CheckInService(repository, planner, DisabledCheckInContextCoach())
    result = asyncio.run(service.generate_plan_proposal("athlete-a", uuid4(), uuid4()))
    assert result.model_dump(mode="json") == expected
    planner.generate_checkin_proposal.assert_not_awaited()


@pytest.mark.parametrize(
    "failure,status,code",
    [
        (CheckInRepositoryNotFoundError(), 404, None),
        (
            CheckInRepositoryConflictError("checkin_proposal_unrecoverable"),
            409,
            "checkin_proposal_unrecoverable",
        ),
        (
            CheckInRepositoryConflictError("checkin_context_stale"),
            409,
            "checkin_context_stale",
        ),
        (CheckInRepositoryUnavailableError("private dependency detail"), 503, None),
    ],
)
def test_recovery_errors_never_generate(
    planning_client: TestClient, failure: Exception, status: int, code: str | None
) -> None:
    repository = AsyncMock()
    repository.fetch_attached_proposal.side_effect = failure
    cast(FastAPI, planning_client.app).state.checkin_repository = repository
    response = planning_client.post(
        f"/api/v1/checkins/{uuid4()}/plan-proposals",
        headers={"Authorization": "Bearer athlete-b"},
    )
    assert response.status_code == status
    assert "private dependency" not in response.text
    if code:
        assert response.json()["error"]["code"] == code
    repository.fetch_planning_context.assert_not_awaited()


def test_invalid_id_does_not_read(planning_client: TestClient) -> None:
    repository = AsyncMock()
    cast(FastAPI, planning_client.app).state.checkin_repository = repository
    response = planning_client.post(
        "/api/v1/checkins/invalid/plan-proposals",
        headers={"Authorization": "Bearer athlete-a"},
    )
    assert response.status_code == 422
    repository.fetch_attached_proposal.assert_not_awaited()


@pytest.mark.parametrize("lost_response", [False, True])
def test_generation_commit_response_loss_and_process_retry(
    planning_client: TestClient, lost_response: bool
) -> None:
    expected = _create_proposal(planning_client)
    repository = AsyncMock()
    persisted: dict[str, Any] | None = None

    async def read(*args: object) -> dict[str, Any] | None:
        return persisted

    async def attach(*args: object) -> dict[str, Any]:
        nonlocal persisted
        persisted = expected
        if lost_response:
            raise CheckInRepositoryUnavailableError
        return {"status": "completed"}

    repository.fetch_attached_proposal.side_effect = read
    repository.fetch_planning_context.return_value = {
        "week_start": "2026-08-03",
        "timezone": "Europe/Amsterdam",
        "confirmed_context": {"restrictions": []},
    }
    repository.attach_plan_proposal.side_effect = attach
    planner = AsyncMock()
    planner.generate_checkin_proposal.return_value = (
        WeeklyPlanProposalResponse.model_validate(expected)
    )
    service = CheckInService(repository, planner, DisabledCheckInContextCoach())
    athlete_id, checkin_id = uuid4(), uuid4()
    if lost_response:
        with pytest.raises(CheckInRepositoryUnavailableError):
            asyncio.run(
                service.generate_plan_proposal("athlete-a", athlete_id, checkin_id)
            )
    else:
        assert (
            asyncio.run(
                service.generate_plan_proposal("athlete-a", athlete_id, checkin_id)
            ).model_dump(mode="json")
            == expected
        )
    assert persisted == expected
    restarted = CheckInService(repository, planner, DisabledCheckInContextCoach())
    for _ in range(3):
        assert (
            asyncio.run(
                restarted.generate_plan_proposal("athlete-a", athlete_id, checkin_id)
            ).model_dump(mode="json")
            == expected
        )
    planner.generate_checkin_proposal.assert_awaited_once()
    repository.attach_plan_proposal.assert_awaited_once()


@pytest.mark.parametrize(
    "body,status,error",
    [
        (None, 200, None),
        ({"plan": {}, "proposal": {}}, 200, None),
        ({"code": "P0002"}, 404, CheckInRepositoryNotFoundError),
        (
            {"code": "PT409", "message": "check-in proposal is not recoverable"},
            409,
            CheckInRepositoryConflictError,
        ),
        ({"message": "private internals"}, 500, CheckInRepositoryUnavailableError),
        ([], 200, CheckInRepositoryUnavailableError),
    ],
)
def test_repository_owner_token_and_checkin_locator(
    body: Any, status: int, error: type[Exception] | None
) -> None:
    import json

    checkin_id = uuid4()

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/v1/rpc/get_checkin_plan_proposal"
        assert request.headers["Authorization"] == "Bearer caller-token"
        assert request.headers["apikey"] == "public-key"
        assert json.loads(request.content) == {"p_checkin_id": str(checkin_id)}
        return httpx.Response(status, json=body)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            repository = SupabaseCheckInRepository(
                Settings(
                    environment="test",
                    supabase_url="https://example.supabase.co",
                    supabase_publishable_key="public-key",
                ),
                client=client,
            )
            if error:
                with pytest.raises(error):
                    await repository.fetch_attached_proposal("caller-token", checkin_id)
            else:
                assert (
                    await repository.fetch_attached_proposal("caller-token", checkin_id)
                    == body
                )

    asyncio.run(run())


@pytest.mark.parametrize("stage", ["context", "generation"])
def test_database_failure_before_attachment_leaves_no_attachment(stage: str) -> None:
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = None
    repository.fetch_planning_context.return_value = {
        "week_start": "2026-08-03",
        "timezone": "Europe/Amsterdam",
        "confirmed_context": {"restrictions": []},
    }
    planner = AsyncMock()
    failure = (
        CheckInRepositoryUnavailableError()
        if stage == "context"
        else PlanningRepositoryUnavailableError()
    )
    if stage == "context":
        repository.fetch_planning_context.side_effect = failure
    else:
        planner.generate_checkin_proposal.side_effect = failure
    service = CheckInService(repository, planner, DisabledCheckInContextCoach())
    with pytest.raises(type(failure)):
        asyncio.run(service.generate_plan_proposal("athlete-a", uuid4(), uuid4()))
    repository.attach_plan_proposal.assert_not_awaited()


def test_concurrent_replays_never_generate(planning_client: TestClient) -> None:
    expected = _create_proposal(planning_client)
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = expected
    planner = AsyncMock()
    service = CheckInService(repository, planner, DisabledCheckInContextCoach())
    athlete_id, checkin_id = uuid4(), uuid4()

    async def run() -> None:
        results = await asyncio.gather(
            *(
                service.generate_plan_proposal("athlete-a", athlete_id, checkin_id)
                for _ in range(10)
            )
        )
        assert all(result.model_dump(mode="json") == expected for result in results)

    asyncio.run(run())
    planner.generate_checkin_proposal.assert_not_awaited()
    repository.attach_plan_proposal.assert_not_awaited()


def test_unconfirmed_open_context_does_not_generate() -> None:
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = None
    repository.fetch_planning_context.side_effect = CheckInRepositoryConflictError(
        "checkin_context_stale"
    )
    planner = AsyncMock()
    service = CheckInService(repository, planner, DisabledCheckInContextCoach())
    with pytest.raises(CheckInRepositoryConflictError, match="checkin_context_stale"):
        asyncio.run(service.generate_plan_proposal("athlete-a", uuid4(), uuid4()))
    planner.generate_checkin_proposal.assert_not_awaited()


def test_planning_dependency_failure_maps_to_safe_503(
    planning_client: TestClient,
) -> None:
    from unittest.mock import patch

    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = None
    repository.fetch_planning_context.return_value = {
        "week_start": "2026-08-03",
        "timezone": "Europe/Amsterdam",
        "confirmed_context": {"restrictions": []},
    }
    cast(FastAPI, planning_client.app).state.checkin_repository = repository
    with patch.object(
        PlanningService,
        "generate_checkin_proposal",
        side_effect=PlanningRepositoryUnavailableError("private internals"),
    ):
        response = planning_client.post(
            f"/api/v1/checkins/{uuid4()}/plan-proposals",
            headers={"Authorization": "Bearer athlete-a"},
        )
    assert response.status_code == 503
    assert "private internals" not in response.text
    repository.attach_plan_proposal.assert_not_awaited()


def test_invalid_persisted_projection_never_exposes_raw_payload(
    planning_client: TestClient,
) -> None:
    repository = AsyncMock()
    repository.fetch_attached_proposal.return_value = {
        "plan": {"private_internal": "do not disclose"},
        "proposal": {},
    }
    cast(FastAPI, planning_client.app).state.checkin_repository = repository
    response = planning_client.post(
        f"/api/v1/checkins/{uuid4()}/plan-proposals",
        headers={"Authorization": "Bearer athlete-a"},
    )
    assert response.status_code == 503
    assert "do not disclose" not in response.text
    assert "private_internal" not in response.text
    repository.fetch_planning_context.assert_not_awaited()
