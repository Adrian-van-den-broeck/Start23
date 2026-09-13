"""Shared deterministic prerequisites for current onboarding and planning."""

from collections.abc import Iterable, Mapping
from typing import Any

from app.modules.onboarding.versioning import CURRENT_RULESET_VERSION, OnboardingStep
from app.modules.physiology.models import Discipline

RACE_REQUIRED_DISCIPLINES: dict[str, tuple[Discipline, ...]] = {
    "run": (Discipline.RUN,),
    "bike": (Discipline.BIKE,),
    "swim": (Discipline.SWIM,),
    "duathlon": (Discipline.BIKE, Discipline.RUN),
    "triathlon": (Discipline.SWIM, Discipline.BIKE, Discipline.RUN),
}


def required_disciplines_for_race_type(
    race_type: object,
) -> tuple[Discipline, ...]:
    """Return the one authoritative current race-to-discipline mapping."""
    return RACE_REQUIRED_DISCIPLINES.get(str(race_type), ())


def _structured_goal_is_current(goal: Mapping[str, Any] | None) -> bool:
    if goal is None:
        return False
    race_type = str(goal.get("race_type", ""))
    disciplines = required_disciplines_for_race_type(race_type)
    if not disciplines:
        return False
    required_distances = {
        f"{discipline.value}_distance_meters" for discipline in disciplines
    }
    return (
        bool(str(goal.get("race_name", "")).strip())
        and goal.get("race_date") is not None
        and goal.get("total_target_time_seconds") is not None
        and all(goal.get(field) is not None for field in required_distances)
    )


def satisfied_onboarding_steps(
    *,
    profile: Mapping[str, Any] | None,
    training_history: Iterable[Mapping[str, Any]],
    goal: Mapping[str, Any] | None,
    zones: Iterable[Mapping[str, Any]],
    discipline_setups: Iterable[Mapping[str, Any]],
) -> tuple[OnboardingStep, ...]:
    """Return current-version steps satisfied by one persistence snapshot."""
    steps: list[OnboardingStep] = []
    if profile is not None and all(
        profile.get(field) is not None
        for field in ("date_of_birth", "resting_heart_rate_bpm")
    ):
        steps.append("profile")

    if profile is not None and profile.get("heart_rate_monitor_confirmed_at"):
        steps.append("heart_rate_monitor")

    if profile is not None and all(
        profile.get(field) is not None
        for field in ("timezone", "timezone_source", "timezone_confirmed_at")
    ):
        steps.append("timezone")

    history = tuple(training_history)
    if {row.get("discipline") for row in history} == {
        discipline.value for discipline in Discipline
    } and all(
        row.get("previous_month_weekly_minutes") is not None
        and row.get("baseline_model_version") == CURRENT_RULESET_VERSION
        for row in history
    ):
        steps.append("history")

    if _structured_goal_is_current(goal):
        steps.append("goal")

    # A setup row records intent only. Planning capability exists only after a
    # calculated/manual profile has passed its separate athlete approval and is
    # active. This also prevents a threshold-only direct RPC from claiming
    # readiness after a partial write.
    del discipline_setups
    required = {
        discipline.value
        for discipline in required_disciplines_for_race_type(
            goal.get("race_type") if goal is not None else None
        )
    }
    configured = {
        str(row.get("discipline"))
        for row in zones
        if row.get("status", "active") == "active"
    }
    if required and configured >= required:
        steps.append("zones")
    return tuple(steps)
