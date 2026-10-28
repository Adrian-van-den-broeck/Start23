"""Actual authenticated transport/service integration and bounded CPU ownership."""

import asyncio
import os
from decimal import getcontext, localcontext
from functools import partial
from multiprocessing import Manager
from typing import Any, cast
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import _availability_payload, planning_client  # noqa: F401

from app.modules.planning import service
from app.modules.planning.domain import PlanningConstraintError, build_weekly_plan
from app.modules.planning.execution import (
    PlanningComputation,
    PlanningComputationUnavailableError,
)


def controlled_build(started: Any, release: Any, parent_pid: int, **kwargs: Any) -> Any:
    assert os.getpid() != parent_pid
    started.set()
    assert release.wait(20), "Test did not release the pure CPU job"
    return build_weekly_plan(**kwargs)


def precision() -> int:
    return getcontext().prec


def controlled_precision(started: Any, release: Any) -> int:
    started.set()
    assert release.wait(20)
    return precision()


def fail_closed() -> None:
    raise PlanningConstraintError(
        "catalog_capacity_unsatisfied",
        "No safe workout combination fits the current week.",
    )


def test_authenticated_read_does_not_wait_for_planning_worker(
    planning_client: TestClient,  # noqa: F811
) -> None:
    async def verify() -> None:
        manager = Manager()
        started, release = manager.Event(), manager.Event()
        controlled = partial(controlled_build, started, release, os.getpid())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=planning_client.app),
            base_url="http://test",
        ) as client:
            with patch.object(service, "build_weekly_plan", controlled):
                task = asyncio.create_task(
                    client.post(
                        "/api/v1/weekly-plans/proposals",
                        headers={"Authorization": "Bearer athlete-a"},
                        json={
                            "week_start": "2026-08-03",
                            "available_dates": _availability_payload(),
                            "confirmed_injuries": [],
                        },
                    )
                )
                try:
                    assert await asyncio.to_thread(started.wait, 20)
                    response = await asyncio.wait_for(
                        client.get(
                            "/api/v1/calendar?from=2026-08-03&to=2026-08-10",
                            headers={"Authorization": "Bearer athlete-b"},
                        ),
                        10,
                    )
                    assert response.status_code == 200
                    assert response.json()["workouts"] == []
                    assert not task.done()
                finally:
                    release.set()
                assert (await task).status_code == 201

    asyncio.run(verify())


def test_cancelled_owner_cannot_persist_late_result(
    planning_client: TestClient,  # noqa: F811
) -> None:
    async def verify() -> None:
        manager = Manager()
        started, release = manager.Event(), manager.Event()
        app = cast(FastAPI, planning_client.app)
        controlled = partial(controlled_build, started, release, os.getpid())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=planning_client.app),
            base_url="http://test",
        ) as client:
            with patch.object(service, "build_weekly_plan", controlled):
                task = asyncio.create_task(
                    client.post(
                        "/api/v1/weekly-plans/proposals",
                        headers={"Authorization": "Bearer athlete-a"},
                        json={
                            "week_start": "2026-08-03",
                            "available_dates": _availability_payload(),
                            "confirmed_injuries": [],
                        },
                    )
                )
                try:
                    assert await asyncio.to_thread(started.wait, 20)
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    assert app.state.planning_repository._plans == {}
                    assert app.state.planning_computation._pending == 1
                finally:
                    release.set()

                async def drained() -> None:
                    while app.state.planning_computation._pending:
                        await asyncio.sleep(0)

                await asyncio.wait_for(drained(), 10)
                assert app.state.planning_repository._plans == {}

    asyncio.run(verify())


def test_bounded_admission_cancellation_and_decimal_context() -> None:
    async def verify() -> None:
        executor = PlanningComputation()
        manager = Manager()
        started, release = manager.Event(), manager.Event()
        controlled = partial(controlled_precision, started, release)
        try:
            with localcontext() as context:
                context.prec = 42
                first = asyncio.create_task(executor.run(controlled))
                assert await asyncio.to_thread(started.wait, 20)
                queued = asyncio.create_task(executor.run(precision))
                await asyncio.sleep(0)
                try:
                    await executor.run(precision)
                except PlanningComputationUnavailableError:
                    pass
                else:
                    raise AssertionError("Unbounded planning admission")
                queued.cancel()
                try:
                    await queued
                except asyncio.CancelledError:
                    pass
                release.set()
                assert await first == 42
            assert await executor.run(precision) == getcontext().prec
        finally:
            release.set()
            await executor.aclose()
        try:
            await executor.run(precision)
        except PlanningComputationUnavailableError:
            pass
        else:
            raise AssertionError("Closed worker admitted a calculation")

    asyncio.run(verify())


def test_fail_closed_code_survives_process_serialization() -> None:
    async def verify() -> None:
        executor = PlanningComputation()
        try:
            try:
                await executor.run(fail_closed)
            except PlanningConstraintError as error:
                assert error.code == "catalog_capacity_unsatisfied"
                assert (
                    str(error) == "No safe workout combination fits the current week."
                )
            else:
                raise AssertionError("Fail-closed calculation was accepted")
            assert await executor.run(precision) == getcontext().prec
        finally:
            await executor.aclose()

    asyncio.run(verify())
