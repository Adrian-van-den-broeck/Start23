"""Private real spawned-worker / ASGI HTTP measurements; TEST_ONLY controls.

--source-root selects a read-only extracted accepted Git archive, including in
spawned children. It never installs reference code into a live application.
"""

# ruff: noqa: E402
import argparse
import asyncio
import json
import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import UUID

if "--source-root" in sys.argv:
    reference_root = Path(sys.argv[sys.argv.index("--source-root") + 1]).resolve()
    sys.path.insert(0, str(reference_root / "backend"))
else:
    reference_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(reference_root / "backend/tests"))

from fastapi.testclient import TestClient
from test_planning import PlanningTokenVerifier, ZoneRejectStub
from v6_repository_fixture import V6MemoryRepository

from app.core.config import Settings
from app.local_v6 import install_local_v6
from app.main import create_app
from app.modules.planning.execution import PlanningComputation
from app.modules.planning.v6_service import InactiveV6CatalogProvider
from app.modules.workouts.joren_v6_official import official_catalog
from benchmarks.v6_exact_search import inputs, measure, peak_memory

LABELS = ("base_221_300", "base_222_200", "normal_baseline_105min")


async def worker_measure(label: str, warm: bool) -> dict[str, Any]:
    executor = PlanningComputation()
    try:
        if warm:
            await executor.run(measure, label, False, False)
        began = perf_counter()
        result = await executor.run(measure, label, True, False)
        result["worker_roundtrip_seconds"] = perf_counter() - began
        return result
    finally:
        await executor.aclose()


def http_measure(label: str, warm: bool) -> dict[str, Any]:
    owners = {"athlete-a": UUID(int=1), "athlete-b": UUID(int=2)}
    repository = V6MemoryRepository(owners, official_catalog())
    if label == "normal_baseline_105min":
        for request in repository._requests.values():
            for row in request["input_snapshot"]["training_history"]:
                row["previous_month_weekly_minutes"] = "105"
    provider = InactiveV6CatalogProvider()
    app = create_app(
        Settings(
            environment="test", supabase_url="http://127.0.0.1:55514", _env_file=None
        ),
        access_token_verifier=PlanningTokenVerifier(owners),
        onboarding_repository=ZoneRejectStub(),  # type: ignore[arg-type]
        planning_repository=repository,
        planning_catalog_provider=provider,
    )
    install_local_v6(app, repository, provider)
    values = inputs(label)
    app.state.v6_controls = replace(
        values["controls"], athlete_scope=owners["athlete-a"]
    )
    payload = {
        "week_start": "2026-10-26",
        "available_dates": [
            (date(2026, 10, 26) + timedelta(days=i)).isoformat() for i in range(7)
        ],
        "confirmed_injuries": [],
    }
    with TestClient(app) as client:
        assert client.portal is not None
        if warm:
            # Prepare the actual process without warming/replaying this request.
            client.portal.call(
                app.state.planning_computation.run,
                measure,
                "base_221_100",
                False,
                False,
            )
        began = perf_counter()
        response = client.post(
            "/api/v1/weekly-plans/proposals",
            json=payload,
            headers={"Authorization": "Bearer athlete-a"},
        )
        elapsed = perf_counter() - began
        body = response.json()
        outcome = "pending" if response.status_code == 201 else body
        if response.status_code != 201:
            assert not repository._plans
        worker_peak = client.portal.call(
            app.state.planning_computation.run, peak_memory
        )
        return {
            "case": label,
            "warm": warm,
            "http_status": response.status_code,
            "wall_seconds": elapsed,
            "outcome": outcome,
            "workouts": body.get("plan", {}).get("workouts", []),
            "worker_peak_working_set_bytes": worker_peak,
            "parent_peak_working_set_bytes": peak_memory(),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for label in LABELS:
        for warm in (False, True):
            worker = asyncio.run(worker_measure(label, warm))
            http = http_measure(label, warm)
            records.append({"worker": worker, "http": http})
            args.output.write_text(
                json.dumps(records, indent=2) + "\n", encoding="utf-8"
            )
            print(label, warm, worker["outcome"], http["http_status"], flush=True)


if __name__ == "__main__":
    main()
