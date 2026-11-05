"""Pure offline partial-approval evidence; never an operational calculation gate.

Historical C2/C2.1/V6 inputs remain immutable. New confirmed parameters apply
only to this version. No I/O, planner, API, persistence or realized calculation.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Literal

from app.modules.workouts.joren_draft import DraftWorkout, SwimDistance, WallRest

DECISION_VERSION = "joren-v6-partial-approval-1"
ESTIMATOR_VERSION = "joren-v6-swim-reference-active-time-offline-1"
EVIDENCE = "docs/catalog/implementation/JOREN_V6_PARTIAL_APPROVAL_REGISTER.md"
CONFIRMED_IF = tuple(map(Decimal, (".55", ".75", ".88", ".98", "1.15")))
REFERENCE_MINUTES = tuple(map(Decimal, ("2.17", "2.00", "1.83", "1.67", "1.50")))
# Exact encoding for the existing experimental seconds-input calculator.
REFERENCE_SECONDS = tuple(map(Decimal, ("130.2", "120", "109.8", "100.2", "90")))
SELECTION_PRIORITIES = (
    "Athlete safety and suitability",
    "Injury, recovery and progression restrictions",
    "Explicit authorized weekly budget as a maximum",
    "One suitable session per sport where feasible",
    "Closeness to the 50/30/20 triathlon target",
    "Remaining budget utilization",
    "Deterministic tie-breaks",
)


@dataclass(frozen=True, slots=True, repr=False)
class EstimatedSegment:
    # The entire immutable event retains token, cell, sequence, span and meters.
    original: SwimDistance | WallRest
    estimated_active_minutes: Fraction


@dataclass(frozen=True, slots=True, repr=False)
class SwimEstimate:
    # Retain the lossless source record; do not replace missing prescribed time.
    original: DraftWorkout
    segments: tuple[EstimatedSegment, ...]
    low_minutes: Fraction
    high_minutes: Fraction
    status: Literal["ESTIMATED_FROM_APPROVED_REFERENCE_PACE"] = field(
        default="ESTIMATED_FROM_APPROVED_REFERENCE_PACE", init=False
    )
    estimator_version: str = field(default=ESTIMATOR_VERSION, init=False)
    decision_version: str = field(default=DECISION_VERSION, init=False)
    evidence_reference: str = field(default=EVIDENCE, init=False)
    authoritative_duration_compliance: Literal["UNVERIFIED"] = field(
        default="UNVERIFIED", init=False
    )
    operational_safety_gate_approved: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True, slots=True, repr=False)
class EstimatedSwimSession:
    occurrence_id: str
    local_date: date
    source: DraftWorkout


@dataclass(frozen=True, slots=True, repr=False)
class EstimatedSwimWeek:
    week_start: date
    estimates: tuple[SwimEstimate, ...]
    low_minutes: Fraction
    high_minutes: Fraction
    high_ratio: Fraction | None
    status: Literal["ESTIMATED_COMPLIANT", "ESTIMATED_EXCEEDED", "NOT_APPLICABLE"]
    # Caller-specified sensitivity scenario, never an inferred uncertainty bound.
    sensitivity_half_width: Fraction
    sensitivity_ratio_min: Fraction | None
    sensitivity_ratio_max: Fraction | None
    boundary_sensitive: bool
    estimator_version: str = field(default=ESTIMATOR_VERSION, init=False)
    decision_version: str = field(default=DECISION_VERSION, init=False)
    authoritative_duration_compliance: Literal["UNVERIFIED"] = field(
        default="UNVERIFIED", init=False
    )
    operational_safety_gate_approved: Literal[False] = field(default=False, init=False)


def estimate_swim(record: DraftWorkout) -> SwimEstimate:
    """Estimate planned active time from individual ordered distance segments.

    Only distance-only prescriptions are supported. Measured/performed time is
    neither an input nor an output. Exact rational arithmetic ignores ambient
    Decimal context. Z1/Z2 are LOW; Z3-Z5 HIGH; stationary wall rest adds zero.
    """
    if record.sport != "swim" or record.distribution_unit != "meters":
        raise ValueError("distance_only_swimming_required")
    if record.planned_duration_seconds is not None or not record.events:
        raise ValueError("distance_only_swimming_required")
    segments = []
    quantities = [Fraction(0)] * 5
    low, high = Fraction(0), Fraction(0)
    for index, event in enumerate(record.events, 1):
        if event.sequence != index:
            raise ValueError("invalid_segment_order")
        if isinstance(event, WallRest):
            if not event.seconds.is_finite() or event.seconds <= 0:
                raise ValueError("invalid_wall_rest")
            minutes = Fraction(0)
        elif isinstance(event, SwimDistance):
            if (
                event.zone not in range(1, 6)
                or not event.meters.is_finite()
                or event.meters <= 0
                or event.meters != event.meters.to_integral_value()
            ):
                raise ValueError("invalid_swim_segment")
            quantities[event.zone - 1] += Fraction(event.meters)
            minutes = (
                Fraction(event.meters)
                * Fraction(REFERENCE_MINUTES[event.zone - 1])
                / 100
            )
            if event.zone <= 2:
                low += minutes
            else:
                high += minutes
        else:
            raise ValueError("distance_only_swimming_required")
        segments.append(EstimatedSegment(event, minutes))
    if (
        tuple(quantities) != record.original_zone_distribution
        or sum(quantities) != record.planned_distance_meters
        or sum(quantities) != record.original_measure
    ):
        raise ValueError("swim_distance_aggregate_mismatch")
    return SwimEstimate(record, tuple(segments), low, high)


def evaluate_swim_week(
    week_start: date,
    sessions: tuple[EstimatedSwimSession, ...],
    *,
    sensitivity_half_width: Fraction,
) -> EstimatedSwimWeek:
    """Diagnostic SWIM sport-week maximum, independently of other sport time.

    Half-width is explicitly supplied in min/100m. Independent zone perturbations
    form a conservative sensitivity envelope; it is not empirical uncertainty or
    an approved safety allowance. Repeated occurrences are counted separately.
    """
    if week_start.weekday() != 0:
        raise ValueError("week_start_must_be_monday")
    if (
        not isinstance(sensitivity_half_width, Fraction)
        or sensitivity_half_width < 0
        or sensitivity_half_width >= min(map(Fraction, REFERENCE_MINUTES))
    ):
        raise ValueError("invalid_sensitivity_scenario")
    if any(
        not week_start <= s.local_date < week_start + timedelta(days=7)
        for s in sessions
    ):
        raise ValueError("session_outside_training_week")
    if any(not s.occurrence_id for s in sessions) or len(
        {s.occurrence_id for s in sessions}
    ) != len(sessions):
        raise ValueError("invalid_occurrence_identity")
    estimates = tuple(estimate_swim(s.source) for s in sessions)
    low = sum((e.low_minutes for e in estimates), Fraction(0))
    high = sum((e.high_minutes for e in estimates), Fraction(0))
    low_delta, high_delta = Fraction(0), Fraction(0)
    for estimate in estimates:
        for segment in estimate.segments:
            event = segment.original
            if isinstance(event, SwimDistance):
                delta = Fraction(event.meters) / 100 * sensitivity_half_width
                if event.zone <= 2:
                    low_delta += delta
                else:
                    high_delta += delta
    total = low + high
    ratio = high / total if total else None
    ratio_min = (
        (high - high_delta) / (high - high_delta + low + low_delta) if total else None
    )
    ratio_max = (
        (high + high_delta) / (high + high_delta + low - low_delta) if total else None
    )
    status: Literal["ESTIMATED_COMPLIANT", "ESTIMATED_EXCEEDED", "NOT_APPLICABLE"]
    status = (
        "NOT_APPLICABLE"
        if not total
        else "ESTIMATED_COMPLIANT"
        if high * 5 <= total
        else "ESTIMATED_EXCEEDED"
    )
    return EstimatedSwimWeek(
        week_start,
        estimates,
        low,
        high,
        ratio,
        status,
        sensitivity_half_width,
        ratio_min,
        ratio_max,
        ratio_min is not None
        and ratio_max is not None
        and ratio_min <= Fraction(1, 5) < ratio_max,
    )
