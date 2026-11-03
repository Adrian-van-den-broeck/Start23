"""D10/D11: known subtotals and completed registration are distinct."""

from decimal import Decimal

import pytest

from app.modules.physiology.weekly_registration import (
    WorkoutRegistration,
    aggregate_week,
)


def measured(occurrence: str | None, value: str = "60") -> WorkoutRegistration:
    return WorkoutRegistration(
        f"activity-{occurrence}",
        occurrence,
        "measured",
        Decimal(value),
        "observed_zone_minutes",
        "phase-13-joren-ruleset-1",
        True,
    )


def estimated(occurrence: str, value: str = "50") -> WorkoutRegistration:
    return WorkoutRegistration(
        f"activity-{occurrence}",
        occurrence,
        "estimated",
        Decimal(value),
        "duration_adjusted_session_rpe",
        "joren-realized-tss-matrix-2",
        True,
    )


def test_owner_110_subtotal_requires_third_occurrence_registration() -> None:
    known = (measured("one"), estimated("two"))
    incomplete = aggregate_week(
        expected_occurrences=("one", "two", "three"),
        registrations=known,
        expected_known=True,
    )
    assert incomplete.known_subtotal == 110
    assert incomplete.unknown_count == 1
    assert incomplete.planner_usable_load is None
    assert not incomplete.progression_eligible
    complete = aggregate_week(
        expected_occurrences=("one", "two", "three"),
        registrations=(*known, WorkoutRegistration(None, "three", "skipped")),
        expected_known=True,
    )
    assert complete.planner_usable_load == 110
    assert complete.skipped_count == 1
    assert complete.completed_count == 2
    assert complete.usable_measured_count == 1
    assert complete.usable_estimated_count == 1
    assert complete.progression_eligible and complete.volume_debt_eligible
    assert complete.reference_baseline_eligible


@pytest.mark.parametrize(
    "status", ["partial_observed", "awaiting_feedback", "unavailable", "unknown"]
)
def test_ambiguous_registration_never_means_skipped(status: str) -> None:
    from typing import cast

    from app.modules.physiology.weekly_registration import RegistrationStatus

    row = WorkoutRegistration(
        "activity" if status != "unknown" else None,
        "two",
        cast(RegistrationStatus, status),
        Decimal("34.20") if status == "partial_observed" else None,
    )
    result = aggregate_week(
        expected_occurrences=("one", "two"),
        registrations=(measured("one", "48"), row),
        expected_known=True,
    )
    assert result.known_subtotal == (
        Decimal("82.20") if status == "partial_observed" else 48
    )
    assert result.skipped_count == 0
    assert result.planner_usable_load is None
    assert not result.volume_debt_eligible and not result.intensity_debt_eligible


def test_all_skipped_is_explicit_zero_and_no_registration_is_unknown() -> None:
    skipped = aggregate_week(
        expected_occurrences=("one",),
        registrations=(WorkoutRegistration(None, "one", "skipped"),),
        expected_known=True,
    )
    assert skipped.planner_usable_load == 0
    unknown = aggregate_week(
        expected_occurrences=("one",), registrations=(), expected_known=True
    )
    assert unknown.known_subtotal == 0 and unknown.planner_usable_load is None
    assert unknown.unknown_count == 1 and unknown.skipped_count == 0
    no_plan = aggregate_week(
        expected_occurrences=(), registrations=(), expected_known=False
    )
    assert no_plan.planner_usable_load is None


def test_extra_supported_activity_and_mismatched_revision() -> None:
    result = aggregate_week(
        expected_occurrences=("one",),
        registrations=(measured("one"), measured(None, "20")),
        expected_known=True,
    )
    assert result.planner_usable_load == 80 and result.extra_supported_count == 1
    wrong_revision = aggregate_week(
        expected_occurrences=("new",),
        registrations=(measured("old"),),
        expected_known=True,
    )
    assert wrong_revision.planner_usable_load is None
    assert wrong_revision.reason == "unmatched_revision_evidence"


def test_duplicate_occurrence_and_duplicate_activity_fail_closed() -> None:
    with pytest.raises(ValueError, match="identity"):
        aggregate_week(
            expected_occurrences=("one",),
            registrations=(measured("one"), estimated("one")),
            expected_known=True,
        )
    with pytest.raises(ValueError, match="identity"):
        aggregate_week(
            expected_occurrences=("one", "one"), registrations=(), expected_known=True
        )


def test_ineligible_estimate_retains_known_value_but_no_planner_total() -> None:
    result = aggregate_week(
        expected_occurrences=("one",),
        registrations=(
            WorkoutRegistration(
                "a",
                "one",
                "estimated",
                Decimal("131.25"),
                "duration_adjusted_session_rpe",
                "joren-realized-tss-matrix-2",
                False,
            ),
        ),
        expected_known=True,
    )
    assert result.known_subtotal == Decimal("131.25")
    assert result.planner_usable_load is None
    assert result.partial_unavailable_count == 1
