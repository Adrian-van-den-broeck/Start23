"""Pure, private, offline prospective diagnostics. Outside the application package.

This contract evaluates evidence; it grants no operational or scientific approval.
Source display decimals are hypothetical exact inputs, not approved source P.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from itertools import product
from math import prod
from typing import Literal

from app.modules.physiology.models import Discipline
from app.modules.physiology.planned_intensity_policy import (
    PlannedSession,
    SportWeekCompliance,
    evaluate_training_week,
)

POLICY_VERSION = "joren-v6-prospective-policy-sandbox-1"
SOURCE_METHOD = "hypothetical-v6-displayed-source-p-exact-decimal-1"
SUITABILITY_CONTRACT = "joren-proposed-suitability-evidence-1"
TRIATHLON = frozenset(Discipline)
TARGETS = {
    Discipline.BIKE: Fraction(1, 2),
    Discipline.RUN: Fraction(3, 10),
    Discipline.SWIM: Fraction(1, 5),
}


class Status(str, Enum):
    LEGACY_VALID = "LEGACY_VALID"
    LEGACY_REJECTED = "LEGACY_REJECTED"
    LEGACY_NOT_EVALUATED = "LEGACY_NOT_EVALUATED"
    PROSPECTIVE_BUDGET_WITHIN = "PROSPECTIVE_BUDGET_WITHIN"
    PROSPECTIVE_BUDGET_EXCEEDED = "PROSPECTIVE_BUDGET_EXCEEDED"
    SPORT_COVERAGE_SATISFIED = "SPORT_COVERAGE_SATISFIED"
    SPORT_COVERAGE_MISSING = "SPORT_COVERAGE_MISSING"
    SPORT_ALLOCATION_DEVIATION = "SPORT_ALLOCATION_DEVIATION"
    SPORT_ALLOCATION_EXACT = "SPORT_ALLOCATION_EXACT"
    SPORT_ALLOCATION_UNDEFINED = "SPORT_ALLOCATION_UNDEFINED"
    SPORT_ALLOCATION_NOT_APPLICABLE = "SPORT_ALLOCATION_NOT_APPLICABLE"
    INTENSITY_TIME_COMPLIANT = "INTENSITY_TIME_COMPLIANT"
    INTENSITY_TIME_EXCEEDED = "INTENSITY_TIME_EXCEEDED"
    INTENSITY_TIME_UNVERIFIED = "INTENSITY_TIME_UNVERIFIED"
    INTENSITY_TIME_NOT_APPLICABLE = "INTENSITY_TIME_NOT_APPLICABLE"
    ATHLETE_SUITABILITY_UNAPPROVED = "ATHLETE_SUITABILITY_UNAPPROVED"
    ATHLETE_SUITABILITY_EXCLUDED = "ATHLETE_SUITABILITY_EXCLUDED"
    ATHLETE_SUITABILITY_SUPPORTED = "ATHLETE_SUITABILITY_SUPPORTED"
    SOURCE_METHOD_UNAPPROVED = "SOURCE_METHOD_UNAPPROVED"
    RESTRICTIONS_BLOCKED = "RESTRICTIONS_BLOCKED"
    RESTRICTIONS_UNVERIFIED = "RESTRICTIONS_UNVERIFIED"


class SuitabilityDimension(str, Enum):
    BEGINNER_CAPABILITY = "beginner_capability"
    SPORT_EXPERIENCE = "sport_specific_experience"
    CONFIRMED_CAPABILITIES = "confirmed_training_capabilities"
    DURATION_DISTANCE = "suitable_session_duration_distance"
    LONG_SESSION = "individual_long_session_scope"
    INJURY = "injury_restrictions"
    RECOVERY_TAPER = "recovery_taper_suitability"
    REPETITION_FREQUENCY = "repetition_weekly_frequency"
    PHASE_INTENSITY = "phase_intensity_requirements"


@dataclass(frozen=True, slots=True)
class SuitabilityEvidence:
    dimension: SuitabilityDimension
    state: Literal["SUPPORTED", "EXCLUDED", "UNRESOLVED"]
    # Scope must identify athlete, template version, phase/week and occurrence
    # context. Sensor/pace availability alone cannot support other dimensions.
    scope: str
    rule_version: str
    approval_reference: str

    def __post_init__(self) -> None:
        if not all((self.scope, self.rule_version, self.approval_reference)):
            raise ValueError("suitability_evidence_requires_provenance")


@dataclass(frozen=True, slots=True)
class RestrictionEvidence:
    state: Literal["ALLOWED", "BLOCKED", "UNVERIFIED"]
    reasons: tuple[str, ...]
    reference: str

    def __post_init__(self) -> None:
        if not self.reasons or not self.reference:
            raise ValueError("restriction_evidence_requires_provenance")


UNRESOLVED_RESTRICTIONS = RestrictionEvidence(
    "UNVERIFIED", ("existing_restrictions_not_evaluated",), "offline-input-missing"
)


@dataclass(frozen=True, slots=True)
class Candidate:
    source_id: str
    sport: Discipline
    private_load: Decimal = field(repr=False)
    session: PlannedSession
    all_easy: bool
    suitability: tuple[SuitabilityEvidence, ...] = ()
    restrictions: RestrictionEvidence = UNRESOLVED_RESTRICTIONS
    source_method: str = SOURCE_METHOD

    def __post_init__(self) -> None:
        if not self.private_load.is_finite() or self.private_load <= 0:
            raise ValueError("invalid_hypothetical_load")
        if self.session.sport != self.sport or self.source_method != SOURCE_METHOD:
            raise ValueError("inconsistent_candidate_provenance")
        if len({e.dimension for e in self.suitability}) != len(self.suitability):
            raise ValueError("duplicate_suitability_dimension")

    @property
    def suitability_state(self) -> Literal["SUPPORTED", "EXCLUDED", "UNRESOLVED"]:
        if any(e.state == "EXCLUDED" for e in self.suitability):
            return "EXCLUDED"
        if len(self.suitability) != len(SuitabilityDimension) or any(
            e.state != "SUPPORTED" for e in self.suitability
        ):
            return "UNRESOLVED"
        return "SUPPORTED"


@dataclass(frozen=True, slots=True)
class LegacyEvidence:
    outcome: Literal["RETURNED_PENDING", "REJECTED", "NOT_RUN"]
    origin: Literal["AUTOMATIC_PLANNER", "EXPLICIT_MANUAL", "OFFLINE_UNSELECTED"]
    reference: str


@dataclass(frozen=True, slots=True)
class Finding:
    status: Status
    reason: str
    sport: Discipline | None = None


@dataclass(frozen=True, slots=True)
class SportAllocation:
    sport: Discipline
    private_load: Decimal = field(repr=False)
    share: Fraction | None
    target_share: Fraction
    share_deviation: Fraction | None
    budget_target: Fraction = field(repr=False)
    budget_deviation: Fraction = field(repr=False)


@dataclass(frozen=True, slots=True)
class Evaluation:
    findings: tuple[Finding, ...]
    legacy: LegacyEvidence
    private_total: Decimal = field(repr=False)
    private_budget: Decimal = field(repr=False)
    # Signed: negative means exceeded. No rounded display enters comparison.
    private_budget_remaining: Decimal = field(repr=False)
    allocation: tuple[SportAllocation, ...]
    intensity: tuple[SportWeekCompliance, ...]
    suitable_coverage: Literal["SUPPORTED", "UNRESOLVED", "MISSING"]
    policy_version: str = POLICY_VERSION
    source_method: str = SOURCE_METHOD
    suitability_contract: str = SUITABILITY_CONTRACT


def exact_sum(values: tuple[Decimal, ...]) -> Decimal:
    """Sum finite decimals without depending on the caller's decimal context."""
    if any(not v.is_finite() for v in values):
        raise ValueError("nonfinite_private_value")
    parts = tuple(v.as_tuple() for v in values)
    exponent = min((int(p.exponent) for p in parts), default=0)
    integer = sum(
        (-1 if p.sign else 1)
        * int("".join(str(d) for d in p.digits))
        * 10 ** (int(p.exponent) - exponent)
        for p in parts
    )
    return Decimal((int(integer < 0), tuple(map(int, str(abs(integer)))), exponent))


def evaluate(
    *,
    week_start: date,
    selected: tuple[Candidate, ...],
    authorized_budget: Decimal,
    required_sports: frozenset[Discipline],
    goal: Literal["TRIATHLON", "OTHER"],
    legacy: LegacyEvidence,
) -> Evaluation:
    """Diagnose a supplied plan. A returned legacy result is never approval."""
    if not authorized_budget.is_finite() or authorized_budget < 0:
        raise ValueError("invalid_authorized_budget")
    if goal == "TRIATHLON" and required_sports != TRIATHLON:
        raise ValueError("triathlon_requires_three_sports")
    total = exact_sum(tuple(c.private_load for c in selected))
    remaining = exact_sum((authorized_budget, total.copy_negate()))
    findings = [
        Finding(
            {
                "RETURNED_PENDING": Status.LEGACY_VALID,
                "REJECTED": Status.LEGACY_REJECTED,
                "NOT_RUN": Status.LEGACY_NOT_EVALUATED,
            }[legacy.outcome],
            f"{legacy.origin}:{legacy.reference}",
        ),
        Finding(
            Status.PROSPECTIVE_BUDGET_WITHIN
            if remaining >= 0
            else Status.PROSPECTIVE_BUDGET_EXCEEDED,
            "exact_hypothetical_decimal_total_compared_to_explicit_budget",
        ),
        Finding(Status.SOURCE_METHOD_UNAPPROVED, SOURCE_METHOD),
    ]
    present = frozenset(c.sport for c in selected)
    findings.append(
        Finding(
            Status.SPORT_COVERAGE_SATISFIED
            if required_sports <= present
            else Status.SPORT_COVERAGE_MISSING,
            "structural_occurrence_coverage_only;individual_suitability_separate",
        )
    )
    for c in selected:
        if c.suitability_state != "SUPPORTED":
            missing = tuple(
                d.value
                for d in SuitabilityDimension
                if not any(
                    e.dimension == d and e.state == "SUPPORTED" for e in c.suitability
                )
            )
            findings.append(
                Finding(
                    Status.ATHLETE_SUITABILITY_EXCLUDED
                    if c.suitability_state == "EXCLUDED"
                    else Status.ATHLETE_SUITABILITY_UNAPPROVED,
                    f"{c.source_id}:" + ",".join(missing),
                    c.sport,
                )
            )
        if c.restrictions.state != "ALLOWED":
            findings.append(
                Finding(
                    Status.RESTRICTIONS_BLOCKED
                    if c.restrictions.state == "BLOCKED"
                    else Status.RESTRICTIONS_UNVERIFIED,
                    f"{c.source_id}:{c.restrictions.reference}:"
                    + ",".join(c.restrictions.reasons),
                    c.sport,
                )
            )
    supported = frozenset(
        c.sport
        for c in selected
        if c.suitability_state == "SUPPORTED" and c.restrictions.state == "ALLOWED"
    )
    possible = frozenset(
        c.sport
        for c in selected
        if c.suitability_state != "EXCLUDED" and c.restrictions.state != "BLOCKED"
    )
    suitable_coverage: Literal["SUPPORTED", "UNRESOLVED", "MISSING"] = (
        "MISSING"
        if not required_sports <= possible
        else "SUPPORTED"
        if required_sports <= supported
        else "UNRESOLVED"
    )
    allocation: tuple[SportAllocation, ...] = ()
    if goal == "TRIATHLON":
        allocation = tuple(
            SportAllocation(
                sport,
                load := exact_sum(
                    tuple(c.private_load for c in selected if c.sport == sport)
                ),
                share := Fraction(load) / Fraction(total) if total else None,
                TARGETS[sport],
                share - TARGETS[sport] if share is not None else None,
                Fraction(authorized_budget) * TARGETS[sport],
                Fraction(load) - Fraction(authorized_budget) * TARGETS[sport],
            )
            for sport in Discipline
        )
        findings.append(
            Finding(
                Status.SPORT_ALLOCATION_UNDEFINED
                if not total
                else Status.SPORT_ALLOCATION_DEVIATION
                if any(a.share_deviation for a in allocation)
                else Status.SPORT_ALLOCATION_EXACT,
                "selected_total_denominator;budget_components_also_reported;soft_target_only",
            )
        )
    else:
        findings.append(
            Finding(Status.SPORT_ALLOCATION_NOT_APPLICABLE, "goal_is_not_triathlon")
        )
    intensity = evaluate_training_week(week_start, tuple(c.session for c in selected))
    for result in intensity:
        findings.append(
            Finding(
                {
                    "ACCEPTED": Status.INTENSITY_TIME_COMPLIANT,
                    "REJECTED": Status.INTENSITY_TIME_EXCEEDED,
                    "UNVERIFIED": Status.INTENSITY_TIME_UNVERIFIED,
                    "NOT APPLICABLE": Status.INTENSITY_TIME_NOT_APPLICABLE,
                }[result.status],
                f"{result.policy_version}:ordered_segments;no_swim_duration_inference",
                result.sport,
            )
        )
    return Evaluation(
        tuple(findings),
        legacy,
        total,
        authorized_budget,
        remaining,
        allocation,
        intensity,
        suitable_coverage,
    )


@dataclass(frozen=True, slots=True)
class Combination:
    source_ids: tuple[str, ...]
    deterministic_ids: tuple[str, ...]
    private_total: Decimal = field(repr=False)
    share_error: Fraction
    legacy_fit: bool


@dataclass(frozen=True, slots=True)
class Feasibility:
    status: Literal["COMPLETE", "BOUND_EXCEEDED"]
    combinations_examined: int
    candidate_space: int
    within_budget: tuple[Combination, ...]
    evidence_mode: Literal["ARITHMETIC_ONLY", "SUPPORTED_SUITABILITY"]
    suitability_evidence_state: Literal["NOT_ASSESSED", "UNRESOLVED", "RESOLVED"]
    scope: str = "exactly_one_occurrence_per_required_sport;no_scheduling_claim"


def enumerate_one_per_sport(
    candidates: tuple[Candidate, ...],
    *,
    required_sports: frozenset[Discipline],
    budget: Decimal,
    legacy_minimum: Decimal,
    maximum_combinations: int,
    evidence_mode: Literal["ARITHMETIC_ONLY", "SUPPORTED_SUITABILITY"],
    deterministic_ids: tuple[tuple[str, str], ...],
) -> Feasibility:
    """Complete finite experiment or explicit unknown; never a truncated winner.

    Caller supplies the actual deck UUID tie keys. No default ranking is selected.
    ARITHMETIC_ONLY intentionally makes no suitability/restriction claim.
    """
    if (
        not budget.is_finite()
        or budget < 0
        or not legacy_minimum.is_finite()
        or legacy_minimum <= 0
        or maximum_combinations <= 0
        or not required_sports
    ):
        raise ValueError("invalid_feasibility_scope")
    keys = dict(deterministic_ids)
    if len({c.source_id for c in candidates}) != len(candidates):
        raise ValueError("ambiguous_candidate_identity")
    if any(c.source_id not in keys for c in candidates):
        raise ValueError("missing_deterministic_identity")
    evidence_state: Literal["NOT_ASSESSED", "UNRESOLVED", "RESOLVED"] = (
        "NOT_ASSESSED"
        if evidence_mode == "ARITHMETIC_ONLY"
        else "UNRESOLVED"
        if any(
            c.suitability_state == "UNRESOLVED" or c.restrictions.state == "UNVERIFIED"
            for c in candidates
            if c.sport in required_sports
        )
        else "RESOLVED"
    )
    groups = tuple(
        tuple(
            c
            for c in candidates
            if c.sport == sport
            and (
                evidence_mode == "ARITHMETIC_ONLY"
                or (
                    c.suitability_state == "SUPPORTED"
                    and c.restrictions.state == "ALLOWED"
                )
            )
        )
        for sport in sorted(required_sports, key=lambda s: s.value)
    )
    space = prod(len(g) for g in groups)
    if space > maximum_combinations:
        return Feasibility(
            "BOUND_EXCEEDED", 0, space, (), evidence_mode, evidence_state
        )
    fits = []
    for combo in product(*groups):
        total = exact_sum(tuple(c.private_load for c in combo))
        if total > budget:
            continue
        error = (
            sum(
                (
                    abs(Fraction(c.private_load) / Fraction(total) - TARGETS[c.sport])
                    for c in combo
                ),
                Fraction(0),
            )
            if required_sports == TRIATHLON
            else Fraction(0)
        )
        fits.append(
            Combination(
                tuple(c.source_id for c in combo),
                tuple(sorted(keys[c.source_id] for c in combo)),
                total,
                error,
                Fraction(budget) - Fraction(total) < Fraction(legacy_minimum),
            )
        )
    return Feasibility(
        "COMPLETE", space, space, tuple(fits), evidence_mode, evidence_state
    )


def rank_experiment(
    combinations: tuple[Combination, ...],
    priority: Literal["ALLOCATION_FIRST", "UTILIZATION_FIRST"],
) -> tuple[Combination, ...]:
    """Two unapproved diagnostic rankings, only after hard constraints/coverage.

    Restrict to equal three-occurrence plans. UUID order mirrors existing tie
    identities; this is not the active planner's complete score or a new default.
    """

    def key(c: Combination) -> tuple[Fraction, Fraction, tuple[str, ...]]:
        utilization = -Fraction(c.private_total)
        return (
            (c.share_error, utilization, c.deterministic_ids)
            if priority == "ALLOCATION_FIRST"
            else (utilization, c.share_error, c.deterministic_ids)
        )

    return tuple(sorted(combinations, key=key))
