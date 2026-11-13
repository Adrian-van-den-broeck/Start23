"""Private count contract after trusted, versioned frequency-policy resolution.

The approved policy separates persistent wishes from individually reviewed weekly
maxima. This value object does not establish authority by itself. Local synthetic
controls remain TEST_ONLY. Counts include retained/completed occurrences;
targets are soft requests, never mandatory minima or inference from hours/load.
"""

from dataclasses import dataclass

from app.modules.physiology.models import Discipline

VERSION = "joren-v6-multi-session-selection-1"
MAX_OCCURRENCES = 24  # Existing engineering count bound, not athlete capability.
MAX_SEARCH_NODES = 200_000


@dataclass(frozen=True, slots=True)
class SessionFrequency:
    sport: Discipline
    maximum: int
    reference: str
    target: int | None = None
    status: str = "soft_target"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.sport, Discipline)
            or type(self.maximum) is not int
            or not 0 <= self.maximum <= MAX_OCCURRENCES
            or not self.reference.strip()
            or self.status != "soft_target"
            or self.target is not None
            and (type(self.target) is not int or not 0 <= self.target <= self.maximum)
        ):
            raise ValueError("invalid_v6_frequency_authorization")

    @property
    def requested(self) -> int:
        # Maximum-only authorization must not become an instruction to fill it.
        return min(1, self.maximum) if self.target is None else self.target
