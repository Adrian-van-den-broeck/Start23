"""Joren C2.1 planned active-time maximum; isolated from active selection."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Literal

from app.modules.physiology.intensity import IntensitySegment, classify_segment
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    IntensityBucket,
    TrainingZone,
)

POLICY_VERSION = "joren-planned-active-time-maximum-1"
POLICY_EVIDENCE = (
    "docs/catalog/implementation/JOREN_C2_UPDATED_DECISIONS.md#c21-approval"
)
TAXONOMY_VERSION = "phase-3-ruleset-3"


@dataclass(frozen=True, slots=True)
class PlannedSegment:
    seconds: Decimal | None
    zone: TrainingZone | None = None
    stationary_rest: bool = False

    def __post_init__(self) -> None:
        if self.seconds is not None and (
            not self.seconds.is_finite() or self.seconds < 0
        ):
            raise ValueError("invalid_planned_duration")
        if self.stationary_rest and self.zone is not None:
            raise ValueError("stationary_rest_has_no_zone")


@dataclass(frozen=True, slots=True)
class PlannedSession:
    sport: Discipline
    local_date: date
    # None means missing prescription, distinct from a confirmed empty session.
    segments: tuple[PlannedSegment, ...] | None


@dataclass(frozen=True, slots=True)
class SportWeekCompliance:
    sport: Discipline
    week_start: date
    status: Literal["ACCEPTED", "REJECTED", "UNVERIFIED", "NOT APPLICABLE"]
    known_low_seconds: Fraction
    known_high_seconds: Fraction
    high_ratio: Fraction | None
    policy_version: str = POLICY_VERSION
    taxonomy_version: str = TAXONOMY_VERSION
    evidence_reference: str = POLICY_EVIDENCE


def evaluate_training_week(
    week_start: date, sessions: tuple[PlannedSession, ...]
) -> tuple[SportWeekCompliance, ...]:
    """Evaluate one athlete-local Monday-Sunday week, independently per sport.

    Exact rational seconds prevent rounding at the 20% boundary. Unknown active
    time/classification withholds compliance and ratio, including an otherwise
    empty swim week. No distance, load or session-focus input is accepted.
    """
    if week_start.weekday() != 0:
        raise ValueError("week_start_must_be_monday")
    if any(
        not week_start <= s.local_date < week_start + timedelta(days=7)
        for s in sessions
    ):
        raise ValueError("session_outside_training_week")
    results = []
    for sport in Discipline:
        low, high = Fraction(0), Fraction(0)
        complete = True
        for session in sessions:
            if session.sport != sport:
                continue
            if session.segments is None:
                complete = False
                continue
            for segment in session.segments:
                if segment.stationary_rest:
                    if sport != Discipline.SWIM:
                        raise ValueError("stationary_rest_requires_swimming")
                    continue
                if segment.seconds is None:
                    complete = False
                    continue
                if segment.seconds == 0:
                    continue
                if segment.zone is None:
                    complete = False
                    continue
                bucket = classify_segment(
                    IntensitySegment(DurationMinutes(Decimal(0)), zone=segment.zone)
                )
                if bucket == IntensityBucket.LOW:
                    low += Fraction(segment.seconds)
                else:
                    high += Fraction(segment.seconds)
        total = low + high
        status: Literal["ACCEPTED", "REJECTED", "UNVERIFIED", "NOT APPLICABLE"]
        if not complete:
            status = "UNVERIFIED"
        elif total == 0:
            status = "NOT APPLICABLE"
        else:
            status = "ACCEPTED" if high * 5 <= total else "REJECTED"
        results.append(
            SportWeekCompliance(
                sport,
                week_start,
                status,
                low,
                high,
                high / total if complete and total else None,
            )
        )
    return tuple(results)
