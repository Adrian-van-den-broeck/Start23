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
        "/api/v1/me/identifying-profile",
        "/api/v1/me/physiology-profile",
        "/api/v1/me/operational-profile",
        "/api/v1/onboarding",
        "/api/v1/onboarding/goal-options",
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
        "/api/v1/weekly-plans/swipe-drafts",
        "/api/v1/weekly-plans/swipe-drafts/{draft_id}",
        "/api/v1/weekly-plans/swipe-drafts/{draft_id}/transitions",
        "/api/v1/weekly-plans/swipe-drafts/{draft_id}/placements/{template_id}",
        "/api/v1/weekly-plans/swipe-drafts/{draft_id}/submit",
        "/api/v1/weekly-plans/{plan_id}",
        "/api/v1/weekly-plans/{plan_id}/deck",
        "/api/v1/weekly-plans/{plan_id}/schedule-proposals",
        "/api/v1/weekly-plans/{plan_id}/pending-workouts/{workout_id}/alternatives",
        "/api/v1/weekly-plans/{plan_id}/pending-workouts/{workout_id}/edit-proposals",
        "/api/v1/weekly-plans/{plan_id}/validate",
        "/api/v1/planned-workouts/{workout_id}",
        "/api/v1/calendar",
        "/api/v1/activities",
        "/api/v1/activities/pending-rpe",
        "/api/v1/activities/{activity_id}",
        "/api/v1/activities/{activity_id}/rpe",
        "/api/v1/activities/{activity_id}/planned-workout-match",
        "/api/v1/checkins",
        "/api/v1/checkins/{checkin_id}",
        "/api/v1/checkins/{checkin_id}/context",
        "/api/v1/checkins/{checkin_id}/context-candidates",
        "/api/v1/checkins/{checkin_id}/context-confirmation",
        "/api/v1/checkins/{checkin_id}/plan-proposals",
        "/api/v1/me/injury-restrictions",
        "/api/v1/planned-external-activities",
        "/api/v1/me/goals/{goal_id}/achievement",
        "/api/v1/onboarding/zone-options/{discipline}",
        "/api/v1/onboarding/disciplines/{discipline}/setup",
        "/api/v1/calibration/protocols/{discipline}",
        "/api/v1/calibration/observations",
        "/api/v1/calibration/evaluate",
        "/api/v1/calibration/evaluations/{evaluation_id}/threshold/confirm",
        "/api/v1/calibration/evaluations/{evaluation_id}/threshold/reject",
        "/api/v1/calibration/status",
        "/api/v1/calibration/test-assignments",
        "/api/v1/calibration/test-assignments/{proposal_id}/approve",
        "/api/v1/calibration/test-assignments/{proposal_id}/reject",
        "/api/v1/me/zone-profile",
        "/api/v1/pioneer-access/redemption",
        "/api/v1/pioneer-access/redemptions",
        "/api/v1/integrations/polar/oauth/start",
        "/api/v1/integrations/polar/oauth/callback",
        "/api/v1/integrations/polar",
        "/api/v1/integrations/polar/imports",
        "/api/v1/integrations/polar/imports/{import_id}/retry",
        "/api/v1/webhooks/polar",
    }


def test_openapi_excludes_hidden_load_fields(client: TestClient) -> None:
    """No planned or realized TSS field can enter the public schema."""
    schema = client.get("/openapi.json").json()

    _assert_no_forbidden_load_key(schema)


def test_pioneer_public_contract_exposes_no_internal_or_privileged_identifier(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    components = schema["components"]["schemas"]

    assert set(components["PioneerRedemptionResponse"]["properties"]) == {
        "program",
        "status",
        "redeemed_at",
    }
    assert set(components["PioneerRedemptionRequest"]["properties"]) == {"code"}
    assert set(components["DisciplineZoneProfileResponse"]["properties"]) >= {
        "available_test_scheduling_modes"
    }


def test_phase_14_write_contracts_exclude_retired_inputs(client: TestClient) -> None:
    """New writes collect only the independently approved Phase 14 fields."""
    schema = client.get("/openapi.json").json()
    components = schema["components"]["schemas"]

    assert "AthleteProfileUpdate" not in components
    assert set(schema["paths"]["/api/v1/me/profile"]) == {"get"}
    assert set(components["AthleteIdentifyingProfileUpdate"]["properties"]) == {
        "first_name",
        "last_name",
    }
    assert set(components["AthletePhysiologyProfileUpdate"]["properties"]) == {
        "date_of_birth",
        "resting_heart_rate_bpm",
    }
    assert set(components["AthleteOperationalProfileUpdate"]["properties"]) == {
        "timezone",
        "timezone_source",
        "timezone_confirmed",
        "heart_rate_monitor_confirmed",
    }
    assert set(components["TrainingHistoryEntryInput"]["properties"]) == {
        "discipline",
        "average_hours_per_week",
    }
    goal_fields = set(components["PrimaryRaceGoalInput"]["properties"])
    assert goal_fields == {
        "race_type",
        "race_name",
        "race_date",
        "swim_distance_meters",
        "bike_distance_meters",
        "run_distance_meters",
        "total_target_time_seconds",
        "swim_target_time_seconds",
        "bike_target_time_seconds",
        "run_target_time_seconds",
        "specific_focus",
    }
    assert {"title", "specific_description", "measurable_outcome"}.isdisjoint(
        goal_fields
    )

    setup_schema = schema["paths"]["/api/v1/onboarding/disciplines/{discipline}/setup"][
        "put"
    ]["requestBody"]["content"]["application/json"]["schema"]
    assert "RpeOnlySetup" not in str(setup_schema)


def test_openapi_documents_authentication_error(client: TestClient) -> None:
    """The current-user operation advertises the stable error envelope."""
    schema = client.get("/openapi.json").json()
    unauthorized = schema["paths"]["/api/v1/me"]["get"]["responses"]["401"]

    assert (
        unauthorized["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )
