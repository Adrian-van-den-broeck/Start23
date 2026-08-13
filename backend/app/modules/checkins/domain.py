"""Pure Phase 8 weekly-context validation and local-week helpers."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.physiology.injury import (
    AllowedIntensity,
    RestrictionStatus,
)
from app.modules.physiology.models import Discipline
from app.modules.planning.domain import AvailabilityWindow


class AthletePlanChoice(str, Enum):
    """Explicit athlete decision shown alongside current advice."""

    KEEP_BLOCKED = "keep_blocked"
    TRAIN_LOW_ONLY = "train_low_only"
    RESUME_UNRESTRICTED = "resume_unrestricted"


_STATUS_INTENSITY = {
    RestrictionStatus.NONE: AllowedIntensity.UNRESTRICTED,
    RestrictionStatus.SELF_REPORTED_LIMITED: AllowedIntensity.LOW_ONLY,
    RestrictionStatus.SELF_REPORTED_BLOCKED: AllowedIntensity.NONE,
    RestrictionStatus.PROFESSIONAL_RESTRICTED: AllowedIntensity.NONE,
    RestrictionStatus.CLEARANCE_REQUIRED: AllowedIntensity.NONE,
    RestrictionStatus.EXPIRED: AllowedIntensity.NONE,
}

_STATUS_CHOICE = {
    RestrictionStatus.NONE: AthletePlanChoice.RESUME_UNRESTRICTED,
    RestrictionStatus.SELF_REPORTED_LIMITED: AthletePlanChoice.TRAIN_LOW_ONLY,
    RestrictionStatus.SELF_REPORTED_BLOCKED: AthletePlanChoice.KEEP_BLOCKED,
    RestrictionStatus.PROFESSIONAL_RESTRICTED: AthletePlanChoice.KEEP_BLOCKED,
    RestrictionStatus.CLEARANCE_REQUIRED: AthletePlanChoice.KEEP_BLOCKED,
    RestrictionStatus.EXPIRED: AthletePlanChoice.KEEP_BLOCKED,
}


@dataclass(frozen=True, slots=True)
class RestrictionDecision:
    """One attributable, weekly reviewed functional restriction decision."""

    discipline: Discipline
    status: RestrictionStatus
    source: str
    athlete_plan_choice: AthletePlanChoice
    professional_advice: str | None = None
    professional_advice_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("Restriction source is required.")
        if self.athlete_plan_choice is not _STATUS_CHOICE[self.status]:
            raise ValueError("Restriction status and athlete plan choice disagree.")
        if (self.professional_advice is None) != (self.professional_advice_at is None):
            raise ValueError(
                "Professional advice and its date must be supplied together."
            )
        if self.status is RestrictionStatus.PROFESSIONAL_RESTRICTED and (
            self.professional_advice is None
        ):
            raise ValueError("A professional restriction requires attributable advice.")
        if self.professional_advice_at is not None and (
            self.professional_advice_at.tzinfo is None
            or self.professional_advice_at.utcoffset() is None
        ):
            raise ValueError("Professional advice time must be timezone-aware.")

    @property
    def allowed_intensity(self) -> AllowedIntensity:
        return _STATUS_INTENSITY[self.status]


def athlete_local_week_start(*, instant: datetime, timezone_name: str) -> date:
    """Return the athlete-local Monday containing one aware instant."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Weekly trigger time must be timezone-aware.")
    local_date = instant.astimezone(ZoneInfo(timezone_name)).date()
    return local_date - timedelta(days=local_date.weekday())


def confirmed_restriction_sets(
    decisions: Sequence[RestrictionDecision],
) -> tuple[frozenset[Discipline], frozenset[Discipline]]:
    """Split confirmed functional restrictions into blocked and low-only sets."""
    if len({item.discipline for item in decisions}) != len(decisions):
        raise ValueError("Each discipline can have only one restriction decision.")
    blocked = frozenset(
        item.discipline
        for item in decisions
        if item.allowed_intensity is AllowedIntensity.NONE
    )
    low_only = frozenset(
        item.discipline
        for item in decisions
        if item.allowed_intensity is AllowedIntensity.LOW_ONLY
    )
    return blocked, low_only


def availability_from_blocked_dates(
    *,
    week_start: date,
    timezone_name: str,
    blocked_dates: frozenset[date],
    strenuous_dates: frozenset[date] = frozenset(),
) -> tuple[AvailabilityWindow, ...]:
    """Create deterministic daytime windows for non-blocked local dates."""
    if week_start.weekday() != 0:
        raise ValueError("The check-in week must start on Monday.")
    week_dates = {week_start + timedelta(days=offset) for offset in range(7)}
    if not blocked_dates <= week_dates or not strenuous_dates <= week_dates:
        raise ValueError("Weekly context dates must fall inside the check-in week.")
    timezone = ZoneInfo(timezone_name)
    unavailable = blocked_dates | strenuous_dates
    return tuple(
        AvailabilityWindow(
            starts_at=datetime.combine(day, time(hour=6), timezone),
            ends_at=datetime.combine(day, time(hour=22), timezone),
        )
        for day in sorted(week_dates - unavailable)
    )


def context_fingerprint(payload: Mapping[str, Any]) -> str:
    """Fingerprint exact structured context before explicit confirmation."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
