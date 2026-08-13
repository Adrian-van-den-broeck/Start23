"""BR-002 deterministic volume and intensity debt calculations."""

from dataclasses import dataclass
from decimal import Decimal

from app.modules.physiology.models import (
    DurationMinutes,
    Fraction,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V3,
    PhysiologySpecification,
)

_TEN_PERCENT_GROWTH = Decimal("1.10")
_NORMAL_HIGH_INTENSITY_FLOOR = Decimal("0.05")
_MINIMUM_RELIABLE_INTENSITY_COVERAGE = Decimal("0.60")


@dataclass(frozen=True, slots=True)
class VolumeDebtResult:
    """Internal result for strict-above-110% weekly volume debt."""

    ruleset_version: RulesetVersion
    activated: bool
    debt: InternalLoad
    regular_projection: InternalLoad
    corrected_target: InternalLoad | None
    requires_review: bool


@dataclass(frozen=True, slots=True)
class IntensityDebtResult:
    """Exact next-week high-intensity correction for one discipline."""

    ruleset_version: RulesetVersion
    debt: Fraction
    corrected_high_fraction: Fraction


@dataclass(frozen=True, slots=True)
class ReliableIntensityDebtResult:
    """Data-quality-gated realized intensity correction for one future week."""

    ruleset_version: RulesetVersion
    evaluated: bool
    coverage: Fraction
    result: IntensityDebtResult | None


def calculate_volume_debt(
    *,
    prior_planned: InternalLoad,
    prior_realized: InternalLoad,
    exceptional_zero_allowed: bool = False,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> VolumeDebtResult:
    """Apply BR-002 debt only when realized load is strictly above 110%."""
    specification.require_approved(frozenset({RuleId.SOFT_BOUNDARIES}))

    regular_projection_value = prior_planned.value * _TEN_PERCENT_GROWTH
    activation_threshold = prior_planned.value * _TEN_PERCENT_GROWTH
    activated = prior_realized.value > activation_threshold
    debt_value = prior_realized.value - prior_planned.value if activated else Decimal(0)
    corrected_value = regular_projection_value - debt_value

    requires_review = corrected_value <= 0 and not exceptional_zero_allowed
    corrected_target = (
        None if requires_review else InternalLoad(max(Decimal(0), corrected_value))
    )
    return VolumeDebtResult(
        ruleset_version=specification.version,
        activated=activated,
        debt=InternalLoad(debt_value),
        regular_projection=InternalLoad(regular_projection_value),
        corrected_target=corrected_target,
        requires_review=requires_review,
    )


def calculate_intensity_debt(
    *,
    planned_high_fraction: Fraction,
    realized_high_fraction: Fraction,
    base_next_high_fraction: Fraction = Fraction(Decimal("0.20")),
    discipline_injury_confirmed: bool = False,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> IntensityDebtResult:
    """Subtract excess high-intensity time with the approved 5% floor."""
    specification.require_approved(frozenset({RuleId.SOFT_BOUNDARIES}))

    debt_value = max(
        Decimal(0),
        realized_high_fraction.value - planned_high_fraction.value,
    )
    floor = Decimal(0) if discipline_injury_confirmed else _NORMAL_HIGH_INTENSITY_FLOOR
    corrected = max(floor, base_next_high_fraction.value - debt_value)
    return IntensityDebtResult(
        ruleset_version=specification.version,
        debt=Fraction(debt_value),
        corrected_high_fraction=Fraction(corrected),
    )


def calculate_reliable_intensity_debt(
    *,
    planned_high: DurationMinutes,
    planned_total: DurationMinutes,
    realized_high: DurationMinutes,
    realized_classified: DurationMinutes,
    realized_total: DurationMinutes,
    base_next_high_fraction: Fraction = Fraction(Decimal("0.20")),
    discipline_injury_confirmed: bool = False,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> ReliableIntensityDebtResult:
    """Ignore unknown time and evaluate only with at least 60% zone coverage."""
    specification.require_approved(frozenset({RuleId.SOFT_BOUNDARIES}))
    if planned_total.value <= 0 or realized_total.value <= 0:
        raise ValueError("Planned and realized totals must be positive.")
    if planned_high.value > planned_total.value:
        raise ValueError("Planned high-intensity time cannot exceed its total.")
    if realized_classified.value > realized_total.value:
        raise ValueError("Classified time cannot exceed realized activity time.")
    if realized_high.value > realized_classified.value:
        raise ValueError("Realized high-intensity time cannot exceed classified time.")

    coverage = Fraction(realized_classified.value / realized_total.value)
    if coverage.value < _MINIMUM_RELIABLE_INTENSITY_COVERAGE:
        return ReliableIntensityDebtResult(
            ruleset_version=specification.version,
            evaluated=False,
            coverage=coverage,
            result=None,
        )
    result = calculate_intensity_debt(
        planned_high_fraction=Fraction(planned_high.value / planned_total.value),
        realized_high_fraction=Fraction(
            realized_high.value / realized_classified.value
            if realized_classified.value > 0
            else Decimal(0)
        ),
        base_next_high_fraction=base_next_high_fraction,
        discipline_injury_confirmed=discipline_injury_confirmed,
        specification=specification,
    )
    return ReliableIntensityDebtResult(
        ruleset_version=specification.version,
        evaluated=True,
        coverage=coverage,
        result=result,
    )
