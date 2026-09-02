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
from app.modules.physiology.models import Discipline
from app.modules.planning.domain import ZoneCapability, eligible_workouts
from app.modules.planning.repository import (
    JsonObject,
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
)
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    TrainingPhase,
    WorkoutTemplate,
    active_catalog,
)

_NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


def test_week_one_calibration_is_eligible_only_for_its_pending_protocol() -> None:
    protocol_id = "start23_week1_bike_calibration_v1"
    without_protocol = eligible_workouts(
        catalog=CURRENT_CATALOG,
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities={Discipline.BIKE: ZoneCapability(frozenset())},
    )
    with_protocol = eligible_workouts(
        catalog=CURRENT_CATALOG,
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            Discipline.BIKE: ZoneCapability(
                frozenset(), protocol_ids=frozenset({protocol_id})
            )
        },
    )

    assert all(
        template.name != "Week-1 fietskalibratie" for template in without_protocol
    )
    calibration = next(
        template
        for template in with_protocol
        if template.name == "Week-1 fietskalibratie"
    )
    assert calibration.zone_requirements == ()
    assert all(segment.zone_target is None for segment in calibration.segments)


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
        "discipline_setups": [
            {
                "discipline": "bike",
                "setup_status": "calibration_pending",
                "protocol_id": "start23_week1_bike_calibration_v1",
            }
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
        self._swipe_drafts: dict[UUID, JsonObject] = {}
        self._swipe_draft_owners: dict[UUID, UUID] = {}

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
                "zone_target": (
                    int(segment.zone_target)
                    if segment.zone_target is not None
                    else None
                ),
                "protocol_target": (
                    {
                        "protocol_id": segment.protocol_target.protocol_id,
                        "segment_id": segment.protocol_target.segment_id,
                        "target_rpe_min": segment.protocol_target.target_rpe_min,
                        "target_rpe_max": segment.protocol_target.target_rpe_max,
                        "intensity_bucket": (
                            segment.protocol_target.intensity_bucket.value
                        ),
                        "optional": segment.protocol_target.optional,
                    }
                    if segment.protocol_target is not None
                    else None
                ),
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
            "available_dates": plan["available_dates"],
            "availability_source": plan["availability_source"],
            "initial_plan_request_id": request["id"],
        }

    async def fetch_plan_revision_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
        revision: int,
    ) -> JsonObject:
        context = await self.fetch_plan_context(athlete_id, plan_id)
        if int(context["revision"]) != revision:
            raise PlanningRepositoryNotFoundError
        return context

    async def fetch_previous_available_dates(
        self,
        athlete_id: UUID,
        week_start: date,
    ) -> tuple[date, ...]:
        previous = week_start - timedelta(days=7)
        for plan_id, plan in self._plans.items():
            if (
                self._plan_owners[plan_id] == athlete_id
                and date.fromisoformat(str(plan["week_start"])) == previous
                and plan["active_revision"] is not None
            ):
                return tuple(
                    date.fromisoformat(str(value)) + timedelta(days=7)
                    for value in plan["available_dates"]
                )
        return ()

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
        if current is not None and current["proposal"]["state"] == "pending":
            old_proposal_id = UUID(str(current["proposal"]["id"]))
            self._proposals[old_proposal_id]["state"] = "expired"
            current["proposal"]["state"] = "expired"
            current["revision_state"] = "expired"
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
                    "scheduled_date": selected["scheduled_date"],
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
            "available_dates": payload["available_dates"],
            "availability_source": payload["availability_source"],
            "workouts": workouts,
            "warnings": warnings,
            "proposal": proposal,
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

    async def create_swipe_draft(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        existing = next(
            (
                row
                for draft_id, row in self._swipe_drafts.items()
                if self._swipe_draft_owners[draft_id] == athlete_id
                and row["week_start"] == payload["week_start"]
                and row["state"] in {"collecting", "placement"}
            ),
            None,
        )
        if existing is not None and (
            existing["context_fingerprint"] == payload["context_fingerprint"]
        ):
            return dict(existing)
        if existing is not None:
            existing["state"] = "cancelled"
            existing["current_template_id"] = None
            existing["revision"] = int(existing["revision"]) + 1
        draft_id = uuid4()
        row = {
            "id": str(draft_id),
            "athlete_id": str(athlete_id),
            **payload,
            "accepted_template_ids": [],
            "passed_template_ids": [],
            "decision_history": [],
            "placements": {},
            "state": payload["state"],
            "revision": 1,
            "proposal_id": None,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
            "submitted_at": None,
        }
        self._swipe_drafts[draft_id] = row
        self._swipe_draft_owners[draft_id] = athlete_id
        return dict(row)

    async def fetch_swipe_draft(
        self,
        access_token: str,
        draft_id: UUID,
    ) -> JsonObject:
        if self._swipe_draft_owners.get(draft_id) != self._owner(access_token):
            raise PlanningRepositoryNotFoundError
        return dict(self._swipe_drafts[draft_id])

    async def update_swipe_draft(
        self,
        athlete_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        payload: JsonObject,
    ) -> JsonObject:
        if self._swipe_draft_owners.get(draft_id) != athlete_id:
            raise PlanningRepositoryNotFoundError
        row = self._swipe_drafts[draft_id]
        if int(row["revision"]) != expected_revision:
            raise PlanningRepositoryConflictError(
                "swipe_draft_stale",
                "The swipe draft changed after this action was prepared.",
            )
        if row["state"] not in {"collecting", "placement"}:
            raise PlanningRepositoryConflictError(
                "swipe_draft_closed",
                "This swipe draft is already closed.",
            )
        for key in (
            "accepted_template_ids",
            "passed_template_ids",
            "current_template_id",
            "decision_history",
            "placements",
            "state",
            "proposal_id",
        ):
            row[key] = payload[key]
        if payload["state"] == "submitted":
            row["plan_id"] = payload["plan_id"]
            row["submitted_at"] = _NOW.isoformat()
        row["revision"] = expected_revision + 1
        row["updated_at"] = _NOW.isoformat()
        return dict(row)

    async def set_plan_proposal_explanation(
        self,
        athlete_id: UUID,
        proposal_id: UUID,
        explanation: str,
    ) -> str:
        if self._proposal_owners.get(proposal_id) != athlete_id:
            raise PlanningRepositoryNotFoundError
        proposal = self._proposals[proposal_id]
        if proposal["state"] == "pending" and proposal["public_explanation"] in {
            "A deterministic weekly plan is ready for review.",
            "A rest-only weekly revision is ready for review.",
        }:
            proposal["public_explanation"] = explanation
            for plan in self._plans.values():
                if plan["proposal"]["id"] == str(proposal_id):
                    plan["proposal"] = proposal
        return str(proposal["public_explanation"])

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
                    "available_dates": plan["available_dates"],
                }
        raise PlanningRepositoryNotFoundError

    async def move_planned_workout(
        self,
        athlete_id: UUID,
        workout_id: UUID,
        expected_revision: int,
        scheduled_date: date,
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
                        workout["scheduled_date"] = scheduled_date.isoformat()
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
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        return tuple(
            workout
            for plan_id, plan in self._plans.items()
            if self._plan_owners[plan_id] == owner
            and plan["active_revision"] is not None
            for workout in plan["workouts"]
            if from_date <= date.fromisoformat(str(workout["scheduled_date"])) < to_date
        )

    async def fetch_calendar_rest_days(
        self,
        access_token: str,
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        rows: list[JsonObject] = []
        for plan_id, plan in self._plans.items():
            if self._plan_owners[plan_id] != owner or plan["active_revision"] is None:
                continue
            week_start = date.fromisoformat(str(plan["week_start"]))
            workout_dates = {
                date.fromisoformat(str(workout["scheduled_date"]))
                for workout in plan["workouts"]
                if workout["status"] != "cancelled"
            }
            for offset in range(7):
                current = week_start + timedelta(days=offset)
                if current not in workout_dates and from_date <= current < to_date:
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


def _availability_payload() -> list[str]:
    return [f"2026-08-{day:02d}" for day in (3, 5, 7)]


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
            "available_dates": _availability_payload(),
            "confirmed_injuries": [],
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _create_swipe_draft(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/weekly-plans/swipe-drafts",
        headers=_headers(),
        json={
            "week_start": "2026-08-03",
            "available_dates": _availability_payload(),
            "confirmed_injuries": [],
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_swipe_draft_is_owner_scoped_idempotent_and_submits_only_pending(
    planning_client: TestClient,
) -> None:
    draft = _create_swipe_draft(planning_client)
    assert draft["state"] == "collecting"
    assert draft["target_workout_count"] == sum(draft["target_composition"].values())
    assert draft["current_candidate"] is not None
    assert "tss" not in str(draft).casefold()

    hidden = planning_client.get(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}",
        headers=_headers("athlete-b"),
    )
    assert hidden.status_code == 404

    first_candidate = draft["current_candidate"]["id"]
    passed = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "action": "pass",
            "candidate_template_id": first_candidate,
        },
    )
    assert passed.status_code == 200, passed.text
    draft = cast(dict[str, Any], passed.json())
    assert draft["passed_count"] == 1
    assert draft["current_candidate"]["id"] != first_candidate

    undone = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={"expected_revision": draft["revision"], "action": "undo"},
    )
    assert undone.status_code == 200, undone.text
    draft = cast(dict[str, Any], undone.json())
    assert draft["current_candidate"]["id"] == first_candidate

    first_revision = draft["revision"]
    accepted = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={
            "expected_revision": first_revision,
            "action": "accept",
            "candidate_template_id": first_candidate,
        },
    )
    assert accepted.status_code == 200, accepted.text
    draft = cast(dict[str, Any], accepted.json())

    duplicate = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={
            "expected_revision": first_revision,
            "action": "accept",
            "candidate_template_id": first_candidate,
        },
    )
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json()["revision"] == draft["revision"]
    assert len(duplicate.json()["accepted_workouts"]) == 1

    stale = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={"expected_revision": first_revision, "action": "undo"},
    )
    assert stale.status_code == 409

    while draft["state"] == "collecting":
        current = draft["current_candidate"]
        assert current is not None and draft["exhausted"] is False
        response = planning_client.post(
            f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "action": "accept",
                "candidate_template_id": current["id"],
            },
        )
        assert response.status_code == 200, response.text
        draft = cast(dict[str, Any], response.json())

    assert draft["state"] == "placement"
    assert len(draft["accepted_workouts"]) == draft["target_workout_count"]
    assert isinstance(draft["warnings"], list)

    incomplete = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "manual",
        },
    )
    assert incomplete.status_code == 409

    for workout, scheduled_date in zip(
        draft["accepted_workouts"],
        draft["available_dates"],
        strict=True,
    ):
        placement = planning_client.put(
            (
                f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"
                f"/placements/{workout['id']}"
            ),
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "scheduled_date": scheduled_date,
            },
        )
        assert placement.status_code == 200, placement.text
        draft = cast(dict[str, Any], placement.json())

    submitted = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "manual",
        },
    )
    assert submitted.status_code == 201, submitted.text
    result = submitted.json()
    assert result["proposal"]["state"] == "pending"
    assert result["plan"]["revision_state"] == "pending_approval"
    assert "tss" not in str(result).casefold()


def test_swipe_draft_preserves_rest_only_week_and_automatic_placement(
    planning_client: TestClient,
) -> None:
    created = planning_client.post(
        "/api/v1/weekly-plans/swipe-drafts",
        headers=_headers(),
        json={
            "week_start": "2026-08-03",
            "available_dates": _availability_payload(),
            "confirmed_injuries": ["swim", "bike", "run"],
        },
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    assert draft["state"] == "placement"
    assert draft["target_workout_count"] == 0
    assert draft["accepted_workouts"] == []
    assert draft["current_candidate"] is None

    submitted = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "automatic",
        },
    )
    assert submitted.status_code == 201, submitted.text
    result = submitted.json()
    assert result["proposal"]["state"] == "pending"
    assert result["plan"]["workouts"] == []
    assert len(result["plan"]["rest_days"]) == 7


def test_swipe_draft_allows_multiple_workouts_on_one_available_date(
    planning_client: TestClient,
) -> None:
    created = planning_client.post(
        "/api/v1/weekly-plans/swipe-drafts",
        headers=_headers(),
        json={
            "week_start": "2026-08-03",
            "available_dates": ["2026-08-03", "2026-08-05"],
            "confirmed_injuries": [],
        },
    )
    assert created.status_code == 201, created.text
    draft = cast(dict[str, Any], created.json())

    while draft["state"] == "collecting":
        current = draft["current_candidate"]
        assert current is not None
        accepted = planning_client.post(
            f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "action": "accept",
                "candidate_template_id": current["id"],
            },
        )
        assert accepted.status_code == 200, accepted.text
        draft = cast(dict[str, Any], accepted.json())

    shared_date = draft["available_dates"][0]
    for workout in draft["accepted_workouts"]:
        placement = planning_client.put(
            (
                f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}"
                f"/placements/{workout['id']}"
            ),
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "scheduled_date": shared_date,
            },
        )
        assert placement.status_code == 200, placement.text
        draft = cast(dict[str, Any], placement.json())

    submitted = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/submit",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "placement_mode": "manual",
        },
    )
    assert submitted.status_code == 201, submitted.text
    result = submitted.json()
    assert {
        workout["scheduled_date"] for workout in result["plan"]["workouts"]
    } == {shared_date}
    assert "tss" not in str(result).casefold()


def test_swipe_draft_exhaustion_is_recoverable_without_lowering_target(
    planning_client: TestClient,
) -> None:
    draft = _create_swipe_draft(planning_client)
    target = draft["target_workout_count"]

    while draft["current_candidate"] is not None:
        passed = planning_client.post(
            f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
            headers=_headers(),
            json={
                "expected_revision": draft["revision"],
                "action": "pass",
                "candidate_template_id": draft["current_candidate"]["id"],
            },
        )
        assert passed.status_code == 200, passed.text
        draft = passed.json()

    assert draft["exhausted"] is True
    assert draft["target_workout_count"] == target
    reset = planning_client.post(
        f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
        headers=_headers(),
        json={
            "expected_revision": draft["revision"],
            "action": "reset_passed",
        },
    )
    assert reset.status_code == 200, reset.text
    recovered = reset.json()
    assert recovered["exhausted"] is False
    assert recovered["passed_count"] == 0
    assert recovered["current_candidate"] is not None
    assert recovered["target_workout_count"] == target


def test_plan_generation_requires_authentication(
    planning_client: TestClient,
) -> None:
    response = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        json={
            "week_start": "2026-08-03",
            "available_dates": _availability_payload(),
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
    assert "weekvoorstel" in first["proposal"]["public_explanation"].lower()
    assert (
        first["plan"]["proposal"]["public_explanation"]
        == first["proposal"]["public_explanation"]
    )
    assert (
        repeated["proposal"]["public_explanation"]
        == first["proposal"]["public_explanation"]
    )
    serialized = json_normalized = str(first).lower().replace("_", "")
    assert "tss" not in serialized
    assert "plannedtss" not in json_normalized
    assert first["plan"]["available_dates"] == _availability_payload()
    assert first["plan"]["availability_source"] == "explicit"
    assert all(
        "scheduled_date" in workout and "scheduled_at" not in workout
        for workout in first["plan"]["workouts"]
    )


def test_previous_week_availability_requires_an_explicit_action_and_active_week(
    planning_client: TestClient,
) -> None:
    unavailable = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers("athlete-b"),
        json={"week_start": "2026-08-03", "reuse_previous_week": True},
    )
    assert unavailable.status_code == 409
    assert (
        unavailable.json()["error"]["code"] == "previous_week_availability_unavailable"
    )

    created = _create_proposal(planning_client)
    approved = planning_client.post(
        f"/api/v1/change-proposals/{created['proposal']['id']}/approve",
        headers=_headers(),
        json={"expected_base_revision": 0},
    )
    assert approved.status_code == 200
    copied = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers(),
        json={"week_start": "2026-08-10", "reuse_previous_week": True},
    )

    assert copied.status_code == 201, copied.text
    assert copied.json()["plan"]["availability_source"] == "previous_week"
    assert copied.json()["plan"]["available_dates"] == [
        "2026-08-10",
        "2026-08-12",
        "2026-08-14",
    ]


def test_pending_workout_replacement_is_revision_and_proposal_bound(
    planning_client: TestClient,
) -> None:
    created = _create_proposal(planning_client)
    plan = created["plan"]
    workout = plan["workouts"][0]
    alternatives = planning_client.get(
        (
            f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
            f"{workout['id']}/alternatives"
        ),
        headers=_headers(),
        params={"expected_revision": plan["revision"]},
    )

    assert alternatives.status_code == 200, alternatives.text
    body = alternatives.json()
    assert body["proposal_id"] == created["proposal"]["id"]
    assert body["can_remove"] is False
    assert body["alternatives"]
    rejected_removal = planning_client.post(
        (
            f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
            f"{workout['id']}/edit-proposals"
        ),
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "expected_proposal_id": created["proposal"]["id"],
            "replacement_template_id": None,
        },
    )
    assert rejected_removal.status_code == 409
    replacement = planning_client.post(
        (
            f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
            f"{workout['id']}/edit-proposals"
        ),
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "expected_proposal_id": created["proposal"]["id"],
            "replacement_template_id": body["alternatives"][0]["id"],
        },
    )

    assert replacement.status_code == 201, replacement.text
    assert replacement.json()["plan"]["revision"] == plan["revision"] + 1
    assert replacement.json()["proposal"]["id"] != created["proposal"]["id"]
    stale = planning_client.post(
        (
            f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/"
            f"{workout['id']}/edit-proposals"
        ),
        headers=_headers(),
        json={
            "expected_revision": plan["revision"],
            "expected_proposal_id": created["proposal"]["id"],
            "replacement_template_id": body["alternatives"][0]["id"],
        },
    )
    assert stale.status_code in {404, 409}


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
            "from": "2026-08-03",
            "to": "2026-08-10",
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
            "scheduled_date": "2026-08-04",
        },
    )
    stale_replay = planning_client.patch(
        f"/api/v1/planned-workouts/{workout_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "scheduled_date": "2026-08-04",
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
            "available_dates": _availability_payload(),
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
                    "scheduled_date": workout["scheduled_date"],
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
                    "scheduled_date": workout["scheduled_date"],
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
                    "scheduled_date": plan["workouts"][0]["scheduled_date"],
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


def test_generic_plan_endpoint_rejects_direct_field_test_template_selection(
    planning_client: TestClient,
) -> None:
    field_test_template_id = "56000000-0000-0000-0000-000000000009"

    response = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers(),
        json={
            "week_start": "2026-08-03",
            "available_dates": _availability_payload(),
            "selected_template_ids": [field_test_template_id],
            "fixed_workout_dates": [
                {
                    "template_id": field_test_template_id,
                    "scheduled_date": "2026-08-03",
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "field_test_assignment_required"


def test_confirmed_injury_is_excluded_from_pending_plan(
    planning_client: TestClient,
) -> None:
    response = planning_client.post(
        "/api/v1/weekly-plans/proposals",
        headers=_headers("athlete-b"),
        json={
            "week_start": "2026-08-03",
            "available_dates": _availability_payload(),
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
