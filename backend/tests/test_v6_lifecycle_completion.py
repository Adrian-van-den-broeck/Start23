"""Real routes/selector with synthetic storage; SQL proof is a separate runner."""

from copy import deepcopy
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import _headers
from test_v6_selection_http import assert_private_free
from test_v6_selection_http import v6_client as v6_client
from v6_repository_fixture import V6MemoryRepository


def confirmed(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers(),
        json={
            "week_start": "2026-10-26",
            "available_dates": [
                "2026-10-26",
                "2026-10-27",
                "2026-10-28",
                "2026-10-29",
                "2026-10-30",
                "2026-10-31",
                "2026-11-01",
            ],
        },
    )
    assert response.status_code == 201, response.text
    plan = response.json()["plan"]
    assert (
        client.post(
            "/api/v1/change-proposals/" + plan["proposal"]["id"] + "/approve",
            headers=_headers(),
            json={"expected_base_revision": 0},
        ).status_code
        == 200
    )
    return client.get("/api/v1/weekly-plans/" + plan["id"], headers=_headers()).json()  # type: ignore[no-any-return]


def test_confirmed_move_replay_source_and_history(v6_client: TestClient) -> None:  # noqa: F811
    plan = confirmed(v6_client)
    assert isinstance(plan["workouts"], list)
    workout = next(w for w in plan["workouts"] if w["discipline"] == "bike")
    url = "/api/v1/planned-workouts/" + workout["physical_workout_id"]
    body = {"expected_revision": 1, "scheduled_date": "2026-11-01"}
    first = v6_client.patch(url, headers=_headers(), json=body)
    assert first.status_code == 200, first.text
    moved = first.json()
    assert moved["revision"] == 2 and moved["active_revision"] == 2
    assert v6_client.patch(url, headers=_headers(), json=body).json() == moved
    assert (
        v6_client.patch(url, headers=_headers("athlete-b"), json=body).status_code
        == 404
    )
    assert_private_free(moved)
    for previous in plan["workouts"]:
        current = next(w for w in moved["workouts"] if w["id"] == previous["id"])
        assert current["physical_workout_id"] != previous["physical_workout_id"]
        assert {
            k: v
            for k, v in current.items()
            if k not in {"physical_workout_id", "scheduled_date"}
        } == {
            k: v
            for k, v in previous.items()
            if k not in {"physical_workout_id", "scheduled_date"}
        }
    historical = v6_client.get(
        "/api/v1/weekly-plans/" + str(plan["id"]) + "?revision=1", headers=_headers()
    ).json()
    assert historical == plan


@pytest.mark.parametrize(
    "change", ["stale", "outside_week", "unavailable", "completed", "foreign"]
)
def test_confirmed_move_rejects_without_mutation(
    v6_client: TestClient, change: str
) -> None:  # noqa: F811
    plan = confirmed(v6_client)
    repo = cast(
        V6MemoryRepository, cast(FastAPI, v6_client.app).state.planning_repository
    )
    pid = UUID(str(plan["id"]))
    assert isinstance(plan["workouts"], list)
    workout = plan["workouts"][0]
    body = {
        "expected_revision": 2 if change == "stale" else 1,
        "scheduled_date": "2026-11-02" if change == "outside_week" else "2026-11-01",
    }
    if change == "unavailable":
        repo._plans[pid]["available_dates"].remove("2026-11-01")
    if change == "completed":
        repo._plans[pid]["workouts"][0]["status"] = "completed"
    before = deepcopy(repo._plans)
    response = v6_client.patch(
        "/api/v1/planned-workouts/" + workout["physical_workout_id"],
        headers=_headers("athlete-b" if change == "foreign" else "athlete-a"),
        json=body,
    )
    assert response.status_code == (404 if change == "foreign" else 409), response.text
    assert before == repo._plans
    assert repo.edit_results == {}


def test_confirmed_move_rejects_high_spacing(v6_client: TestClient) -> None:
    """Approved source sessions; existing synthetic budget, no new rule constants."""
    import asyncio
    from datetime import date, timedelta
    from decimal import Decimal

    from test_v6_automatic_selection import plan as make_plan

    from app.modules.physiology.models import Discipline, InternalLoad
    from app.modules.planning.domain import PlanningTarget, PlanningTargetBasis
    from app.modules.planning.v6_selection import V6Controls
    from app.modules.planning.v6_service import V6PlanningService
    from app.modules.workouts.catalog import TrainingPhase

    app = cast(FastAPI, v6_client.app)
    repo = cast(V6MemoryRepository, app.state.planning_repository)
    controls = V6Controls(
        authorized_target=PlanningTarget(
            TrainingPhase.BASE,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            InternalLoad(Decimal(400)),
        )
    )
    app.state.v6_controls = controls
    lookup = {t.source_workout_id: t for t in repo.catalog.values()}
    start = date(2026, 10, 26)
    dates = tuple(start + timedelta(days=n) for n in range(7))
    draft = make_plan(
        tuple(repo.catalog.values()),
        controls=controls,
        available_dates=dates,
        selected_template_ids=tuple(
            lookup[n].id for n in ("TR-RUN-018", "TR-RUN-018", "TR-RUN-016")
        ),
    )
    owner = repo._owner("athlete-a")
    source = repo._requests[owner]
    payload = V6PlanningService._proposal_payload(
        request_id=UUID(source["id"]),
        input_fingerprint=source["input_fingerprint"],
        generation_fingerprint="TEST_ONLY:confirmed-high-spacing",
        plan_id=None,
        expected_base_revision=0,
        week_start=start,
        timezone_name="UTC",
        available_dates=dates,
        availability_source="explicit",
        injuries=frozenset(),
        low_only_disciplines=frozenset(),
        goal_disciplines=frozenset(Discipline),
        draft=draft,
        workout_source="auto_planned",
    )
    result = asyncio.run(repo.create_plan_proposal(owner, payload))
    v6_client.post(
        "/api/v1/change-proposals/" + result["proposal_id"] + "/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    plan = v6_client.get(
        "/api/v1/weekly-plans/" + result["plan_id"], headers=_headers()
    ).json()
    highs = [w for w in plan["workouts"] if w["intensity_bucket"] == "high"]
    assert len(highs) == 2
    before = deepcopy(repo._plans)
    response = v6_client.patch(
        "/api/v1/planned-workouts/" + highs[0]["physical_workout_id"],
        headers=_headers(),
        json={"expected_revision": 1, "scheduled_date": highs[1]["scheduled_date"]},
    )
    assert response.status_code == 409, response.text
    assert repo._plans == before
