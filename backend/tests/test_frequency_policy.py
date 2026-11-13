"""Synthetic value inputs; no issued authorization or enrolled reviewer."""

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

import httpx
import pytest

from app.core.config import Settings
from app.modules.onboarding.frequency import Preferences, PreferenceSave
from app.modules.onboarding.repository import (
    RepositoryUnavailableError,
    SupabaseOnboardingRepository,
)
from app.modules.physiology.models import Discipline
from app.modules.planning.domain import PlanningConstraintError
from app.modules.planning.frequency_policy import (
    EVIDENCE_REFERENCES,
    POLICY,
    resolve_frequency,
)
from app.modules.planning.v6_selection import V6Controls
from app.modules.planning.v6_service import (
    controls_json,
    effective_controls,
    frozen_controls,
    private_json,
)

OWNER = UUID(int=980)
WEEK = date(2026, 11, 16)
NOW = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)


def context(preference: int | None = None) -> dict[str, Any]:
    return {
        "policy_version": POLICY,
        "athlete_id": str(OWNER),
        "week_start": WEEK.isoformat(),
        "timezone": "Europe/Amsterdam",
        "preference": {
            "revision": 1,
            "preferences": {"run": preference, "bike": None, "swim": None},
            "confirmed_at": NOW.isoformat(),
            "reconfirmation_required": [],
        },
        "decisions": [],
        "basis": {"fingerprint": "synthetic-input"},
        "retained_counts": {},
        "unmatched_activities": [],
    }


def reviewed_input(c: dict[str, Any], maximum: int = 2) -> None:
    # In-memory value fixture only. No SQL registry/approval record is created.
    c["decisions"] = [
        {
            "id": str(UUID(int=981)),
            "revision": 1,
            "sport": "run",
            "athlete_id": str(OWNER),
            "week_start": WEEK.isoformat(),
            "timezone": c["timezone"],
            "maximum": maximum,
            "policy_version": POLICY,
            "status": "authorized",
            "reviewer_reference": "fixture:review-reference",
            "operator_reference": "fixture:operator-reference",
            "reviewer_authorized": True,
            "reviewed_at": NOW.isoformat(),
            "decided_at": NOW.isoformat(),
            "expires_at": "2026-11-23T00:00:00+01:00",
            "evidence_context": deepcopy(c["basis"]),
            "evidence": {
                **{key: "fixture:reference" for key in EVIDENCE_REFERENCES},
                "period_from": "2026-10-01",
                "period_to": "2026-11-12",
            },
        }
    ]


def resolve(c: dict[str, Any]) -> tuple[Any, ...]:
    return resolve_frequency(
        c, athlete_id=OWNER, week_start=WEEK, timezone_name="Europe/Amsterdam", now=NOW
    )


@pytest.mark.parametrize(
    "p,m,target", [(None, 3, 1), (0, 3, 0), (5, 2, 2), (2, 3, 2), (2, 0, 0)]
)
def test_separate_soft_preference_and_week_maximum(
    p: int | None, m: int, target: int
) -> None:
    c = context(p)
    reviewed_input(c, m)
    f = resolve(c)[0]
    assert f.maximum == m and f.requested == target
    assert c["preference"]["preferences"]["run"] == p


@pytest.mark.parametrize("p,expected", [(None, None), (0, 0), (1, 1), (8, 1)])
def test_missing_authority_uses_only_legacy_envelope(
    p: int | None, expected: int | None
) -> None:
    frequencies = resolve(context(p))
    assert (frequencies[0].requested if frequencies else None) == expected


@pytest.mark.parametrize(
    "change",
    [
        "revoked",
        "suspended",
        "expired",
        "superseded",
        "missing_evidence",
        "stale_basis",
        "reconfirm",
        "reviewer_disabled",
        "timezone",
    ],
)
def test_invalid_review_never_expands(change: str) -> None:
    c = context(5)
    reviewed_input(c)
    d = c["decisions"][0]
    if change in {"revoked", "suspended", "superseded"}:
        d["status"] = change
    elif change == "expired":
        d["expires_at"] = "2026-11-12T00:00:00Z"
    elif change == "missing_evidence":
        d["evidence"].pop("review_record_reference")
    elif change == "stale_basis":
        c["basis"] = {"fingerprint": "changed"}
    elif change == "reconfirm":
        c["preference"]["reconfirmation_required"] = ["run"]
    elif change == "reviewer_disabled":
        d["reviewer_authorized"] = False
    elif change == "timezone":
        d["timezone"] = "UTC"
    assert resolve(c)[0].requested == 1


def test_test_only_is_rejected_by_regular_real_athlete_resolver() -> None:
    c = context(2)
    reviewed_input(c)
    c["decisions"][0]["reviewer_reference"] = "TEST_ONLY: no actual reviewer"
    with pytest.raises(ValueError, match="test_only_frequency_authority"):
        resolve(c)


def test_retained_occurrences_are_not_retroactively_capped_or_deleted() -> None:
    c = context(2)
    c["retained_counts"] = {"run": 3}
    assert resolve(c)[0].maximum == 3 and resolve(c)[0].requested == 1
    reviewed_input(c, 2)
    with pytest.raises(PlanningConstraintError) as error:
        resolve(c)
    assert error.value.code == "v6_frequency_retained_conflict"
    assert c["retained_counts"]["run"] == 3


def test_unmatched_activity_blocks_expansion_without_synthetic_occurrences() -> None:
    c = context(3)
    reviewed_input(c, 3)
    c["unmatched_activities"] = [str(UUID(int=985))]
    c["retained_counts"] = {"run": 1}
    assert next(f for f in resolve(c) if f.sport is Discipline.RUN).maximum == 1


def test_frozen_context_survives_restart_but_cannot_revive() -> None:
    c = context(2)
    reviewed_input(c)
    controls = V6Controls(
        athlete_scope=OWNER,
        week_scope=WEEK,
        session_frequency=resolve(c),
        frequency_policy_context=private_json(c),
    )
    import json

    stored = json.loads(controls_json(controls))
    assert frozen_controls(stored) == controls
    assert effective_controls(stored, controls) == controls
    c["decisions"][0]["status"] = "revoked"
    current = V6Controls(
        athlete_scope=OWNER,
        week_scope=WEEK,
        session_frequency=resolve(c),
        frequency_policy_context=private_json(c),
    )
    with pytest.raises(PlanningConstraintError, match="changed"):
        effective_controls(stored, current)


@pytest.mark.parametrize(
    "values",
    [
        {"run": 0, "bike": None, "swim": 1},
        {"run": None, "bike": None, "swim": None},
        {"run": 24, "bike": 0, "swim": 0},
    ],
)
def test_optional_zero_and_revocable_preferences(values: dict[str, int | None]) -> None:
    assert Preferences.model_validate(values).model_dump() == values


@pytest.mark.parametrize(
    "values",
    [
        {"run": True, "bike": None, "swim": None},
        {"run": 1.5, "bike": None, "swim": None},
        {"run": -1, "bike": None, "swim": None},
        {"run": 25, "bike": None, "swim": None},
        {"run": 24, "bike": 1, "swim": None},
    ],
)
def test_invalid_technical_input_is_rejected(values: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        Preferences.model_validate(values)


def test_client_cannot_supply_authoritative_owner_or_maximum() -> None:
    with pytest.raises(ValueError):
        PreferenceSave.model_validate(
            {
                "expected_revision": 0,
                "operation_id": str(UUID(int=1)),
                "preferences": {"run": 2, "bike": None, "swim": None},
                "athlete_id": str(OWNER),
                "maximum": 5,
            }
        )


def test_preference_transport_uses_owner_token_and_fails_closed_on_read_error() -> None:
    import asyncio

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(503, json={"private": "not public"})

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            repo = SupabaseOnboardingRepository(
                Settings(
                    environment="test",
                    _env_file=None,
                    supabase_publishable_key="sb_publishable_test",
                ),
                client=client,
            )
            with pytest.raises(RepositoryUnavailableError):
                await repo.fetch_frequency_preferences("verified-token")

    asyncio.run(exercise())
    assert captured[0].headers["Authorization"] == "Bearer verified-token"
    assert captured[0].url.path.endswith("rpc/get_frequency_preferences")
