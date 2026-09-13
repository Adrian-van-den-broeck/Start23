"""Race-discipline and false-readiness regression tests."""

from collections.abc import Mapping
from typing import Any

import pytest

from app.modules.onboarding.eligibility import (
    required_disciplines_for_race_type,
    satisfied_onboarding_steps,
)
from app.modules.physiology.models import Discipline


@pytest.mark.parametrize(
    ("race_type", "required"),
    [
        ("run", (Discipline.RUN,)),
        ("bike", (Discipline.BIKE,)),
        ("swim", (Discipline.SWIM,)),
        ("duathlon", (Discipline.BIKE, Discipline.RUN)),
        (
            "triathlon",
            (Discipline.SWIM, Discipline.BIKE, Discipline.RUN),
        ),
    ],
)
def test_authoritative_race_required_discipline_matrix(
    race_type: str,
    required: tuple[Discipline, ...],
) -> None:
    assert required_disciplines_for_race_type(race_type) == required


@pytest.mark.parametrize(
    ("race_type", "active_disciplines"),
    [
        ("run", {"run"}),
        ("bike", {"bike"}),
        ("swim", {"swim"}),
        ("duathlon", {"bike", "run"}),
        ("triathlon", {"swim", "bike", "run"}),
    ],
)
def test_zone_readiness_uses_only_race_required_active_profiles(
    race_type: str,
    active_disciplines: set[str],
) -> None:
    goal: Mapping[str, Any] = {
        "race_type": race_type,
        "race_name": "Race",
        "race_date": "2099-01-01",
        "total_target_time_seconds": 3600,
        **{f"{discipline}_distance_meters": 1000 for discipline in active_disciplines},
    }
    active = [
        {"discipline": discipline, "status": "active"}
        for discipline in active_disciplines
    ]
    pending = [
        {"discipline": discipline, "status": "pending"}
        for discipline in active_disciplines
    ]
    setup_intent = [
        {"discipline": discipline, "setup_status": "configured"}
        for discipline in active_disciplines
    ]

    ready = satisfied_onboarding_steps(
        profile=None,
        training_history=(),
        goal=goal,
        zones=active,
        discipline_setups=(),
    )
    not_ready = satisfied_onboarding_steps(
        profile=None,
        training_history=(),
        goal=goal,
        zones=pending,
        discipline_setups=setup_intent,
    )

    assert "zones" in ready
    assert "zones" not in not_ready


def test_all_three_training_history_is_independent_of_run_zone_requirement() -> None:
    goal = {
        "race_type": "run",
        "race_name": "Run",
        "race_date": "2099-01-01",
        "run_distance_meters": 10000,
        "total_target_time_seconds": 3600,
    }
    steps = satisfied_onboarding_steps(
        profile=None,
        training_history=(
            {
                "discipline": "run",
                "previous_month_weekly_minutes": 180,
                "baseline_model_version": "phase-13-joren-ruleset-1",
            },
        ),
        goal=goal,
        zones=({"discipline": "run", "status": "active"},),
        discipline_setups=(),
    )

    assert "zones" in steps
    assert "history" not in steps
