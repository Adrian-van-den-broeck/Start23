"""Local authenticated ASGI head-of-line measurement using synthetic repositories."""

import argparse
import asyncio
import json
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import httpx
from fastapi import FastAPI

from benchmarks.planning import ROOT, START, full_catalog

sys.path.insert(0, str(ROOT / "tests"))
from test_planning import (  # noqa: E402
    MemoryPlanningRepository,
    PlanningTokenVerifier,
    ZoneRejectStub,
)

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.modules.workouts.catalog import WorkoutTemplate  # noqa: E402


class Catalog:
    def __init__(self) -> None:
        self.ready: asyncio.Future[float] = asyncio.get_running_loop().create_future()

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        catalog = full_catalog()
        if not self.ready.done():
            self.ready.set_result(time.perf_counter())
        return catalog

    async def aclose(self) -> None:
        pass


async def measure(concurrent: int, operation: str) -> dict[str, Any]:
    owners = {f"athlete-{index}": UUID(int=index + 1) for index in range(concurrent)}
    repo = MemoryPlanningRepository(owners)
    for row in repo._requests.values():
        snapshot = row["input_snapshot"]
        snapshot["goal"]["race_date"] = "2027-03-15"
        snapshot["goal"]["target_date"] = "2027-03-15"
        for entry, minutes in zip(
            snapshot["training_history"], (120, 300, 180), strict=True
        ):
            entry["previous_month_weekly_minutes"] = minutes
    catalog = Catalog()
    app = create_app(
        Settings(environment="test"),
        access_token_verifier=PlanningTokenVerifier(owners),
        onboarding_repository=ZoneRejectStub(),  # type: ignore[arg-type]
        planning_repository=repo,
        planning_catalog_provider=catalog,
    )

    async def fixture_catalog(_self: object) -> tuple[WorkoutTemplate, ...]:
        return full_catalog()

    with patch("test_planning.StaticCatalogProvider.fetch_catalog", fixture_catalog):
        return await requests(app, concurrent, catalog, operation)


async def requests(
    app: FastAPI, concurrent: int, catalog: Catalog, operation: str
) -> dict[str, Any]:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://benchmark"
        ) as client:
            start = time.perf_counter()

            async def planning(index: int) -> dict[str, int | float]:
                response = await client.post(
                    "/api/v1/weekly-plans/"
                    + ("swipe-drafts" if operation == "swipe" else "proposals"),
                    headers={"Authorization": f"Bearer athlete-{index}"},
                    json={
                        "week_start": START.isoformat(),
                        "available_dates": [
                            (START + timedelta(days=day)).isoformat()
                            for day in range(7)
                        ],
                        "confirmed_injuries": [],
                    },
                )
                return {
                    "status": response.status_code,
                    "seconds": time.perf_counter() - start,
                }

            tasks = [
                asyncio.create_task(planning(index)) for index in range(concurrent)
            ]
            # Include scheduler delay: starting the stopwatch only after this
            # sleep resumes would hide the very event-loop starvation measured.
            intended_issue = await catalog.ready
            actual_issue = time.perf_counter()
            light = await client.get(
                "/api/v1/calendar?from=2026-10-26&to=2026-11-02",
                headers={"Authorization": "Bearer athlete-0"},
            )
            completed = time.perf_counter()
            return {
                "planning": await asyncio.gather(*tasks),
                "authenticated_read_status": light.status_code,
                "scheduler_delay_seconds": actual_issue - intended_issue,
                "authenticated_read_wait_seconds": completed - intended_issue,
            }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--operation", choices=("proposal", "swipe"), default="proposal"
    )
    parser.add_argument("--counts", type=int, nargs="+", default=[1, 2])
    args = parser.parse_args()
    result = {}
    for count in args.counts:
        result[str(count)] = [
            await measure(count, args.operation) for _ in range(args.runs)
        ]
        print(json.dumps({"concurrent": count, "runs": result[str(count)]}), flush=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
