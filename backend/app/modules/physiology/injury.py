"""BR-010 deterministic injury load redistribution."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from app.modules.physiology.models import (
    Discipline,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)

_REDISTRIBUTION_COEFFICIENT = Decimal("0.80")


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
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> InjuryRedistributionResult:
    """Redistribute 80% by remaining existing proportions, pending application."""
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
