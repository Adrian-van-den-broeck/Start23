"""Previously incomplete TEST_ONLY requests through real transport and workers."""

import asyncio
import os
from dataclasses import replace
from multiprocessing import Manager
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import _headers
from test_v6_selection_http import assert_private_free, v6_client  # noqa: F401

from app.modules.planning.execution import (
    PlanningComputation,
    PlanningComputationUnavailableError,
)
from app.modules.planning.v6_selection import V6Plan, build_v6_plan
from benchmarks.v6_exact_search import inputs


@pytest.mark.parametrize(
    "label",
    (
        "base_221_300",
        "base_222_200",
        "normal_baseline_105min",
    ),
)
def test_previously_incomplete_request_is_pending_and_separately_confirmed(
    v6_client: TestClient,  # noqa: F811
    label: str,
) -> None:
    app = cast(FastAPI, v6_client.app)
    repo = app.state.planning_repository
    values = inputs(label)
    if label == "normal_baseline_105min":
        for request in repo._requests.values():
            for row in request["input_snapshot"]["training_history"]:
                row["previous_month_weekly_minutes"] = "105"
    app.state.v6_controls = replace(
        values["controls"], athlete_scope=repo._token_owners["athlete-a"]
    )
    payload = {
        "week_start": "2026-10-26",
        "available_dates": [d.isoformat() for d in values["available_dates"]],
    }
    response = v6_client.post(
        "/api/v1/weekly-plans/proposals", json=payload, headers=_headers()
    )
    assert response.status_code == 201, response.text
    created = response.json()
    pending = created["plan"]
    assert len(pending["workouts"]) == (6 if label == "base_222_200" else 5)
    assert pending["revision_state"] == "pending_approval"
    assert pending["active_revision"] is None
    retry = v6_client.post(
        "/api/v1/weekly-plans/proposals", json=payload, headers=_headers()
    )
    assert retry.json() == created
    foreign = v6_client.get(
        "/api/v1/weekly-plans/" + pending["id"], headers=_headers("athlete-b")
    )
    assert foreign.status_code == 404
    calendar = v6_client.get(
        "/api/v1/calendar?from=2026-10-26&to=2026-11-02", headers=_headers()
    )
    assert calendar.json()["workouts"] == []
    confirmed = v6_client.post(
        "/api/v1/change-proposals/" + created["proposal"]["id"] + "/approve",
        json={"expected_base_revision": 0},
        headers=_headers(),
    )
    assert confirmed.status_code == 200, confirmed.text
    active = v6_client.get(
        "/api/v1/weekly-plans/" + pending["id"], headers=_headers()
    ).json()
    assert active["revision_state"] == "active"
    assert_private_free(created)
    assert_private_free(active)


def held_v6_result(started: Any, release: Any, parent_pid: int) -> V6Plan:
    assert os.getpid() != parent_pid
    result = build_v6_plan(**inputs("base_221_300"))
    started.set()
    assert release.wait(20), "TEST_ONLY worker barrier was not released"
    return result


def test_optimized_worker_keeps_admission_and_cancelled_owner_capacity() -> None:
    async def verify() -> None:
        executor = PlanningComputation()
        manager = Manager()
        started, release = manager.Event(), manager.Event()
        try:
            first = asyncio.create_task(
                executor.run(held_v6_result, started, release, os.getpid())
            )
            assert await asyncio.to_thread(started.wait, 20)
            second = asyncio.create_task(
                executor.run(build_v6_plan, **inputs("base_222_200"))
            )
            await asyncio.sleep(0)
            with pytest.raises(PlanningComputationUnavailableError):
                await executor.run(build_v6_plan, **inputs("base_221_300"))
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert executor._pending == 2
            second.cancel()
            with pytest.raises(asyncio.CancelledError):
                await second
            assert executor._pending == 1
            release.set()

            async def drain() -> None:
                while executor._pending:
                    await asyncio.sleep(0)

            await asyncio.wait_for(drain(), 10)
            result = await executor.run(build_v6_plan, **inputs("base_222_200"))
            assert len(result.workouts) == 6
        finally:
            release.set()
            await executor.aclose()
            manager.shutdown()

    asyncio.run(verify())
