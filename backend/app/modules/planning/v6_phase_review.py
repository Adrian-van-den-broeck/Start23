"""Disabled C4/C5 review seam, with no route, persistence or activation switch.

Reviews a supplied complete sport-week, including retained occurrences. It cannot
select, publish, approve or mutate a plan. Missing official load and ranking
authority are fixed gates, never caller-overridable approval booleans.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from typing import Literal
from uuid import UUID

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
    SportWeekCompliance,
    evaluate_training_week,
)
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.joren_draft import TimedZone, WallRest
from app.modules.workouts.joren_v6_phase import PhaseTemplate
from app.modules.workouts.planned_swim_estimate import estimate_swim

VERSION = "joren-v6-phase-tss-review-1"
LOAD_BASIS = "hypothetical-source-display-exact-rational-1"
ALLOCATION_METRIC = "review-only-selected-total-share-l1-1"
TARGETS = {
    Discipline.BIKE: Fraction(1, 2),
    Discipline.RUN: Fraction(3, 10),
    Discipline.SWIM: Fraction(1, 5),
}
DIMENSIONS = frozenset(
    {
        "injury",
        "recovery",
        "progression",
        "duration_distance",
        "capability",
        "scheduling",
        "occurrence_restrictions",
    }
)


@dataclass(frozen=True, slots=True, repr=False)
class ReviewOccurrence:
    occurrence_id: UUID
    template: PhaseTemplate
    local_date: date
    # Optional separately attributable, individualized prescribed segment times.
    # These never overwrite source meters or the reference estimate.
    prescribed_seconds: tuple[Decimal, ...] | None = None
    prescribed_time_reference: str | None = None

    def __post_init__(self) -> None:
        if (self.prescribed_seconds is None) != (
            self.prescribed_time_reference is None
        ):
            raise ValueError("prescribed_time_requires_provenance")
        if self.prescribed_seconds is not None:
            if (
                self.template.predecessor.sport != "swim"
                or not self.prescribed_time_reference
            ):
                raise ValueError("invalid_prescribed_time_scope")
            if len(self.prescribed_seconds) != len(self.template.predecessor.events):
                raise ValueError("prescribed_time_segment_mismatch")
            if any(not v.is_finite() or v <= 0 for v in self.prescribed_seconds):
                raise ValueError("invalid_prescribed_time")


@dataclass(frozen=True, slots=True, repr=False)
class ReviewScope:
    athlete_id: UUID
    expected_revision: UUID
    week_start: date
    phase: TrainingPhase
    authorized_budget: Decimal
    goal_sports: frozenset[Discipline]
    available_dates: frozenset[date]
    # Complete retained week + proposed additions, preventing remaining-capacity
    # checks from forgetting existing occurrences or their intensity denominator.
    retained: tuple[ReviewOccurrence, ...] = ()
    proposed: tuple[ReviewOccurrence, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.week_start.weekday() != 0
            or not self.goal_sports
            or not self.authorized_budget.is_finite()
            or self.authorized_budget < 0
            or any(
                not self.week_start <= d < self.week_start + timedelta(days=7)
                for d in self.available_dates
            )
        ):
            raise ValueError("invalid_review_week_scope")
        rows = self.retained + self.proposed
        if len({r.occurrence_id for r in rows}) != len(rows):
            raise ValueError("duplicate_occurrence_id")
        if any(
            not self.week_start <= r.local_date < self.week_start + timedelta(days=7)
            for r in rows
        ):
            raise ValueError("occurrence_outside_review_week")


def scope_digest(scope: ReviewScope) -> str:
    """Evidence binds athlete, version, exact budget, dates and frozen revisions."""
    return sha256(
        json.dumps(
            {
                "version": VERSION,
                "athlete": str(scope.athlete_id),
                "expected_revision": str(scope.expected_revision),
                "week": scope.week_start.isoformat(),
                "phase": scope.phase.value,
                "budget": str(scope.authorized_budget),
                "goals": sorted(s.value for s in scope.goal_sports),
                "available_dates": sorted(d.isoformat() for d in scope.available_dates),
                "retained_count": len(scope.retained),
                "rows": [
                    (
                        str(r.occurrence_id),
                        str(r.template.revision_id),
                        r.template.source_sha256,
                        r.local_date.isoformat(),
                        tuple(map(str, r.prescribed_seconds))
                        if r.prescribed_seconds is not None
                        else None,
                        r.prescribed_time_reference,
                    )
                    for r in scope.retained + scope.proposed
                ],
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class SafeguardEvidence:
    dimension: str
    scope_sha256: str
    state: Literal["SUPPORTED", "BLOCKED", "UNVERIFIED"]
    rule_version: str
    reference: str

    def __post_init__(self) -> None:
        if (
            self.dimension not in DIMENSIONS
            or not self.scope_sha256
            or not self.rule_version
            or not self.reference
            or self.state not in {"SUPPORTED", "BLOCKED", "UNVERIFIED"}
        ):
            raise ValueError("invalid_safeguard_evidence")


@dataclass(frozen=True, slots=True, repr=False)
class ReviewResult:
    scope_sha256: str
    private_total: Fraction
    private_remaining_before_additions: Fraction
    private_remaining: Fraction
    budget_within: bool
    present_sports: frozenset[Discipline]
    coverage: Literal["THREE", "TWO", "ONE", "ZERO"]
    authoritative_intensity: tuple[SportWeekCompliance, ...]
    estimated_swim_high_ratio: Fraction | None
    estimated_swim_status: str
    constraint_failures: tuple[str, ...]
    unresolved_safeguards: tuple[str, ...]
    diagnostic_allocation_l1: Fraction | None
    # Always review-only even when the supplied conditional safeguards pass.
    activation_gates: tuple[str, ...]
    version: str = field(default=VERSION, init=False)
    load_basis: str = field(default=LOAD_BASIS, init=False)
    allocation_metric: str = field(default=ALLOCATION_METRIC, init=False)
    operational_approval: Literal[False] = field(default=False, init=False)
    selected_recommendation: None = field(default=None, init=False)


def review_week(
    scope: ReviewScope,
    evidence: tuple[SafeguardEvidence, ...] = (),
    *,
    maximum_uses: tuple[tuple[UUID, int], ...] = (),
) -> ReviewResult:
    """Exact hard ceiling and per-sport time maximum; no HIGH minimum.

    Load compatibility uses source display only as a labeled hypothetical while
    official numerical authority is unresolved. Suitability is a separate gate.
    Existing restrictions must be evaluated externally for this exact scope;
    absence of a decision never becomes permission or an experience category.
    """
    digest = scope_digest(scope)
    if len({e.dimension for e in evidence}) != len(evidence):
        raise ValueError("duplicate_safeguard_dimension")
    if any(e.scope_sha256 != digest for e in evidence):
        raise ValueError("stale_or_cross_scope_safeguard_evidence")
    if len(dict(maximum_uses)) != len(maximum_uses) or any(
        type(n) is not int or n < 0 for _, n in maximum_uses
    ):
        raise ValueError("invalid_repeat_contract")
    rows = scope.retained + scope.proposed
    loads = tuple(
        Fraction(r.template.predecessor.load.original_displayed_value) for r in rows
    )
    total = sum(loads, Fraction(0))
    budget = Fraction(scope.authorized_budget)
    before = budget - sum(loads[: len(scope.retained)], Fraction(0))
    failures = set()
    if total > budget:
        failures.add("authorized_weekly_budget_exceeded")
    for row in scope.proposed:
        if scope.phase not in row.template.phases:
            failures.add("source_phase_not_allowed")
        if row.local_date not in scope.available_dates:
            failures.add("date_unavailable")
        if Discipline(row.template.predecessor.sport) not in scope.goal_sports:
            failures.add("sport_outside_goal")
    counts = Counter(r.template.revision_id for r in rows)
    if any(counts[k] > n for k, n in maximum_uses):
        failures.add("repeat_limit_exceeded")
    sessions = []
    swim_low, swim_high = Fraction(0), Fraction(0)
    has_estimate = False
    for row in rows:
        record = row.template.predecessor
        segments = []
        for i, event in enumerate(record.events):
            rest = isinstance(event, WallRest)
            seconds = (
                row.prescribed_seconds[i]
                if row.prescribed_seconds is not None
                else event.seconds
                if isinstance(event, TimedZone | WallRest)
                else None
            )
            segments.append(
                PlannedSegment(
                    seconds,
                    None if isinstance(event, WallRest) else TrainingZone(event.zone),
                    rest,
                )
            )
        sessions.append(
            PlannedSession(Discipline(record.sport), row.local_date, tuple(segments))
        )
        if record.sport == "swim":
            # Reference estimates are reported independently even when an
            # authoritative individualized prescription is also available.
            estimate = estimate_swim(record)
            swim_low += estimate.low_minutes
            swim_high += estimate.high_minutes
            has_estimate |= row.prescribed_seconds is None
    intensity = evaluate_training_week(scope.week_start, tuple(sessions))
    if any(r.status == "REJECTED" for r in intensity):
        failures.add("maximum_high_active_time_exceeded")
    ratio = swim_high / (swim_low + swim_high) if swim_low + swim_high else None
    estimate_status = (
        "NOT_APPLICABLE"
        if ratio is None
        else "ESTIMATED_COMPLIANT"
        if ratio <= Fraction(1, 5)
        else "ESTIMATED_EXCEEDED"
    )
    if has_estimate and estimate_status == "ESTIMATED_EXCEEDED":
        failures.add("estimated_maximum_high_active_time_exceeded")
    supported = {e.dimension for e in evidence if e.state == "SUPPORTED"}
    failures.update(e.dimension + "_blocked" for e in evidence if e.state == "BLOCKED")
    unresolved = set(
        DIMENSIONS - supported - {e.dimension for e in evidence if e.state == "BLOCKED"}
    )
    if any(r.status == "UNVERIFIED" for r in intensity) and not has_estimate:
        unresolved.add("authoritative_active_time")
    present = frozenset(Discipline(r.template.predecessor.sport) for r in rows)
    allocation = None
    if scope.goal_sports == frozenset(Discipline) and total:
        allocation = sum(
            (
                abs(
                    sum(
                        (
                            v
                            for r, v in zip(rows, loads)
                            if Discipline(r.template.predecessor.sport) == s
                        ),
                        Fraction(0),
                    )
                    / total
                    - TARGETS[s]
                )
                for s in Discipline
            ),
            Fraction(0),
        )
    gates = [
        "official_planned_tss_authority_binding",
        "allocation_metric_and_residual_ties",
        "catalog_activation",
        "durable_snapshot_and_release_contracts",
    ]
    if has_estimate:
        gates.append("operational_acceptance_of_estimated_swim_time")
    coverage: Literal["THREE", "TWO", "ONE", "ZERO"] = (
        "ZERO"
        if not present
        else "ONE"
        if len(present) == 1
        else "TWO"
        if len(present) == 2
        else "THREE"
    )
    return ReviewResult(
        digest,
        total,
        before,
        budget - total,
        total <= budget,
        present,
        coverage,
        intensity,
        ratio,
        estimate_status,
        tuple(sorted(failures)),
        tuple(sorted(unresolved)),
        allocation,
        tuple(gates),
    )
