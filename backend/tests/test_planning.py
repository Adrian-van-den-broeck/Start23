"""Phase 6 API workflow, ownership, approval, and TSS-contract tests."""

from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.onboarding.repository import RepositoryNotFoundError
from app.modules.planning.repository import (
    JsonObject,
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
)
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    WorkoutTemplate,
    active_catalog,
)

_NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


class PlanningTokenVerifier:
    """Derive one of two test owners exclusively from the bearer token."""

    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            owner = self._owners[access_token]
        except KeyError as error:
            raise InvalidAccessTokenError from error
        return AuthenticatedIdentity(user_id=owner, role="authenticated")


class StaticCatalogProvider:
    """Provide the validated reviewed catalog without external services."""

    async def fetch_catalog(self) -> tuple[WorkoutTemplate, ...]:
        return CURRENT_CATALOG

    async def aclose(self) -> None:
        return None


class ZoneRejectStub:
    """Let the shared rejection route fall through to a plan proposal."""

    async def reject_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        del access_token, proposal_id
        raise RepositoryNotFoundError

    async def aclose(self) -> None:
        return None


def _snapshot(athlete_id: UUID) -> JsonObject:
    return {
        "profile": {
            "athlete_id": str(athlete_id),
            "timezone": "UTC",
            "revision": 1,
        },
        "training_history": [
            {"discipline": "swim", "weekly_minutes": 60},
            {"discipline": "bike", "weekly_minutes": 120},
            {"discipline": "run", "weekly_minutes": 90},
        ],
        "goal": {
            "id": str(uuid4()),
            "target_date": "2026-12-06",
            "race_discipline_profile": ["swim", "bike", "run"],
            "revision": 1,
        },
        "zones": [
            {
                "discipline": "swim",
                "fallback_active": False,
                "metric": {"kind": "swim_css_seconds_per_100m", "value": 100},
            },
            {
                "discipline": "bike",
                "fallback_active": False,
                "metric": {"kind": "bike_ftp_watts", "value": 250},
            },
            {
                "discipline": "run",
                "fallback_active": False,
                "metric": {"kind": "run_lthr_bpm", "value": 170},
            },
        ],
        "ruleset_version": "phase-3-ruleset-2",
    }


class MemoryPlanningRepository:
    """Small owner-scoped fake that preserves pending/active revision behavior."""

    def __init__(self, token_owners: dict[str, UUID]) -> None:
        self._token_owners = token_owners
        self._requests = {
            owner: {
                "id": str(uuid4()),
                "athlete_id": str(owner),
                "status": "pending",
                "input_fingerprint": "a" * 32,
                "input_snapshot": _snapshot(owner),
            }
            for owner in token_owners.values()
        }
        self._plans: dict[UUID, JsonObject] = {}
        self._plan_owners: dict[UUID, UUID] = {}
        self._proposals: dict[UUID, JsonObject] = {}
        self._proposal_owners: dict[UUID, UUID] = {}
        self._fingerprints: dict[tuple[UUID, str], tuple[UUID, UUID, int]] = {}

    def _owner(self, token: str) -> UUID:
        try:
            return self._token_owners[token]
        except KeyError as error:
            raise PlanningRepositoryNotFoundError from error

    @staticmethod
    def _segments(template: WorkoutTemplate) -> list[JsonObject]:
        return [
            {
                "sequence": segment.sequence,
                "name": segment.name,
                "instructions": segment.instructions,
                "duration_minutes": str(segment.duration_minutes),
                "distance_meters": segment.distance_meters,
                "zone": int(segment.zone),
                "expected_rpe": segment.expected_rpe,
                "is_swim_technique": segment.is_swim_technique,
            }
            for segment in template.segments
        ]

    async def fetch_initial_request(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject | None:
        if self._owner(access_token) != athlete_id:
            return None
        return dict(self._requests[athlete_id])

    async def fetch_plan_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
    ) -> JsonObject:
        if self._plan_owners.get(plan_id) != athlete_id:
            raise PlanningRepositoryNotFoundError
        plan = self._plans[plan_id]
        request = self._requests[athlete_id]
        return {
            **request,
            "plan_id": str(plan_id),
            "week_start": plan["week_start"],
            "active_revision": plan["active_revision"],
            "revision": plan["revision"],
            "phase": plan["phase"],
            "confirmed_injuries": plan["confirmed_injuries"],
            "low_only_disciplines": plan.get("low_only_disciplines", []),
            "target_tss": plan["_target_tss"],
            "initial_plan_request_id": request["id"],
        }

    async def fetch_load_history(
        self,
        athlete_id: UUID,
        before_week: date,
    ) -> tuple[JsonObject, ...]:
        del athlete_id, before_week
        return ()

    async def create_plan_proposal(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        fingerprint = str(payload["generation_fingerprint"])
        existing = self._fingerprints.get((athlete_id, fingerprint))
        if existing is not None:
            plan_id, proposal_id, revision = existing
            return {
                "plan_id": str(plan_id),
                "proposal_id": str(proposal_id),
                "revision": revision,
            }
        plan_id = (
            UUID(str(payload["plan_id"])) if payload["plan_id"] is not None else uuid4()
        )
        current = self._plans.get(plan_id)
        active_revision = current["active_revision"] if current is not None else None
        if (active_revision or 0) != int(payload["expected_base_revision"]):
            raise PlanningRepositoryConflictError
        revision = int(current["revision"]) + 1 if current is not None else 1
        revision_id = uuid4()
        proposal_id = uuid4()
        templates = {template.id: template for template in active_catalog()}
        workouts: list[JsonObject] = []
        for selected in payload["workouts"]:
            template = templates[UUID(str(selected["template_id"]))]
            workouts.append(
                {
                    "id": str(uuid4()),
                    "template_id": str(template.id),
                    "template_key": str(template.template_key),
                    "template_version": template.version,
                    "discipline": template.discipline.value,
                    "name": template.name,
                    "description": template.description,
                    "duration_minutes": str(template.duration_minutes),
                    "distance_meters": template.distance_meters,
                    "intensity_bucket": template.intensity_bucket.value,
                    "expected_rpe_min": template.expected_rpe_min,
                    "expected_rpe_max": template.expected_rpe_max,
                    "segments": self._segments(template),
                    "scheduled_at": selected["scheduled_at"],
                    "timezone": payload["timezone"],
                    "source": selected["source"],
                    "status": "scheduled",
                    "warnings": [],
                }
            )
        warnings = [
            {
                "id": str(uuid4()),
                "rule_id": item["rule_id"],
                "code": item["code"],
                "severity": item["severity"],
                "message": item["message"],
                "planned_workout_id": None,
            }
            for item in payload["warnings"]
        ]
        proposal = {
            "id": str(proposal_id),
            "kind": "plan_revision",
            "state": "pending",
            "reason_codes": [item["code"] for item in payload["warnings"]]
            or ["weekly_plan_ready"],
            "public_explanation": ("A deterministic weekly plan is ready for review."),
            "ruleset_version": payload["ruleset_version"],
            "created_at": _NOW.isoformat(),
            "decided_at": None,
            "applied_at": None,
            "decision_actor": None,
            "target_plan_revision_id": str(revision_id),
            "base_plan_revision": payload["expected_base_revision"],
            "target_zone_profile_id": None,
            "base_zone_profile_id": None,
        }
        plan = {
            "id": str(plan_id),
            "week_start": payload["week_start"],
            "timezone": payload["timezone"],
            "state": "active" if active_revision is not None else "pending_approval",
            "active_revision": active_revision,
            "revision_id": str(revision_id),
            "revision": revision,
            "revision_state": "pending_approval",
            "phase": payload["phase"],
            "target_basis": payload["target_basis"],
            "taper_period": payload["taper_period"],
            "total_duration_minutes": payload["total_duration_minutes"],
            "low_intensity_percent": payload["low_intensity_percent"],
            "high_intensity_percent": payload["high_intensity_percent"],
            "confirmed_injuries": payload["confirmed_injuries"],
            "low_only_disciplines": payload.get("low_only_disciplines", []),
            "workouts": workouts,
            "warnings": warnings,
            "proposal": proposal,
            "_availability": payload["availability"],
            "_target_tss": payload["target_tss"],
        }
        self._plans[plan_id] = plan
        self._plan_owners[plan_id] = athlete_id
        self._proposals[proposal_id] = proposal
        self._proposal_owners[proposal_id] = athlete_id
        self._fingerprints[(athlete_id, fingerprint)] = (
            plan_id,
            proposal_id,
            revision,
        )
        return {
            "plan_id": str(plan_id),
            "proposal_id": str(proposal_id),
            "revision": revision,
        }

    async def fetch_plan(
        self,
        access_token: str,
        plan_id: UUID,
        revision: int | None = None,
    ) -> JsonObject:
        if self._plan_owners.get(plan_id) != self._owner(access_token):
            raise PlanningRepositoryNotFoundError
        plan = self._plans[plan_id]
        if revision is not None and int(plan["revision"]) != revision:
            raise PlanningRepositoryNotFoundError
        return {key: value for key, value in plan.items() if not key.startswith("_")}

    async def fetch_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        if self._proposal_owners.get(proposal_id) != self._owner(access_token):
            raise PlanningRepositoryNotFoundError
        return dict(self._proposals[proposal_id])

    async def list_proposals(
        self,
        access_token: str,
        state: str | None = None,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        return tuple(
            dict(proposal)
            for proposal_id, proposal in self._proposals.items()
            if self._proposal_owners[proposal_id] == owner
            and (state is None or proposal["state"] == state)
        )

    async def approve_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_revision: int,
    ) -> JsonObject:
        proposal = await self.fetch_proposal(access_token, proposal_id)
        plan_id = next(
            plan_id
            for plan_id, plan in self._plans.items()
            if plan["revision_id"] == proposal["target_plan_revision_id"]
        )
        plan = self._plans[plan_id]
        if proposal["base_plan_revision"] != expected_base_revision:
            raise PlanningRepositoryConflictError(
                "proposal_stale",
                "This proposal is based on an older plan revision.",
            )
        if proposal["state"] == "applied":
            return {
                "proposal_id": str(proposal_id),
                "state": "applied",
                "plan_id": str(plan_id),
                "active_revision": plan["revision"],
                "target_revision_id": proposal["target_plan_revision_id"],
            }
        if proposal["state"] != "pending":
            raise PlanningRepositoryConflictError(
                "proposal_not_pending",
                "This proposal was already decided.",
            )
        if (plan["active_revision"] or 0) != expected_base_revision:
            raise PlanningRepositoryConflictError(
                "proposal_stale",
                "This proposal is based on an older plan revision.",
            )
        proposal["state"] = "applied"
        proposal["decided_at"] = _NOW.isoformat()
        proposal["applied_at"] = _NOW.isoformat()
        proposal["decision_actor"] = str(self._owner(access_token))
        self._proposals[proposal_id] = proposal
        plan["state"] = "active"
        plan["revision_state"] = "active"
        plan["active_revision"] = plan["revision"]
        plan["proposal"] = proposal
        return {
            "proposal_id": str(proposal_id),
            "state": "applied",
            "plan_id": str(plan_id),
            "active_revision": plan["revision"],
            "target_revision_id": proposal["target_plan_revision_id"],
        }

    async def reject_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        proposal = await self.fetch_proposal(access_token, proposal_id)
        plan_id = next(
            plan_id
            for plan_id, plan in self._plans.items()
            if plan["revision_id"] == proposal["target_plan_revision_id"]
        )
        plan = self._plans[plan_id]
        if proposal["state"] == "rejected":
            return {
                "proposal_id": str(proposal_id),
                "state": "rejected",
                "plan_id": str(plan_id),
                "active_revision": plan["active_revision"],
                "target_revision_id": proposal["target_plan_revision_id"],
            }
        if proposal["state"] != "pending":
            raise PlanningRepositoryConflictError(
                "proposal_not_pending",
                "This proposal was already decided.",
            )
        proposal["state"] = "rejected"
        proposal["decided_at"] = _NOW.isoformat()
        proposal["decision_actor"] = str(self._owner(access_token))
        plan["revision_state"] = "rejected"
        plan["proposal"] = proposal
        return {
            "proposal_id": str(proposal_id),
            "state": "rejected",
            "plan_id": str(plan_id),
            "active_revision": plan["active_revision"],
            "target_revision_id": proposal["target_plan_revision_id"],
        }

    async def fetch_workout_context(
        self,
        access_token: str,
        workout_id: UUID,
    ) -> JsonObject:
        owner = self._owner(access_token)
        for plan_id, plan in self._plans.items():
            if self._plan_owners[plan_id] == owner and any(
                workout["id"] == str(workout_id) for workout in plan["workouts"]
            ):
                return {
                    "plan": {
                        key: value
                        for key, value in plan.items()
                        if not key.startswith("_")
                    },
                    "availability": plan["_availability"],
                }
        raise PlanningRepositoryNotFoundError

    async def move_planned_workout(
        self,
        athlete_id: UUID,
        workout_id: UUID,
        expected_revision: int,
        scheduled_at: datetime,
        warnings: list[JsonObject],
    ) -> JsonObject:
        for plan_id, plan in self._plans.items():
            if self._plan_owners[plan_id] != athlete_id:
                continue
            if any(workout["id"] == str(workout_id) for workout in plan["workouts"]):
                if plan["active_revision"] != expected_revision:
                    raise PlanningRepositoryConflictError(
                        "plan_revision_stale",
                        "The plan changed after this operation was prepared.",
                    )
                plan["revision"] = expected_revision + 1
                plan["active_revision"] = expected_revision + 1
                for workout in plan["workouts"]:
                    if workout["id"] == str(workout_id):
                        workout["scheduled_at"] = scheduled_at.isoformat()
                        workout["source"] = "athlete_moved"
                plan["warnings"] = [
                    {
                        "id": str(uuid4()),
                        "planned_workout_id": str(workout_id),
                        **warning,
                    }
                    for warning in warnings
                ]
                return {"plan_id": str(plan_id), "revision": plan["revision"]}
        raise PlanningRepositoryNotFoundError

    async def fetch_calendar(
        self,
        access_token: str,
        from_datetime: datetime,
        to_datetime: datetime,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        return tuple(
            workout
            for plan_id, plan in self._plans.items()
            if self._plan_owners[plan_id] == owner
            and plan["active_revision"] is not None
            for workout in plan["workouts"]
            if from_datetime
            <= datetime.fromisoformat(str(workout["scheduled_at"]))
            < to_datetime
        )

    async def fetch_calendar_rest_days(
        self,
        access_token: str,
        from_datetime: datetime,
        to_datetime: datetime,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        rows: list[JsonObject] = []
        for plan_id, plan in self._plans.items():
            if self._plan_owners[plan_id] != owner or plan["active_revision"] is None:
                continue
            week_start = date.fromisoformat(str(plan["week_start"]))
            workout_dates = {
                datetime.fromisoformat(str(workout["scheduled_at"])).date()
                for workout in plan["workouts"]
                if workout["status"] != "cancelled"
            }
            for offset in range(7):
                current = week_start + timedelta(days=offset)
                instant = datetime.combine(current, datetime.min.time(), timezone.utc)
                if (
                    current not in workout_dates
                    and from_datetime <= instant < to_datetime
                ):
                    rows.append(
                        {
                            "date": current.isoformat(),
                            "reason": (
                                "restriction_rest"
                                if plan["target_basis"] == "injury_rest_only"
                                else "planned_rest"
                            ),
                        }
                    )
        return tuple(rows)

    async def aclose(self) -> None:
        return None


def _availability_payload() -> list[dict[str, str]]:
    return [
        {
            "starts_at": datetime(
                2026,
                8,
                day,
                7,
                tzinfo=timezone.utc,
            ).isoformat(),
            "ends_at": datetime(
                2026,
                8,
                day,
                9,
                tzinfo=timezone.utc,
            ).isoformat(),
        }
        for day in (3, 5, 7)
    ]


@pytest.fixture
def planning_client() -> Iterator[TestClient]:
    athlete_a = uuid4()
    athlete_b = uuid4()
    owners = {"athlete-a": athlete_a, "athlete-b": athlete_b}
    with TestClient(
        create_app(
            Settings(environment="test"),
            access_token_verifier=PlanningTokenVerifier(owners),
            onboarding_repository=ZoneRejectStub(),  # type: ignore[arg-type]
            planning_repository=MemoryPlanningRepository(owners),
            planning_catalog_provider=StaticCatalogProvider(),
        )
    ) as client:
        yield client


def _headers(token: str = "athlete-a") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_proposal(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers(),
        json={
            "week_start": "2026-08-03",
            "availability": _availability_payload(),
            "confirmed_injuries": [],
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_plan_generation_requires_authentication(
    planning_client: TestClient,
) -> None:
    response = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        json={
            "week_start": "2026-08-03",
            "availability": _availability_payload(),
        },
    )

    assert response.status_code == 401


def test_generated_plan_remains_pending_is_idempotent_and_hides_tss(
    planning_client: TestClient,
) -> None:
    first = _create_proposal(planning_client)
    repeated = _create_proposal(planning_client)

    assert first["proposal"]["state"] == "pending"
    assert first["plan"]["revision_state"] == "pending_approval"
    assert first["plan"]["active_revision"] is None
    assert repeated["proposal"]["id"] == first["proposal"]["id"]
    assert repeated["plan"]["id"] == first["plan"]["id"]
    serialized = json_normalized = str(first).lower().replace("_", "")
    assert "tss" not in serialized
    assert "plannedtss" not in json_normalized


def test_plan_approval_is_owner_scoped_atomic_and_stale_safe(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    proposal_id = created["proposal"]["id"]
    plan_id = created["plan"]["id"]

    other_athlete = planning_client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers("athlete-b"),
        json={"expected_base_revision": 0},
    )
    stale = planning_client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_revision": 1},
    )
    approved = planning_client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    repeated = planning_client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    active = planning_client.get(
        f"/api/v1/weekly-plans/{plan_id}",
        headers=_headers(),
    )
    calendar = planning_client.get(
        "/api/v1/calendar",
        headers=_headers(),
        params={
            "from": "2026-08-03T00:00:00Z",
            "to": "2026-08-10T00:00:00Z",
        },
    )

    assert other_athlete.status_code == 404
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "proposal_stale"
    assert approved.status_code == 200
    assert approved.json()["state"] == "applied"
    assert repeated.status_code == 200
    assert repeated.json() == approved.json()
    assert active.json()["active_revision"] == 1
    assert active.json()["revision_state"] == "active"
    assert calendar.status_code == 200
    assert len(calendar.json()["workouts"]) == 3
    assert "tss" not in calendar.text.lower()


def test_cross_athlete_plan_read_is_not_disclosed(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)

    response = planning_client.get(
        f"/api/v1/weekly-plans/{created['plan']['id']}",
        headers=_headers("athlete-b"),
    )

    assert response.status_code == 404


def test_direct_calendar_move_applies_new_revision_with_soft_warning(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    proposal_id = created["proposal"]["id"]
    approved = planning_client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approved.status_code == 200
    workout_id = created["plan"]["workouts"][0]["id"]

    moved = planning_client.patch(
        f"/api/v1/planned-workouts/{workout_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "scheduled_at": "2026-08-04T12:00:00Z",
        },
    )
    stale_replay = planning_client.patch(
        f"/api/v1/planned-workouts/{workout_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "scheduled_at": "2026-08-04T13:00:00Z",
        },
    )

    assert moved.status_code == 200
    assert moved.json()["active_revision"] == 2
    assert moved.json()["revision"] == 2
    assert "outside_confirmed_availability" in {
        warning["code"] for warning in moved.json()["warnings"]
    }
    assert stale_replay.status_code == 409
    assert stale_replay.json()["error"]["code"] == "plan_revision_stale"


def test_rejected_schedule_proposal_keeps_the_active_base_revision(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    approved = planning_client.post(
        f"/api/v1/change-proposals/{created['proposal']['id']}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approved.status_code == 200
    plan_id = created["plan"]["id"]
    selection = [workout["template_id"] for workout in created["plan"]["workouts"]]

    replacement = planning_client.post(
        f"/api/v1/weekly-plans/{plan_id}/schedule-proposals",
        headers=_headers(),
        json={
            "expected_base_revision": 1,
            "availability": _availability_payload(),
            "confirmed_injuries": [],
            "selected_template_ids": selection,
        },
    )
    assert replacement.status_code == 201, replacement.text
    assert replacement.json()["plan"]["revision_state"] == "pending_approval"
    assert replacement.json()["plan"]["active_revision"] == 1

    rejected = planning_client.post(
        (f"/api/v1/change-proposals/{replacement.json()['proposal']['id']}/reject"),
        headers=_headers(),
    )
    repeated = planning_client.post(
        (f"/api/v1/change-proposals/{replacement.json()['proposal']['id']}/reject"),
        headers=_headers(),
    )

    assert rejected.status_code == 200
    assert rejected.json()["state"] == "rejected"
    assert rejected.json()["active_revision"] == 1
    assert repeated.status_code == 200
    assert repeated.json() == rejected.json()


def test_deck_and_layout_validation_use_server_owned_workout_facts(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    plan = created["plan"]
    plan_id = plan["id"]

    deck = planning_client.get(
        f"/api/v1/weekly-plans/{plan_id}/deck",
        headers=_headers(),
    )
    valid = planning_client.post(
        f"/api/v1/weekly-plans/{plan_id}/validate",
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "workouts": [
                {
                    "workout_id": workout["id"],
                    "scheduled_at": workout["scheduled_at"],
                }
                for workout in plan["workouts"]
            ],
        },
    )
    spoofed = planning_client.post(
        f"/api/v1/weekly-plans/{plan_id}/validate",
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "workouts": [
                {
                    "workout_id": workout["id"],
                    "scheduled_at": workout["scheduled_at"],
                    "discipline": "run",
                    "intensity_bucket": "low",
                }
                for workout in plan["workouts"]
            ],
        },
    )
    incomplete = planning_client.post(
        f"/api/v1/weekly-plans/{plan_id}/validate",
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "workouts": [
                {
                    "workout_id": plan["workouts"][0]["id"],
                    "scheduled_at": plan["workouts"][0]["scheduled_at"],
                }
            ],
        },
    )

    assert deck.status_code == 200
    assert deck.json()["plan_id"] == plan_id
    assert deck.json()["templates"]
    assert "tss" not in deck.text.lower()
    assert valid.status_code == 200
    assert spoofed.status_code == 422
    assert incomplete.status_code == 422


def test_confirmed_injury_is_excluded_from_pending_plan(
    planning_client: TestClient,
) -> None:
    response = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers("athlete-b"),
        json={
            "week_start": "2026-08-03",
            "availability": _availability_payload(),
            "confirmed_injuries": ["run"],
        },
    )

    assert response.status_code == 201
    disciplines = {
        workout["discipline"] for workout in response.json()["plan"]["workouts"]
    }
    assert disciplines == {"swim", "bike"}
    assert "injured_disciplines_excluded" in {
        warning["code"] for warning in response.json()["plan"]["warnings"]
    }
