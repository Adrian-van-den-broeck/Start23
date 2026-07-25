"""BR-002 deterministic volume and intensity debt calculations."""

from dataclasses import dataclass
from decimal import Decimal

from app.modules.physiology.models import (
    Fraction,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)

_TEN_PERCENT_GROWTH = Decimal("1.10")
_NORMAL_HIGH_INTENSITY_FLOOR = Decimal("0.05")


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


def calculate_volume_debt(
    *,
    prior_planned: InternalLoad,
    prior_realized: InternalLoad,
    exceptional_zero_allowed: bool = False,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
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
    discipline_injury_confirmed: bool = False,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> IntensityDebtResult:
    """Subtract excess high-intensity time with the approved 5% floor."""
    specification.require_approved(frozenset({RuleId.SOFT_BOUNDARIES}))

    debt_value = max(
        Decimal(0),
        realized_high_fraction.value - planned_high_fraction.value,
    )
    floor = Decimal(0) if discipline_injury_confirmed else _NORMAL_HIGH_INTENSITY_FLOOR
    corrected = max(floor, planned_high_fraction.value - debt_value)
    return IntensityDebtResult(
        ruleset_version=specification.version,
        debt=Fraction(debt_value),
        corrected_high_fraction=Fraction(corrected),
    )
