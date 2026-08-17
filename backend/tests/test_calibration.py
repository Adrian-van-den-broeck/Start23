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

    async def fetch_status(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject:
        assert self._owner(access_token) == athlete_id
        return {
            "setups": deepcopy(list(self._setups[athlete_id].values())),
            "evaluations": deepcopy(self._evaluations[athlete_id]),
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
            9,
            duration_seconds=1800,
            reported_block_rpe=9,
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
    assert response.json()["zone_status"] == "pending_protocol"
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


def test_valid_field_test_creates_only_pending_threshold_result(
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
    assert body["zone_status"] == "pending_protocol"
    assert body["review_status"] == "pending_athlete_confirmation"
    assert body["requires_athlete_confirmation"] is True
    assert "zone_model_not_approved" in body["reason_codes"]
    assert "boundaries" not in body
    assert "tss" not in response.text.lower()


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
            9,
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
    assert status_b.json() == {"setups": [], "evaluations": []}
