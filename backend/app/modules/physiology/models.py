"""Pure value objects shared by deterministic physiology rules."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, IntEnum
from re import fullmatch
from uuid import UUID


class RuleId(str, Enum):
    """Stable business-rule identifiers."""

    FULL_AUTONOMY = "BR-001"
    SOFT_BOUNDARIES = "BR-002"
    TIME_INTENSITY = "BR-003"
    PROGRESSIVE_LOAD = "BR-004"
    HIDDEN_LOAD = "BR-005"
    ANTI_STACK = "BR-006"
    RECOVERY_CYCLE = "BR-007"
    TAPER = "BR-008"
    DISCIPLINE_ZONES = "BR-009"
    INJURY_REDISTRIBUTION = "BR-010"


class ConstraintStage(IntEnum):
    """Locked evaluation order from the Phase 0 decision record."""

    IDENTITY_OWNERSHIP_VALIDITY_INJURY = 10
    RACE_TAPER = 20
    RECOVERY_WEEK = 30
    PHYSIOLOGICAL_DEBT = 40
    PROGRESSIVE_LOAD = 50
    INTENSITY_AND_PLACEMENT = 60
    AVAILABILITY_AND_PREFERENCES = 70


class EvaluationState(str, Enum):
    """Qualitative outcome of one deterministic rule evaluation."""

    SATISFIED = "satisfied"
    WARNING = "warning"
    CONFLICT = "conflict"
    NOT_EVALUATED = "not_evaluated"


class Discipline(str, Enum):
    """Supported MVP training disciplines."""

    SWIM = "swim"
    BIKE = "bike"
    RUN = "run"


class IntensityBucket(str, Enum):
    """Time-based intensity buckets used by BR-003 and BR-006."""

    LOW = "low"
    HIGH = "high"


class TrainingZone(IntEnum):
    """Canonical zone numbers used for deterministic classification."""

    ZONE_1 = 1
    ZONE_2 = 2
    ZONE_3 = 3
    ZONE_4 = 4
    ZONE_5 = 5


@dataclass(frozen=True, slots=True)
class RulesetVersion:
    """Auditable identifier for an approved deterministic ruleset."""

    value: str

    def __post_init__(self) -> None:
        if fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", self.value) is None:
            raise ValueError("Ruleset version must be a stable lowercase identifier.")


@dataclass(frozen=True, slots=True)
class InternalLoad:
    """Non-negative server-only load value that is hidden from representations."""

    value: Decimal = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value.is_finite() or self.value < 0:
            raise ValueError("Internal load must be finite and non-negative.")


@dataclass(frozen=True, slots=True)
class DurationMinutes:
    """Finite non-negative duration in canonical minutes."""

    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or self.value < 0:
            raise ValueError("Duration must be finite and non-negative.")


@dataclass(frozen=True, slots=True)
class Fraction:
    """Exact decimal fraction in the inclusive range zero through one."""

    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or not Decimal(0) <= self.value <= Decimal(1):
            raise ValueError("Fraction must be finite and between zero and one.")


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    """Qualitative, framework-independent result of one rule."""

    rule_id: RuleId
    stage: ConstraintStage
    state: EvaluationState
    code: str

    def __post_init__(self) -> None:
        if fullmatch(r"[a-z][a-z0-9_]{2,63}", self.code) is None:
            raise ValueError("Evaluation code must be a stable snake_case identifier.")


@dataclass(frozen=True, slots=True)
class DecisionRun:
    """Auditable ordered result produced by one approved ruleset."""

    run_id: UUID
    ruleset_version: RulesetVersion
    evaluations: tuple[RuleEvaluation, ...]
