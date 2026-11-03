"""Private U-001 registration and consumer contract. No inferred skipped work."""

from collections import Counter
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Literal

POLICY = "weekly-registration-2"
RegistrationStatus = Literal[
    "measured",
    "estimated",
    "skipped",
    "partial_observed",
    "awaiting_feedback",
    "unavailable",
    "unknown",
]


@dataclass(frozen=True, slots=True, repr=False)
class WorkoutRegistration:
    activity_id: str | None
    occurrence_id: str | None
    status: RegistrationStatus
    value: Decimal | None = None
    method: str = "unavailable"
    version: str = "unavailable"
    eligible: bool = False
    calculation_id: str | None = None


@dataclass(frozen=True, slots=True, repr=False)
class WeeklyCompleteness:
    known_subtotal: Decimal
    planned_count: int
    completed_count: int
    skipped_count: int
    unknown_count: int
    pending_feedback_count: int
    usable_measured_count: int
    usable_estimated_count: int
    partial_unavailable_count: int
    extra_supported_count: int
    methods: tuple[tuple[str, int], ...]
    planner_usable_load: Decimal | None
    reason: str | None
    progression_eligible: bool
    volume_debt_eligible: bool
    intensity_debt_eligible: bool
    reference_baseline_eligible: bool
    calculation_ids: tuple[str, ...]
    policy: str = POLICY


def aggregate_week(
    *,
    expected_occurrences: tuple[str, ...],
    registrations: tuple[WorkoutRegistration, ...],
    expected_known: bool,
) -> WeeklyCompleteness:
    """Evaluate the authoritative occurrence set, including supported extra work.

    Completed counts performed planned occurrences, even if feedback/load is
    missing. Extra activities are counted separately. Partial values belong in
    the known subtotal but never in a proven complete weekly total.
    """
    if len(set(expected_occurrences)) != len(expected_occurrences):
        raise ValueError("Duplicate expected workout identity.")
    expected = set(expected_occurrences)
    activity_ids = [
        row.activity_id for row in registrations if row.activity_id is not None
    ]
    occurrence_ids = [
        row.occurrence_id for row in registrations if row.occurrence_id is not None
    ]
    if len(set(activity_ids)) != len(activity_ids) or len(set(occurrence_ids)) != len(
        occurrence_ids
    ):
        raise ValueError("Ambiguous workout registration identity.")
    for row in registrations:
        if row.status not in {
            "measured",
            "estimated",
            "skipped",
            "partial_observed",
            "awaiting_feedback",
            "unavailable",
            "unknown",
        }:
            raise ValueError("Unsupported registration state.")
        if row.value is not None and (not row.value.is_finite() or row.value < 0):
            raise ValueError("Invalid registration value.")
        if row.status == "skipped" and (
            row.activity_id is not None
            or row.value is not None
            or row.occurrence_id not in expected
        ):
            raise ValueError("A skipped workout cannot be a completed activity.")
        if row.status in {"measured", "estimated"} and row.value is None:
            raise ValueError("Usable registration requires evidence.")
        if row.eligible and row.status in {"measured", "estimated"}:
            supported = (
                row.status == "measured"
                and row.method == "observed_zone_minutes"
                and row.version == "phase-13-joren-ruleset-1"
            ) or (
                row.status == "estimated"
                and (
                    (
                        row.method == "average_hr_zone_duration"
                        and row.version == "phase-13-joren-ruleset-1"
                    )
                    or (
                        row.method == "duration_adjusted_session_rpe"
                        and row.version == "joren-realized-tss-matrix-2"
                    )
                )
            )
            if not supported:
                raise ValueError("Unsupported weekly method/version combination.")
        if (
            row.status in {"unknown", "awaiting_feedback", "unavailable"}
            and row.value is not None
        ):
            raise ValueError("Unavailable registration cannot claim a numeric value.")
    by_occurrence = {
        row.occurrence_id: row for row in registrations if row.occurrence_id in expected
    }
    unknown = len(expected - set(by_occurrence)) + sum(
        row.status == "unknown" for row in registrations
    )
    pending = sum(row.status == "awaiting_feedback" for row in registrations)
    unavailable = sum(
        row.status in {"partial_observed", "unavailable"}
        or (row.status in {"measured", "estimated"} and not row.eligible)
        for row in registrations
    )
    orphaned = any(
        row.occurrence_id is not None and row.occurrence_id not in expected
        for row in registrations
    )
    reason = (
        "expected_occurrences_unknown"
        if not expected_known
        else "unmatched_revision_evidence"
        if orphaned
        else "unknown_workout_completion"
        if unknown
        else "pending_feedback"
        if pending
        else "partial_or_unavailable_load"
        if unavailable
        else None
    )
    with localcontext(Context(prec=50)):
        subtotal = sum(
            (row.value for row in registrations if row.value is not None), Decimal(0)
        )
    eligible = reason is None
    return WeeklyCompleteness(
        known_subtotal=subtotal,
        planned_count=len(expected),
        completed_count=sum(
            row.activity_id is not None for row in by_occurrence.values()
        ),
        skipped_count=sum(row.status == "skipped" for row in by_occurrence.values()),
        unknown_count=unknown,
        pending_feedback_count=pending,
        usable_measured_count=sum(
            row.status == "measured" and row.eligible for row in registrations
        ),
        usable_estimated_count=sum(
            row.status == "estimated" and row.eligible for row in registrations
        ),
        partial_unavailable_count=unavailable,
        extra_supported_count=sum(
            row.occurrence_id is None
            and row.eligible
            and row.status in {"measured", "estimated"}
            for row in registrations
        ),
        methods=tuple(
            sorted(
                Counter(f"{row.method}@{row.version}" for row in registrations).items()
            )
        ),
        planner_usable_load=subtotal if eligible else None,
        reason=reason,
        progression_eligible=eligible,
        volume_debt_eligible=eligible,
        # Existing observed/classified-minute requirements still apply after this
        # registration gate. No Session-RPE intensity minutes are synthesized.
        intensity_debt_eligible=eligible,
        reference_baseline_eligible=eligible,
        calculation_ids=tuple(
            sorted(
                row.calculation_id
                for row in registrations
                if row.calculation_id is not None
            )
        ),
    )
