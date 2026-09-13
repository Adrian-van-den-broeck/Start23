"""R1 tests for version-aware onboarding state assessment."""

from app.modules.onboarding.versioning import (
    CURRENT_ONBOARDING_VERSION,
    CURRENT_REQUIRED_STEPS,
    CURRENT_RULESET_VERSION,
    assess_onboarding_version,
)


def test_current_completion_requires_matching_versions_and_evidence() -> None:
    state = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version=CURRENT_ONBOARDING_VERSION,
        completed_ruleset_version=CURRENT_RULESET_VERSION,
        satisfied_steps=CURRENT_REQUIRED_STEPS,
    )

    assert state.status == "completed"
    assert state.current_step == "completed"
    assert not state.upgrade_required
    assert state.missing_upgrade_steps == ()


def test_fresh_user_starts_once_at_profile_with_all_current_requirements() -> None:
    state = assess_onboarding_version(
        persisted_status="not_started",
        completed_onboarding_version=None,
        completed_ruleset_version=None,
        satisfied_steps=(),
    )

    assert state.status == "not_started"
    assert state.current_step == "profile"
    assert state.completed_steps == ()
    assert state.missing_upgrade_steps == ()
    assert not state.can_complete


def test_interrupted_upgrade_resumes_from_first_missing_step_deterministically() -> (
    None
):
    first = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version="phase-13-onboarding-v1",
        completed_ruleset_version=CURRENT_RULESET_VERSION,
        satisfied_steps=("profile", "heart_rate_monitor", "history", "goal"),
    )
    replay = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version="phase-13-onboarding-v1",
        completed_ruleset_version=CURRENT_RULESET_VERSION,
        satisfied_steps=("profile", "heart_rate_monitor", "history", "goal"),
    )

    assert first == replay
    assert first.status == "upgrade_required"
    assert first.current_step == "timezone"
    assert first.missing_upgrade_steps == ("timezone", "zones")


def test_legacy_completion_derives_only_missing_current_steps() -> None:
    state = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version="legacy-unversioned",
        completed_ruleset_version="phase-3-ruleset-3",
        satisfied_steps=("profile", "goal"),
    )

    assert state.status == "upgrade_required"
    assert state.completed_steps == ("profile", "goal")
    assert state.missing_upgrade_steps == (
        "heart_rate_monitor",
        "timezone",
        "history",
        "zones",
    )
    assert state.current_step == "heart_rate_monitor"
    assert not state.can_complete


def test_legacy_completion_with_valid_data_needs_review_not_reentry() -> None:
    state = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version="legacy-unversioned",
        completed_ruleset_version=CURRENT_RULESET_VERSION,
        satisfied_steps=CURRENT_REQUIRED_STEPS,
    )

    assert state.status == "upgrade_required"
    assert state.current_step == "review"
    assert state.can_complete
    assert state.missing_upgrade_steps == ()


def test_current_version_cannot_mask_lost_mandatory_evidence() -> None:
    state = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version=CURRENT_ONBOARDING_VERSION,
        completed_ruleset_version=CURRENT_RULESET_VERSION,
        satisfied_steps=(
            "profile",
            "heart_rate_monitor",
            "timezone",
            "history",
            "goal",
        ),
    )

    assert state.status == "upgrade_required"
    assert state.missing_upgrade_steps == ("zones",)
    assert state.current_step == "zones"
