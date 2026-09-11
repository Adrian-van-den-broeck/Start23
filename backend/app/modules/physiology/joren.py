"""Phase 13's immutable Decimal calculation policy; no I/O or activation."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType
from typing import Final

from app.modules.physiology.models import Discipline, InternalLoad, RulesetVersion

VERSION: Final = RulesetVersion("phase-13-joren-ruleset-1")
SRPE_FALLBACK_ENABLED: Final = False
HR_ANCHORS: Final = tuple(
    map(
        Decimal,
        (
            "0.70",
            "0.78",
            "0.84",
            "0.88",
            "0.91",
            "0.94",
            "0.97",
            "1.00",
            "1.03",
            "1.06",
        ),
    )
)
SWIM_ANCHORS: Final = tuple(
    map(
        Decimal,
        (
            "1.25",
            "1.18",
            "1.12",
            "1.08",
            "1.06",
            "1.04",
            "1.01",
            "1.00",
            "0.96",
            "0.92",
        ),
    )
)
SRPE_FACTORS: Final = tuple(
    map(
        Decimal,
        (
            "0.45",
            "0.55",
            "0.65",
            "0.75",
            "0.82",
            "0.88",
            "0.94",
            "1.00",
            "1.05",
            "1.15",
        ),
    )
)
SPORT_MULTIPLIERS: Final = MappingProxyType(
    {
        Discipline.SWIM: Decimal("0.90"),
        Discipline.BIKE: Decimal("1.00"),
        Discipline.RUN: Decimal("1.15"),
    }
)
ZONE_COEFFICIENTS: Final = MappingProxyType(
    {
        Discipline.SWIM: tuple(map(Decimal, ("0.45", "0.72", "1.08", "1.44", "1.80"))),
        Discipline.BIKE: tuple(map(Decimal, ("0.50", "0.80", "1.20", "1.60", "2.00"))),
        Discipline.RUN: tuple(map(Decimal, ("0.58", "0.92", "1.38", "1.84", "2.30"))),
    }
)


def _nonnegative(value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("A finite non-negative Decimal is required.")


def _rpe_index(rpe: int) -> int:
    if type(rpe) is not int or not 1 <= rpe <= 10:
        raise ValueError("RPE must be an integer from 1 through 10.")
    return rpe - 1


def rounded(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True, slots=True, repr=False)
class StartingBaseline:
    """Private exact components and independently rounded final weekly total."""

    by_discipline: Mapping[Discipline, InternalLoad]
    total: InternalLoad
    zero_base: bool
    ruleset_version: RulesetVersion = VERSION


def starting_baseline(minutes: Mapping[Discipline, Decimal]) -> StartingBaseline:
    if not minutes or not set(minutes) <= set(Discipline):
        raise ValueError("Explicit component discipline history is required.")
    for value in minutes.values():
        _nonnegative(value)
    if sum(minutes.values(), Decimal(0)) > Decimal(168 * 60):
        raise ValueError("Combined weekly duration cannot exceed 168 hours.")
    components = {
        sport: InternalLoad(
            value * Decimal("56.25") * SPORT_MULTIPLIERS[sport] / Decimal(60)
        )
        for sport, value in minutes.items()
    }
    total = sum((value.value for value in components.values()), Decimal(0))
    zero_base = total == 0
    # 45.0 is the Start23 product decision, not an exact value selected by the PDF.
    final = (
        Decimal("45.0")
        if zero_base
        else total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    )
    return StartingBaseline(
        MappingProxyType(components), InternalLoad(final), zero_base
    )


@dataclass(frozen=True, slots=True)
class IntegerZone:
    """Inclusive integer bounds; None is an unbounded outer edge."""

    zone: int
    lower: int | None
    upper: int | None

    def contains(self, value: int) -> bool:
        return (self.lower is None or value >= self.lower) and (
            self.upper is None or value <= self.upper
        )


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    discipline: Discipline
    threshold: int
    zones: tuple[IntegerZone, ...]
    warning_codes: tuple[str, ...] = ()
    ruleset_version: RulesetVersion = VERSION
    requires_athlete_confirmation: bool = True


def threshold_zones(discipline: Discipline, threshold: int) -> tuple[IntegerZone, ...]:
    if type(threshold) is not int or threshold <= 0:
        raise ValueError("Threshold must be a positive whole number.")
    value = Decimal(threshold)
    if discipline is Discipline.SWIM:
        # Round the displayed CSS first. Own the percentage gaps using adjacent
        # inclusive bounds, preserving inverse pace. 115% belongs to Z2.
        a, b, c, d = (
            rounded(value * Decimal(f)) for f in ("0.98", "1.02", "1.07", "1.15")
        )
        if not 0 < a <= b < c < d:
            raise ValueError("Threshold cannot represent five discrete zones.")
        return (
            IntegerZone(1, d + 1, None),
            IntegerZone(2, c + 1, d),
            IntegerZone(3, b + 1, c),
            IntegerZone(4, a, b),
            IntegerZone(5, None, a - 1),
        )
    if discipline not in {Discipline.RUN, Discipline.BIKE}:
        raise ValueError("Unsupported discipline.")
    a, b, c = (rounded(value * Decimal(f)) for f in ("0.82", "0.89", "0.95"))
    if not 0 < a <= b < c < threshold:
        raise ValueError("Threshold cannot represent five discrete zones.")
    return (
        IntegerZone(1, None, a - 1),
        IntegerZone(2, a, b),
        IntegerZone(3, b + 1, c),
        IntegerZone(4, c + 1, threshold),
        IntegerZone(5, threshold + 1, None),
    )


def calibrate(
    *, discipline: Discipline, observation: Decimal, rpe: int
) -> CalibrationResult:
    """Observation is HR bpm for run/bike, seconds per 100m for swim."""
    _nonnegative(observation)
    if observation == 0:
        raise ValueError("Calibration observation must be positive.")
    anchors = SWIM_ANCHORS if discipline is Discipline.SWIM else HR_ANCHORS
    threshold = rounded(observation / anchors[_rpe_index(rpe)])
    warnings = (
        ("calculated_threshold_unusually_low",)
        if discipline is not Discipline.SWIM and threshold < 140
        else ()
    )
    return CalibrationResult(
        discipline, threshold, threshold_zones(discipline, threshold), warnings
    )


@dataclass(frozen=True, slots=True, repr=False)
class ZoneLoad:
    """Private measurement provenance; absence is never synthesized as zero."""

    load: InternalLoad | None = field(repr=False)
    total_minutes: Decimal | None
    valid_minutes: Decimal
    coverage_ratio: Decimal | None
    status: str
    calculation_method: str = "observed_zone_minutes"
    ruleset_version: RulesetVersion = VERSION
    assigned_zone: int | None = None


def zone_load(
    *,
    discipline: Discipline,
    total_minutes: Decimal | None,
    minutes_by_zone: tuple[Decimal, ...] | None,
    planned: bool = False,
) -> ZoneLoad:
    if total_minutes is not None:
        _nonnegative(total_minutes)
    if minutes_by_zone is not None:
        if len(minutes_by_zone) != 5:
            raise ValueError("Exactly five zone durations are required.")
        for value in minutes_by_zone:
            _nonnegative(value)
    valid = sum(minutes_by_zone or (), Decimal(0))
    if total_minutes is None and valid > 0:
        raise ValueError("Zone time requires reliable total duration.")
    if total_minutes is not None and valid > total_minutes:
        raise ValueError("Zone time cannot exceed total duration.")
    ratio = valid / total_minutes if total_minutes else None
    available = minutes_by_zone is not None and total_minutes is not None and valid > 0
    load = (
        InternalLoad(
            sum(
                (
                    duration * factor
                    for duration, factor in zip(
                        minutes_by_zone or (), ZONE_COEFFICIENTS[discipline]
                    )
                ),
                Decimal(0),
            )
        )
        if available
        else None
    )
    return ZoneLoad(
        load,
        total_minutes,
        valid,
        ratio,
        "complete"
        if available and valid == total_minutes
        else "partial_observed"
        if available
        else "unavailable",
        "planned_zone_minutes" if planned else "observed_zone_minutes",
    )


def srpe_formula(
    *, discipline: Discipline, duration_minutes: Decimal, rpe: int
) -> InternalLoad:
    """Reference formula only; active missing-data policy never selects it."""
    _nonnegative(duration_minutes)
    factor = SRPE_FACTORS[_rpe_index(rpe)]
    return InternalLoad(
        duration_minutes
        / Decimal(60)
        * factor**2
        * Decimal(100)
        * SPORT_MULTIPLIERS[discipline]
    )


def taper_window(race_date: date) -> tuple[date, date]:
    return race_date - timedelta(days=7), race_date - timedelta(days=1)


def is_taper_day(day: date, race_date: date) -> bool:
    start, end = taper_window(race_date)
    return start <= day <= end


def average_hr_zone_load(
    *, discipline: Discipline, total_minutes: Decimal, zone: int
) -> ZoneLoad:
    """2026-09-11 amendment: full duration in the known mean-HR zone.

    This is an estimate based on average HR, not observed time in zone. Swimming
    has no HR calibration/loading route under this ruleset.
    """
    _nonnegative(total_minutes)
    if (
        discipline not in {Discipline.RUN, Discipline.BIKE}
        or type(zone) is not int
        or not 1 <= zone <= 5
    ):
        raise ValueError("A known run/bike heart-rate zone is required.")
    if total_minutes == 0:
        raise ValueError("A reliable positive duration is required.")
    return ZoneLoad(
        InternalLoad(total_minutes * ZONE_COEFFICIENTS[discipline][zone - 1]),
        total_minutes,
        Decimal(0),
        Decimal(0),
        "estimated_from_average_hr",
        "average_hr_zone_duration",
        VERSION,
        zone,
    )
