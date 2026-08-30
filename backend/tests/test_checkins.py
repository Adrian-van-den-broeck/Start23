"""Phase 8 check-in API ownership, confirmation, and TSS-boundary tests."""

from collections.abc import Iterator
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.checkins.repository import (
    CheckInRepositoryConflictError,
    CheckInRepositoryNotFoundError,
    JsonObject,
)


class CheckInTokenVerifier:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self.owners = owners

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        try:
            return AuthenticatedIdentity(
                user_id=self.owners[access_token],
                role="authenticated",
            )
        except KeyError as error:
            raise InvalidAccessTokenError from error


class MemoryCheckInRepository:
    def __init__(self, owners: dict[str, UUID]) -> None:
        self.owners = owners
        self.rows: dict[UUID, JsonObject] = {}
        self.row_owners: dict[UUID, UUID] = {}

    def _owner(self, token: str) -> UUID:
        try:
            return self.owners[token]
        except KeyError as error:
            raise CheckInRepositoryNotFoundError from error

    async def start_or_resume(
        self,
        access_token: str,
        week_start: date,
    ) -> JsonObject:
        owner = self._owner(access_token)
        existing = next(
            (
                row
                for checkin_id, row in self.rows.items()
                if self.row_owners[checkin_id] == owner
                and row["week_start"] == week_start.isoformat()
            ),
            None,
        )
        if existing is not None:
            return dict(existing)
        checkin_id = uuid4()
        row = {
            "id": str(checkin_id),
            "week_start": week_start.isoformat(),
            "timezone": "Europe/Amsterdam",
            "status": "open",
            "context_revision": 0,
            "plan_proposal_id": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "context": None,
        }
        self.rows[checkin_id] = row
        self.row_owners[checkin_id] = owner
        return dict(row)

    async def fetch(self, access_token: str, checkin_id: UUID) -> JsonObject:
        if self.row_owners.get(checkin_id) != self._owner(access_token):
            raise CheckInRepositoryNotFoundError
        return dict(self.rows[checkin_id])

    async def save_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
        payload: JsonObject,
    ) -> JsonObject:
        row = await self.fetch(access_token, checkin_id)
        if row["context_revision"] != expected_revision:
            raise CheckInRepositoryConflictError("checkin_context_stale")
        revision = expected_revision + 1
        row["context_revision"] = revision
        row["context"] = {
            "revision": revision,
            "state": "draft",
            "source": "structured_form",
            "expires_at": datetime(2026, 8, 10, tzinfo=timezone.utc).isoformat(),
            "fingerprint": fingerprint,
            **payload,
            "confirmed_at": None,
        }
        self.rows[checkin_id] = row
        return dict(row)

    async def confirm_context(
        self,
        access_token: str,
        checkin_id: UUID,
        expected_revision: int,
        fingerprint: str,
    ) -> JsonObject:
        row = await self.fetch(access_token, checkin_id)
        context = row["context"]
        if (
            row["context_revision"] != expected_revision
            or context is None
            or context["fingerprint"] != fingerprint
        ):
            raise CheckInRepositoryConflictError("checkin_context_stale")
        context["state"] = "confirmed"
        context["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        self.rows[checkin_id] = row
        return dict(row)

    async def fetch_planning_context(
        self, athlete_id: UUID, checkin_id: UUID
    ) -> JsonObject:
        del athlete_id, checkin_id
        raise AssertionError("not used")

    async def attach_plan_proposal(
        self, athlete_id: UUID, checkin_id: UUID, proposal_id: UUID
    ) -> JsonObject:
        del athlete_id, checkin_id, proposal_id
        raise AssertionError("not used")

    async def list_restrictions(self, access_token: str) -> tuple[JsonObject, ...]:
        self._owner(access_token)
        return ()

    async def list_external_activities(
        self, access_token: str, week_start: date | None
    ) -> tuple[JsonObject, ...]:
        self._owner(access_token)
        del week_start
        return ()

    async def mark_goal_achieved(
        self,
        access_token: str,
        goal_id: UUID,
        achieved_at: date,
    ) -> JsonObject:
        self._owner(access_token)
        return {
            "goal_id": str(goal_id),
            "status": "active",
            "achieved_at": achieved_at.isoformat(),
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def aclose(self) -> None:
        return None


def _contains_forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key.lower() in {"tss", "planned_tss", "realized_tss"}
            or _contains_forbidden(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden(child) for child in value)
    return False


def _headers(token: str = "athlete-a") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def checkin_client() -> Iterator[TestClient]:
    owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
    repository = MemoryCheckInRepository(owners)
    with TestClient(
        create_app(
            Settings(environment="test"),
            access_token_verifier=CheckInTokenVerifier(owners),
            checkin_repository=repository,
        )
    ) as client:
        yield client


def test_checkin_is_resumable_owner_scoped_confirmed_and_tss_free(
    checkin_client: TestClient,
) -> None:
    client = checkin_client
    started = client.post(
        "/api/v1/checkins",
        headers=_headers(),
        json={"week_start": "2026-08-03"},
    ).json()
    checkin_id = started["id"]

    resumed = client.post(
        "/api/v1/checkins",
        headers=_headers(),
        json={"week_start": "2026-08-03"},
    )
    assert resumed.status_code == 200
    assert resumed.json()["id"] == checkin_id
    assert (
        client.get(
            f"/api/v1/checkins/{checkin_id}", headers=_headers("athlete-b")
        ).status_code
        == 404
    )

    context = client.put(
        f"/api/v1/checkins/{checkin_id}/context",
        headers=_headers(),
        json={
            "expected_revision": 0,
            "blocked_dates": ["2026-08-05"],
            "fatigue_level": "moderate",
            "missed_workout_reasons": ["fatigue"],
            "recurring_activities_confirmed": True,
            "external_activities": [],
            "restrictions": [
                {
                    "discipline": "run",
                    "status": "self_reported_limited",
                    "source": "athlete",
                    "athlete_plan_choice": "train_low_only",
                }
            ],
        },
    )
    assert context.status_code == 200
    candidate = context.json()["context"]
    assert candidate["source"] == "structured_form"
    assert candidate["expires_at"] is not None

    confirmed = client.post(
        f"/api/v1/checkins/{checkin_id}/context-confirmation",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "context_fingerprint": candidate["fingerprint"],
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["context"]["state"] == "confirmed"
    assert not _contains_forbidden(confirmed.json())


def test_context_revision_and_week_dates_are_stale_safe(
    checkin_client: TestClient,
) -> None:
    client = checkin_client
    checkin_id = client.post(
        "/api/v1/checkins",
        headers=_headers(),
        json={"week_start": "2026-08-03"},
    ).json()["id"]
    outside = client.put(
        f"/api/v1/checkins/{checkin_id}/context",
        headers=_headers(),
        json={
            "expected_revision": 0,
            "blocked_dates": ["2026-08-10"],
            "recurring_activities_confirmed": True,
        },
    )
    assert outside.status_code == 422

    valid = client.put(
        f"/api/v1/checkins/{checkin_id}/context",
        headers=_headers(),
        json={
            "expected_revision": 0,
            "blocked_dates": [],
            "recurring_activities_confirmed": True,
        },
    )
    assert valid.status_code == 200
    stale = client.put(
        f"/api/v1/checkins/{checkin_id}/context",
        headers=_headers(),
        json={
            "expected_revision": 0,
            "blocked_dates": [],
            "recurring_activities_confirmed": True,
        },
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "checkin_context_stale"


def test_context_extraction_fallback_is_inert_and_asks_for_clarification(
    checkin_client: TestClient,
) -> None:
    started = checkin_client.post(
        "/api/v1/checkins",
        headers=_headers(),
        json={"week_start": "2026-08-03"},
    ).json()
    response = checkin_client.post(
        f"/api/v1/checkins/{started['id']}/context-candidates",
        headers=_headers(),
        json={"athlete_text": "Woensdag lukt niet en ik ben moe."},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "deterministic_fallback"
    assert body["requires_structured_confirmation"] is True
    assert body["candidate"]["clarifying_questions"]
    resumed = checkin_client.get(
        f"/api/v1/checkins/{started['id']}",
        headers=_headers(),
    ).json()
    assert resumed["context"] is None
    assert resumed["context_revision"] == 0


def test_goal_achievement_is_explicit_and_owner_authenticated(
    checkin_client: TestClient,
) -> None:
    response = checkin_client.post(
        f"/api/v1/me/goals/{uuid4()}/achievement",
        headers=_headers(),
        json={"achieved_at": "2026-08-10"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"
