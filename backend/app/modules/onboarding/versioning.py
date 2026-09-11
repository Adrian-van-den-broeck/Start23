"""Version-aware onboarding prerequisite assessment.

This module is deliberately persistence- and framework-independent so the
onboarding service and the planner can share the same state rules in R2.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias

from app.modules.physiology.joren import VERSION as JOREN_RULESET_VERSION

OnboardingStep: TypeAlias = Literal[
    "profile",
    "history",
    "goal",
    "zones",
    "review",
    "completed",
]
OnboardingStatus: TypeAlias = Literal[
    "not_started",
    "in_progress",
    "upgrade_required",
    "completed",
]

CURRENT_ONBOARDING_VERSION: Final = "phase-13-onboarding-v1"
CURRENT_RULESET_VERSION: Final = JOREN_RULESET_VERSION.value
LEGACY_UNVERSIONED_ONBOARDING: Final = "legacy-unversioned"
CURRENT_REQUIRED_STEPS: tuple[OnboardingStep, ...] = (
    "profile",
    "history",
    "goal",
    "zones",
)
CURRENT_COMPLETION_STEPS: tuple[OnboardingStep, ...] = (
    *CURRENT_REQUIRED_STEPS,
    "review",
)


@dataclass(frozen=True)
class OnboardingVersionAssessment:
    """Current interpretation without changing historical completion data."""

    status: OnboardingStatus
    current_step: OnboardingStep
    completed_steps: tuple[OnboardingStep, ...]
    can_complete: bool
    upgrade_required: bool
    missing_upgrade_steps: tuple[OnboardingStep, ...]


def assess_onboarding_version(
    *,
    persisted_status: str,
    completed_onboarding_version: str | None,
    completed_ruleset_version: str | None,
    satisfied_steps: Iterable[OnboardingStep],
) -> OnboardingVersionAssessment:
    """Evaluate current prerequisites without reinterpreting old completion."""
    satisfied = frozenset(satisfied_steps)
    completed_required = tuple(
        step for step in CURRENT_REQUIRED_STEPS if step in satisfied
    )
    missing = tuple(step for step in CURRENT_REQUIRED_STEPS if step not in satisfied)
    can_complete = not missing
    completion_is_current = (
        persisted_status == "completed"
        and completed_onboarding_version == CURRENT_ONBOARDING_VERSION
        and completed_ruleset_version == CURRENT_RULESET_VERSION
        and can_complete
    )
    if completion_is_current:
        return OnboardingVersionAssessment(
            status="completed",
            current_step="completed",
            completed_steps=CURRENT_COMPLETION_STEPS,
            can_complete=True,
            upgrade_required=False,
            missing_upgrade_steps=(),
        )

    if persisted_status == "completed":
        return OnboardingVersionAssessment(
            status="upgrade_required",
            current_step=missing[0] if missing else "review",
            completed_steps=completed_required,
            can_complete=can_complete,
            upgrade_required=True,
            missing_upgrade_steps=missing,
        )

    status: OnboardingStatus = (
        "in_progress" if persisted_status == "in_progress" else "not_started"
    )
    return OnboardingVersionAssessment(
        status=status,
        current_step=missing[0] if missing else "review",
        completed_steps=completed_required,
        can_complete=can_complete,
        upgrade_required=False,
        missing_upgrade_steps=(),
    )
