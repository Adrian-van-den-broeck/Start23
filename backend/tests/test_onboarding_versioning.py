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


def test_legacy_completion_derives_only_missing_current_steps() -> None:
    state = assess_onboarding_version(
        persisted_status="completed",
        completed_onboarding_version="legacy-unversioned",
        completed_ruleset_version="phase-3-ruleset-3",
        satisfied_steps=("profile", "goal"),
    )

    assert state.status == "upgrade_required"
    assert state.completed_steps == ("profile", "goal")
    assert state.missing_upgrade_steps == ("history", "zones")
    assert state.current_step == "history"
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
        satisfied_steps=("profile", "history", "goal"),
    )

    assert state.status == "upgrade_required"
    assert state.missing_upgrade_steps == ("zones",)
    assert state.current_step == "zones"
