"""BR-003 deterministic time-based intensity classification."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.modules.physiology.models import (
    DurationMinutes,
    Fraction,
    IntensityBucket,
    RuleId,
    RulesetVersion,
    TrainingZone,
)
from app.modules.physiology.specification import (
    PHASE_3_RULESET_V3,
    PhysiologySpecification,
)

_WARNING_MULTIPLIER = Decimal("1.30")


@dataclass(frozen=True, slots=True)
class IntensitySegment:
    """One homogeneous duration segment within a workout."""

    duration: DurationMinutes
    zone: TrainingZone | None = None
    is_swim_technique: bool = False

    def __post_init__(self) -> None:
        if self.zone is None and not self.is_swim_technique:
            raise ValueError("A segment requires a zone or swim-technique flag.")


@dataclass(frozen=True, slots=True)
class WorkoutIntensity:
    """Segments used to classify a workout by its dominant time bucket."""

    segments: tuple[IntensitySegment, ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("A workout requires at least one intensity segment.")
        if sum((segment.duration.value for segment in self.segments), Decimal(0)) <= 0:
            raise ValueError("A workout requires positive total duration.")


@dataclass(frozen=True, slots=True)
class TimeDistribution:
    """Exact weekly low/high duration distribution."""

    ruleset_version: RulesetVersion
    evaluated: bool
    low_duration: DurationMinutes
    high_duration: DurationMinutes
    low_fraction: Fraction | None
    high_fraction: Fraction | None


@dataclass(frozen=True, slots=True)
class DisplayTimeDistribution:
    """Stable athlete-facing whole percentages plus exact detail minutes."""

    low_percent: int
    high_percent: int
    low_minutes: DurationMinutes
    high_minutes: DurationMinutes


@dataclass(frozen=True, slots=True)
class IntensityTarget:
    """Approved standard race-oriented time-distribution target."""

    low_fraction: Fraction
    high_fraction: Fraction


STANDARD_RACE_INTENSITY_TARGET = IntensityTarget(
    low_fraction=Fraction(Decimal("0.80")),
    high_fraction=Fraction(Decimal("0.20")),
)


def classify_segment(
    segment: IntensitySegment,
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> IntensityBucket:
    """Classify canonical zones and swim technique into low/high buckets."""
    specification.require_approved(frozenset({RuleId.TIME_INTENSITY}))
    if segment.is_swim_technique:
        return IntensityBucket.LOW
    if segment.zone in {TrainingZone.ZONE_1, TrainingZone.ZONE_2}:
        return IntensityBucket.LOW
    return IntensityBucket.HIGH


def classify_workout(
    workout: WorkoutIntensity,
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> IntensityBucket:
    """Classify by dominant duration; exact ties conservatively belong to high."""
    specification.require_approved(frozenset({RuleId.TIME_INTENSITY}))
    low = sum(
        (
            segment.duration.value
            for segment in workout.segments
            if classify_segment(segment, specification=specification)
            is IntensityBucket.LOW
        ),
        Decimal(0),
    )
    high = sum(
        (
            segment.duration.value
            for segment in workout.segments
            if classify_segment(segment, specification=specification)
            is IntensityBucket.HIGH
        ),
        Decimal(0),
    )
    return IntensityBucket.HIGH if high >= low else IntensityBucket.LOW


def calculate_time_distribution(
    workouts: tuple[WorkoutIntensity, ...],
    *,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> TimeDistribution:
    """Assign whole workout duration to its dominant category and aggregate."""
    specification.require_approved(frozenset({RuleId.TIME_INTENSITY}))

    low = Decimal(0)
    high = Decimal(0)
    for workout in workouts:
        duration = sum(
            (segment.duration.value for segment in workout.segments),
            Decimal(0),
        )
        if (
            classify_workout(workout, specification=specification)
            is IntensityBucket.LOW
        ):
            low += duration
        else:
            high += duration

    total = low + high
    if total == 0:
        return TimeDistribution(
            ruleset_version=specification.version,
            evaluated=False,
            low_duration=DurationMinutes(Decimal(0)),
            high_duration=DurationMinutes(Decimal(0)),
            low_fraction=None,
            high_fraction=None,
        )
    return TimeDistribution(
        ruleset_version=specification.version,
        evaluated=True,
        low_duration=DurationMinutes(low),
        high_duration=DurationMinutes(high),
        low_fraction=Fraction(low / total),
        high_fraction=Fraction(high / total),
    )


def display_time_distribution(
    distribution: TimeDistribution,
) -> DisplayTimeDistribution:
    """Round low half-up and derive high as its complement so totals equal 100."""
    if (
        not distribution.evaluated
        or distribution.low_fraction is None
        or distribution.high_fraction is None
    ):
        raise ValueError("An evaluated intensity distribution is required.")
    low_percent = int(
        (distribution.low_fraction.value * Decimal(100)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
    )
    return DisplayTimeDistribution(
        low_percent=low_percent,
        high_percent=100 - low_percent,
        low_minutes=distribution.low_duration,
        high_minutes=distribution.high_duration,
    )


def intensive_duration_warning(
    *,
    planned: DurationMinutes,
    realized: DurationMinutes,
    specification: PhysiologySpecification = PHASE_3_RULESET_V3,
) -> bool:
    """Warn only when realized intensive duration is strictly over planned +30%."""
    specification.require_approved(frozenset({RuleId.TIME_INTENSITY}))
    if planned.value == 0:
        return realized.value > 0
    return realized.value > planned.value * _WARNING_MULTIPLIER
