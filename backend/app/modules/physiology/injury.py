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
