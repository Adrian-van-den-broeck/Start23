"""Shared deterministic prerequisites for current onboarding and planning."""

from collections.abc import Iterable, Mapping
from typing import Any

from app.modules.calibration.service import is_current_mvp_setup_values
from app.modules.onboarding.versioning import CURRENT_RULESET_VERSION, OnboardingStep
from app.modules.physiology.models import Discipline

_RACE_DISCIPLINES: dict[str, frozenset[str]] = {
    "run": frozenset({"run"}),
    "bike": frozenset({"bike"}),
    "swim": frozenset({"swim"}),
    "triathlon": frozenset({"swim", "bike", "run"}),
    "duathlon": frozenset({"bike", "run"}),
}


def _structured_goal_is_current(goal: Mapping[str, Any] | None) -> bool:
    if goal is None:
        return False
    race_type = str(goal.get("race_type", ""))
    disciplines = _RACE_DISCIPLINES.get(race_type)
    if disciplines is None:
        return False
    required_distances = {f"{discipline}_distance_meters" for discipline in disciplines}
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

    configured = {
        str(row.get("discipline"))
        for row in zones
        if row.get("status", "active") == "active"
    }
    configured.update(
        str(row.get("discipline"))
        for row in discipline_setups
        if row.get("setup_status")
        in {"configured", "test_pending", "calibration_pending"}
        and is_current_mvp_setup_values(
            discipline=str(row.get("discipline")),
            setup_route=str(row.get("setup_route")),
            guidance_mode=str(row.get("guidance_mode")),
            protocol_id=(
                str(row["protocol_id"]) if row.get("protocol_id") is not None else None
            ),
        )
    )
    if configured == {discipline.value for discipline in Discipline}:
        steps.append("zones")
    return tuple(steps)
