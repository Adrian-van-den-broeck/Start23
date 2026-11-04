"""Probe safety checks using synthetic responses; never connect to a service."""

import os
from typing import Any
from unittest.mock import patch
from urllib.request import Request

from scripts import verify_a6_readonly as probe


def test_local_readiness_stops_before_account_requests() -> None:
    with patch.object(
        probe, "get", return_value=(200, {"environment": "local"})
    ) as get:
        assert probe.main() == 2
    get.assert_called_once_with("/ready")


def test_foreign_plan_disclosure_fails_gate() -> None:
    responses: list[tuple[int, Any]] = [
        (200, {"environment": "production"}),
        (200, {"paths": {"/api/v1/weekly-plans/recovery": {"get": {}}}}),
        (200, {"role": "authenticated", "athlete_id": "A"}),
        (200, {"active": {"id": "owned-plan"}, "pending": None, "draft": None}),
        (200, {"role": "authenticated", "athlete_id": "B"}),
        (200, {"active": None, "pending": None, "draft": None}),
        (200, {"id": "owned-plan"}),
    ]
    with (
        patch.dict(
            os.environ,
            {"WOMBO_TESTER_A_ACCESS_TOKEN": "A", "WOMBO_TESTER_B_ACCESS_TOKEN": "B"},
        ),
        patch.object(probe, "get", side_effect=responses),
    ):
        assert probe.main() == 2


def test_redirects_never_forward_bearer_credentials() -> None:
    request = Request(probe.BASE, headers={"Authorization": "Bearer synthetic"})
    assert (
        probe.NoRedirect().redirect_request(
            request, None, 302, "redirect", {}, "https://other.invalid"
        )
        is None
    )
