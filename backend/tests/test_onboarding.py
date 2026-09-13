"""Phase 4 API tests for validation, ownership, zones, and completion."""

from collections.abc import Iterator
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.calibration.service import is_current_mvp_setup
from app.modules.onboarding.repository import (
    JsonObject,
    RepositoryConflictError,
    RepositoryNotFoundError,
)
from app.modules.onboarding.service import OnboardingService
from app.modules.onboarding.versioning import (
    CURRENT_ONBOARDING_VERSION,
    CURRENT_RULESET_VERSION,
)

_NOW = datetime(2026, 7, 27, 12, tzinfo=timezone.utc)


def test_discipline_setup_projection_omits_owner_identity() -> None:
    setup = OnboardingService._discipline_setup(
        {
            "athlete_id": str(uuid4()),
            "discipline": "swim",
            "setup_route": "calibration_week",
            "guidance_mode": "pace",
            "setup_status": "calibration_pending",
            "protocol_id": "start23_week1_swim_calibration_v1",
            "pool_length_meters": 25,
            "threshold_status": "unknown",
            "zone_status": "unknown",
            "source": "week1_calibration",
            "validation_status": "not_assessed",
            "confidence": "not_assessed",
            "known_thresholds": [],
            "known_zone_profiles": [],
            "revision": 1,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
    )

    assert setup.discipline.value == "swim"
    assert "athlete_id" not in setup.model_dump()


def test_legacy_rpe_only_setup_remains_readable() -> None:
    setup = OnboardingService._discipline_setup(
        {
            "athlete_id": str(uuid4()),
            "discipline": "run",
            "setup_route": "rpe_only",
            "guidance_mode": "rpe_only",
            "setup_status": "configured",
            "protocol_id": None,
            "pool_length_meters": None,
            "threshold_status": "unknown",
            "zone_status": "unknown",
            "source": "none",
            "validation_status": "not_assessed",
            "confidence": "not_assessed",
            "known_thresholds": [],
            "known_zone_profiles": [],
            "revision": 1,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
    )

    assert setup.setup_route.value == "rpe_only"
    assert setup.guidance_mode.value == "rpe_only"
    assert not is_current_mvp_setup(setup)


def test_legacy_profile_and_history_values_are_not_reinterpreted() -> None:
    profile = OnboardingService._profile(
        {
            "athlete_id": str(uuid4()),
            "date_of_birth": "1990-05-20",
            "height_cm": "181.5",
            "weight_kg": "74.2",
            "resting_heart_rate_bpm": 52,
            "motivation_text": "Historical free text",
            "motivation_tag": "historical-tag",
            "timezone": "Europe/Amsterdam",
            "onboarding_status": "in_progress",
            "revision": 1,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
    )
    history = tuple(
        OnboardingService._history(
            {
                "discipline": discipline,
                "weekly_minutes": 90,
                "experience_years": "2.0",
                "confirmed_at": _NOW.isoformat(),
                "updated_at": _NOW.isoformat(),
            }
        )
        for discipline in ("swim", "bike", "run")
    )

    assert profile is not None
    assert {
        "height_cm",
        "weight_kg",
        "motivation_text",
        "motivation_tag",
    }.isdisjoint(profile.model_dump())
    assert all(entry.average_weekly_distance is None for entry in history)
    assert OnboardingService._history_is_complete(history) is False


class TokenVerifier:
    """Resolve deterministic local tokens without a Supabase network call."""

    def __init__(self, token_owners: dict[str, UUID]) -> None:
        self._token_owners = token_owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            owner = self._token_owners[access_token]
        except KeyError as error:
            raise InvalidAccessTokenError from error
        return AuthenticatedIdentity(
            user_id=owner, role="authenticated", athlete_id=owner
        )


class MemoryOnboardingRepository:
    """Owner-partitioned repository implementing the same Phase 4 contract."""

    def __init__(self, token_owners: dict[str, UUID]) -> None:
        self._token_owners = token_owners
        self._states: dict[UUID, JsonObject] = {
            owner: {
                "profile": None,
                "session": None,
                "training_history": [],
                "goals": [],
                "zone_profiles": [],
                "zone_metrics": [],
                "zone_boundaries": [],
            }
            for owner in token_owners.values()
        }
        self._initial_requests: dict[UUID, UUID] = {}
        self._proposals: dict[UUID, JsonObject] = {}

    def _owner(self, access_token: str) -> UUID:
        return self._token_owners[access_token]

    async def fetch_state(self, access_token: str, athlete_id: UUID) -> JsonObject:
        assert athlete_id == self._owner(access_token)
        state = deepcopy(self._states[athlete_id])
        state["zone_proposals"] = [
            {
                "id": str(proposal_id),
                "target_zone_profile_id": str(proposal["target_id"]),
                "base_zone_profile_id": (
                    str(proposal["base_id"])
                    if proposal["base_id"] is not None
                    else None
                ),
            }
            for proposal_id, proposal in self._proposals.items()
            if proposal["owner"] == athlete_id and proposal["state"] == "pending"
        ]
        return state

    async def upsert_profile(
        self,
        access_token: str,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        assert athlete_id == self._owner(access_token)
        state = self._states[athlete_id]
        existing = state["profile"]
        revision = int(existing["revision"]) + 1 if existing else 1
        created_at = existing["created_at"] if existing else _NOW.isoformat()
        row = {
            "athlete_id": str(athlete_id),
            "date_of_birth": None,
            "height_cm": None,
            "weight_kg": None,
            "resting_heart_rate_bpm": None,
            "motivation_text": None,
            "motivation_tag": None,
            "timezone": "UTC",
            "timezone_source": None,
            "timezone_confirmed_at": None,
            "heart_rate_monitor_confirmed_at": None,
            "onboarding_status": "in_progress",
            "revision": revision,
            "created_at": created_at,
            "updated_at": _NOW.isoformat(),
            **(existing or {}),
            **values,
        }
        row["revision"] = revision
        row["updated_at"] = _NOW.isoformat()
        state["profile"] = row
        return deepcopy(row)

    async def fetch_identifying_profile(
        self, access_token: str, athlete_id: UUID
    ) -> JsonObject | None:
        assert athlete_id == self._owner(access_token)
        profile = self._states[athlete_id]["profile"]
        if profile is None:
            return None
        return {
            "athlete_id": str(athlete_id),
            "first_name": profile.get("first_name"),
            "last_name": profile.get("last_name"),
            "revision": profile["revision"],
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"],
        }

    async def fetch_physiology_profile(
        self, access_token: str, athlete_id: UUID
    ) -> JsonObject | None:
        assert athlete_id == self._owner(access_token)
        profile = self._states[athlete_id]["profile"]
        if profile is None:
            return None
        return {
            "athlete_id": str(athlete_id),
            "date_of_birth": profile.get("date_of_birth"),
            "resting_heart_rate_bpm": profile.get("resting_heart_rate_bpm"),
            "revision": profile["revision"],
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"],
        }

    async def fetch_operational_profile(
        self, access_token: str, athlete_id: UUID
    ) -> JsonObject | None:
        assert athlete_id == self._owner(access_token)
        profile = self._states[athlete_id]["profile"]
        if profile is None:
            return None
        return {
            "athlete_id": str(athlete_id),
            "timezone": profile["timezone"],
            "timezone_source": profile.get("timezone_source"),
            "timezone_confirmed_at": profile.get("timezone_confirmed_at"),
            "heart_rate_monitor_confirmed_at": profile.get(
                "heart_rate_monitor_confirmed_at"
            ),
            "onboarding_status": profile["onboarding_status"],
            "revision": profile["revision"],
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"],
        }

    async def upsert_identifying_profile(
        self, access_token: str, values: JsonObject
    ) -> JsonObject:
        owner = self._owner(access_token)
        await self.upsert_profile(access_token, owner, values)
        result = await self.fetch_identifying_profile(access_token, owner)
        assert result is not None
        return result

    async def upsert_physiology_profile(
        self, access_token: str, values: JsonObject
    ) -> JsonObject:
        owner = self._owner(access_token)
        await self.upsert_profile(access_token, owner, values)
        result = await self.fetch_physiology_profile(access_token, owner)
        assert result is not None
        return result

    async def upsert_operational_profile(
        self, access_token: str, values: JsonObject
    ) -> JsonObject:
        owner = self._owner(access_token)
        persisted = dict(values)
        if persisted.pop("timezone_confirmed", None):
            persisted["timezone_confirmed_at"] = _NOW.isoformat()
        if persisted.pop("heart_rate_monitor_confirmed", None):
            persisted["heart_rate_monitor_confirmed_at"] = _NOW.isoformat()
        await self.upsert_profile(access_token, owner, persisted)
        result = await self.fetch_operational_profile(access_token, owner)
        assert result is not None
        return result

    async def replace_training_history(
        self,
        access_token: str,
        entries: list[JsonObject],
    ) -> list[JsonObject]:
        owner = self._owner(access_token)
        rows = [
            {
                "athlete_id": str(owner),
                **entry,
                "history_window_months": None,
                "previous_month_weekly_minutes": str(
                    Decimal(entry["average_hours_per_week"]) * 60
                ),
                "baseline_model_version": "phase-13-joren-ruleset-1",
                "source": "athlete",
                "confirmed_at": _NOW.isoformat(),
                "updated_at": _NOW.isoformat(),
            }
            for entry in entries
        ]
        self._states[owner]["training_history"] = rows
        return deepcopy(rows)

    async def save_primary_goal(
        self,
        access_token: str,
        goal_id: UUID | None,
        values: JsonObject,
    ) -> JsonObject:
        owner = self._owner(access_token)
        goals: list[JsonObject] = self._states[owner]["goals"]
        if goal_id is None and goals:
            legacy = next(
                (goal for goal in goals if goal.get("race_type") is None),
                None,
            )
            if legacy is None:
                raise RepositoryConflictError
            legacy.update(values)
            legacy["revision"] = int(legacy["revision"]) + 1
            legacy["updated_at"] = _NOW.isoformat()
            return deepcopy(legacy)
        if goal_id is not None:
            matching = next(
                (goal for goal in goals if goal["id"] == str(goal_id)),
                None,
            )
            if matching is None:
                raise RepositoryConflictError
            matching.update(values)
            matching["revision"] = int(matching["revision"]) + 1
            matching["updated_at"] = _NOW.isoformat()
            return deepcopy(matching)
        row = {
            "id": str(uuid4()),
            "athlete_id": str(owner),
            "priority": "A",
            "goal_type": "race",
            **values,
            "status": "active",
            "revision": 1,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
        goals.append(row)
        return deepcopy(row)

    async def save_zone_profile(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        owner = self._owner(access_token)
        state = self._states[owner]
        profiles: list[JsonObject] = state["zone_profiles"]
        discipline_profiles = [
            profile
            for profile in profiles
            if profile["discipline"] == values["discipline"]
        ]
        active = next(
            (
                profile
                for profile in discipline_profiles
                if profile["status"] == "active"
            ),
            None,
        )
        profile_id = uuid4()
        profile_status = "active" if active is None else "pending"
        profile = {
            "id": str(profile_id),
            "athlete_id": str(owner),
            "discipline": values["discipline"],
            "version": len(discipline_profiles) + 1,
            "setup_method": values["setup_method"],
            "status": profile_status,
            "validated": values["setup_method"] == "manual",
            "fallback_active": values["setup_method"] == "fallback",
            "needs_testing": values["setup_method"] == "fallback",
            "requires_review": values["requires_review"],
            "review_reason": values["review_reason"],
            "ruleset_version": values["ruleset_version"],
            "effective_from": (
                _NOW.isoformat() if profile_status == "active" else None
            ),
            "created_at": _NOW.isoformat(),
        }
        profiles.append(profile)
        if values["metric_kind"] is not None:
            state["zone_metrics"].append(
                {
                    "zone_profile_id": str(profile_id),
                    "athlete_id": str(owner),
                    "metric_kind": values["metric_kind"],
                    "value": values["metric_value"],
                }
            )
        state["zone_boundaries"].extend(
            {
                "zone_profile_id": str(profile_id),
                "athlete_id": str(owner),
                **boundary,
            }
            for boundary in values["boundaries"]
        )
        proposal_id = uuid4() if active is not None else None
        if proposal_id is not None:
            assert active is not None
            self._proposals[proposal_id] = {
                "owner": owner,
                "target_id": profile_id,
                "base_id": UUID(str(active["id"])),
                "state": "pending",
            }
        return {
            "profile_id": str(profile_id),
            "version": profile["version"],
            "status": profile_status,
            "proposal_id": str(proposal_id) if proposal_id is not None else None,
        }

    async def save_fallback_zone_profile(
        self,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        access_token = next(
            token for token, owner in self._token_owners.items() if owner == athlete_id
        )
        return await self.save_zone_profile(access_token, values)

    async def save_calculated_zone_profile(
        self,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        state = self._states[athlete_id]
        profiles: list[JsonObject] = state["zone_profiles"]
        discipline_profiles = [
            profile
            for profile in profiles
            if profile["discipline"] == values["discipline"]
        ]
        active = next(
            (
                profile
                for profile in discipline_profiles
                if profile["status"] == "active"
            ),
            None,
        )
        profile_id = uuid4()
        proposal_id = uuid4()
        profile = {
            "id": str(profile_id),
            "athlete_id": str(athlete_id),
            "discipline": values["discipline"],
            "version": len(discipline_profiles) + 1,
            "setup_method": "calculated",
            "status": "pending",
            "validated": False,
            "fallback_active": False,
            "needs_testing": False,
            "requires_review": True,
            "review_reason": "athlete_confirmation_required",
            "ruleset_version": "start23-zone-model-1.0",
            "zone_model_version": "start23-zone-model-1.0",
            "source_method": values["source_method"],
            "source_quality": values["source_quality"],
            "calculated_at": _NOW.isoformat(),
            "review_status": "pending_athlete_confirmation",
            "reviewer_id": None,
            "reviewed_at": None,
            "evidence_version": "voorstel-start23-zone-1-5-rekenmodel-v1.0",
            "effective_from": None,
            "created_at": _NOW.isoformat(),
            "metric_profiles": deepcopy(values["metric_profiles"]),
        }
        profiles.append(profile)
        self._proposals[proposal_id] = {
            "owner": athlete_id,
            "target_id": profile_id,
            "base_id": UUID(str(active["id"])) if active is not None else None,
            "state": "pending",
        }
        return {
            "profile_id": str(profile_id),
            "version": profile["version"],
            "status": "pending",
            "proposal_id": str(proposal_id),
            "base_zone_profile_id": (str(active["id"]) if active is not None else None),
        }

    async def complete_onboarding(
        self,
        access_token: str,
        expected_session_revision: int,
    ) -> UUID:
        owner = self._owner(access_token)
        existing_session = self._states[owner]["session"]
        if existing_session is not None:
            if (
                existing_session.get("completed_onboarding_version")
                == CURRENT_ONBOARDING_VERSION
                and existing_session.get("completed_ruleset_version")
                == CURRENT_RULESET_VERSION
            ):
                return self._initial_requests[owner]
            if int(existing_session["revision"]) != expected_session_revision:
                raise RepositoryConflictError
        elif expected_session_revision != 0:
            raise RepositoryConflictError
        request_id = self._initial_requests.setdefault(owner, uuid4())
        state = self._states[owner]
        state["profile"]["onboarding_status"] = "completed"
        state["session"] = {
            "athlete_id": str(owner),
            "status": "completed",
            "current_step": "completed",
            "completed_steps": ["profile", "history", "goal", "zones", "review"],
            "initial_plan_request_id": str(request_id),
            "completed_onboarding_version": CURRENT_ONBOARDING_VERSION,
            "completed_ruleset_version": CURRENT_RULESET_VERSION,
            "revision": (
                int(existing_session["revision"]) + 1
                if existing_session is not None
                else 1
            ),
        }
        return request_id

    async def approve_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_zone_profile_id: UUID | None,
    ) -> JsonObject:
        owner = self._owner(access_token)
        proposal = self._proposals.get(proposal_id)
        if (
            proposal is None
            or proposal["owner"] != owner
            or proposal["state"] != "pending"
        ):
            raise RepositoryNotFoundError
        if proposal["base_id"] != expected_base_zone_profile_id:
            raise RepositoryConflictError
        profiles: list[JsonObject] = self._states[owner]["zone_profiles"]
        base = (
            next(
                profile
                for profile in profiles
                if profile["id"] == str(proposal["base_id"])
            )
            if proposal["base_id"] is not None
            else None
        )
        target = next(
            profile
            for profile in profiles
            if profile["id"] == str(proposal["target_id"])
        )
        if (base is not None and base["status"] != "active") or target[
            "status"
        ] != "pending":
            raise RepositoryConflictError
        if base is not None:
            base["status"] = "superseded"
        target["status"] = "active"
        target["effective_from"] = _NOW.isoformat()
        if target["setup_method"] == "calculated":
            target["review_status"] = "confirmed_by_athlete"
        proposal["state"] = "applied"
        return {
            "proposal_id": str(proposal_id),
            "state": "applied",
            "active_zone_profile_id": str(proposal["target_id"]),
            "superseded_zone_profile_id": (
                str(proposal["base_id"]) if proposal["base_id"] is not None else None
            ),
        }

    async def reject_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        owner = self._owner(access_token)
        proposal = self._proposals.get(proposal_id)
        if (
            proposal is None
            or proposal["owner"] != owner
            or proposal["state"] != "pending"
        ):
            raise RepositoryNotFoundError
        profiles: list[JsonObject] = self._states[owner]["zone_profiles"]
        target = next(
            profile
            for profile in profiles
            if profile["id"] == str(proposal["target_id"])
        )
        target["status"] = "rejected"
        if target["setup_method"] == "calculated":
            target["review_status"] = "rejected_by_athlete"
        proposal["state"] = "rejected"
        return {
            "proposal_id": str(proposal_id),
            "state": "rejected",
            "active_zone_profile_id": (
                str(proposal["base_id"]) if proposal["base_id"] is not None else None
            ),
            "superseded_zone_profile_id": None,
        }

    async def aclose(self) -> None:
        return None


@pytest.fixture
def onboarding_context() -> Iterator[tuple[TestClient, UUID, UUID]]:
    athlete_a = uuid4()
    athlete_b = uuid4()
    token_owners = {"athlete-a": athlete_a, "athlete-b": athlete_b}
    repository = MemoryOnboardingRepository(token_owners)
    application = create_app(
        Settings(environment="test"),
        access_token_verifier=TokenVerifier(token_owners),
        onboarding_repository=repository,
    )
    with TestClient(application) as client:
        yield client, athlete_a, athlete_b


def _headers(token: str = "athlete-a") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _complete_profile(client: TestClient, token: str = "athlete-a") -> None:
    response = client.patch(
        "/api/v1/me/profile",
        headers=_headers(token),
        json={
            "date_of_birth": "1990-05-20",
            "resting_heart_rate_bpm": 52,
        },
    )
    assert response.status_code == 200
    monitor = client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(token),
        json={"heart_rate_monitor_confirmed": True},
    )
    timezone_response = client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(token),
        json={
            "timezone": "Europe/Amsterdam",
            "timezone_source": "manual",
            "timezone_confirmed": True,
        },
    )
    assert monitor.status_code == 200
    assert timezone_response.status_code == 200
    assert {
        "height_cm",
        "weight_kg",
        "motivation_text",
        "motivation_tag",
    }.isdisjoint(response.json())


def _complete_history(client: TestClient, token: str = "athlete-a") -> None:
    response = client.put(
        "/api/v1/me/training-history",
        headers=_headers(token),
        json={
            "entries": [
                {"discipline": discipline, "average_hours_per_week": hours}
                for discipline, hours in (("swim", "2"), ("bike", "4"), ("run", "3"))
            ]
        },
    )
    assert response.status_code == 200


def _complete_goal(client: TestClient, token: str = "athlete-a") -> UUID:
    response = client.post(
        "/api/v1/me/goals",
        headers=_headers(token),
        json={
            "race_type": "triathlon",
            "race_name": "Amsterdam Olympic triathlon",
            "race_date": (date.today() + timedelta(days=120)).isoformat(),
            "swim_distance_meters": 1500,
            "bike_distance_meters": 40000,
            "run_distance_meters": 10000,
            "total_target_time_seconds": 10800,
            "specific_focus": "Finish with an even run.",
        },
    )
    assert response.status_code == 201
    assert "feasibility_score" not in response.json()
    return UUID(response.json()["id"])


def _boundaries(descending: bool = False) -> list[dict[str, Any]]:
    if descending:
        return [
            {
                "zone_number": zone,
                "lower_value": 150 - zone * 10,
                "upper_value": 160 - zone * 10,
            }
            for zone in range(1, 6)
        ]
    return [
        {
            "zone_number": zone,
            "lower_value": 90 + zone * 10,
            "upper_value": 100 + zone * 10,
        }
        for zone in range(1, 6)
    ]


def _manual_zone(
    client: TestClient,
    discipline: str,
    metric_kind: str,
    metric_value: int,
    *,
    descending: bool = False,
    token: str = "athlete-a",
) -> dict[str, Any]:
    response = client.put(
        f"/api/v1/me/zones/{discipline}",
        headers=_headers(token),
        json={
            "setup_method": "manual",
            "confirmed": True,
            "metric_kind": metric_kind,
            "metric_value": metric_value,
            "boundaries": _boundaries(descending),
        },
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def test_onboarding_requires_authentication(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    response = client.get("/api/v1/onboarding")

    assert response.status_code == 401


def test_goal_options_distinguish_race_from_unavailable_personal_goals(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context

    unauthenticated = client.get("/api/v1/onboarding/goal-options")
    response = client.get("/api/v1/onboarding/goal-options", headers=_headers())

    assert unauthenticated.status_code == 401
    assert response.status_code == 200
    assert response.json() == [
        {
            "goal_kind": "race_event",
            "goal_family": "race_event",
            "label": "Wedstrijd of evenement",
            "availability": "available",
            "requires_target_date": True,
            "cycle_anchor": "race_date",
            "unavailable_reason": None,
        },
        {
            "goal_kind": "personal_goal",
            "goal_family": "general_fitness",
            "label": "Algemene fitheid",
            "availability": "coming_later",
            "requires_target_date": False,
            "cycle_anchor": "cycle_week_1",
            "unavailable_reason": "deterministic_rules_not_approved",
        },
        {
            "goal_kind": "personal_goal",
            "goal_family": "weight_loss",
            "label": "Gewichtsverlies",
            "availability": "coming_later",
            "requires_target_date": False,
            "cycle_anchor": "cycle_week_1",
            "unavailable_reason": "deterministic_rules_not_approved",
        },
        {
            "goal_kind": "personal_goal",
            "goal_family": "muscle_gain",
            "label": "Spieropbouw",
            "availability": "coming_later",
            "requires_target_date": False,
            "cycle_anchor": "cycle_week_1",
            "unavailable_reason": "deterministic_rules_not_approved",
        },
    ]
    assert all("tss" not in key.lower() for item in response.json() for key in item)


def test_personal_goal_cannot_be_submitted_as_a_race_goal(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context

    response = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "goal_type": "general_fitness",
            "title": "Build year-round fitness",
            "specific_description": "Train consistently without an event.",
            "measurable_outcome": "Complete three sessions each week.",
            "feasibility_score": 8,
            "target_date": (date.today() + timedelta(days=120)).isoformat(),
            "race_discipline_profile": ["swim", "bike", "run"],
        },
    )

    assert response.status_code == 422


def test_profile_rejects_invalid_timezone_and_authoritative_user_id(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, athlete_b = onboarding_context
    invalid_timezone = client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={"timezone": "Mars/Olympus"},
    )
    override = client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={"athlete_id": str(athlete_b), "timezone": "UTC"},
    )

    assert invalid_timezone.status_code == 422
    assert override.status_code == 422


def test_profile_rejects_values_outside_database_integer_range(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    response = client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={"resting_heart_rate_bpm": 32768},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "retired_field,value",
    [
        ("height_cm", "181.5"),
        ("weight_kg", "74.2"),
        ("motivation_text", "Finish a race."),
        ("motivation_tag", "first-race"),
    ],
)
def test_profile_rejects_retired_write_fields(
    onboarding_context: tuple[TestClient, UUID, UUID],
    retired_field: str,
    value: str,
) -> None:
    client, _, _ = onboarding_context

    response = client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={"timezone": "Europe/Amsterdam", retired_field: value},
    )

    assert response.status_code == 422


def test_training_history_requires_each_triathlon_discipline(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    response = client.put(
        "/api/v1/me/training-history",
        headers=_headers(),
        json={
            "entries": [
                {
                    "discipline": "run",
                    "average_weekly_distance": 30,
                    "distance_unit": "kilometers",
                    "average_sessions_per_week": 3,
                }
            ]
            * 3
        },
    )

    assert response.status_code == 422


def test_history_uses_previous_month_hours_and_keeps_load_private(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    wrong_unit = client.put(
        "/api/v1/me/training-history",
        headers=_headers(),
        json={
            "entries": [
                {
                    "discipline": "swim",
                    "average_weekly_distance": 4000,
                    "distance_unit": "kilometers",
                    "average_sessions_per_week": 2,
                },
                {
                    "discipline": "bike",
                    "average_weekly_distance": 120,
                    "distance_unit": "kilometers",
                    "average_sessions_per_week": 2,
                },
                {
                    "discipline": "run",
                    "average_weekly_distance": 30,
                    "distance_unit": "kilometers",
                    "average_sessions_per_week": 3,
                },
            ]
        },
    )

    assert wrong_unit.status_code == 422

    _complete_history(client)
    state = client.get("/api/v1/onboarding", headers=_headers())
    timestamp = _NOW.isoformat().replace("+00:00", "Z")

    assert state.status_code == 200
    assert [
        row["previous_month_weekly_minutes"] for row in state.json()["training_history"]
    ] == ["120", "240", "180"]
    assert all(
        row["baseline_model_version"] == "phase-13-joren-ruleset-1"
        for row in state.json()["training_history"]
    )
    assert all(
        row["confirmed_at"] == timestamp for row in state.json()["training_history"]
    )
    assert "tss" not in state.text.lower()


def test_only_one_primary_race_goal_and_owned_updates(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    goal_id = _complete_goal(client)
    duplicate = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "race_type": "run",
            "race_name": "Another race",
            "race_date": (date.today() + timedelta(days=180)).isoformat(),
            "run_distance_meters": 10000,
            "total_target_time_seconds": 3600,
        },
    )
    other_athlete_update = client.put(
        f"/api/v1/me/goals/{goal_id}",
        headers=_headers("athlete-b"),
        json={
            "race_type": "run",
            "race_name": "Stolen goal",
            "race_date": (date.today() + timedelta(days=180)).isoformat(),
            "run_distance_meters": 10000,
            "total_target_time_seconds": 3600,
        },
    )

    assert duplicate.status_code == 409
    assert other_athlete_update.status_code == 409


@pytest.mark.parametrize(
    ("race_type", "distances"),
    [
        ("run", {"run_distance_meters": 10000}),
        ("bike", {"bike_distance_meters": 100000}),
        ("swim", {"swim_distance_meters": 3000}),
        (
            "triathlon",
            {
                "swim_distance_meters": 1500,
                "bike_distance_meters": 40000,
                "run_distance_meters": 10000,
            },
        ),
        (
            "duathlon",
            {"bike_distance_meters": 40000, "run_distance_meters": 10000},
        ),
    ],
)
def test_all_current_race_types_accept_exact_applicable_distances(
    onboarding_context: tuple[TestClient, UUID, UUID],
    race_type: str,
    distances: dict[str, int],
) -> None:
    client, _, _ = onboarding_context
    response = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "race_type": race_type,
            "race_name": f"Test {race_type}",
            "race_date": (date.today() + timedelta(days=120)).isoformat(),
            "total_target_time_seconds": 14400,
            "specific_focus": "Controlled pacing",
            **distances,
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["race_name"] == f"Test {race_type}"
    assert {"title", "specific_description", "measurable_outcome"}.isdisjoint(
        response.json()
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"race_type": "run", "bike_distance_meters": 10000},
        {"race_type": "triathlon", "swim_distance_meters": 1500},
        {
            "race_type": "duathlon",
            "swim_distance_meters": 750,
            "bike_distance_meters": 20000,
            "run_distance_meters": 5000,
        },
    ],
)
def test_race_goal_rejects_missing_or_inapplicable_distances(
    onboarding_context: tuple[TestClient, UUID, UUID],
    payload: dict[str, Any],
) -> None:
    client, _, _ = onboarding_context
    response = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "race_name": "Invalid race",
            "race_date": (date.today() + timedelta(days=120)).isoformat(),
            "total_target_time_seconds": 3600,
            **payload,
        },
    )
    assert response.status_code == 422


def test_legacy_generic_goal_is_upgraded_in_place_without_deleting_history(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, _ = onboarding_context
    app = cast(FastAPI, client.app)
    repository = cast(MemoryOnboardingRepository, app.state.onboarding_repository)
    legacy_id = uuid4()
    repository._states[athlete_a]["goals"] = [
        {
            "id": str(legacy_id),
            "athlete_id": str(athlete_a),
            "priority": "A",
            "goal_type": "race",
            "title": "Historical title",
            "specific_description": "Historical detail",
            "measurable_outcome": "Historical outcome",
            "target_date": (date.today() + timedelta(days=120)).isoformat(),
            "race_discipline_profile": ["run"],
            "status": "active",
            "revision": 3,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
    ]

    before = client.get("/api/v1/onboarding", headers=_headers())
    upgraded = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "race_type": "run",
            "race_name": "Current race",
            "race_date": (date.today() + timedelta(days=120)).isoformat(),
            "run_distance_meters": 10000,
            "total_target_time_seconds": 3600,
        },
    )

    stored = repository._states[athlete_a]["goals"][0]
    assert before.status_code == 200
    assert before.json()["primary_goal"] is None
    assert upgraded.status_code == 201
    assert upgraded.json()["id"] == str(legacy_id)
    assert upgraded.json()["revision"] == 4
    assert "title" not in upgraded.json()
    assert stored["title"] == "Historical title"
    assert stored["race_name"] == "Current race"
    assert len(repository._states[athlete_a]["goals"]) == 1


def test_monitor_and_timezone_are_independent_server_prerequisites(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    profile = client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={
            "date_of_birth": "1990-05-20",
            "resting_heart_rate_bpm": 52,
        },
    )
    invalid_timezone = client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(),
        json={
            "timezone": "Amsterdam-ish",
            "timezone_source": "manual",
            "timezone_confirmed": True,
        },
    )
    state = client.get("/api/v1/onboarding", headers=_headers())

    assert profile.status_code == 200
    assert invalid_timezone.status_code == 422
    assert state.json()["current_step"] == "heart_rate_monitor"
    assert state.json()["can_complete"] is False

    monitor = client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(),
        json={"heart_rate_monitor_confirmed": True},
    )
    after_monitor = client.get("/api/v1/onboarding", headers=_headers())
    timezone_response = client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(),
        json={
            "timezone": "Europe/Amsterdam",
            "timezone_source": "device",
            "timezone_confirmed": True,
        },
    )
    after_timezone = client.get("/api/v1/onboarding", headers=_headers())

    assert monitor.status_code == 200
    assert monitor.json()["timezone"] == "UTC"
    assert after_monitor.json()["current_step"] == "timezone"
    assert timezone_response.status_code == 200
    assert after_timezone.json()["profile"]["timezone"] == "Europe/Amsterdam"
    assert after_timezone.json()["profile"]["timezone_source"] == "device"
    assert after_timezone.json()["current_step"] == "history"


def test_first_zones_activate_and_replacement_remains_pending(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    first = _manual_zone(
        client,
        "run",
        "run_lthr_bpm",
        170,
    )
    replacement = _manual_zone(
        client,
        "run",
        "run_lthr_bpm",
        172,
    )
    state = client.get("/api/v1/onboarding", headers=_headers()).json()

    assert first["profile"]["status"] == "active"
    assert first["proposal_id"] is None
    assert first["profile"]["requires_review"] is True
    assert first["profile"]["source"] == "athlete_entered"
    assert first["profile"]["validation_status"] == "confirmed_by_athlete"
    assert "validated" not in first["profile"]
    assert replacement["profile"]["status"] == "pending"
    assert replacement["proposal_id"] is not None
    assert (
        len(
            [
                zone
                for zone in state["zones"]
                if zone["discipline"] == "run" and zone["status"] == "active"
            ]
        )
        == 1
    )


def test_known_thresholds_create_multi_metric_pending_zones_before_activation(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    calculated = client.put(
        "/api/v1/me/zones/run",
        headers=_headers(),
        json={
            "setup_method": "calculated",
            "confirmed": True,
            "thresholds": [
                {
                    "metric_kind": "run_lthr_bpm",
                    "value": 172,
                },
                {
                    "metric_kind": "run_threshold_pace_seconds_per_km",
                    "value": 290,
                },
            ],
            "boundary_overrides": [],
        },
    )

    assert calculated.status_code == 200, calculated.text
    body = calculated.json()
    assert body["profile"]["status"] == "pending"
    assert body["profile"]["source"] == "athlete_entered"
    assert body["profile"]["zone_model_version"] == "start23-zone-model-1.0"
    assert len(body["profile"]["metric_profiles"]) == 2
    assert body["profile"]["metric"]["metric_kind"] == (
        "run_threshold_pace_seconds_per_km"
    )
    assert body["profile"]["boundaries"][0]["upper_value"] is None
    assert body["proposal_id"] is not None

    approved = client.post(
        f"/api/v1/change-proposals/{body['proposal_id']}/approve",
        headers=_headers(),
        json={"expected_base_zone_profile_id": None},
    )

    assert approved.status_code == 200, approved.text
    assert approved.json()["state"] == "applied"
    assert approved.json()["superseded_zone_profile_id"] is None


def test_physician_or_lab_values_remain_pending_with_measured_provenance(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context

    response = client.put(
        "/api/v1/me/zones/bike",
        headers=_headers(),
        json={
            "setup_method": "calculated",
            "confirmed": True,
            "source_quality": "measured_lab",
            "thresholds": [
                {"metric_kind": "bike_ftp_watts", "value": 245},
            ],
            "boundary_overrides": [],
        },
    )

    assert response.status_code == 200, response.text
    profile = response.json()["profile"]
    assert profile["status"] == "pending"
    assert profile["source_method"] == "physician_or_lab_reported"
    assert profile["source_quality"] == "measured_lab"
    assert response.json()["proposal_id"] is not None


def test_zone_proposal_approval_is_owned_atomic_and_stale_safe(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    first = _manual_zone(client, "run", "run_lthr_bpm", 170)
    replacement = _manual_zone(client, "run", "run_lthr_bpm", 172)
    proposal_id = replacement["proposal_id"]
    base_id = first["profile"]["id"]

    wrong_base = client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_zone_profile_id": str(uuid4())},
    )
    other_athlete = client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers("athlete-b"),
        json={"expected_base_zone_profile_id": base_id},
    )
    approved = client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_zone_profile_id": base_id},
    )
    replay = client.post(
        f"/api/v1/change-proposals/{proposal_id}/approve",
        headers=_headers(),
        json={"expected_base_zone_profile_id": base_id},
    )
    state = client.get("/api/v1/onboarding", headers=_headers()).json()

    assert wrong_base.status_code == 409
    assert other_athlete.status_code == 404
    assert approved.status_code == 200
    assert approved.json()["state"] == "applied"
    assert approved.json()["active_zone_profile_id"] == replacement["profile"]["id"]
    assert replay.status_code == 404
    assert (
        len(
            [
                zone
                for zone in state["zones"]
                if zone["discipline"] == "run" and zone["status"] == "active"
            ]
        )
        == 1
    )


def test_zone_proposal_rejection_keeps_base_active(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    first = _manual_zone(client, "bike", "bike_ftp_watts", 240)
    replacement = _manual_zone(client, "bike", "bike_ftp_watts", 250)

    rejected = client.post(
        f"/api/v1/change-proposals/{replacement['proposal_id']}/reject",
        headers=_headers(),
    )
    state = client.get("/api/v1/onboarding", headers=_headers()).json()

    assert rejected.status_code == 200
    assert rejected.json()["state"] == "rejected"
    assert rejected.json()["active_zone_profile_id"] == first["profile"]["id"]
    assert [
        zone["id"]
        for zone in state["zones"]
        if zone["discipline"] == "bike" and zone["status"] == "active"
    ] == [first["profile"]["id"]]


def test_fallback_is_unvalidated_and_not_available_for_swim(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    _complete_profile(client)
    bike = client.put(
        "/api/v1/me/zones/bike",
        headers=_headers(),
        json={"setup_method": "fallback", "confirmed": True},
    )
    swim = client.put(
        "/api/v1/me/zones/swim",
        headers=_headers(),
        json={"setup_method": "fallback", "confirmed": True},
    )

    assert bike.status_code == 200
    assert "validated" not in bike.json()["profile"]
    assert bike.json()["profile"]["source"] == "estimated"
    assert bike.json()["profile"]["validation_status"] == "unreviewed"
    assert bike.json()["profile"]["fallback_active"] is True
    assert bike.json()["profile"]["needs_testing"] is True
    assert bike.json()["profile"]["review_reason"] == "fallback_unvalidated"
    assert swim.status_code == 422


def test_swim_zones_reject_numeric_order_opposite_to_intensity(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    response = client.put(
        "/api/v1/me/zones/swim",
        headers=_headers(),
        json={
            "setup_method": "manual",
            "confirmed": True,
            "metric_kind": "swim_css_seconds_per_100m",
            "metric_value": 100,
            "boundaries": [
                {"zone_number": 1, "lower_value": 100, "upper_value": 120},
                {"zone_number": 2, "lower_value": 120, "upper_value": 130},
                {"zone_number": 3, "lower_value": 130, "upper_value": 150},
                {"zone_number": 4, "lower_value": 150, "upper_value": 170},
                {"zone_number": 5, "lower_value": 170, "upper_value": 190},
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["message"] == (
        "Descending zone boundaries must be contiguous."
    )


def test_onboarding_completion_is_resumable_and_idempotent(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = onboarding_context
    before = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": 0},
    )
    _complete_profile(client)
    _complete_history(client)
    _complete_goal(client)
    _manual_zone(
        client,
        "swim",
        "swim_css_seconds_per_100m",
        100,
        descending=True,
    )
    _manual_zone(client, "bike", "bike_ftp_watts", 250)
    _manual_zone(client, "run", "run_lthr_bpm", 170)
    ready = client.get("/api/v1/onboarding", headers=_headers())
    completed = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": ready.json()["onboarding_revision"]},
    )
    repeated = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": ready.json()["onboarding_revision"]},
    )

    assert before.status_code == 422
    assert ready.status_code == 200
    assert ready.json()["can_complete"] is True
    assert completed.status_code == 200
    assert completed.json()["onboarding"]["status"] == "completed"
    assert completed.json()["initial_plan_request_status"] == "pending"
    assert (
        repeated.json()["initial_plan_request_id"]
        == completed.json()["initial_plan_request_id"]
    )


def test_cross_athlete_state_is_isolated(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, athlete_b = onboarding_context
    _complete_profile(client, "athlete-a")
    state_a = client.get(
        "/api/v1/onboarding",
        headers=_headers("athlete-a"),
    )
    state_b = client.get(
        "/api/v1/onboarding",
        headers=_headers("athlete-b"),
    )

    assert state_a.json()["profile"]["athlete_id"] == str(athlete_a)
    assert state_b.json()["profile"] is None
    assert str(athlete_a) not in state_b.text
    assert str(athlete_b) not in state_a.text


def test_profile_domains_have_separate_owner_scoped_mutation_paths(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, _ = onboarding_context
    _complete_profile(client)

    identifying = client.patch(
        "/api/v1/me/identifying-profile",
        headers=_headers(),
        json={"first_name": "Ada", "last_name": "Lovelace"},
    )
    physiology = client.patch(
        "/api/v1/me/physiology-profile",
        headers=_headers(),
        json={"resting_heart_rate_bpm": 53},
    )
    operational = client.get("/api/v1/me/operational-profile", headers=_headers())

    assert identifying.status_code == 200
    assert identifying.json()["athlete_id"] == str(athlete_a)
    assert "resting_heart_rate_bpm" not in identifying.json()
    assert physiology.status_code == 200
    assert physiology.json()["resting_heart_rate_bpm"] == 53
    assert "first_name" not in physiology.json()
    assert operational.status_code == 200
    assert set(operational.json()).isdisjoint(
        {"first_name", "last_name", "date_of_birth", "resting_heart_rate_bpm"}
    )


def test_legacy_completion_upgrades_only_after_matching_revision(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, _ = onboarding_context
    _complete_profile(client)
    _complete_history(client)
    _complete_goal(client)
    _manual_zone(client, "swim", "swim_css_seconds_per_100m", 100, descending=True)
    _manual_zone(client, "bike", "bike_ftp_watts", 250)
    _manual_zone(client, "run", "run_lthr_bpm", 170)
    app = cast(FastAPI, client.app)
    repository = cast(MemoryOnboardingRepository, app.state.onboarding_repository)
    legacy_request_id = uuid4()
    repository._states[athlete_a]["session"] = {
        "athlete_id": str(athlete_a),
        "status": "completed",
        "current_step": "completed",
        "completed_steps": ["profile", "history", "goal", "zones", "review"],
        "initial_plan_request_id": str(legacy_request_id),
        "completed_onboarding_version": "legacy-unversioned",
        "completed_ruleset_version": "legacy-unversioned",
        "revision": 5,
    }

    resumable = client.get("/api/v1/onboarding", headers=_headers())
    stale = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": 4},
    )
    upgraded = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": 5},
    )

    assert resumable.json()["status"] == "upgrade_required"
    assert resumable.json()["missing_upgrade_steps"] == []
    assert resumable.json()["current_step"] == "review"
    assert stale.status_code == 409
    assert upgraded.status_code == 200
    assert upgraded.json()["onboarding"]["status"] == "completed"


def test_legacy_completed_user_resumes_only_new_r4_steps_then_completes(
    onboarding_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, _ = onboarding_context
    client.patch(
        "/api/v1/me/profile",
        headers=_headers(),
        json={"date_of_birth": "1990-05-20", "resting_heart_rate_bpm": 52},
    )
    _complete_history(client)
    _manual_zone(client, "swim", "swim_css_seconds_per_100m", 100, descending=True)
    _manual_zone(client, "bike", "bike_ftp_watts", 250)
    _manual_zone(client, "run", "run_lthr_bpm", 170)
    app = cast(FastAPI, client.app)
    repository = cast(MemoryOnboardingRepository, app.state.onboarding_repository)
    legacy_goal_id = uuid4()
    repository._states[athlete_a]["goals"] = [
        {
            "id": str(legacy_goal_id),
            "athlete_id": str(athlete_a),
            "priority": "A",
            "goal_type": "race",
            "title": "Legacy 10K",
            "specific_description": "Retained historical goal",
            "measurable_outcome": "Finish",
            "target_date": (date.today() + timedelta(days=120)).isoformat(),
            "race_discipline_profile": ["run"],
            "status": "active",
            "revision": 2,
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
    ]
    repository._states[athlete_a]["session"] = {
        "athlete_id": str(athlete_a),
        "status": "completed",
        "current_step": "completed",
        "completed_steps": ["profile", "history", "goal", "zones", "review"],
        "initial_plan_request_id": str(uuid4()),
        "completed_onboarding_version": "phase-13-onboarding-v1",
        "completed_ruleset_version": "phase-13-joren-ruleset-1",
        "revision": 7,
    }

    first = client.get("/api/v1/onboarding", headers=_headers()).json()
    client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(),
        json={"heart_rate_monitor_confirmed": True},
    )
    second = client.get("/api/v1/onboarding", headers=_headers()).json()
    client.patch(
        "/api/v1/me/operational-profile",
        headers=_headers(),
        json={
            "timezone": "Europe/Amsterdam",
            "timezone_source": "manual",
            "timezone_confirmed": True,
        },
    )
    third = client.get("/api/v1/onboarding", headers=_headers()).json()
    upgraded_goal = client.post(
        "/api/v1/me/goals",
        headers=_headers(),
        json={
            "race_type": "run",
            "race_name": "Current 10K",
            "race_date": (date.today() + timedelta(days=120)).isoformat(),
            "run_distance_meters": 10000,
            "total_target_time_seconds": 3600,
        },
    )
    ready = client.get("/api/v1/onboarding", headers=_headers()).json()
    completed = client.post(
        "/api/v1/onboarding/complete",
        headers=_headers(),
        json={"expected_onboarding_revision": 7},
    )

    assert first["current_step"] == "heart_rate_monitor"
    assert first["completed_steps"] == ["profile", "history", "zones"]
    assert second["current_step"] == "timezone"
    assert third["current_step"] == "goal"
    assert upgraded_goal.status_code == 201
    assert upgraded_goal.json()["id"] == str(legacy_goal_id)
    assert ready["current_step"] == "review"
    assert ready["missing_upgrade_steps"] == []
    assert completed.status_code == 200
    assert completed.json()["onboarding"]["status"] == "completed"
    assert repository._states[athlete_a]["goals"][0]["title"] == "Legacy 10K"
