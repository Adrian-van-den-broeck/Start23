"""A6 authenticated recovery contracts; transport doubles are not RLS proof."""

import asyncio
from datetime import date, datetime
from typing import Any, cast
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import (
    MemoryPlanningRepository,
    _create_proposal,
    _create_swipe_draft,
    _headers,
)
from test_planning import planning_client as planning_client

from app.core.config import Settings
from app.modules.planning.repository import (
    PlanningRepositoryUnavailableError,
    SupabasePlanningRepository,
)


def _recovery(client: TestClient, token: str = "athlete-a") -> httpx.Response:
    return cast(
        httpx.Response,
        client.get("/api/v1/weekly-plans/recovery", headers=_headers(token)),
    )


def test_reinstall_discovers_exact_pending_without_approving(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    first = _recovery(planning_client)
    assert first.status_code == 200, first.text
    assert first.json() == {"active": None, "pending": created["plan"], "draft": None}
    assert _recovery(planning_client).json() == first.json()
    repository = cast(
        MemoryPlanningRepository,
        cast(FastAPI, planning_client.app).state.planning_repository,
    )
    assert len(repository._plans) == len(repository._proposals) == 1
    assert created["proposal"]["state"] == "pending"


def test_remote_approval_recovers_authoritative_active_revision(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    approved = planning_client.post(
        f"/api/v1/change-proposals/{created['proposal']['id']}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approved.status_code == 200, approved.text
    found = _recovery(planning_client)
    assert found.status_code == 200, found.text
    assert found.json()["pending"] is None
    active = found.json()["active"]
    assert active["id"] == created["plan"]["id"]
    assert active["revision_id"] == created["plan"]["revision_id"]
    assert active["active_revision"] == active["revision"]
    assert active["revision_state"] == "active"


def test_discovery_and_foreign_plan_draft_proposal_reads_are_owner_scoped(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    assert _recovery(planning_client, "athlete-b").json() == {
        "active": None,
        "pending": None,
        "draft": None,
    }
    for path in (
        f"weekly-plans/{created['plan']['id']}",
        f"weekly-plans/swipe-drafts/{uuid4()}",
        f"change-proposals/{created['proposal']['id']}",
    ):
        foreign = planning_client.get(f"/api/v1/{path}", headers=_headers("athlete-b"))
        assert foreign.status_code == 404, foreign.text
        assert created["plan"]["id"] not in foreign.text


def test_client_owner_query_cannot_override_verified_token(
    planning_client: TestClient,
) -> None:
    _create_proposal(planning_client)
    response = planning_client.get(
        f"/api/v1/weekly-plans/recovery?athlete_id={uuid4()}&user_id=athlete-a",
        headers=_headers("athlete-b"),
    )
    assert response.status_code == 200
    assert response.json() == {"active": None, "pending": None, "draft": None}
    assert planning_client.get("/api/v1/weekly-plans/recovery").status_code == 401


@pytest.mark.parametrize("bad", [None, {}, {"active": {"private_load": 19}}])
def test_malformed_discovery_is_safe_unavailability(
    planning_client: TestClient, monkeypatch: pytest.MonkeyPatch, bad: Any
) -> None:
    repository = cast(FastAPI, planning_client.app).state.planning_repository

    async def malformed(*_args: Any) -> Any:
        return bad

    monkeypatch.setattr(repository, "discover_planning", malformed)
    response = _recovery(planning_client)
    assert response.status_code == 503, response.text
    assert "private_load" not in response.text


def test_revision_changes_between_discovery_and_read_fail_closed(
    planning_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = _create_proposal(planning_client)
    repository = cast(FastAPI, planning_client.app).state.planning_repository

    async def changed(*_args: Any) -> dict[str, Any]:
        return {
            "active": None,
            "pending": {
                "plan_id": created["plan"]["id"],
                "id": str(uuid4()),
                "revision_number": created["plan"]["revision"],
            },
            "draft": None,
        }

    monkeypatch.setattr(repository, "discover_planning", changed)
    assert _recovery(planning_client).status_code == 503


def test_recovery_public_contract_is_bounded_and_load_free(
    planning_client: TestClient,
) -> None:
    _create_proposal(planning_client)
    response = _recovery(planning_client)
    assert response.status_code == 200

    def inspect(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert "tss" not in key.lower() and "load" not in key.lower()
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)

    inspect(response.json())
    schema = planning_client.get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/weekly-plans/recovery"]["get"]
    assert not operation.get("requestBody")
    assert "PlanningRecoveryResponse" in str(operation["responses"]["200"])
    assert set(
        schema["components"]["schemas"]["PlanningRecoveryResponse"]["properties"]
    ) == {
        "active",
        "pending",
        "draft",
    }


@pytest.mark.parametrize("has_current", [False, True])
def test_repository_uses_bounded_authenticated_ordered_public_queries(
    has_current: bool,
) -> None:
    athlete_id, plan_id = uuid4(), uuid4()
    requests: list[httpx.Request] = []
    week = date.fromordinal(
        datetime.now(ZoneInfo("Europe/Amsterdam")).date().toordinal()
        - datetime.now(ZoneInfo("Europe/Amsterdam")).date().weekday()
    ).isoformat()

    target = date.fromordinal(date.fromisoformat(week).toordinal() + 7).isoformat()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["authorization"] == "Bearer caller-token"
        assert request.headers["apikey"] == "sb_publishable_test"
        if request.url.path.endswith("get_operational_athlete_profile"):
            return httpx.Response(200, json={"timezone": "Europe/Amsterdam"})
        params = request.url.params
        assert params["internal_athlete_id"] == f"eq.{athlete_id}"
        assert params["limit"] == "1"
        assert "order" in params and "*" not in params["select"]
        assert "tss" not in str(request.url) and "load" not in str(request.url)
        table = request.url.path.rsplit("/", 1)[-1]
        if table == "weekly_plans":
            assert params["state"] == "eq.active"
            if params["week_start"] == f"lte.{target}":
                assert params["order"] == "week_start.desc,id.asc"
                if not has_current:
                    return httpx.Response(200, json=[])
            else:
                assert params["week_start"] == f"gt.{target}"
                assert params["order"] == "week_start.asc,id.asc"
            return httpx.Response(
                200,
                json=[
                    {
                        "id": str(plan_id),
                        "week_start": week,
                        "active_revision": 2,
                        "state": "active",
                    }
                ],
            )
        if table == "plan_revisions":
            assert "!plan_revisions_plan_id_athlete_id_fkey!inner" in params["select"]
            assert params["state"] == "eq.pending_approval"
            assert params["plan.week_start"] == f"gte.{week}"
            assert params["order"] == "plan(week_start).asc,revision_number.desc,id.asc"
        elif table == "swipe_week_drafts":
            assert params["state"] == "in.(collecting,placement)"
            assert params["week_start"] == f"gte.{week}"
        else:
            pytest.fail(f"Unexpected discovery path {table}")
        return httpx.Response(200, json=[])

    async def exercise() -> dict[str, Any]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabasePlanningRepository(
                Settings(
                    environment="test", supabase_publishable_key="sb_publishable_test"
                ),
                client=client,
            )
            return await repository.discover_planning("caller-token", athlete_id)

    result = asyncio.run(exercise())
    assert result["active"]["id"] == str(plan_id)
    assert len(requests) == (4 if has_current else 5)


@pytest.mark.parametrize("payload", [None, {}, "bad", [None], [{}, {}]])
def test_repository_never_interprets_bad_discovery_as_empty(payload: Any) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("get_operational_athlete_profile"):
            return httpx.Response(200, json={"timezone": "Europe/Amsterdam"})
        return httpx.Response(200, json=payload)

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repository = SupabasePlanningRepository(
                Settings(
                    environment="test", supabase_publishable_key="sb_publishable_test"
                ),
                client=client,
            )
            with pytest.raises(PlanningRepositoryUnavailableError):
                await repository.discover_planning("caller-token", UUID(int=1))

    asyncio.run(exercise())


def test_foreign_existing_draft_is_denied_without_details(
    planning_client: TestClient,
) -> None:
    created = _create_swipe_draft(planning_client)
    response = planning_client.get(
        f"/api/v1/weekly-plans/swipe-drafts/{created['id']}",
        headers=_headers("athlete-b"),
    )
    assert response.status_code == 404
    assert created["id"] not in response.text
    assert _recovery(planning_client, "athlete-b").json()["draft"] is None


def test_owned_draft_discovery_retains_exact_identity_and_status(
    planning_client: TestClient,
) -> None:
    created = _create_swipe_draft(planning_client)
    for _ in range(2):
        response = _recovery(planning_client)
        assert response.status_code == 200, response.text
        assert response.json() == {
            "active": None,
            "pending": None,
            "draft": {
                key: created[key] for key in ("id", "revision", "state", "week_start")
            },
        }
