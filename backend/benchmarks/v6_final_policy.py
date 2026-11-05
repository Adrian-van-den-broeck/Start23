"""Versioned private offline witnesses, never a selector or operational gate.

No ranking, prescription, physiological factors or runtime integration. Evidence
permissions are supplied by the caller; missing evidence remains unresolved.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from itertools import combinations, product
from typing import Literal

from app.modules.physiology.models import Discipline
from app.modules.physiology.planned_intensity_policy import evaluate_training_week
from benchmarks.prospective_planning_policy import (
    SOURCE_METHOD,
    TRIATHLON,
    Candidate,
    RestrictionEvidence,
    exact_sum,
)
from benchmarks.v6_partial_approval import SwimEstimate

POLICY_VERSION = "joren-v6-final-prospective-policy-1"
DECISION_REFERENCE = (
    "docs/catalog/implementation/JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md"
)
SCOPE = "one_supplied_occurrence_per_present_sport;all_nonempty_sport_subsets"


@dataclass(frozen=True, slots=True, repr=False)
class PolicyInput:
    candidate: Candidate
    swim_estimate: SwimEstimate | None = None

    def __post_init__(self) -> None:
        if self.swim_estimate is not None and (
            self.candidate.sport != Discipline.SWIM
            or self.swim_estimate.original.original_workout_id
            != self.candidate.source_id
        ):
            raise ValueError("inconsistent_estimate_provenance")
        if self.swim_estimate is not None and any(
            s.seconds is not None and not s.stationary_rest
            for s in (self.candidate.session.segments or ())
        ):
            raise ValueError("estimate_cannot_override_prescribed_time")


@dataclass(frozen=True, slots=True)
class IntensityEvidence:
    status: Literal["COMPLIANT", "EXCEEDED", "UNVERIFIED"]
    high_ratio: Fraction | None
    provenance: str
    # Reference estimates never become authoritative prescribed/actual time.
    authoritative_duration_compliance: str


def intensity_evidence(row: PolicyInput, week_start: date) -> IntensityEvidence:
    """No HIGH minimum in any phase, including BUILD; exact maximum unchanged."""
    authoritative = next(
        r
        for r in evaluate_training_week(week_start, (row.candidate.session,))
        if r.sport == row.candidate.sport
    )
    if row.swim_estimate is not None:
        estimate = row.swim_estimate
        total = estimate.low_minutes + estimate.high_minutes
        return IntensityEvidence(
            "UNVERIFIED"
            if not total
            else "COMPLIANT"
            if estimate.high_minutes * 5 <= total
            else "EXCEEDED",
            estimate.high_minutes / total if total else None,
            estimate.status + ":" + estimate.estimator_version,
            authoritative.status,
        )
    return IntensityEvidence(
        "COMPLIANT"
        if authoritative.status == "ACCEPTED"
        else "EXCEEDED"
        if authoritative.status == "REJECTED"
        else "UNVERIFIED",
        authoritative.high_ratio,
        authoritative.policy_version,
        authoritative.status,
    )


@dataclass(frozen=True, slots=True, repr=False)
class Witness:
    source_ids: tuple[str, ...]
    sports: tuple[Discipline, ...]
    private_total: Decimal
    intensity: tuple[IntensityEvidence, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Feasibility:
    status: Literal[
        "FULL_WEEK_WITNESSES",
        "PARTIAL_WEEK_WITNESSES",
        "UNRESOLVED_FAIL_CLOSED",
        "NO_PLAN_REST_FAIL_CLOSED",
        "BOUND_EXCEEDED",
    ]
    candidate_space: int
    examined: int
    arithmetic_witnesses: tuple[Witness, ...]
    supported_witnesses: tuple[Witness, ...]
    unresolved_ids: tuple[str, ...]
    excluded_ids: tuple[str, ...]
    # A finite witness does not prove feasibility over repeats/other schedules.
    scope: str = field(default=SCOPE, init=False)
    policy_version: str = field(default=POLICY_VERSION, init=False)
    decision_reference: str = field(default=DECISION_REFERENCE, init=False)
    source_method: str = field(default=SOURCE_METHOD, init=False)
    source_method_approved: Literal[False] = field(default=False, init=False)
    operational_approval: Literal[False] = field(default=False, init=False)
    ranking: Literal["UNRESOLVED_NO_DEFAULT"] = field(
        default="UNRESOLVED_NO_DEFAULT", init=False
    )


def enumerate_weeks(
    rows: tuple[PolicyInput, ...],
    *,
    week_start: date,
    authorized_budget: Decimal,
    available_dates: frozenset[date],
    safeguards: RestrictionEvidence,
    maximum_combinations: int,
) -> Feasibility:
    """Enumerate finite triathlon witnesses without choosing any alternative.

    Caller evidence must cover phase, injury, recovery/taper, progression and
    plan-level scheduling safeguards for this exact scope. Date membership alone
    never supplies those permissions. Estimates are conditional offline evidence.
    Unknown eligible evidence cannot prove full coverage infeasible.
    """
    if (
        week_start.weekday() != 0
        or not authorized_budget.is_finite()
        or authorized_budget < 0
        or maximum_combinations <= 0
        or any(
            not week_start <= d < week_start + timedelta(days=7)
            for d in available_dates
        )
    ):
        raise ValueError("invalid_explicit_week_scope")
    if len({r.candidate.source_id for r in rows}) != len(rows):
        raise ValueError("ambiguous_candidate_identity")
    # Evaluate before enumeration so malformed dates/segments always fail closed.
    intensities = {
        r.candidate.source_id: intensity_evidence(r, week_start) for r in rows
    }
    groups = {
        sport: tuple(
            sorted(
                (r for r in rows if r.candidate.sport == sport),
                key=lambda r: r.candidate.source_id,
            )
        )
        for sport in sorted(TRIATHLON, key=lambda s: s.value)
    }
    subsets = tuple(
        subset for size in (1, 2, 3) for subset in combinations(groups, size)
    )
    space = sum(
        _product_size(tuple(len(groups[s]) for s in subset)) for subset in subsets
    )
    if space > maximum_combinations:
        return Feasibility("BOUND_EXCEEDED", space, 0, (), (), (), ())
    excluded, unresolved, supported = set(), set(), set()
    for r in rows:
        c = r.candidate
        intensity = intensities[c.source_id]
        if (
            c.suitability_state == "EXCLUDED"
            or c.restrictions.state == "BLOCKED"
            or safeguards.state == "BLOCKED"
            or c.session.local_date not in available_dates
            or intensity.status == "EXCEEDED"
        ):
            excluded.add(c.source_id)
        elif (
            c.suitability_state != "SUPPORTED"
            or c.restrictions.state != "ALLOWED"
            or safeguards.state != "ALLOWED"
            or intensity.status == "UNVERIFIED"
        ):
            unresolved.add(c.source_id)
        else:
            supported.add(c.source_id)
    arithmetic, witnesses = [], []
    for subset in subsets:
        for combo in product(*(groups[s] for s in subset)):
            total = exact_sum(tuple(r.candidate.private_load for r in combo))
            if total > authorized_budget:
                continue
            ids = tuple(r.candidate.source_id for r in combo)
            witness = Witness(ids, subset, total, tuple(intensities[k] for k in ids))
            arithmetic.append(witness)
            if all(k in supported for k in ids):
                witnesses.append(witness)
    status: Literal[
        "FULL_WEEK_WITNESSES",
        "PARTIAL_WEEK_WITNESSES",
        "UNRESOLVED_FAIL_CLOSED",
        "NO_PLAN_REST_FAIL_CLOSED",
        "BOUND_EXCEEDED",
    ]
    if any(len(w.sports) == 3 for w in witnesses):
        status = "FULL_WEEK_WITNESSES"
    elif unresolved:
        status = "UNRESOLVED_FAIL_CLOSED"
    elif witnesses:
        status = "PARTIAL_WEEK_WITNESSES"
    else:
        status = "NO_PLAN_REST_FAIL_CLOSED"
    return Feasibility(
        status,
        space,
        space,
        tuple(arithmetic),
        tuple(witnesses),
        tuple(sorted(unresolved)),
        tuple(sorted(excluded)),
    )


def _product_size(sizes: tuple[int, ...]) -> int:
    result = 1
    for size in sizes:
        result *= size
    return result
