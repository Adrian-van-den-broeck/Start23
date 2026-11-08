"""Real selector/routes, synthetic ownership/storage. Export public mobile evidence."""

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from test_planning import _headers
from test_v6_selection_http import assert_private_free, create, v6_client  # noqa: F401

from app.modules.planning.v6_service import V6PlanningService
from app.modules.workouts.joren_v6_official import official_catalog


def test_mobile_trace(v6_client: TestClient) -> None:  # noqa: F811
    trace: dict[str, Any] = {}
    draft = create(v6_client, draft=True)
    trace["initial"] = draft
    url = f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"

    def transition(action: str) -> dict[str, Any]:
        candidate = draft["current_candidate"]
        body = {"expected_revision": draft["revision"], "action": action}
        if action in {"accept", "pass"}:
            body.update(
                candidate_template_id=candidate["id"],
                candidate_occurrence_id=candidate["occurrence_id"],
            )
        response = v6_client.post(url + "/transitions", headers=_headers(), json=body)
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]

    original = draft["current_candidate"]["id"]
    draft = transition("pass")
    trace["passed"] = draft
    assert draft["current_candidate"]["id"] != original
    draft = transition("accept")
    trace["accepted"] = draft
    retained = draft["accepted_workouts"][0]
    while draft["state"] == "collecting":
        draft = transition("accept")
    trace["placement"] = draft
    occurrence = retained["occurrence_id"]
    placed = v6_client.put(
        url + f"/placements/{occurrence}",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "scheduled_date": "2026-10-28",
        },
    )
    assert placed.status_code == 200, placed.text
    draft = placed.json()
    draft = transition("undo")
    assert retained in draft["accepted_workouts"]
    assert draft["placements"] == [
        {"occurrence_id": occurrence, "scheduled_date": "2026-10-28"}
    ]
    draft = transition("accept")
    trace["dated"] = draft
    response = v6_client.post(
        url + "/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "automatic",
        },
    )
    assert response.status_code == 201, response.text
    plan = response.json()["plan"]
    trace["pending"] = plan
    calendar_url = "/api/v1/calendar?from=2026-10-26&to=2026-11-02"
    pending_calendar = v6_client.get(calendar_url, headers=_headers())
    assert pending_calendar.status_code == 200, pending_calendar.text
    assert pending_calendar.json()["workouts"] == []
    target = next(w for w in plan["workouts"] if w["id"] != occurrence)
    edit_url = f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/{target['id']}"
    choices = v6_client.get(
        edit_url + "/alternatives",
        headers=_headers(),
        params={"expected_revision": plan["revision"]},
    )
    assert choices.status_code == 200, choices.text
    trace["alternatives"] = choices.json()
    choice = choices.json()["alternatives"][0]
    edited = v6_client.post(
        edit_url + "/edit-proposals",
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "expected_proposal_id": plan["proposal"]["id"],
            "replacement_template_id": choice["id"],
        },
    )
    assert edited.status_code == 201, edited.text
    updated = edited.json()["plan"]
    trace["edited"] = updated
    before = next(w for w in plan["workouts"] if w["id"] == occurrence)
    after = next(w for w in updated["workouts"] if w["id"] == occurrence)
    assert (before["template_id"], before["scheduled_date"]) == (
        after["template_id"],
        after["scheduled_date"],
    )
    assert before["physical_workout_id"] != after["physical_workout_id"]
    stale = v6_client.post(
        edit_url + "/edit-proposals",
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "expected_proposal_id": plan["proposal"]["id"],
            "replacement_template_id": target["template_id"],
        },
    )
    assert stale.status_code in {404, 409}, stale.text
    approval = v6_client.post(
        f"/api/v1/change-proposals/{updated['proposal']['id']}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approval.status_code == 200, approval.text
    trace["approval"] = approval.json()
    active = v6_client.get(f"/api/v1/weekly-plans/{plan['id']}", headers=_headers())
    assert active.status_code == 200, active.text
    trace["active"] = active.json()
    calendar = v6_client.get(calendar_url, headers=_headers())
    assert calendar.status_code == 200, calendar.text
    trace["calendar"] = calendar.json()
    assert {w["id"] for w in trace["calendar"]["workouts"]} == {
        w["id"] for w in updated["workouts"]
    }
    assert trace["active"]["revision_state"] == "active"
    assert_private_free(trace)
    trace["sourceWithWallRest"] = V6PlanningService._deck_item(
        next(
            t
            for t in official_catalog()
            if any(
                e.kind == "stationary_wall_rest"
                for e in t.source_revision.predecessor.events
            )
        )
    ).model_dump(mode="json")
    output = os.environ.get("WOMBO_V6_PUBLIC_TRACE")
    if output:
        Path(output).write_text(
            json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
