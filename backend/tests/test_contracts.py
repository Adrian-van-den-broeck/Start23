"""Cross-cutting public API contract tests."""

from collections.abc import Iterator, Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.modules.planning.schemas import ProposalApprovalRequest

_FORBIDDEN_LOAD_KEYS = {"tss", "ptss", "rtss", "plannedtss", "realizedtss"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create a test application for OpenAPI contract inspection."""
    settings = Settings(environment="test")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _assert_no_forbidden_load_key(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            normalized_key = "".join(
                character for character in str(key).lower() if character.isalnum()
            )
            assert normalized_key not in _FORBIDDEN_LOAD_KEYS
            _assert_no_forbidden_load_key(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _assert_no_forbidden_load_key(nested_value)


def test_nullable_zone_base_remains_typed_and_plan_base_cannot_be_null() -> None:
    zone_approval = ProposalApprovalRequest(
        expected_base_zone_profile_id=None,
    )

    assert zone_approval.expected_base_zone_profile_id is None
    with pytest.raises(ValidationError):
        ProposalApprovalRequest(expected_base_revision=None)


def test_openapi_contains_expected_foundation_paths(client: TestClient) -> None:
    """Foundation and identity routes remain stable."""
    schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/health",
        "/ready",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/me",
        "/api/v1/me/profile",
        "/api/v1/onboarding",
        "/api/v1/me/training-history",
        "/api/v1/me/goals",
        "/api/v1/me/goals/{goal_id}",
        "/api/v1/me/zones/{discipline}",
        "/api/v1/onboarding/complete",
        "/api/v1/change-proposals/{proposal_id}/approve",
        "/api/v1/change-proposals/{proposal_id}/reject",
        "/api/v1/change-proposals",
        "/api/v1/change-proposals/{proposal_id}",
        "/api/v1/workout-catalog",
        "/api/v1/weekly-plans/proposals",
        "/api/v1/weekly-plans/{plan_id}",
        "/api/v1/weekly-plans/{plan_id}/deck",
        "/api/v1/weekly-plans/{plan_id}/schedule-proposals",
        "/api/v1/weekly-plans/{plan_id}/validate",
        "/api/v1/planned-workouts/{workout_id}",
        "/api/v1/calendar",
        "/api/v1/activities",
        "/api/v1/activities/pending-rpe",
        "/api/v1/activities/{activity_id}",
        "/api/v1/activities/{activity_id}/rpe",
        "/api/v1/checkins",
        "/api/v1/checkins/{checkin_id}",
        "/api/v1/checkins/{checkin_id}/context",
        "/api/v1/checkins/{checkin_id}/context-confirmation",
        "/api/v1/checkins/{checkin_id}/plan-proposals",
        "/api/v1/me/injury-restrictions",
        "/api/v1/planned-external-activities",
        "/api/v1/me/goals/{goal_id}/achievement",
        "/api/v1/onboarding/zone-options",
        "/api/v1/onboarding/disciplines/{discipline}/setup",
        "/api/v1/calibration/protocols/{discipline}",
        "/api/v1/calibration/observations",
        "/api/v1/calibration/evaluate",
        "/api/v1/calibration/evaluations/{evaluation_id}/threshold/confirm",
        "/api/v1/calibration/evaluations/{evaluation_id}/threshold/reject",
        "/api/v1/calibration/status",
        "/api/v1/integrations/polar/oauth/start",
        "/api/v1/integrations/polar/oauth/callback",
        "/api/v1/integrations/polar",
        "/api/v1/integrations/polar/imports",
        "/api/v1/webhooks/polar",
    }


def test_openapi_excludes_hidden_load_fields(client: TestClient) -> None:
    """No planned or realized TSS field can enter the public schema."""
    schema = client.get("/openapi.json").json()

    _assert_no_forbidden_load_key(schema)


def test_openapi_documents_authentication_error(client: TestClient) -> None:
    """The current-user operation advertises the stable error envelope."""
    schema = client.get("/openapi.json").json()
    unauthorized = schema["paths"]["/api/v1/me"]["get"]["responses"]["401"]

    assert (
        unauthorized["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )
