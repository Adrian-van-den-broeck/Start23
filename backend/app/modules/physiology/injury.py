"""BR-010 deterministic injury load redistribution."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from app.modules.physiology.models import (
    Discipline,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    JOREN_PLANNING_RULESET_V2,
    PHASE_3_RULESET_V3,
    PhysiologySpecification,
)

_REDISTRIBUTION_COEFFICIENT = Decimal("0.80")
MVP_AUTOMATIC_INJURY_REDISTRIBUTION = False


class RestrictionStatus(str, Enum):
    """Functional restriction state; deliberately not a diagnosis/severity."""

    NONE = "none"
    SELF_REPORTED_LIMITED = "self_reported_limited"
    SELF_REPORTED_BLOCKED = "self_reported_blocked"
    PROFESSIONAL_RESTRICTED = "professional_restricted"
    CLEARANCE_REQUIRED = "clearance_required"
    EXPIRED = "expired"


class AllowedIntensity(str, Enum):
    """Training capability allowed by one discipline restriction."""

    NONE = "none"
    LOW_ONLY = "low_only"
    UNRESTRICTED = "unrestricted"


@dataclass(frozen=True, slots=True)
class DisciplineRestriction:
    """Confirmed functional limitation with an explicit review, never auto-clear."""

    discipline: Discipline
    status: RestrictionStatus
    allowed_intensity: AllowedIntensity
    start_at: datetime
    review_at: datetime
    end_at: datetime | None
    source: str
    free_text_present: bool
    clearance_required: bool

    def __post_init__(self) -> None:
        timestamps = (self.start_at, self.review_at, self.end_at)
        if any(
            value is not None and (value.tzinfo is None or value.utcoffset() is None)
            for value in timestamps
        ):
            raise ValueError("Restriction timestamps must be timezone-aware.")
        if self.review_at < self.start_at:
            raise ValueError("Restriction review cannot precede its start.")
        if self.end_at is not None and self.end_at < self.start_at:
            raise ValueError("Restriction end cannot precede its start.")
        if not self.source.strip():
            raise ValueError("Restriction source is required.")
        expected = {
            RestrictionStatus.NONE: AllowedIntensity.UNRESTRICTED,
            RestrictionStatus.SELF_REPORTED_LIMITED: AllowedIntensity.LOW_ONLY,
            RestrictionStatus.SELF_REPORTED_BLOCKED: AllowedIntensity.NONE,
            RestrictionStatus.PROFESSIONAL_RESTRICTED: AllowedIntensity.NONE,
            RestrictionStatus.CLEARANCE_REQUIRED: AllowedIntensity.NONE,
            RestrictionStatus.EXPIRED: AllowedIntensity.NONE,
        }[self.status]
        if self.allowed_intensity is not expected:
            raise ValueError("Restriction status and allowed intensity disagree.")

    @classmethod
    def self_reported_limited(
        cls,
        *,
        discipline: Discipline,
        start_at: datetime,
        source: str = "athlete",
    ) -> "DisciplineRestriction":
        """Create the MVP seven-day recheck state without automatic expiry."""
        return cls(
            discipline=discipline,
            status=RestrictionStatus.SELF_REPORTED_LIMITED,
            allowed_intensity=AllowedIntensity.LOW_ONLY,
            start_at=start_at,
            review_at=start_at + timedelta(days=7),
            end_at=None,
            source=source,
            free_text_present=False,
            clearance_required=False,
        )

    def requires_recheck(self, *, as_of: datetime) -> bool:
        """A due review does not silently lift the active restriction."""
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("Restriction evaluation must be timezone-aware.")
        return self.status is not RestrictionStatus.NONE and as_of >= self.review_at


@dataclass(frozen=True, slots=True)
class DisciplineAllocation:
    """One exact redistributed internal-load allocation."""

    discipline: Discipline
    load: InternalLoad


@dataclass(frozen=True, slots=True)
class InjuryRedistributionResult:
    """Proportional redistribution result for a confirmed injury."""

    ruleset_version: RulesetVersion
    evaluated: bool
    removed_load: InternalLoad
    redistributed_load: InternalLoad
    allocations: tuple[DisciplineAllocation, ...]
    rest_only: bool
    requires_review: bool
    cross_training_consent_required: bool = False


def redistribute_confirmed_injury_load(
    *,
    pre_injury_targets: Mapping[Discipline, InternalLoad],
    recipient_safe_caps: Mapping[Discipline, InternalLoad],
    blocked_disciplines: frozenset[Discipline],
    cross_training_opt_ins: frozenset[Discipline] = frozenset(),
    specification: PhysiologySpecification = JOREN_PLANNING_RULESET_V2,
) -> InjuryRedistributionResult:
    """Allocate at most 80% of blocked load to safe low-impact capacity.

    Positive current/historical discipline basis supplies proportional weights.
    A zero-basis opt-in records athlete choice, but cannot create an unreviewed
    nonzero capacity. The caller supplies only caps from the existing progression
    boundary; this function never invents a sport load coefficient.
    """
    specification.require_approved(frozenset({RuleId.INJURY_REDISTRIBUTION}))
    removed = sum(
        (
            target.value
            for sport, target in pre_injury_targets.items()
            if sport in blocked_disciplines
        ),
        Decimal(0),
    )
    transferable = removed * _REDISTRIBUTION_COEFFICIENT
    low_impact = (Discipline.BIKE, Discipline.SWIM)
    consent_required = any(
        sport not in blocked_disciplines
        and sport in recipient_safe_caps
        and pre_injury_targets.get(sport, InternalLoad(Decimal(0))).value == 0
        and sport not in cross_training_opt_ins
        for sport in low_impact
    )
    weights = {
        sport: pre_injury_targets[sport].value
        for sport in low_impact
        if sport not in blocked_disciplines
        and pre_injury_targets.get(sport, InternalLoad(Decimal(0))).value > 0
        and recipient_safe_caps.get(sport, InternalLoad(Decimal(0))).value
        > pre_injury_targets[sport].value
    }
    capacity = {
        sport: recipient_safe_caps[sport].value - pre_injury_targets[sport].value
        for sport in weights
    }
    allocations = {sport: Decimal(0) for sport in weights}
    remaining = transferable
    active = set(weights)
    while remaining > 0 and active:
        total_weight = sum((weights[sport] for sport in active), Decimal(0))
        provisional = {
            sport: remaining * weights[sport] / total_weight for sport in active
        }
        capped = {
            sport
            for sport in active
            if provisional[sport] >= capacity[sport] - allocations[sport]
        }
        if not capped:
            ordered = sorted(active, key=lambda sport: sport.value)
            allocated = Decimal(0)
            for sport in ordered[:-1]:
                allocations[sport] += provisional[sport]
                allocated += provisional[sport]
            allocations[ordered[-1]] += remaining - allocated
            remaining = Decimal(0)
            break
        for sport in capped:
            amount = capacity[sport] - allocations[sport]
            allocations[sport] += amount
            remaining -= amount
        active -= capped
    distributed = transferable - remaining
    return InjuryRedistributionResult(
        ruleset_version=specification.version,
        evaluated=bool(blocked_disciplines),
        removed_load=InternalLoad(removed),
        redistributed_load=InternalLoad(distributed),
        allocations=tuple(
            DisciplineAllocation(sport, InternalLoad(value))
            for sport, value in sorted(
                allocations.items(), key=lambda item: item[0].value
            )
            if value > 0
        ),
        rest_only=bool(blocked_disciplines)
        and all(
            sport in blocked_disciplines
            for sport in pre_injury_targets
            if pre_injury_targets[sport].value > 0
        )
        and distributed == 0,
        requires_review=False,
        cross_training_consent_required=consent_required,
    )


def redistribute_injury_load(
    *,
    planned_loads: Mapping[Discipline, InternalLoad],
    blocked_disciplines: frozenset[Discipline],
    confirmed: bool,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> InjuryRedistributionResult:
    """Retain the legacy 80% calculation for analysis, never MVP planning."""
    specification.require_approved(frozenset({RuleId.INJURY_REDISTRIBUTION}))
    if not confirmed:
        return InjuryRedistributionResult(
            ruleset_version=specification.version,
            evaluated=False,
            removed_load=InternalLoad(Decimal(0)),
            redistributed_load=InternalLoad(Decimal(0)),
            allocations=(),
            rest_only=False,
            requires_review=False,
        )

    removed = sum(
        (
            load.value
            for discipline, load in planned_loads.items()
            if discipline in blocked_disciplines
        ),
        Decimal(0),
    )
    redistributed = removed * _REDISTRIBUTION_COEFFICIENT
    eligible = sorted(
        (
            discipline
            for discipline in planned_loads
            if discipline not in blocked_disciplines
        ),
        key=lambda discipline: discipline.value,
    )
    if not eligible:
        return InjuryRedistributionResult(
            ruleset_version=specification.version,
            evaluated=True,
            removed_load=InternalLoad(removed),
            redistributed_load=InternalLoad(Decimal(0)),
            allocations=(),
            rest_only=True,
            requires_review=False,
        )

    existing_total = sum(
        (planned_loads[discipline].value for discipline in eligible),
        Decimal(0),
    )
    if existing_total == 0 and len(eligible) > 1:
        return InjuryRedistributionResult(
            ruleset_version=specification.version,
            evaluated=True,
            removed_load=InternalLoad(removed),
            redistributed_load=InternalLoad(Decimal(0)),
            allocations=(),
            rest_only=False,
            requires_review=True,
        )

    allocations: tuple[DisciplineAllocation, ...]
    if len(eligible) == 1:
        allocations = (DisciplineAllocation(eligible[0], InternalLoad(redistributed)),)
    else:
        allocation_values: list[DisciplineAllocation] = []
        allocated = Decimal(0)
        for index, discipline in enumerate(eligible):
            value = (
                redistributed - allocated
                if index == len(eligible) - 1
                else redistributed * planned_loads[discipline].value / existing_total
            )
            allocated += value
            allocation_values.append(
                DisciplineAllocation(discipline, InternalLoad(value))
            )
        allocations = tuple(allocation_values)

    return InjuryRedistributionResult(
        ruleset_version=specification.version,
        evaluated=True,
        removed_load=InternalLoad(removed),
        redistributed_load=InternalLoad(redistributed),
        allocations=allocations,
        rest_only=False,
        requires_review=False,
    )


def apply_mvp_injury_policy(
    *,
    planned_loads: Mapping[Discipline, InternalLoad],
    blocked_disciplines: frozenset[Discipline],
    confirmed: bool,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> InjuryRedistributionResult:
    """Remove confirmed blocked load and redistribute exactly zero in the MVP."""
    specification.require_approved(frozenset({RuleId.INJURY_REDISTRIBUTION}))
    if not confirmed:
        removed = Decimal(0)
        evaluated = False
    else:
        removed = sum(
            (
                load.value
                for discipline, load in planned_loads.items()
                if discipline in blocked_disciplines
            ),
            Decimal(0),
        )
        evaluated = True
    return InjuryRedistributionResult(
        ruleset_version=specification.version,
        evaluated=evaluated,
        removed_load=InternalLoad(removed),
        redistributed_load=InternalLoad(Decimal(0)),
        allocations=(),
        rest_only=confirmed and set(planned_loads) <= set(blocked_disciplines),
        requires_review=False,
    )
