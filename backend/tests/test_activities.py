"""Phase 7 canonical activity, RPE, ownership, and privacy API tests."""

from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.activities.repository import (
    ActivityRepositoryConflictError,
    ActivityRepositoryNotFoundError,
    JsonObject,
)

_NOW = datetime(2026, 8, 11, 8, tzinfo=timezone.utc)


class ActivityTokenVerifier:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self._owners = owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            owner = self._owners[access_token]
        except KeyError as error:
            raise InvalidAccessTokenError from error
        return AuthenticatedIdentity(user_id=owner, role="authenticated")


class MemoryActivityRepository:
    """Owner-scoped fake retaining idempotency and weekly RPE revisions."""

    def __init__(self, token_owners: dict[str, UUID]) -> None:
        self._token_owners = token_owners
        self._rows: dict[UUID, JsonObject] = {}
        self._owners: dict[UUID, UUID] = {}
        self._idempotency: dict[tuple[UUID, UUID], tuple[str, UUID]] = {}
        self.planned_workouts = {owner: uuid4() for owner in token_owners.values()}

    def _owner(self, token: str) -> UUID:
        try:
            return self._token_owners[token]
        except KeyError as error:
            raise ActivityRepositoryNotFoundError from error

    async def create_activity(
        self,
        access_token: str,
        idempotency_key: UUID,
        request_fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        owner = self._owner(access_token)
        existing = self._idempotency.get((owner, idempotency_key))
        if existing is not None:
            fingerprint, activity_id = existing
            if fingerprint != request_fingerprint:
                raise ActivityRepositoryConflictError("idempotency_key_reused")
            return dict(self._rows[activity_id])
        planned_id = payload.get("planned_workout_id")
        if planned_id is not None and planned_id != str(self.planned_workouts[owner]):
            raise ActivityRepositoryNotFoundError
        if planned_id is not None and any(
            row["planned_workout_id"] == planned_id for row in self._rows.values()
        ):
            raise ActivityRepositoryConflictError("planned_workout_already_matched")
        activity_id = uuid4()
        row: JsonObject = {
            "id": str(activity_id),
            "planned_workout_id": planned_id,
            "discipline": payload["discipline"],
            "source": "canonical_summary",
            "started_at": payload["started_at"],
            "timezone": payload["timezone"],
            "duration_minutes": payload["duration_minutes"],
            "distance_meters": payload.get("distance_meters"),
            "elevation_gain_meters": payload.get("elevation_gain_meters"),
            "rpe": None,
            "rpe_submitted_at": None,
            "match_status": "matched" if planned_id is not None else "unmatched",
            "processing_state": "awaiting_rpe",
            "qualitative_result": "awaiting_rpe",
            "public_message": (
                "Voeg je ervaren inspanning toe om de training af te ronden."
            ),
            "correction_proposal_id": None,
            "metrics": payload.get("metrics"),
            "created_at": _NOW.isoformat(),
            "updated_at": _NOW.isoformat(),
        }
        self._rows[activity_id] = row
        self._owners[activity_id] = owner
        self._idempotency[(owner, idempotency_key)] = (
            request_fingerprint,
            activity_id,
        )
        return dict(row)

    async def fetch_activity(self, access_token: str, activity_id: UUID) -> JsonObject:
        if self._owners.get(activity_id) != self._owner(access_token):
            raise ActivityRepositoryNotFoundError
        return dict(self._rows[activity_id])

    async def list_activities(
        self,
        access_token: str,
        *,
        pending_rpe: bool,
    ) -> tuple[JsonObject, ...]:
        owner = self._owner(access_token)
        return tuple(
            dict(row)
            for activity_id, row in self._rows.items()
            if self._owners[activity_id] == owner
            and (not pending_rpe or row["processing_state"] == "awaiting_rpe")
        )

    async def fetch_processing_context(
        self,
        athlete_id: UUID,
        activity_id: UUID,
    ) -> JsonObject:
        if self._owners.get(activity_id) != athlete_id:
            raise ActivityRepositoryNotFoundError
        row = self._rows[activity_id]
        return {
            "duration_minutes": row["duration_minutes"],
            "processing_state": row["processing_state"],
            "rpe": row["rpe"],
            "planned": (
                {
                    "planned_tss": "4",
                    "expected_rpe_min": 3,
                    "expected_rpe_max": 5,
                    "intensity_bucket": "low",
                }
                if row["planned_workout_id"] is not None
                else None
            ),
        }

    async def complete_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        if self._owners.get(activity_id) != athlete_id:
            raise ActivityRepositoryNotFoundError
        row = self._rows[activity_id]
        if row["processing_state"] == "complete":
            if row["rpe"] != payload["rpe"]:
                raise ActivityRepositoryConflictError("activity_rpe_immutable")
            return dict(row)
        row.update(
            {
                "rpe": payload["rpe"],
                "rpe_submitted_at": _NOW.isoformat(),
                "processing_state": "complete",
                "qualitative_result": payload["qualitative_result"],
                "public_message": payload["public_message"],
                "correction_proposal_id": (
                    str(uuid4()) if payload["correction_reason"] is not None else None
                ),
                "updated_at": _NOW.isoformat(),
            }
        )
        return dict(row)

    async def revise_activity_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        if self._owners.get(activity_id) != athlete_id:
            raise ActivityRepositoryNotFoundError
        row = self._rows[activity_id]
        if row["rpe"] == payload["rpe"]:
            return dict(row)
        row.update(
            {
                "rpe": payload["rpe"],
                "rpe_submitted_at": _NOW.isoformat(),
                "qualitative_result": payload["qualitative_result"],
                "public_message": payload["public_message"],
                "correction_proposal_id": None,
                "updated_at": _NOW.isoformat(),
            }
        )
        return dict(row)

    async def aclose(self) -> None:
        return None


@pytest.fixture
def activity_client() -> Iterator[tuple[TestClient, MemoryActivityRepository]]:
    owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
    repository = MemoryActivityRepository(owners)
    with TestClient(
        create_app(
            Settings(environment="test"),
            access_token_verifier=ActivityTokenVerifier(owners),
            activity_repository=repository,
        )
    ) as client:
        yield client, repository


def _headers(token: str = "athlete-a", key: UUID | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(key or uuid4()),
    }


def _summary(
    planned_workout_id: UUID | None = None,
    *,
    duration: str = "60",
) -> JsonObject:
    return {
        "planned_workout_id": (
            str(planned_workout_id) if planned_workout_id is not None else None
        ),
        "discipline": "run",
        "started_at": "2026-08-11T08:00:00Z",
        "timezone": "Europe/Amsterdam",
        "duration_minutes": duration,
        "distance_meters": 10000,
        "metrics": {
            "average_heart_rate_bpm": 150,
            "max_heart_rate_bpm": 170,
            "low_intensity_minutes": duration,
            "high_intensity_minutes": "0",
        },
    }


def _assert_no_load_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = "".join(c for c in str(key).lower() if c.isalnum())
            assert normalized not in {
                "tss",
                "ptss",
                "rtss",
                "plannedtss",
                "realizedtss",
            }
            _assert_no_load_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_load_keys(nested)


def test_activity_creation_is_idempotent_and_awaits_rpe(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    key = uuid4()
    first = client.post(
        "/api/v1/activities",
        headers=_headers(key=key),
        json=_summary(),
    )
    replay = client.post(
        "/api/v1/activities",
        headers=_headers(key=key),
        json=_summary(),
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    assert first.json()["processing_state"] == "awaiting_rpe"
    assert first.json()["match_status"] == "unmatched"
    _assert_no_load_keys(first.json())


def test_planned_external_activity_accepts_actual_summary_without_load_fields(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    payload = _summary()
    payload["planned_external_activity_id"] = str(uuid4())

    response = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["processing_state"] == "awaiting_rpe"
    _assert_no_load_keys(response.json())


def test_activity_cannot_reference_two_planning_sources(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, repository = activity_client
    owner = repository._token_owners["athlete-a"]
    payload = _summary(repository.planned_workouts[owner])
    payload["planned_external_activity_id"] = str(uuid4())

    response = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=payload,
    )

    assert response.status_code == 422


def test_reused_idempotency_key_with_changed_payload_conflicts(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    key = uuid4()
    assert (
        client.post(
            "/api/v1/activities", headers=_headers(key=key), json=_summary()
        ).status_code
        == 201
    )

    response = client.post(
        "/api/v1/activities",
        headers=_headers(key=key),
        json=_summary(duration="61"),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "idempotency_key_reused"


def test_matched_activity_rpe_can_be_corrected_in_the_current_week(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, repository = activity_client
    planned_id = repository.planned_workouts[repository._token_owners["athlete-a"]]
    created = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=_summary(planned_id),
    )
    activity_id = created.json()["id"]

    completed = client.put(
        f"/api/v1/activities/{activity_id}/rpe",
        headers=_headers(),
        json={"rpe": 4},
    )
    replay = client.put(
        f"/api/v1/activities/{activity_id}/rpe",
        headers=_headers(),
        json={"rpe": 4},
    )
    changed = client.put(
        f"/api/v1/activities/{activity_id}/rpe",
        headers=_headers(),
        json={"rpe": 5},
    )

    assert completed.status_code == 200
    assert completed.json()["qualitative_result"] == "perfect_match"
    assert completed.json()["correction_proposal_id"] is None
    assert replay.json() == completed.json()
    assert changed.status_code == 200
    assert changed.json()["rpe"] == 5
    _assert_no_load_keys(completed.json())


def test_hidden_fatigue_and_unplanned_load_create_only_pending_references(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, repository = activity_client
    owner = repository._token_owners["athlete-a"]
    planned = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=_summary(repository.planned_workouts[owner]),
    ).json()
    unplanned = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=_summary(),
    ).json()

    fatigue = client.put(
        f"/api/v1/activities/{planned['id']}/rpe",
        headers=_headers(),
        json={"rpe": 7},
    )
    extra = client.put(
        f"/api/v1/activities/{unplanned['id']}/rpe",
        headers=_headers(),
        json={"rpe": 3},
    )

    assert fatigue.json()["qualitative_result"] == "hidden_fatigue"
    assert fatigue.json()["correction_proposal_id"] is not None
    assert extra.json()["qualitative_result"] == "unplanned"
    assert extra.json()["correction_proposal_id"] is not None


def test_activity_reads_are_owner_scoped(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    created = client.post(
        "/api/v1/activities", headers=_headers(), json=_summary()
    ).json()

    other = client.get(
        f"/api/v1/activities/{created['id']}",
        headers=_headers("athlete-b"),
    )

    assert other.status_code == 404


def test_invalid_canonical_summary_is_rejected_before_persistence(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    payload = _summary()
    payload["started_at"] = "2026-08-11T08:00:00"
    payload["metrics"] = {
        "normalized_power_watts": 250,
        "low_intensity_minutes": "40",
        "high_intensity_minutes": "10",
    }

    response = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


def test_partial_reliable_intensity_and_bike_speed_telemetry_are_accepted(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    payload = _summary(duration="100")
    payload["discipline"] = "bike"
    payload["metrics"] = {
        "average_speed_kmh": "31.5",
        "max_speed_kmh": "48.2",
        "low_intensity_minutes": "40",
        "high_intensity_minutes": "20",
    }

    response = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["metrics"]["average_speed_kmh"] == "31.5"
    assert response.json()["metrics"]["low_intensity_minutes"] == "40"


def test_speed_telemetry_cannot_be_used_as_a_run_zone_input(
    activity_client: tuple[TestClient, MemoryActivityRepository],
) -> None:
    client, _ = activity_client
    payload = _summary()
    payload["metrics"] = {"average_speed_kmh": "15"}

    response = client.post(
        "/api/v1/activities",
        headers=_headers(),
        json=payload,
    )

    assert response.status_code == 422
