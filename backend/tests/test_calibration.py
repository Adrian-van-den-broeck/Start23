"""Phase 8.5 API tests for setup, observations, and evaluation."""

from collections.abc import Iterator
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.calibration.repository import (
    CalibrationRepositoryConflictError,
    CalibrationRepositoryNotFoundError,
    JsonObject,
)

_NOW = datetime(2026, 8, 13, 15, tzinfo=timezone.utc)


class TokenVerifier:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            owner = self._owners[access_token]
        except KeyError as error:
            raise InvalidAccessTokenError from error
        return AuthenticatedIdentity(user_id=owner, role="authenticated")


class MemoryCalibrationRepository:
    """Owner-partitioned calibration repository with production idempotency."""

    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners
        self._setups: dict[UUID, dict[str, JsonObject]] = {
            owner: {} for owner in owners.values()
        }
        self._observations: dict[UUID, list[JsonObject]] = {
            owner: [] for owner in owners.values()
        }
        self._evaluations: dict[UUID, list[JsonObject]] = {
            owner: [] for owner in owners.values()
        }
        self._decisions: dict[UUID, list[JsonObject]] = {
            owner: [] for owner in owners.values()
        }
        self._test_assignments: dict[UUID, list[JsonObject]] = {
            owner: [] for owner in owners.values()
        }

    def _owner(self, token: str) -> UUID:
        return self._owners[token]

    async def save_setup(self, access_token: str, values: JsonObject) -> JsonObject:
        owner = self._owner(access_token)
        discipline = str(values["discipline"])
        previous = self._setups[owner].get(discipline)
        row = {
            "athlete_id": str(owner),
            **deepcopy(values),
            "revision": int(previous["revision"]) + 1 if previous else 1,
            "created_at": previous["created_at"] if previous else _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
        self._setups[owner][discipline] = row
        return deepcopy(row)

    async def save_observation(
        self,
        access_token: str,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        owner = self._owner(access_token)
        identity = (
            values["protocol_id"],
            values["activity_id"],
            values["segment_id"],
        )
        existing = next(
            (
                row
                for row in self._observations[owner]
                if (
                    row["protocol_id"],
                    row["activity_id"],
                    row["segment_id"],
                )
                == identity
            ),
            None,
        )
        if existing is not None:
            if existing["fingerprint"] != fingerprint:
                raise CalibrationRepositoryConflictError
            return deepcopy(existing)
        row = {
            **deepcopy(values),
            "id": str(uuid4()),
            "fingerprint": fingerprint,
            "created_at": _NOW.isoformat(),
        }
        self._observations[owner].append(row)
        return deepcopy(row)

    async def list_observations(
        self,
        access_token: str,
        athlete_id: UUID,
        protocol_id: str,
        activity_id: UUID,
    ) -> list[JsonObject]:
        assert self._owner(access_token) == athlete_id
        return deepcopy(
            [
                row
                for row in self._observations[athlete_id]
                if row["protocol_id"] == protocol_id
                and row["activity_id"] == str(activity_id)
            ]
        )

    async def save_evaluation(
        self,
        athlete_id: UUID,
        values: JsonObject,
        fingerprint: str,
    ) -> JsonObject:
        existing = next(
            (
                row
                for row in self._evaluations[athlete_id]
                if row["fingerprint"] == fingerprint
            ),
            None,
        )
        if existing is not None:
            return deepcopy(existing)
        row = {
            **deepcopy(values),
            "id": str(uuid4()),
            "fingerprint": fingerprint,
            "created_at": _NOW.isoformat(),
        }
        self._evaluations[athlete_id].append(row)
        return deepcopy(row)

    async def get_evaluation(
        self,
        access_token: str,
        athlete_id: UUID,
        evaluation_id: UUID,
    ) -> JsonObject:
        if self._owner(access_token) != athlete_id:
            raise CalibrationRepositoryNotFoundError
        row = next(
            (
                row
                for row in self._evaluations[athlete_id]
                if row["id"] == str(evaluation_id)
            ),
            None,
        )
        if row is None:
            raise CalibrationRepositoryNotFoundError
        return deepcopy(row)

    async def save_calculated_zone_profile(
        self,
        athlete_id: UUID,
        values: JsonObject,
    ) -> JsonObject:
        evaluation_id = values.get("calibration_evaluation_id")
        existing = next(
            (
                row
                for row in self._decisions[athlete_id]
                if row["evaluation_id"] == evaluation_id
            ),
            None,
        )
        if existing is not None:
            return deepcopy(existing)
        row = {
            "evaluation_id": evaluation_id,
            "state": "accepted",
            "zone_profile_id": str(uuid4()),
            "zone_proposal_id": str(uuid4()),
            "base_zone_profile_id": None,
            "decided_at": _NOW.isoformat(),
        }
        self._decisions[athlete_id].append(row)
        return deepcopy(row)

    async def reject_threshold(
        self,
        athlete_id: UUID,
        evaluation_id: UUID,
    ) -> JsonObject:
        if not any(
            row["id"] == str(evaluation_id) for row in self._evaluations[athlete_id]
        ):
            raise CalibrationRepositoryNotFoundError
        existing = next(
            (
                row
                for row in self._decisions[athlete_id]
                if row["evaluation_id"] == str(evaluation_id)
            ),
            None,
        )
        if existing is not None:
            return deepcopy(existing)
        row = {
            "evaluation_id": str(evaluation_id),
            "state": "rejected",
            "zone_profile_id": None,
            "zone_proposal_id": None,
            "base_zone_profile_id": None,
            "decided_at": _NOW.isoformat(),
        }
        self._decisions[athlete_id].append(row)
        return deepcopy(row)

    async def fetch_status(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject:
        assert self._owner(access_token) == athlete_id
        return {
            "setups": deepcopy(list(self._setups[athlete_id].values())),
            "evaluations": deepcopy(self._evaluations[athlete_id]),
            "threshold_decisions": deepcopy(self._decisions[athlete_id]),
            "zone_proposals": [
                {"id": row["zone_proposal_id"], "state": "pending"}
                for row in self._decisions[athlete_id]
                if row["zone_proposal_id"] is not None
            ],
        }

    async def fetch_athlete_timezone(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> str:
        assert self._owner(access_token) == athlete_id
        return "Europe/Amsterdam"

    async def create_test_assignment(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        owner = self._owner(access_token)
        row = {
            "id": str(uuid4()),
            **deepcopy(values),
            "state": "pending_approval",
            "plan_id": None,
            "target_plan_revision_id": None,
            "plan_proposal_id": None,
            "revision": 1,
            "proposal_id": str(uuid4()),
            "proposal_state": "pending",
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
            "decided_at": None,
        }
        self._test_assignments[owner].append(row)
        return deepcopy(row)

    async def save_integrated_test_assignment(
        self,
        access_token: str,
        values: JsonObject,
    ) -> JsonObject:
        owner = self._owner(access_token)
        row = {
            "id": str(uuid4()),
            **deepcopy(values),
            "state": "pending_approval",
            "revision": 1,
            "proposal_id": values["plan_proposal_id"],
            "proposal_state": "pending",
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
            "decided_at": None,
        }
        self._test_assignments[owner].append(row)
        return deepcopy(row)

    async def approve_test_assignment(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_revision: int,
    ) -> JsonObject:
        owner = self._owner(access_token)
        row = next(
            row
            for row in self._test_assignments[owner]
            if row["proposal_id"] == str(proposal_id)
        )
        if int(row["revision"]) != expected_revision:
            raise CalibrationRepositoryConflictError
        row["state"] = "scheduled"
        row["proposal_state"] = "applied"
        return {
            "proposal_id": str(proposal_id),
            "state": "applied",
            "test_assignment_id": row["id"],
            "test_assignment_state": "scheduled",
        }

    async def reject_test_assignment(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        owner = self._owner(access_token)
        row = next(
            row
            for row in self._test_assignments[owner]
            if row["proposal_id"] == str(proposal_id)
        )
        row["state"] = "rejected"
        row["proposal_state"] = "rejected"
        return {
            "proposal_id": str(proposal_id),
            "state": "rejected",
            "test_assignment_id": row["id"],
            "test_assignment_state": "rejected",
        }

    async def fetch_zone_profile_state(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject:
        assert self._owner(access_token) == athlete_id
        assignments = deepcopy(self._test_assignments[athlete_id])
        return {
            "setups": deepcopy(list(self._setups[athlete_id].values())),
            "zone_profiles": [],
            "zone_metrics": [],
            "zone_boundaries": [],
            "zone_proposals": [],
            "test_assignments": assignments,
            "test_proposals": [
                {
                    "id": row["proposal_id"],
                    "state": row["proposal_state"],
                    "target_test_assignment_id": row["id"],
                }
                for row in assignments
            ],
        }

    async def aclose(self) -> None:
        return None


@pytest.fixture
def calibration_context() -> Iterator[tuple[TestClient, UUID, UUID]]:
    athlete_a = uuid4()
    athlete_b = uuid4()
    owners = {"athlete-a": athlete_a, "athlete-b": athlete_b}
    repository = MemoryCalibrationRepository(owners)
    app = create_app(
        Settings(environment="test"),
        access_token_verifier=TokenVerifier(owners),
        calibration_repository=repository,
    )
    with TestClient(app) as client:
        yield client, athlete_a, athlete_b


def _headers(token: str = "athlete-a") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _segment_payload(
    activity_id: UUID,
    segment_id: str,
    target_rpe: int,
    **overrides: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "activity_id": str(activity_id),
        "protocol_id": "start23_run_threshold_30min_v1",
        "discipline": "run",
        "segment_id": segment_id,
        "performed_at": _NOW.isoformat(),
        "completed": True,
        "interrupted": False,
        "quality_status": "sufficient",
        "target_rpe": target_rpe,
    }
    payload.update(overrides)
    return payload


def _save_run_test(client: TestClient, activity_id: UUID) -> None:
    payloads = (
        _segment_payload(activity_id, "warmup", 3, duration_seconds=900),
        _segment_payload(activity_id, "strides", 6, duration_seconds=300),
        _segment_payload(
                activity_id,
                "test_30min",
                8,
                duration_seconds=1800,
                reported_block_rpe=8,
            average_pace_seconds_per_km=290,
            average_heart_rate_last_20min_bpm=171.6,
            data_completeness=0.98,
            stable_segment=True,
        ),
        _segment_payload(
            activity_id,
            "cooldown",
            2,
            duration_seconds=600,
            reported_session_rpe=8,
        ),
    )
    for payload in payloads:
        response = client.post(
            "/api/v1/calibration/observations",
            headers=_headers(),
            json=payload,
        )
        assert response.status_code == 201, response.text


def test_standalone_field_test_requires_confirmation_and_appears_in_profile(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    setup = client.put(
        "/api/v1/onboarding/disciplines/run/setup",
        headers=_headers(),
        json={
            "setup_route": "field_test",
            "guidance_mode": "heart_rate",
            "protocol_id": "start23_run_threshold_30min_v1",
        },
    )
    scheduled = client.post(
        "/api/v1/calibration/test-assignments",
        headers=_headers(),
        json={
            "discipline": "run",
            "protocol_id": "start23_run_threshold_30min_v1",
            "scheduling_mode": "standalone",
            "scheduled_date": "2099-08-29",
        },
    )

    assert setup.status_code == 200
    assert scheduled.status_code == 201, scheduled.text
    assignment = scheduled.json()["assignment"]
    assert assignment["state"] == "pending_approval"
    assert scheduled.json()["plan_proposal"] is None

    approved = client.post(
        f"/api/v1/calibration/test-assignments/{assignment['proposal_id']}/approve",
        headers=_headers(),
        json={"expected_revision": assignment["revision"]},
    )
    profile = client.get("/api/v1/me/zone-profile", headers=_headers())

    assert approved.status_code == 200
    assert approved.json()["test_assignment_state"] == "scheduled"
    assert profile.status_code == 200, profile.text
    assert len(profile.json()["disciplines"]) == 3
    run = next(
        item for item in profile.json()["disciplines"] if item["discipline"] == "run"
    )
    assert run["numeric_zone_visibility"] == "rpe_guided"
    assert run["test_assignments"][0]["state"] == "scheduled"
    assert "tss" not in profile.text.lower()


def test_four_zone_options_are_authenticated_and_tss_free(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    unauthorized = client.get("/api/v1/onboarding/zone-options")
    response = client.get(
        "/api/v1/onboarding/zone-options",
        headers=_headers(),
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert [item["setup_route"] for item in response.json()] == [
        "known_values",
        "field_test",
        "calibration_week",
        "rpe_only",
    ]
    assert "tss" not in response.text.lower()


def test_threshold_only_known_values_accept_empty_optional_zones(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    response = client.put(
        "/api/v1/onboarding/disciplines/run/setup",
        headers=_headers(),
        json={
            "setup_route": "known_values",
            "guidance_mode": "pace",
            "thresholds": [
                {
                    "metric_kind": "run_threshold_pace_seconds_per_km",
                    "value": 290,
                }
            ],
            "zone_profiles": [],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["threshold_status"] == "user_provided"
    assert response.json()["zone_status"] == "pending_athlete_confirmation"
    assert response.json()["validation_status"] == "self_reported"


def test_css_only_known_value_does_not_require_zone_boundaries(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    response = client.put(
        "/api/v1/onboarding/disciplines/swim/setup",
        headers=_headers(),
        json={
            "setup_route": "known_values",
            "guidance_mode": "pace",
            "thresholds": [{"metric_kind": "swim_css_seconds_per_100m", "value": 102}],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["known_zone_profiles"] == []


def test_swim_calibration_week_accepts_pace_and_pool_length(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    response = client.put(
        "/api/v1/onboarding/disciplines/swim/setup",
        headers=_headers(),
        json={
            "setup_route": "calibration_week",
            "guidance_mode": "pace",
            "pool_length_meters": 25,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["protocol_id"] == "start23_week1_swim_calibration_v1"
    assert response.json()["setup_status"] == "calibration_pending"


def test_rpe_only_is_explicit_empty_and_rejects_authoritative_user_id(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, athlete_a, _ = calibration_context
    valid = client.put(
        "/api/v1/onboarding/disciplines/bike/setup",
        headers=_headers(),
        json={"setup_route": "rpe_only", "guidance_mode": "rpe_only"},
    )
    forged = client.put(
        "/api/v1/onboarding/disciplines/bike/setup",
        headers=_headers(),
        json={
            "setup_route": "rpe_only",
            "guidance_mode": "rpe_only",
            "user_id": str(athlete_a),
        },
    )

    assert valid.status_code == 200
    assert valid.json()["threshold_status"] == "unknown"
    assert valid.json()["zone_status"] == "unknown"
    assert forged.status_code == 422


def test_field_test_protocol_must_match_discipline_and_guidance(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    wrong_discipline = client.put(
        "/api/v1/onboarding/disciplines/run/setup",
        headers=_headers(),
        json={
            "setup_route": "field_test",
            "guidance_mode": "power",
            "protocol_id": "start23_bike_ftp_30min_v1",
        },
    )
    protocols = client.get(
        "/api/v1/calibration/protocols/bike",
        headers=_headers(),
    )

    assert wrong_discipline.status_code == 422
    assert protocols.status_code == 200
    assert {item["protocol_id"] for item in protocols.json()} == {
        "start23_bike_ftp_30min_v1",
        "start23_bike_fthr_20min_v1",
        "start23_week1_bike_calibration_v1",
    }
    assert all(
        segment["rpe_display_label"].startswith(
            f"Zone {segment['rpe_zone_number']} · RPE "
        )
        and segment["rpe_training_type"]
        and segment["rpe_description"]
        for protocol in protocols.json()
        for segment in protocol["segments"]
    )


def test_observation_retry_is_idempotent_and_conflicting_revision_is_rejected(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    activity_id = uuid4()
    payload = _segment_payload(activity_id, "warmup", 3, duration_seconds=900)
    first = client.post(
        "/api/v1/calibration/observations",
        headers=_headers(),
        json=payload,
    )
    repeated = client.post(
        "/api/v1/calibration/observations",
        headers=_headers(),
        json=payload,
    )
    changed = client.post(
        "/api/v1/calibration/observations",
        headers=_headers(),
        json={**payload, "duration_seconds": 800},
    )

    assert first.status_code == repeated.status_code == 201
    assert first.json()["id"] == repeated.json()["id"]
    assert changed.status_code == 409


def test_valid_field_test_creates_pending_threshold_and_zone_candidates(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    activity_id = uuid4()
    _save_run_test(client, activity_id)
    response = client.post(
        "/api/v1/calibration/evaluate",
        headers=_headers(),
        json={
            "activity_id": str(activity_id),
            "protocol_id": "start23_run_threshold_30min_v1",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "threshold_estimated"
    assert body["threshold_status"] == "threshold_estimated"
    assert body["zone_status"] == "pending_athlete_confirmation"
    assert body["review_status"] == "pending_athlete_confirmation"
    assert body["requires_athlete_confirmation"] is True
    assert "zone_profile_pending_athlete_confirmation" in body["reason_codes"]
    assert body["zone_model_version"] == "start23-zone-model-1.0"
    assert len(body["zone_profiles"]) == 2
    assert body["zone_profiles"][0]["is_primary"] is True
    assert body["zone_profiles"][0]["boundaries"][0]["upper_value"] is None
    assert "tss" not in response.text.lower()


def test_threshold_confirmation_is_owned_idempotent_and_keeps_zones_pending(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    activity_id = uuid4()
    _save_run_test(client, activity_id)
    evaluation = client.post(
        "/api/v1/calibration/evaluate",
        headers=_headers(),
        json={
            "activity_id": str(activity_id),
            "protocol_id": "start23_run_threshold_30min_v1",
        },
    ).json()
    path = f"/api/v1/calibration/evaluations/{evaluation['id']}/threshold/confirm"

    other = client.post(
        path,
        headers=_headers("athlete-b"),
        json={"confirmed": True},
    )
    accepted = client.post(path, headers=_headers(), json={"confirmed": True})
    repeated = client.post(path, headers=_headers(), json={"confirmed": True})

    assert other.status_code == 404
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["state"] == "accepted"
    assert accepted.json()["zone_profile_id"] is not None
    assert accepted.json()["zone_proposal_id"] is not None
    assert accepted.json()["base_zone_profile_id"] is None
    assert accepted.json()["zone_proposal_state"] == "pending"
    assert repeated.json() == accepted.json()
    status = client.get("/api/v1/calibration/status", headers=_headers()).json()
    assert status["threshold_decisions"][0]["zone_proposal_state"] == "pending"


def test_threshold_rejection_creates_no_zone_profile(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    activity_id = uuid4()
    _save_run_test(client, activity_id)
    evaluation = client.post(
        "/api/v1/calibration/evaluate",
        headers=_headers(),
        json={
            "activity_id": str(activity_id),
            "protocol_id": "start23_run_threshold_30min_v1",
        },
    ).json()

    rejected = client.post(
        f"/api/v1/calibration/evaluations/{evaluation['id']}/threshold/reject",
        headers=_headers(),
    )

    assert rejected.status_code == 200
    assert rejected.json()["state"] == "rejected"
    assert rejected.json()["zone_profile_id"] is None


def test_missing_session_rpe_blocks_evaluation_not_observation_persistence(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    activity_id = uuid4()
    _save_run_test(client, activity_id)
    # A second activity intentionally omits the session score.
    for payload in (
        _segment_payload(activity_id := uuid4(), "warmup", 3, duration_seconds=900),
        _segment_payload(activity_id, "strides", 6, duration_seconds=300),
        _segment_payload(
            activity_id,
            "test_30min",
            8,
            duration_seconds=1800,
            reported_block_rpe=9,
            average_pace_seconds_per_km=290,
            stable_segment=True,
        ),
        _segment_payload(activity_id, "cooldown", 2, duration_seconds=600),
    ):
        assert (
            client.post(
                "/api/v1/calibration/observations",
                headers=_headers(),
                json=payload,
            ).status_code
            == 201
        )

    evaluated = client.post(
        "/api/v1/calibration/evaluate",
        headers=_headers(),
        json={
            "activity_id": str(activity_id),
            "protocol_id": "start23_run_threshold_30min_v1",
        },
    )

    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "insufficient_data"
    assert "missing_session_rpe" in evaluated.json()["reason_codes"]


def test_status_is_cross_athlete_isolated(
    calibration_context: tuple[TestClient, UUID, UUID],
) -> None:
    client, _, _ = calibration_context
    saved = client.put(
        "/api/v1/onboarding/disciplines/run/setup",
        headers=_headers("athlete-a"),
        json={"setup_route": "rpe_only", "guidance_mode": "rpe_only"},
    )
    status_a = client.get(
        "/api/v1/calibration/status",
        headers=_headers("athlete-a"),
    )
    status_b = client.get(
        "/api/v1/calibration/status",
        headers=_headers("athlete-b"),
    )

    assert saved.status_code == 200
    assert len(status_a.json()["setups"]) == 1
    assert status_b.json() == {
        "setups": [],
        "evaluations": [],
        "threshold_decisions": [],
    }
