"""V2 selection at the real API/service boundary. SQL atomicity is separate."""

from collections.abc import Iterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from test_activities import (
    ActivityTokenVerifier,
    MemoryActivityRepository,
    _headers,
    _summary,
)
from test_realized_context import planned_context

from app.core.config import Settings
from app.main import create_app
from app.modules.activities.repository import JsonObject
from app.modules.physiology.realized_v2 import VERSION


class V2MemoryRepository(MemoryActivityRepository):
    def __init__(self, owners: dict[str, UUID]) -> None:
        super().__init__(owners)
        self.basis = planned_context(planned_tss="120", planned_duration_minutes="120")
        self.confirmed = True
        self.snapshot_history: list[JsonObject] = []

    async def fetch_processing_context(
        self, athlete_id: UUID, activity_id: UUID
    ) -> JsonObject:
        context = await super().fetch_processing_context(athlete_id, activity_id)
        previous = self.load_snapshots.get(activity_id, {}).get("rpe_estimate")
        context.update(
            {
                "realized_version": VERSION,
                "performed_duration_confirmed": self.confirmed,
                "approved_workout_basis": previous["provenance"].get("planned")
                if previous is not None
                else self.basis,
                "selected_realized_v2": previous,
            }
        )
        return context

    async def revise_activity_rpe(
        self, athlete_id: UUID, activity_id: UUID, payload: JsonObject
    ) -> JsonObject:
        if self._rows[activity_id]["rpe"] != payload["rpe"]:
            self.snapshot_history.append(dict(self.load_snapshots[activity_id]))
        return await super().revise_activity_rpe(athlete_id, activity_id, payload)


@pytest.fixture
def v2_client() -> Iterator[tuple[TestClient, V2MemoryRepository]]:
    owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
    repository = V2MemoryRepository(owners)
    with TestClient(
        create_app(
            Settings(
                environment="test",
                realized_v2_storage_ready=True,
                realized_v2_selection_enabled=True,
            ),
            activity_repository=repository,
            access_token_verifier=ActivityTokenVerifier(owners),
        )
    ) as client:
        yield client, repository


def create_and_rate(
    client: TestClient, repo: V2MemoryRepository, **changes: Any
) -> UUID:
    owner = repo._token_owners["athlete-a"]
    summary = {
        **_summary(repo.planned_workouts[owner], duration="60"),
        "metrics": None,
        "performed_duration_confirmed": True,
        **changes,
    }
    created = client.post("/api/v1/activities", headers=_headers(), json=summary)
    assert created.status_code == 201
    identifier = UUID(created.json()["id"])
    response = client.put(
        f"/api/v1/activities/{identifier}/rpe", headers=_headers(), json={"rpe": 3}
    )
    assert response.status_code == 200
    assert not any(
        key in str(response.json()).lower()
        for key in ("tss", "factor", "provenance", "planner_eligible", "duration_ratio")
    )
    return identifier


def test_owner_a_half_duration_example_and_subjective_feedback(
    v2_client: tuple[TestClient, V2MemoryRepository],
) -> None:
    client, repo = v2_client
    identifier = create_and_rate(client, repo)
    payload = repo.load_snapshots[identifier]
    assert payload["realized_tss"] is None  # observation remains unavailable
    assert payload["load_status"] == "unavailable"
    assert payload["rpe_estimate"]["value"] == "60.000"
    assert payload["rpe_estimate"]["provenance"]["reported_zone"] == 2
    assert not payload["rpe_estimate"]["planner_eligible"]
    assert payload["qualitative_result"] == "deviation"


@pytest.mark.parametrize(
    "bins,expected",
    [
        (["0", "60", "0", "0", "0"], "55.20"),
        (["10", "20", "8", "3", "0"], "40.76"),
    ],
)
def test_observations_override_rpe_without_rescaling(
    v2_client: tuple[TestClient, V2MemoryRepository], bins: list[str], expected: str
) -> None:
    client, repo = v2_client
    identifier = create_and_rate(client, repo, metrics={"zone_minutes": bins})
    payload = repo.load_snapshots[identifier]
    assert payload["realized_tss"] == expected
    assert payload["rpe_estimate"]["value"] is None
    response = client.put(
        f"/api/v1/activities/{identifier}/rpe",
        headers=_headers(),
        json={"rpe": 9, "expected_current_rpe": 3},
    )
    assert response.status_code == 200
    assert repo.load_snapshots[identifier]["realized_tss"] == expected
    assert repo._rows[identifier]["rpe"] == 9


def test_all_zero_evidence_not_replaced_and_duration_not_inferred(
    v2_client: tuple[TestClient, V2MemoryRepository],
) -> None:
    client, repo = v2_client
    identifier = create_and_rate(client, repo, metrics={"zone_minutes": ["0"] * 5})
    assert repo.load_snapshots[identifier]["rpe_estimate"]["value"] is None
    repo.confirmed = False
    # Unplanned submissions have no eligible approved basis in real SQL.
    repo.basis = planned_context(planned_duration_minutes=None)
    repo.planned_workouts[repo._token_owners["athlete-a"]] = uuid4()
    identifier = create_and_rate(client, repo)
    assert repo.load_snapshots[identifier]["rpe_estimate"]["value"] is None


def test_original_basis_survives_correction_and_duplicate_retry(
    v2_client: tuple[TestClient, V2MemoryRepository],
) -> None:
    client, repo = v2_client
    identifier = create_and_rate(client, repo, duration_minutes="120")
    before = repo.load_snapshots[identifier]
    repo.basis = planned_context(planned_tss="9999", planned_duration_minutes="1")
    for _ in range(2):
        response = client.put(
            f"/api/v1/activities/{identifier}/rpe",
            headers=_headers(),
            json={"rpe": 8, "expected_current_rpe": 3},
        )
        assert response.status_code == 200
    assert len(repo.snapshot_history) == 1
    updated = repo.load_snapshots[identifier]["rpe_estimate"]
    assert updated["value"] == "150.000"
    assert (
        updated["provenance"]["planned"]
        == before["rpe_estimate"]["provenance"]["planned"]
    )
    assert updated["planner_eligible"]
    stale = client.put(
        f"/api/v1/activities/{identifier}/rpe",
        headers=_headers(),
        json={"rpe": 2, "expected_current_rpe": 3},
    )
    assert stale.status_code == 409
    assert len(repo.snapshot_history) == 1


def test_selection_configuration_cannot_activate_hosted_or_without_storage() -> None:
    with pytest.raises(ValueError):
        Settings(realized_v2_selection_enabled=True)
    with pytest.raises(ValueError, match="release gates"):
        Settings(environment="staging", realized_v2_storage_ready=True)
