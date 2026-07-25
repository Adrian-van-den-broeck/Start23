"""BR-004 deterministic baseline, progression, and load snapshot rules."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from app.modules.physiology.models import (
    DurationMinutes,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)

_HISTORY_DAYS = 42
_REGULAR_THRESHOLD = Decimal("0.80")
_GROWTH_FACTOR = Decimal("1.10")


class ProgressionBasis(str, Enum):
    """Source used for a next-week load target."""

    REGULAR = "regular"
    BASELINE = "baseline"


@dataclass(frozen=True, slots=True)
class WeeklyLoad:
    """One explicit Monday-starting athlete-week load snapshot."""

    week_start: date
    load: InternalLoad
    is_recovery_week: bool = False

    def __post_init__(self) -> None:
        if self.week_start.weekday() != 0:
            raise ValueError("Weekly load samples must start on Monday.")


@dataclass(frozen=True, slots=True)
class ProgressionResult:
    """Exact next-week target before higher-precedence constraints."""

    ruleset_version: RulesetVersion
    basis: ProgressionBasis
    target: InternalLoad


def calculate_42_day_average(
    samples: tuple[WeeklyLoad, ...],
    *,
    as_of: date,
    exclude_recovery_weeks: bool = False,
    rule_id: RuleId = RuleId.PROGRESSIVE_LOAD,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> InternalLoad | None:
    """Average available weekly snapshots whose starts fall in the latest 42 days."""
    specification.require_approved(frozenset({rule_id}))
    earliest = as_of - timedelta(days=_HISTORY_DAYS - 1)
    selected: dict[date, WeeklyLoad] = {}
    for sample in samples:
        if sample.week_start in selected:
            raise ValueError("Weekly load samples must have unique start dates.")
        selected[sample.week_start] = sample

    eligible = [
        sample
        for sample in selected.values()
        if earliest <= sample.week_start <= as_of
        and not (exclude_recovery_weeks and sample.is_recovery_week)
    ]
    if not eligible:
        return None
    total = sum((sample.load.value for sample in eligible), Decimal(0))
    return InternalLoad(total / Decimal(len(eligible)))


def calculate_progressive_target(
    *,
    prior_planned: InternalLoad,
    prior_realized: InternalLoad,
    baseline: InternalLoad | None,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> ProgressionResult:
    """Use regular 10% growth at >=80%; otherwise use the 42-day baseline."""
    specification.require_approved(frozenset({RuleId.PROGRESSIVE_LOAD}))

    regular = (
        prior_planned.value > 0
        and prior_realized.value >= prior_planned.value * _REGULAR_THRESHOLD
    )
    if regular:
        return ProgressionResult(
            ruleset_version=specification.version,
            basis=ProgressionBasis.REGULAR,
            target=InternalLoad(prior_planned.value * _GROWTH_FACTOR),
        )
    if baseline is None:
        raise ValueError("A baseline is required for heavy undershoot or zero load.")
    return ProgressionResult(
        ruleset_version=specification.version,
        basis=ProgressionBasis.BASELINE,
        target=baseline,
    )


def snapshot_personalized_load(
    *,
    expected_rpe: Decimal,
    duration: DurationMinutes,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> InternalLoad:
    """Snapshot personalized planned load as expected RPE times duration hours."""
    specification.require_approved(frozenset({RuleId.PROGRESSIVE_LOAD}))
    if (
        not expected_rpe.is_finite()
        or expected_rpe < Decimal(1)
        or expected_rpe > Decimal(10)
    ):
        raise ValueError("Expected RPE must be between 1 and 10.")
    return InternalLoad(expected_rpe * duration.value / Decimal(60))
