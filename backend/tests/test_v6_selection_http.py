"""Real routes + spawned planning worker + existing state/confirmation contracts."""

from collections.abc import Iterator
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_planning import PlanningTokenVerifier, ZoneRejectStub, _headers
from v6_repository_fixture import V6MemoryRepository

from app.core.config import Settings
from app.local_v6 import install_local_v6
from app.main import create_app
from app.modules.physiology.models import InternalLoad
from app.modules.planning.domain import PlanningTarget, PlanningTargetBasis
from app.modules.planning.v6_selection import V6Controls
from app.modules.planning.v6_service import InactiveV6CatalogProvider, V6PlanningService
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.joren_v6_official import official_catalog


@pytest.fixture
def v6_client() -> Iterator[TestClient]:
    owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
    catalog = official_catalog()
    repository = V6MemoryRepository(owners, catalog)
    provider = InactiveV6CatalogProvider()
    app = create_app(
        Settings(
            environment="test", supabase_url="http://127.0.0.1:55439", _env_file=None
        ),
        access_token_verifier=PlanningTokenVerifier(owners),
        onboarding_repository=ZoneRejectStub(),  # type: ignore[arg-type]
        planning_repository=repository,
        planning_catalog_provider=provider,
    )

    install_local_v6(app, repository, provider)
    with TestClient(app) as client:
        yield client


def create(client: TestClient, draft: bool = False) -> dict[str, Any]:
    response = client.post(
        "/api/v1/weekly-plans/" + ("swipe-drafts" if draft else "proposals"),
        headers=_headers(),
        json={
            "week_start": "2026-10-26",
            "available_dates": ["2026-10-26", "2026-10-28", "2026-10-31"],
            "confirmed_injuries": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def assert_private_free(value: Any) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            assert not any(
                s in k.lower()
                for s in (
                    "tss",
                    "planned_load",
                    "official",
                    "numeric_lexeme",
                    "v6_frozen",
                )
            )
            assert_private_free(v)
    elif isinstance(value, list):
        for item in value:
            assert_private_free(item)


def test_multi_session_draft_duplicate_source_dates_undo_and_submit(
    v6_client: TestClient,
) -> None:
    """TEST_ONLY frequency authority, existing real worker and route contracts."""
    from datetime import date

    from app.modules.physiology.models import Discipline
    from app.modules.planning.v6_frequency import SessionFrequency

    app = cast(FastAPI, v6_client.app)
    repo = app.state.planning_repository
    app.state.v6_controls = V6Controls(
        athlete_scope=repo._token_owners["athlete-a"],
        week_scope=date(2026, 10, 26),
        authorized_target=PlanningTarget(
            TrainingPhase.BASE,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            InternalLoad(Decimal("100")),
        ),
        session_frequency=tuple(
            SessionFrequency(s, n, "TEST_ONLY requested sessions", n)
            for s, n in (
                (Discipline.RUN, 2),
                (Discipline.BIKE, 2),
                (Discipline.SWIM, 1),
            )
        ),
    )
    draft = create(v6_client, True)
    assert draft["target_workout_count"] == 5
    url = f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"

    def accept(row: dict[str, Any]) -> dict[str, Any]:
        candidate = row["current_candidate"]
        response = v6_client.post(
            url + "/transitions",
            headers=_headers(),
            json={
                "expected_revision": row["revision"],
                "action": "accept",
                "candidate_template_id": candidate["id"],
                "candidate_occurrence_id": candidate["occurrence_id"],
            },
        )
        assert response.status_code == 200, response.text
        return cast(dict[str, Any], response.json())

    for _ in range(5):
        draft = accept(draft)
    runs = [w for w in draft["accepted_workouts"] if w["discipline"] == "run"]
    assert len(runs) == 2 and runs[0]["id"] == runs[1]["id"]
    assert runs[0]["occurrence_id"] != runs[1]["occurrence_id"]
    dates = dict(zip((w["occurrence_id"] for w in runs), ("2026-10-26", "2026-10-31")))
    bikes = [w for w in draft["accepted_workouts"] if w["discipline"] == "bike"]
    dates.update(zip((w["occurrence_id"] for w in bikes), ("2026-10-26", "2026-10-28")))
    for workout in draft["accepted_workouts"]:
        occurrence = workout["occurrence_id"]
        response = v6_client.put(
            url + "/placements/" + occurrence,
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "scheduled_date": dates.get(occurrence, "2026-10-28"),
            },
        )
        assert response.status_code == 200, response.text
        draft = response.json()
    undo = v6_client.post(
        url + "/transitions",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "action": "undo",
        },
    )
    assert undo.status_code == 200, undo.text
    draft = accept(undo.json())
    for occurrence, day in dates.items():
        assert {"occurrence_id": occurrence, "scheduled_date": day} in draft[
            "placements"
        ]
    # Restore the last accepted occurrence's placement for a complete manual layout.
    last = draft["accepted_workouts"][-1]["occurrence_id"]
    placed = v6_client.put(
        url + "/placements/" + last,
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "scheduled_date": "2026-10-28",
        },
    )
    assert placed.status_code == 200, placed.text
    draft = placed.json()
    submitted = v6_client.post(
        url + "/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "manual",
        },
    )
    assert submitted.status_code == 201, submitted.text
    result = submitted.json()
    assert len(result["plan"]["workouts"]) == 5
    assert result["plan"]["revision_state"] == "pending_approval"
    for occurrence, day in dates.items():
        assert (
            next(w for w in result["plan"]["workouts"] if w["id"] == occurrence)[
                "scheduled_date"
            ]
            == day
        )
    assert_private_free(result)


def test_automatic_proposal_and_each_sport_swipe(v6_client: TestClient) -> None:
    result = create(v6_client)
    plan = result["plan"]
    assert plan["revision_state"] == "pending_approval"
    assert {w["discipline"] for w in plan["workouts"]} == {"run", "bike", "swim"}
    assert_private_free(result)
    other = v6_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers("athlete-b"),
        json={
            "week_start": "2026-10-26",
            "available_dates": ["2026-10-26", "2026-10-28", "2026-10-31"],
        },
    )
    assert other.status_code == 201, other.text
    assert {w["id"] for w in plan["workouts"]}.isdisjoint(
        w["id"] for w in other.json()["plan"]["workouts"]
    )
    repo = cast(
        V6MemoryRepository, cast(FastAPI, v6_client.app).state.planning_repository
    )
    payload = repo.frozen_payloads[UUID(plan["id"]), plan["revision"]]
    assert payload["planning_ruleset_version"] == "joren-v6-automatic-selection-1"
    assert all(
        w["planned_method"] == "joren-v6-planned-if2-1" for w in payload["workouts"]
    )
    for sport in ("run", "bike", "swim"):
        before = plan
        current = next(w for w in before["workouts"] if w["discipline"] == sport)
        url = f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/{current['id']}"
        choices = v6_client.get(
            url + "/alternatives",
            headers=_headers(),
            params={"expected_revision": plan["revision"]},
        )
        assert choices.status_code == 200, choices.text
        alternatives = choices.json()["alternatives"]
        assert alternatives
        assert_private_free(choices.json())
        body = {
            "expected_revision": plan["revision"],
            "expected_proposal_id": plan["proposal"]["id"],
            "replacement_template_id": alternatives[0]["template_id"]
            if "template_id" in alternatives[0]
            else alternatives[0]["id"],
        }
        response = v6_client.post(
            url + "/edit-proposals", headers=_headers(), json=body
        )
        assert response.status_code == 201, response.text
        plan = response.json()["plan"]
        assert (
            plan["revision_state"] == "pending_approval"
            and plan["active_revision"] is None
        )
        retained = {w["id"]: w for w in before["workouts"] if w["id"] != current["id"]}
        for w in plan["workouts"]:
            if w["id"] in retained:
                # Retain logical/source/date fields across immutable physical revisions.
                assert {k: v for k, v in w.items() if k != "physical_workout_id"} == {
                    k: v
                    for k, v in retained[w["id"]].items()
                    if k != "physical_workout_id"
                }
                assert (
                    w["physical_workout_id"] != retained[w["id"]]["physical_workout_id"]
                )
        assert len(retained) == 2
        retry = v6_client.post(url + "/edit-proposals", headers=_headers(), json=body)
        assert retry.status_code == 201 and retry.json() == response.json(), retry.text
        foreign = v6_client.get(
            url + "/alternatives",
            headers=_headers("athlete-b"),
            params={"expected_revision": plan["revision"]},
        )
        assert foreign.status_code == 404
        assert_private_free(response.json())


def test_card_swiping_retention_retry_undo_and_submit(v6_client: TestClient) -> None:
    draft = create(v6_client, True)
    assert draft["target_workout_count"] == 3
    url = f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"
    retained = []
    for i in range(3):
        candidate = draft["current_candidate"]
        assert candidate is not None
        body = {
            "expected_revision": draft["revision"],
            "action": "accept",
            "candidate_template_id": candidate["template_id"]
            if "template_id" in candidate
            else candidate["id"],
            "candidate_occurrence_id": candidate["occurrence_id"],
        }
        response = v6_client.post(url + "/transitions", headers=_headers(), json=body)
        assert response.status_code == 200, response.text
        draft = response.json()
        retained.append(candidate["occurrence_id"])
        assert [w["occurrence_id"] for w in draft["accepted_workouts"]] == retained
        retry = v6_client.post(url + "/transitions", headers=_headers(), json=body)
        assert retry.status_code == 200 and retry.json() == draft, retry.text
    assert draft["state"] == "placement"
    placed_occurrence = draft["accepted_workouts"][0]["occurrence_id"]
    placed = v6_client.put(
        url + "/placements/" + placed_occurrence,
        headers=_headers(),
        json={"expected_revision": draft["revision"], "scheduled_date": "2026-10-28"},
    )
    assert placed.status_code == 200, placed.text
    draft = placed.json()
    undo = v6_client.post(
        url + "/transitions",
        headers=_headers(),
        json={"expected_revision": draft["revision"], "action": "undo"},
    )
    assert undo.status_code == 200, undo.text
    draft = undo.json()
    assert len(draft["accepted_workouts"]) == 2
    assert draft["placements"] == [
        {"occurrence_id": placed_occurrence, "scheduled_date": "2026-10-28"}
    ]
    candidate = draft["current_candidate"]
    response = v6_client.post(
        url + "/transitions",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "action": "accept",
            "candidate_template_id": candidate.get("template_id", candidate.get("id")),
            "candidate_occurrence_id": candidate["occurrence_id"],
        },
    )
    assert response.status_code == 200, response.text
    draft = response.json()
    submitted = v6_client.post(
        url + "/submit",
        headers=_headers(),
        json={"expected_revision": draft["revision"], "placement_mode": "automatic"},
    )
    assert submitted.status_code == 201, submitted.text
    plan = submitted.json()["plan"]
    assert plan["revision_state"] == "pending_approval"
    approved = v6_client.post(
        f"/api/v1/change-proposals/{plan['proposal']['id']}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["state"] == "applied"
    assert_private_free(submitted.json())


def test_phase_budget_injury_and_repeat_replacement_rejection(
    v6_client: TestClient,
) -> None:
    plan = create(v6_client)["plan"]
    repo = cast(
        V6MemoryRepository, cast(FastAPI, v6_client.app).state.planning_repository
    )
    catalog = tuple(repo.catalog.values())
    current = next(w for w in plan["workouts"] if w["discipline"] == "run")
    url = (
        f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
        f"{current['id']}/edit-proposals"
    )
    base = {
        "expected_revision": plan["revision"],
        "expected_proposal_id": plan["proposal"]["id"],
    }
    from copy import deepcopy

    original = deepcopy(repo._plans[UUID(plan["id"])]["workouts"])
    for identifier in ("TR-RUN-021", "TR-RUN-005", "TR-RUN-017"):
        candidate = next(t for t in catalog if t.source_workout_id == identifier)
        response = v6_client.post(
            url,
            headers=_headers(),
            json={**base, "replacement_template_id": str(candidate.id)},
        )
        assert response.status_code == 409, response.text
        assert_private_free(response.json())
    candidate = next(t for t in catalog if t.source_workout_id == "TR-RUN-026")
    repo._plans[UUID(plan["id"])]["confirmed_injuries"] = ["run"]
    response = v6_client.post(
        url,
        headers=_headers(),
        json={**base, "replacement_template_id": str(candidate.id)},
    )
    assert response.status_code == 409, response.text
    repo._plans[UUID(plan["id"])]["confirmed_injuries"] = []
    bike = next(w for w in plan["workouts"] if w["discipline"] == "bike")
    cast(FastAPI, v6_client.app).state.v6_controls = V6Controls(
        maximum_uses=((UUID(bike["template_id"]), 0),)
    )
    response = v6_client.post(
        url,
        headers=_headers(),
        json={**base, "replacement_template_id": str(candidate.id)},
    )
    assert response.status_code == 409, response.text
    assert repo._plans[UUID(plan["id"])]["workouts"] == original
    assert repo._plans[UUID(plan["id"])]["revision"] == 1


def test_exhaustion_pass_reset_stale_and_foreign_requests(
    v6_client: TestClient,
) -> None:
    draft = create(v6_client, True)
    url = f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"
    # Retain the initial BIKE choice, then exhaust every remaining valid card.
    current = draft["current_candidate"]
    body = {
        "expected_revision": draft["revision"],
        "action": "accept",
        "candidate_template_id": current.get("template_id", current.get("id")),
        "candidate_occurrence_id": current["occurrence_id"],
    }
    response = v6_client.post(url + "/transitions", headers=_headers(), json=body)
    assert response.status_code == 200, response.text
    draft = response.json()
    accepted = draft["accepted_workouts"]
    seen = []
    while draft["current_candidate"] is not None:
        current = draft["current_candidate"]
        seen.append(current.get("template_id", current.get("id")))
        response = v6_client.post(
            url + "/transitions",
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "action": "pass",
                "candidate_template_id": current.get("template_id", current.get("id")),
                "candidate_occurrence_id": current["occurrence_id"],
            },
        )
        assert response.status_code == 200, response.text
        draft = response.json()
        assert draft["accepted_workouts"] == accepted
        assert len(seen) <= 77
    assert len(seen) == len(set(seen)) and draft["exhausted"]
    stale = v6_client.post(url + "/transitions", headers=_headers(), json=body)
    assert stale.status_code == 409
    foreign = v6_client.get(url, headers=_headers("athlete-b"))
    assert foreign.status_code == 404
    reset = v6_client.post(
        url + "/transitions",
        headers=_headers(),
        json={"expected_revision": draft["revision"], "action": "reset_passed"},
    )
    assert reset.status_code == 200, reset.text
    assert (
        reset.json()["accepted_workouts"] == accepted
        and reset.json()["current_candidate"] is not None
    )


def test_concurrent_edit_cas_and_exact_retry(v6_client: TestClient) -> None:
    from concurrent.futures import ThreadPoolExecutor

    plan = create(v6_client)["plan"]
    current = next(w for w in plan["workouts"] if w["discipline"] == "run")
    repo = cast(
        V6MemoryRepository, cast(FastAPI, v6_client.app).state.planning_repository
    )
    replacement = next(
        t for t in repo.catalog.values() if t.source_workout_id == "TR-RUN-026"
    )
    body = {
        "expected_revision": plan["revision"],
        "expected_proposal_id": plan["proposal"]["id"],
        "replacement_template_id": str(replacement.id),
    }
    url = (
        f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
        f"{current['id']}/edit-proposals"
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: v6_client.post(url, headers=_headers(), json=body), range(2)
            )
        )
    assert any(r.status_code == 201 for r in results)
    assert all(r.status_code in (201, 409) for r in results)
    assert repo._plans[UUID(plan["id"])]["revision"] == 2
    retried = v6_client.post(url, headers=_headers(), json=body)
    assert retried.status_code == 201
    stale = v6_client.post(
        url,
        headers=_headers(),
        json={
            **body,
            "replacement_template_id": current.get("template_id", current.get("id")),
        },
    )
    assert stale.status_code in (404, 409)


def test_build_four_high_limit_and_repeated_occurrence_preservation(
    v6_client: TestClient,
) -> None:
    app = cast(FastAPI, v6_client.app)
    app.state.v6_controls = V6Controls(
        authorized_target=PlanningTarget(
            TrainingPhase.BUILD,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            InternalLoad(Decimal(200)),
            build_week=4,
        )
    )
    repo = cast(V6MemoryRepository, app.state.planning_repository)
    lookup = {t.source_workout_id: t for t in repo.catalog.values()}
    names = ("TR-BIKE-001", "TR-RUN-025", "TR-RUN-025", "TR-SWIM-021")
    # Existing repeated occurrences enter through trusted snapshot storage, not
    # by weakening the legacy public request's unique-template constraint.
    import asyncio
    from datetime import date

    from test_v6_automatic_selection import plan as make_plan

    from app.modules.physiology.models import Discipline
    from app.modules.planning.schemas import WeeklyPlanResponse

    dates = (date(2026, 10, 26), date(2026, 10, 28), date(2026, 10, 31))
    draft = make_plan(
        tuple(repo.catalog.values()),
        controls=app.state.v6_controls,
        available_dates=dates,
        selected_template_ids=tuple(lookup[n].id for n in names),
    )
    owner = repo._owner("athlete-a")
    source = repo._requests[owner]
    payload = V6PlanningService._proposal_payload(
        request_id=UUID(source["id"]),
        input_fingerprint=source["input_fingerprint"],
        generation_fingerprint="TEST_ONLY:existing-repeated-pending-snapshot",
        plan_id=None,
        expected_base_revision=0,
        week_start=dates[0],
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
    p = WeeklyPlanResponse.model_validate(
        asyncio.run(repo.fetch_plan("athlete-a", UUID(result["plan_id"]), 1))
    ).model_dump(mode="json")
    swim = next(w for w in p["workouts"] if w["discipline"] == "swim")
    bad = v6_client.post(
        f"/api/v1/weekly-plans/{p['id']}/pending-workouts/{swim['id']}/edit-proposals",
        headers=_headers(),
        json={
            "expected_revision": p["revision"],
            "expected_proposal_id": p["proposal"]["id"],
            "replacement_template_id": str(lookup["TR-SWIM-010"].id),
        },
    )
    assert bad.status_code == 409, bad.text  # under budget, but >20% SWIM active HIGH
    bike = next(w for w in p["workouts"] if w["discipline"] == "bike")
    choices = v6_client.get(
        f"/api/v1/weekly-plans/{p['id']}/pending-workouts/{bike['id']}/alternatives",
        headers=_headers(),
        params={"expected_revision": p["revision"]},
    )
    assert choices.status_code == 200, choices.text
    assert str(lookup["TR-BIKE-020"].id) in {
        t["id"] for t in choices.json()["alternatives"]
    }
    runs = [w for w in p["workouts"] if w["discipline"] == "run"]
    assert len(runs) == 2
    changed = v6_client.post(
        f"/api/v1/weekly-plans/{p['id']}/pending-workouts/{runs[0]['id']}/edit-proposals",
        headers=_headers(),
        json={
            "expected_revision": p["revision"],
            "expected_proposal_id": p["proposal"]["id"],
            "replacement_template_id": str(lookup["TR-RUN-026"].id),
        },
    )
    assert changed.status_code == 201, changed.text
    retained_run = next(
        w for w in changed.json()["plan"]["workouts"] if w["id"] == runs[1]["id"]
    )
    assert {
        k: v
        for k, v in retained_run.items()
        if k not in {"physical_workout_id", "source_prescription"}
    } == {
        k: v
        for k, v in runs[1].items()
        if k not in {"physical_workout_id", "source_prescription"}
    }
    assert retained_run["physical_workout_id"] != runs[1]["physical_workout_id"]
    assert retained_run["source_prescription"] is not None
