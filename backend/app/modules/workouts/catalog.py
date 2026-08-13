"""Validated, reviewed Phase 5 workout catalog."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID

from app.modules.physiology.intensity import (
    IntensitySegment,
    WorkoutIntensity,
    classify_workout,
)
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.physiology.progression import snapshot_personalized_load


class TrainingPhase(str, Enum):
    """Supported race-oriented periodization tags."""

    BASE = "base"
    BUILD = "build"
    RECOVERY = "recovery"
    TAPER = "taper"


class ZoneRequirement(str, Enum):
    """Canonical athlete-zone capability required by a template."""

    HEART_RATE = "heart_rate"
    PACE = "pace"
    POWER = "power"


class FallbackCompatibility(str, Enum):
    """Whether an unvalidated heart-rate fallback can drive the workout."""

    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True, slots=True)
class WorkoutSegment:
    """One immutable, ordered catalog segment."""

    sequence: int
    name: str
    instructions: str
    duration_minutes: Decimal
    zone: TrainingZone
    expected_rpe: int
    distance_meters: int | None = None
    is_swim_technique: bool = False

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Segment sequence must be positive.")
        if not self.name.strip() or not self.instructions.strip():
            raise ValueError("Every segment requires a name and instructions.")
        if not self.duration_minutes.is_finite() or self.duration_minutes <= 0:
            raise ValueError("Segment duration must be finite and positive.")
        if self.distance_meters is not None and self.distance_meters <= 0:
            raise ValueError("Segment distance must be positive when supplied.")
        if not 1 <= self.expected_rpe <= 10:
            raise ValueError("Segment expected RPE must be between 1 and 10.")


@dataclass(frozen=True, slots=True)
class WorkoutTemplate:
    """One immutable internal catalog version."""

    id: UUID
    template_key: UUID
    version: int
    discipline: Discipline
    name: str
    description: str
    duration_minutes: Decimal
    distance_meters: int | None
    intensity_bucket: IntensityBucket
    expected_rpe_min: int
    expected_rpe_max: int
    training_phases: tuple[TrainingPhase, ...]
    zone_requirements: tuple[ZoneRequirement, ...]
    fallback_compatibility: FallbackCompatibility
    segments: tuple[WorkoutSegment, ...]
    internal_planned_load: InternalLoad = field(repr=False)

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("Template version must be positive.")
        if not self.name.strip() or not self.description.strip():
            raise ValueError("Every template requires a name and description.")
        if not self.duration_minutes.is_finite() or self.duration_minutes <= 0:
            raise ValueError("Template duration must be finite and positive.")
        if self.distance_meters is not None and self.distance_meters <= 0:
            raise ValueError("Template distance must be positive when supplied.")
        if not 1 <= self.expected_rpe_min <= self.expected_rpe_max <= 10:
            raise ValueError("Template expected RPE range must be within 1 through 10.")
        if not self.training_phases or len(set(self.training_phases)) != len(
            self.training_phases
        ):
            raise ValueError("Template training phases must be non-empty and unique.")
        if len(set(self.zone_requirements)) != len(self.zone_requirements):
            raise ValueError("Template zone requirements must be unique.")
        if not self.segments:
            raise ValueError("A workout template requires at least one segment.")
        if tuple(segment.sequence for segment in self.segments) != tuple(
            range(1, len(self.segments) + 1)
        ):
            raise ValueError("Segment sequences must be contiguous and start at one.")
        if any(
            not self.expected_rpe_min <= segment.expected_rpe <= self.expected_rpe_max
            for segment in self.segments
        ):
            raise ValueError("Segment RPE must fall within the template RPE range.")

        segment_duration = sum(
            (segment.duration_minutes for segment in self.segments),
            Decimal(0),
        )
        if segment_duration != self.duration_minutes:
            raise ValueError("Segment durations must equal the template duration.")
        segment_distance = sum(
            (
                segment.distance_meters
                for segment in self.segments
                if segment.distance_meters is not None
            ),
            0,
        )
        if self.distance_meters is None and segment_distance:
            raise ValueError("Segment distance requires a template distance.")
        if (
            self.distance_meters is not None
            and segment_distance != self.distance_meters
        ):
            raise ValueError("Segment distances must equal the template distance.")
        if any(
            segment.is_swim_technique and self.discipline is not Discipline.SWIM
            for segment in self.segments
        ):
            raise ValueError("Only swim segments can be marked as technique.")
        if self.fallback_compatibility is FallbackCompatibility.COMPATIBLE and any(
            requirement is not ZoneRequirement.HEART_RATE
            for requirement in self.zone_requirements
        ):
            raise ValueError(
                "Fallback-compatible templates may require only heart-rate zones."
            )

        calculated_bucket = classify_workout(
            WorkoutIntensity(
                tuple(
                    IntensitySegment(
                        duration=DurationMinutes(segment.duration_minutes),
                        zone=segment.zone,
                        is_swim_technique=segment.is_swim_technique,
                    )
                    for segment in self.segments
                )
            )
        )
        if calculated_bucket is not self.intensity_bucket:
            raise ValueError(
                "Declared intensity bucket must match deterministic segment dominance."
            )


@dataclass(frozen=True, slots=True)
class PlannedWorkoutSnapshot:
    """Immutable Phase 6 input detached from later catalog versions."""

    template_id: UUID
    template_key: UUID
    template_version: int
    name: str
    duration_minutes: Decimal
    distance_meters: int | None
    intensity_bucket: IntensityBucket
    expected_rpe_min: int
    expected_rpe_max: int
    segments: tuple[WorkoutSegment, ...]
    internal_planned_load: InternalLoad = field(repr=False)


def snapshot_template(template: WorkoutTemplate) -> PlannedWorkoutSnapshot:
    """Capture all planning values, including hidden load, by value."""
    return PlannedWorkoutSnapshot(
        template_id=template.id,
        template_key=template.template_key,
        template_version=template.version,
        name=template.name,
        duration_minutes=template.duration_minutes,
        distance_meters=template.distance_meters,
        intensity_bucket=template.intensity_bucket,
        expected_rpe_min=template.expected_rpe_min,
        expected_rpe_max=template.expected_rpe_max,
        segments=template.segments,
        internal_planned_load=template.internal_planned_load,
    )


def _segment(
    sequence: int,
    name: str,
    minutes: str,
    zone: int,
    rpe: int,
    *,
    technique: bool = False,
    distance: int | None = None,
) -> WorkoutSegment:
    return WorkoutSegment(
        sequence=sequence,
        name=name,
        instructions=f"Complete {name.lower()} in Zone {zone}.",
        duration_minutes=Decimal(minutes),
        zone=TrainingZone(zone),
        expected_rpe=rpe,
        distance_meters=distance,
        is_swim_technique=technique,
    )


def _template(
    *,
    id: str,
    key: str,
    version: int,
    discipline: Discipline,
    name: str,
    description: str,
    phases: tuple[TrainingPhase, ...],
    requirements: tuple[ZoneRequirement, ...],
    fallback: FallbackCompatibility,
    segments: tuple[WorkoutSegment, ...],
    distance_meters: int | None = None,
) -> WorkoutTemplate:
    duration = sum((segment.duration_minutes for segment in segments), Decimal(0))
    minimum_rpe = min(segment.expected_rpe for segment in segments)
    maximum_rpe = max(segment.expected_rpe for segment in segments)
    workout = WorkoutIntensity(
        tuple(
            IntensitySegment(
                duration=DurationMinutes(segment.duration_minutes),
                zone=segment.zone,
                is_swim_technique=segment.is_swim_technique,
            )
            for segment in segments
        )
    )
    load = snapshot_personalized_load(
        expected_rpe=Decimal(minimum_rpe + maximum_rpe) / Decimal(2),
        duration=DurationMinutes(duration),
    )
    return WorkoutTemplate(
        id=UUID(id),
        template_key=UUID(key),
        version=version,
        discipline=discipline,
        name=name,
        description=description,
        duration_minutes=duration,
        distance_meters=distance_meters,
        intensity_bucket=classify_workout(workout),
        expected_rpe_min=minimum_rpe,
        expected_rpe_max=maximum_rpe,
        training_phases=phases,
        zone_requirements=requirements,
        fallback_compatibility=fallback,
        segments=segments,
        internal_planned_load=load,
    )


REVIEWED_CATALOG: tuple[WorkoutTemplate, ...] = (
    _template(
        id="51000000-0000-0000-0000-000000000001",
        key="50000000-0000-0000-0000-000000000001",
        version=1,
        discipline=Discipline.SWIM,
        name="Technique foundation",
        description="Relaxed technique work with an aerobic finish.",
        phases=(TrainingPhase.BASE, TrainingPhase.RECOVERY),
        requirements=(ZoneRequirement.PACE,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Easy warm-up", "10", 1, 2, technique=True, distance=400),
            _segment(2, "Technique drills", "20", 2, 3, technique=True, distance=800),
            _segment(3, "Aerobic finish", "10", 2, 3, distance=400),
        ),
        distance_meters=1600,
    ),
    _template(
        id="51000000-0000-0000-0000-000000000002",
        key="50000000-0000-0000-0000-000000000002",
        version=1,
        discipline=Discipline.SWIM,
        name="Threshold repeats",
        description="Controlled threshold blocks with easy swimming around them.",
        phases=(TrainingPhase.BUILD,),
        requirements=(ZoneRequirement.PACE,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Warm-up", "10", 2, 3, distance=400),
            _segment(2, "Threshold repeats", "30", 4, 8, distance=1200),
            _segment(3, "Cool-down", "10", 1, 2, distance=400),
        ),
        distance_meters=2000,
    ),
    _template(
        id="51000000-0000-0000-0000-000000000003",
        key="50000000-0000-0000-0000-000000000003",
        version=1,
        discipline=Discipline.BIKE,
        name="Aerobic endurance",
        description="Steady low-intensity endurance ride.",
        phases=(TrainingPhase.BASE, TrainingPhase.BUILD, TrainingPhase.RECOVERY),
        requirements=(ZoneRequirement.HEART_RATE,),
        fallback=FallbackCompatibility.COMPATIBLE,
        segments=(
            _segment(1, "Easy roll-out", "10", 1, 2),
            _segment(2, "Endurance riding", "40", 2, 4),
            _segment(3, "Easy finish", "10", 1, 2),
        ),
    ),
    _template(
        id="51000000-0000-0000-0000-000000000004",
        key="50000000-0000-0000-0000-000000000004",
        version=1,
        discipline=Discipline.BIKE,
        name="Power intervals",
        description="High-intensity bike intervals guided by power.",
        phases=(TrainingPhase.BUILD,),
        requirements=(ZoneRequirement.POWER,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Warm-up", "10", 2, 3),
            _segment(2, "Power intervals", "30", 4, 8),
            _segment(3, "Cool-down", "10", 1, 2),
        ),
    ),
    _template(
        id="51000000-0000-0000-0000-000000000005",
        key="50000000-0000-0000-0000-000000000005",
        version=1,
        discipline=Discipline.RUN,
        name="Easy aerobic run",
        description="Comfortable aerobic running with a relaxed finish.",
        phases=(TrainingPhase.BASE, TrainingPhase.RECOVERY, TrainingPhase.TAPER),
        requirements=(ZoneRequirement.HEART_RATE,),
        fallback=FallbackCompatibility.COMPATIBLE,
        segments=(
            _segment(1, "Easy start", "10", 1, 2),
            _segment(2, "Aerobic running", "25", 2, 4),
            _segment(3, "Relaxed finish", "5", 1, 2),
        ),
    ),
    _template(
        id="51000000-0000-0000-0000-000000000006",
        key="50000000-0000-0000-0000-000000000006",
        version=1,
        discipline=Discipline.RUN,
        name="Tempo intervals",
        description="Structured high-intensity running with easy bookends.",
        phases=(TrainingPhase.BUILD,),
        requirements=(ZoneRequirement.PACE,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Warm-up", "10", 2, 3),
            _segment(2, "Tempo intervals", "25", 4, 8),
            _segment(3, "Cool-down", "10", 1, 2),
        ),
    ),
    _template(
        id="52000000-0000-0000-0000-000000000005",
        key="50000000-0000-0000-0000-000000000005",
        version=2,
        discipline=Discipline.RUN,
        name="Easy aerobic run",
        description="Comfortable aerobic running with a longer steady middle.",
        phases=(TrainingPhase.BASE, TrainingPhase.RECOVERY, TrainingPhase.TAPER),
        requirements=(ZoneRequirement.HEART_RATE,),
        fallback=FallbackCompatibility.COMPATIBLE,
        segments=(
            _segment(1, "Easy start", "10", 1, 2),
            _segment(2, "Aerobic running", "30", 2, 4),
            _segment(3, "Relaxed finish", "5", 1, 2),
        ),
    ),
)

PHASE_6_CATALOG_ADDITIONS: tuple[WorkoutTemplate, ...] = (
    _template(
        id="53000000-0000-0000-0000-000000000007",
        key="50000000-0000-0000-0000-000000000007",
        version=1,
        discipline=Discipline.BIKE,
        name="Power-guided aerobic endurance",
        description="Steady low-intensity endurance riding guided by power zones.",
        phases=(TrainingPhase.BASE, TrainingPhase.BUILD, TrainingPhase.RECOVERY),
        requirements=(ZoneRequirement.POWER,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Easy roll-out", "10", 1, 2),
            _segment(2, "Power-zone endurance", "40", 2, 4),
            _segment(3, "Easy finish", "10", 1, 2),
        ),
    ),
)

CURRENT_CATALOG = REVIEWED_CATALOG + PHASE_6_CATALOG_ADDITIONS


def active_catalog(
    catalog: tuple[WorkoutTemplate, ...] = CURRENT_CATALOG,
) -> tuple[WorkoutTemplate, ...]:
    """Return the highest immutable version of every logical template."""
    latest: dict[UUID, WorkoutTemplate] = {}
    seen_versions: set[tuple[UUID, int]] = set()
    for template in catalog:
        version_key = (template.template_key, template.version)
        if version_key in seen_versions:
            raise ValueError("Catalog template versions must be unique.")
        seen_versions.add(version_key)
        current = latest.get(template.template_key)
        if current is None or template.version > current.version:
            latest[template.template_key] = template
    if {template.discipline for template in latest.values()} != set(Discipline):
        raise ValueError("The active catalog must cover swim, bike, and run.")
    return tuple(
        sorted(
            latest.values(),
            key=lambda template: (template.discipline.value, template.name),
        )
    )
