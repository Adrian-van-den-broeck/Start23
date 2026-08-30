"""Pure Phase 8 weekly context and athlete-local calendar tests."""

from datetime import date, datetime, timezone

import pytest

from app.modules.checkins.domain import (
    AthletePlanChoice,
    RestrictionDecision,
    athlete_local_week_start,
    available_dates_from_blocked_dates,
    confirmed_restriction_sets,
    context_fingerprint,
)
from app.modules.physiology.injury import RestrictionStatus
from app.modules.physiology.models import Discipline


def test_local_week_uses_athlete_monday_not_utc_monday() -> None:
    instant = datetime(2026, 10, 25, 23, 30, tzinfo=timezone.utc)

    assert athlete_local_week_start(
        instant=instant,
        timezone_name="Europe/Amsterdam",
    ) == date(2026, 10, 26)


def test_blocked_and_strenuous_dates_create_local_availability() -> None:
    available_dates = available_dates_from_blocked_dates(
        week_start=date(2026, 8, 3),
        blocked_dates=frozenset({date(2026, 8, 4)}),
        strenuous_dates=frozenset({date(2026, 8, 6)}),
    )

    assert list(available_dates) == [
        date(2026, 8, 3),
        date(2026, 8, 5),
        date(2026, 8, 7),
        date(2026, 8, 8),
        date(2026, 8, 9),
    ]


def test_restrictions_split_blocked_and_low_only_without_diagnosis() -> None:
    blocked, low_only = confirmed_restriction_sets(
        (
            RestrictionDecision(
                discipline=Discipline.RUN,
                status=RestrictionStatus.SELF_REPORTED_BLOCKED,
                source="athlete",
                athlete_plan_choice=AthletePlanChoice.KEEP_BLOCKED,
            ),
            RestrictionDecision(
                discipline=Discipline.BIKE,
                status=RestrictionStatus.SELF_REPORTED_LIMITED,
                source="athlete",
                athlete_plan_choice=AthletePlanChoice.TRAIN_LOW_ONLY,
            ),
        )
    )

    assert blocked == frozenset({Discipline.RUN})
    assert low_only == frozenset({Discipline.BIKE})


def test_professional_restriction_requires_attributable_advice() -> None:
    with pytest.raises(ValueError, match="requires attributable advice"):
        RestrictionDecision(
            discipline=Discipline.SWIM,
            status=RestrictionStatus.PROFESSIONAL_RESTRICTED,
            source="physician",
            athlete_plan_choice=AthletePlanChoice.KEEP_BLOCKED,
        )


def test_context_fingerprint_is_order_stable_and_content_sensitive() -> None:
    first = context_fingerprint({"blocked_dates": [], "fatigue_level": "low"})
    reordered = context_fingerprint({"fatigue_level": "low", "blocked_dates": []})
    changed = context_fingerprint({"fatigue_level": "high", "blocked_dates": []})

    assert first == reordered
    assert first != changed
