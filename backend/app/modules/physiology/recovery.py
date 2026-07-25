"""BR-007 deterministic build/recovery cycle calculations."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.modules.physiology.models import InternalLoad, RuleId, RulesetVersion
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)

_MESOCYCLE_WEEKS = 5
_RECOVERY_FACTOR = Decimal("0.60")
_MINIMUM_RECOVERY_FACTOR = Decimal("0.40")


class WeekPhase(str, Enum):
    """Planning phase for one calendar week."""

    BUILD = "build"
    RECOVERY = "recovery"
    TAPER = "taper"


@dataclass(frozen=True, slots=True)
class RecoveryTarget:
    """Exact approved recovery target."""

    ruleset_version: RulesetVersion
    factor: Decimal
    target: InternalLoad


def forward_mesocycle_phase(
    week_number: int,
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> WeekPhase:
    """Return build for weeks 1-4 and recovery for each fifth week."""
    specification.require_approved(frozenset({RuleId.RECOVERY_CYCLE}))
    if week_number < 1:
        raise ValueError("Week number must be positive.")
    return (
        WeekPhase.RECOVERY if week_number % _MESOCYCLE_WEEKS == 0 else WeekPhase.BUILD
    )


def retrospective_mesocycle_phase(
    *,
    week_number: int,
    total_weeks_to_a_race: int,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> WeekPhase:
    """Align recovery weeks backward from the A-race week."""
    specification.require_approved(frozenset({RuleId.RECOVERY_CYCLE}))
    if total_weeks_to_a_race < 1:
        raise ValueError("Total weeks to the A-race must be positive.")
    if not 1 <= week_number <= total_weeks_to_a_race:
        raise ValueError("Week number must fall inside the race horizon.")
    remaining = total_weeks_to_a_race - week_number
    return WeekPhase.RECOVERY if remaining % _MESOCYCLE_WEEKS == 0 else WeekPhase.BUILD


def resolve_week_phase(
    *,
    recovery_due: bool,
    taper_due: bool,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> WeekPhase:
    """Apply the approved rule that taper overrides recovery."""
    specification.require_approved(frozenset({RuleId.RECOVERY_CYCLE}))
    if taper_due:
        return WeekPhase.TAPER
    return WeekPhase.RECOVERY if recovery_due else WeekPhase.BUILD


def calculate_recovery_target(
    *,
    week_four_planned: InternalLoad,
    factor: Decimal = _RECOVERY_FACTOR,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> RecoveryTarget:
    """Calculate an exact recovery target within the approved 40%-60% range."""
    specification.require_approved(frozenset({RuleId.RECOVERY_CYCLE}))
    if (
        not factor.is_finite()
        or not _MINIMUM_RECOVERY_FACTOR <= factor <= _RECOVERY_FACTOR
    ):
        raise ValueError("Recovery factor must be between 0.40 and 0.60.")
    return RecoveryTarget(
        ruleset_version=specification.version,
        factor=factor,
        target=InternalLoad(week_four_planned.value * factor),
    )
