"""BR-008 deterministic race taper calculations."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from zoneinfo import ZoneInfo

from app.modules.physiology.models import InternalLoad, RuleId, RulesetVersion
from app.modules.physiology.progression import WeeklyLoad, calculate_42_day_average
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V1,
    PhysiologySpecification,
)


class RacePriority(str, Enum):
    """Race hierarchy used to resolve overlapping taper windows."""

    A = "A"
    B = "B"
    C = "C"


class TaperPeriod(str, Enum):
    """Supported taper calculation windows."""

    A_T_MINUS_2 = "a_t_minus_2"
    A_T_MINUS_1 = "a_t_minus_1"
    B_TAPER_WEEK = "b_taper_week"


_TAPER_FACTORS = {
    TaperPeriod.A_T_MINUS_2: Decimal("0.60"),
    TaperPeriod.A_T_MINUS_1: Decimal("0.35"),
    TaperPeriod.B_TAPER_WEEK: Decimal("0.50"),
}
_PRIORITY_ORDER = {
    RacePriority.A: 0,
    RacePriority.B: 1,
    RacePriority.C: 2,
}


@dataclass(frozen=True, slots=True)
class RaceEvent:
    """Minimum race facts needed for overlap resolution."""

    race_id: str
    priority: RacePriority
    starts_at: datetime

    def __post_init__(self) -> None:
        if not self.race_id.strip():
            raise ValueError("Race identifier cannot be blank.")
        if self.starts_at.tzinfo is None or self.starts_at.utcoffset() is None:
            raise ValueError("Race start time must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class TaperTarget:
    """Exact race taper target from the approved build-load baseline."""

    ruleset_version: RulesetVersion
    period: TaperPeriod
    factor: Decimal
    target: InternalLoad


def calculate_taper_baseline(
    samples: tuple[WeeklyLoad, ...],
    *,
    as_of: date,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> InternalLoad | None:
    """Use available 42-day data while excluding recovery-week samples."""
    specification.require_approved(frozenset({RuleId.TAPER}))
    return calculate_42_day_average(
        samples,
        as_of=as_of,
        exclude_recovery_weeks=True,
        rule_id=RuleId.TAPER,
        specification=specification,
    )


def calculate_taper_target(
    *,
    priority: RacePriority,
    period: TaperPeriod | None,
    baseline: InternalLoad,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> TaperTarget | None:
    """Calculate A/B taper targets; C-races intentionally return no taper."""
    specification.require_approved(frozenset({RuleId.TAPER}))
    if priority is RacePriority.C:
        if period is not None:
            raise ValueError("C-races do not have a taper period.")
        return None
    if period is None:
        raise ValueError("A- and B-races require a taper period.")
    if priority is RacePriority.A and period is TaperPeriod.B_TAPER_WEEK:
        raise ValueError("A-races require an A-race taper period.")
    if priority is RacePriority.B and period is not TaperPeriod.B_TAPER_WEEK:
        raise ValueError("B-races require the B-race taper week.")

    factor = _TAPER_FACTORS[period]
    return TaperTarget(
        ruleset_version=specification.version,
        period=period,
        factor=factor,
        target=InternalLoad(baseline.value * factor),
    )


def select_controlling_race(
    races: tuple[RaceEvent, ...],
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> RaceEvent | None:
    """Select highest priority, then earliest race, then stable identifier."""
    specification.require_approved(frozenset({RuleId.TAPER}))
    if not races:
        return None
    return min(
        races,
        key=lambda race: (
            _PRIORITY_ORDER[race.priority],
            race.starts_at,
            race.race_id,
        ),
    )


def athlete_week_bounds(
    instant: datetime,
    *,
    timezone_name: str,
    specification: PhysiologySpecification = PHASE_3_RULESET_V1,
) -> tuple[date, date]:
    """Return Monday-Sunday dates in the athlete's IANA timezone."""
    specification.require_approved(frozenset({RuleId.TAPER}))
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Instant must be timezone-aware.")
    local_date = instant.astimezone(ZoneInfo(timezone_name)).date()
    monday = local_date - timedelta(days=local_date.weekday())
    return monday, monday + timedelta(days=6)
