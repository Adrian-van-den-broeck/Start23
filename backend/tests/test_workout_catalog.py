"""Phase 5 catalog validation, versioning, and public API tests."""

from collections.abc import Iterator
from dataclasses import replace
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.physiology.models import IntensityBucket, InternalLoad
from app.modules.workouts.catalog import (
    REVIEWED_CATALOG,
    FallbackCompatibility,
    ZoneRequirement,
    active_catalog,
    as_rpe_guided_template,
    snapshot_template,
)


class CatalogTokenVerifier:
    """Accept one deterministic local token."""

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        if access_token != "athlete":
            raise InvalidAccessTokenError
        return AuthenticatedIdentity(user_id=uuid4(), role="authenticated")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(
        create_app(
            Settings(environment="test"),
            access_token_verifier=CatalogTokenVerifier(),
        )
    ) as test_client:
        yield test_client


def test_reviewed_catalog_has_latest_swim_bike_and_run_templates() -> None:
    latest = active_catalog()

    assert len(REVIEWED_CATALOG) == 7
    assert len(latest) == 11
    assert {template.discipline.value for template in latest} == {
        "swim",
        "bike",
        "run",
    }
    assert (
        next(
            template for template in latest if template.name == "Easy aerobic run"
        ).version
        == 2
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("segments", (), "at least one segment"),
        ("expected_rpe_min", 9, "RPE range"),
        ("intensity_bucket", IntensityBucket.HIGH, "intensity bucket"),
        ("duration_minutes", Decimal("999"), "durations"),
    ],
)
def test_catalog_validation_rejects_incomplete_or_inconsistent_templates(
    field: str,
    value: Any,
    message: str,
) -> None:
    template = REVIEWED_CATALOG[0]

    with pytest.raises(ValueError, match=message):
        replace(template, **{field: value})


def test_fallback_compatibility_rejects_non_heart_rate_requirements() -> None:
    template = REVIEWED_CATALOG[2]

    with pytest.raises(ValueError, match="heart-rate"):
        replace(
            template,
            zone_requirements=(ZoneRequirement.POWER,),
            fallback_compatibility=FallbackCompatibility.COMPATIBLE,
        )


def test_snapshot_remains_stable_when_a_new_catalog_version_exists() -> None:
    version_one = next(
        template
        for template in REVIEWED_CATALOG
        if template.name == "Easy aerobic run" and template.version == 1
    )
    version_two = next(
        template
        for template in REVIEWED_CATALOG
        if template.name == "Easy aerobic run" and template.version == 2
    )

    snapshot = snapshot_template(version_one)

    assert snapshot.template_version == 1
    assert snapshot.duration_minutes == Decimal(40)
    assert snapshot.internal_planned_load.value == Decimal(2)
    assert version_two.duration_minutes == Decimal(45)
    assert version_two.internal_planned_load.value == Decimal("2.25")


def test_swim_template_can_be_projected_to_rpe_without_losing_technique_detail() -> (
    None
):
    swim = next(
        template
        for template in active_catalog()
        if template.discipline.value == "swim"
        and any(segment.is_swim_technique for segment in template.segments)
        and not template.explicit_scheduling_only
    )

    projected = as_rpe_guided_template(swim)

    assert all(segment.zone_target is None for segment in projected.segments)
    assert all(segment.rpe_target is not None for segment in projected.segments)
    assert any(segment.is_swim_technique for segment in projected.segments)


def test_internal_load_is_hidden_from_representations() -> None:
    template = REVIEWED_CATALOG[0]
    snapshot = snapshot_template(template)

    assert "internal_planned_load" not in repr(template)
    assert "internal_planned_load" not in repr(snapshot)
    assert "value" not in repr(InternalLoad(Decimal("12.5")))


def test_catalog_endpoint_requires_authentication_and_omits_hidden_load(
    client: TestClient,
) -> None:
    unauthorized = client.get("/api/v1/workout-catalog")
    response = client.get(
        "/api/v1/workout-catalog",
        headers={"Authorization": "Bearer athlete"},
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["templates"]) == 11
    calibration = next(
        template
        for template in payload["templates"]
        if template["name"] == "Week-1 fietskalibratie"
    )
    assert calibration["zone_requirements"] == []
    assert all(
        segment["zone_target"] is None
        and segment["protocol_target"]["protocol_id"]
        == "start23_week1_bike_calibration_v1"
        for segment in calibration["segments"]
    )
    serialized = response.text.lower().replace("_", "")
    assert "tss" not in serialized
    assert "internalplannedload" not in serialized
