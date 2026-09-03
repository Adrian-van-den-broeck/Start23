"""Validated, reviewed Phase 5 workout catalog."""

from dataclasses import dataclass, field, replace
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
from app.modules.physiology.rpe_zones import rpe_zone, zone_for_rpe_value


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


EXPLICIT_FIELD_TEST_PROTOCOL_IDS = frozenset(
    {
        "start23_run_threshold_30min_v1",
        "start23_bike_ftp_30min_v1",
        "start23_bike_fthr_20min_v1",
        "start23_swim_css_400_200_v1",
    }
)


@dataclass(frozen=True, slots=True)
class ProtocolTarget:
    """Zone-independent execution target from one reviewed protocol segment."""

    protocol_id: str
    segment_id: str
    target_rpe_min: int
    target_rpe_max: int
    intensity_bucket: IntensityBucket
    optional: bool = False

    def __post_init__(self) -> None:
        if not self.protocol_id.strip() or not self.segment_id.strip():
            raise ValueError("A protocol target requires protocol and segment IDs.")
        if not 1 <= self.target_rpe_min <= self.target_rpe_max <= 10:
            raise ValueError("Protocol target RPE must be within 1 through 10.")


@dataclass(frozen=True, slots=True)
class RpeTarget:
    """Zone-free execution target derived from a reviewed catalog segment."""

    target_rpe_min: int
    target_rpe_max: int
    intensity_bucket: IntensityBucket
    heart_rate_observation_required: bool = True

    def __post_init__(self) -> None:
        if not 1 <= self.target_rpe_min <= self.target_rpe_max <= 10:
            raise ValueError("RPE target must be within 1 through 10.")


@dataclass(frozen=True, slots=True)
class WorkoutSegment:
    """One immutable, ordered catalog segment."""

    sequence: int
    name: str
    instructions: str
    duration_minutes: Decimal
    expected_rpe: int
    zone_target: TrainingZone | None = None
    protocol_target: ProtocolTarget | None = None
    rpe_target: RpeTarget | None = None
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
        target_count = sum(
            target is not None
            for target in (self.zone_target, self.protocol_target, self.rpe_target)
        )
        if target_count != 1:
            raise ValueError(
                "Every segment requires exactly one zone, protocol, or RPE target."
            )
        if self.protocol_target is not None and not (
            self.protocol_target.target_rpe_min
            <= self.expected_rpe
            <= self.protocol_target.target_rpe_max
        ):
            raise ValueError("Segment RPE must fall within its protocol target.")
        if self.rpe_target is not None and not (
            self.rpe_target.target_rpe_min
            <= self.expected_rpe
            <= self.rpe_target.target_rpe_max
        ):
            raise ValueError("Segment RPE must fall within its RPE target.")

    @property
    def zone(self) -> TrainingZone:
        """Backward-compatible access for true zone-target segments only."""
        if self.zone_target is None:
            raise ValueError("A protocol target deliberately has no training zone.")
        return self.zone_target


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
    explicit_scheduling_only: bool = False

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
                        zone=segment.zone_target,
                        is_swim_technique=segment.is_swim_technique,
                        explicit_bucket=(
                            segment.protocol_target.intensity_bucket
                            if segment.protocol_target is not None
                            else segment.rpe_target.intensity_bucket
                            if segment.rpe_target is not None
                            else None
                        ),
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


def as_rpe_guided_template(template: WorkoutTemplate) -> WorkoutTemplate:
    """Remove numeric zone targets while preserving reviewed RPE and private load.

    Protocol-targeted segments already are zone-independent and remain unchanged.
    This projection is deterministic and never alters the durable catalog version.
    """

    segments: list[WorkoutSegment] = []
    for segment in template.segments:
        if segment.protocol_target is not None or segment.rpe_target is not None:
            segments.append(segment)
            continue
        assert segment.zone_target is not None
        guidance = rpe_zone(template.discipline, segment.zone_target)
        bucket = classify_workout(
            WorkoutIntensity(
                (
                    IntensitySegment(
                        duration=DurationMinutes(segment.duration_minutes),
                        zone=segment.zone_target,
                        is_swim_technique=segment.is_swim_technique,
                    ),
                )
            )
        )
        segments.append(
            replace(
                segment,
                instructions=(
                    f"{segment.name}: volg {guidance.display_label}; "
                    f"{guidance.description} "
                    "gebruik geen onbevestigde numerieke zones."
                ),
                expected_rpe=min(
                    max(segment.expected_rpe, guidance.rpe_min), guidance.rpe_max
                ),
                zone_target=None,
                rpe_target=RpeTarget(
                    target_rpe_min=guidance.rpe_min,
                    target_rpe_max=guidance.rpe_max,
                    intensity_bucket=bucket,
                ),
            )
        )
    projected_segments = tuple(segments)
    minimum_rpe, maximum_rpe = _template_rpe_range(projected_segments)
    return replace(
        template,
        expected_rpe_min=minimum_rpe,
        expected_rpe_max=maximum_rpe,
        zone_requirements=(),
        segments=projected_segments,
    )


def _template_rpe_range(
    segments: tuple[WorkoutSegment, ...],
) -> tuple[int, int]:
    """Return the complete execution-target RPE range for some segments."""
    minimum_rpe = min(
        (
            segment.protocol_target.target_rpe_min
            if segment.protocol_target is not None
            else segment.rpe_target.target_rpe_min
            if segment.rpe_target is not None
            else segment.expected_rpe
        )
        for segment in segments
    )
    maximum_rpe = max(
        (
            segment.protocol_target.target_rpe_max
            if segment.protocol_target is not None
            else segment.rpe_target.target_rpe_max
            if segment.rpe_target is not None
            else segment.expected_rpe
        )
        for segment in segments
    )
    return minimum_rpe, maximum_rpe


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
        zone_target=TrainingZone(zone),
        expected_rpe=rpe,
        distance_meters=distance,
        is_swim_technique=technique,
    )


def _protocol_segment(
    sequence: int,
    name: str,
    minutes: str,
    rpe_min: int,
    rpe_max: int,
    intensity_bucket: IntensityBucket,
    *,
    protocol_id: str,
    segment_id: str,
    purpose: str,
    optional: bool = False,
) -> WorkoutSegment:
    """Create a reviewed instruction target without manufacturing a zone."""
    return WorkoutSegment(
        sequence=sequence,
        name=name,
        instructions=purpose,
        duration_minutes=Decimal(minutes),
        expected_rpe=(rpe_min + rpe_max) // 2,
        protocol_target=ProtocolTarget(
            protocol_id=protocol_id,
            segment_id=segment_id,
            target_rpe_min=rpe_min,
            target_rpe_max=rpe_max,
            intensity_bucket=intensity_bucket,
            optional=optional,
        ),
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
    explicit_scheduling_only: bool = False,
) -> WorkoutTemplate:
    duration = sum((segment.duration_minutes for segment in segments), Decimal(0))
    minimum_rpe, maximum_rpe = _template_rpe_range(segments)
    workout = WorkoutIntensity(
        tuple(
            IntensitySegment(
                duration=DurationMinutes(segment.duration_minutes),
                zone=segment.zone_target,
                is_swim_technique=segment.is_swim_technique,
                explicit_bucket=(
                    segment.protocol_target.intensity_bucket
                    if segment.protocol_target is not None
                    else segment.rpe_target.intensity_bucket
                    if segment.rpe_target is not None
                    else None
                ),
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
        explicit_scheduling_only=explicit_scheduling_only,
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

PHASE_8_5_PROTOCOL_ADDITIONS: tuple[WorkoutTemplate, ...] = (
    _template(
        id="54000000-0000-0000-0000-000000000008",
        key="50000000-0000-0000-0000-000000000008",
        version=1,
        discipline=Discipline.BIKE,
        name="Week-1 fietskalibratie",
        description=(
            "Submaximale fietskalibratie op protocol en RPE, zonder verzonnen zones."
        ),
        phases=(TrainingPhase.BASE,),
        requirements=(),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _protocol_segment(
                1,
                "Warming-up",
                "15",
                2,
                3,
                IntensityBucket.LOW,
                protocol_id="start23_week1_bike_calibration_v1",
                segment_id="warmup",
                purpose="Rustig opwarmen volgens het kalibratieprotocol.",
            ),
            _protocol_segment(
                2,
                "Comfortabel blok",
                "20",
                3,
                4,
                IntensityBucket.LOW,
                protocol_id="start23_week1_bike_calibration_v1",
                segment_id="comfortable_20min",
                purpose="Rijd comfortabel en gelijkmatig; registreer de observaties.",
            ),
            _protocol_segment(
                3,
                "Gestaag blok (optioneel)",
                "10",
                5,
                6,
                IntensityBucket.HIGH,
                protocol_id="start23_week1_bike_calibration_v1",
                segment_id="steady_10min_optional",
                purpose="Voer alleen uit als het comfortabele blok goed voelde.",
                optional=True,
            ),
            _protocol_segment(
                4,
                "Cooling-down",
                "10",
                1,
                2,
                IntensityBucket.LOW,
                protocol_id="start23_week1_bike_calibration_v1",
                segment_id="cooldown",
                purpose="Rustig uitrijden en daarna sessie-RPE registreren.",
            ),
        ),
    ),
)

PHASE_11_FIELD_TEST_ADDITIONS: tuple[WorkoutTemplate, ...] = (
    _template(
        id="55000000-0000-0000-0000-000000000009",
        key="50000000-0000-0000-0000-000000000009",
        version=1,
        discipline=Discipline.RUN,
        name="Loopdrempel 30-minuten veldtest",
        description="Beoordeelde veldtest op protocol en RPE; alleen na dagkeuze.",
        phases=(TrainingPhase.BASE, TrainingPhase.BUILD),
        requirements=(),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        explicit_scheduling_only=True,
        segments=(
            _protocol_segment(
                1,
                "Rustige opwarming",
                "15",
                2,
                3,
                IntensityBucket.LOW,
                protocol_id="start23_run_threshold_30min_v1",
                segment_id="warmup",
                purpose="Rustig lopen; volledige zinnen mogelijk.",
            ),
            _protocol_segment(
                2,
                "Korte versnellingen",
                "5",
                5,
                7,
                IntensityBucket.HIGH,
                protocol_id="start23_run_threshold_30min_v1",
                segment_id="strides",
                purpose="Korte gecontroleerde versnellingen; niet maximaal.",
            ),
            _protocol_segment(
                3,
                "30-minuten tijdrit",
                "30",
                8,
                9,
                IntensityBucket.HIGH,
                protocol_id="start23_run_threshold_30min_v1",
                segment_id="test_30min",
                purpose="Zo hard mogelijk maar gelijkmatig; geen sprintstart.",
            ),
            _protocol_segment(
                4,
                "Uitlopen",
                "10",
                1,
                2,
                IntensityBucket.LOW,
                protocol_id="start23_run_threshold_30min_v1",
                segment_id="cooldown",
                purpose="Zeer rustig uitlopen en sessie-RPE registreren.",
            ),
        ),
    ),
    _template(
        id="55000000-0000-0000-0000-000000000010",
        key="50000000-0000-0000-0000-000000000010",
        version=1,
        discipline=Discipline.BIKE,
        name="Fiets FTP 30-minuten veldtest",
        description="Beoordeelde vermogensveldtest; alleen na dagkeuze.",
        phases=(TrainingPhase.BASE, TrainingPhase.BUILD),
        requirements=(),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        explicit_scheduling_only=True,
        segments=(
            _protocol_segment(
                1,
                "Opwarming",
                "20",
                2,
                4,
                IntensityBucket.LOW,
                protocol_id="start23_bike_ftp_30min_v1",
                segment_id="warmup",
                purpose="Rustig opbouwen met korte gecontroleerde versnellingen.",
            ),
            _protocol_segment(
                2,
                "30-minuten vermogenstest",
                "30",
                8,
                9,
                IntensityBucket.HIGH,
                protocol_id="start23_bike_ftp_30min_v1",
                segment_id="test_30min",
                purpose=(
                    "Zo hard mogelijk maar gelijkmatig; vermijd pieken en vrijloop."
                ),
            ),
            _protocol_segment(
                3,
                "Cooling-down",
                "10",
                1,
                2,
                IntensityBucket.LOW,
                protocol_id="start23_bike_ftp_30min_v1",
                segment_id="cooldown",
                purpose="Zeer rustig uitfietsen en sessie-RPE registreren.",
            ),
        ),
    ),
    _template(
        id="55000000-0000-0000-0000-000000000011",
        key="50000000-0000-0000-0000-000000000011",
        version=1,
        discipline=Discipline.BIKE,
        name="Fiets drempelhartslag veldtest",
        description="Beoordeelde hartslagveldtest; alleen na dagkeuze.",
        phases=(TrainingPhase.BASE, TrainingPhase.BUILD),
        requirements=(),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        explicit_scheduling_only=True,
        segments=(
            _protocol_segment(
                1,
                "Opwarming",
                "20",
                2,
                4,
                IntensityBucket.LOW,
                protocol_id="start23_bike_fthr_20min_v1",
                segment_id="warmup",
                purpose="Rustig opbouwen met korte versnellingen.",
            ),
            _protocol_segment(
                2,
                "20-minuten tijdrit",
                "20",
                8,
                9,
                IntensityBucket.HIGH,
                protocol_id="start23_bike_fthr_20min_v1",
                segment_id="test_20min",
                purpose="Gelijkmatige zware solo-inspanning; geen sprintstart.",
            ),
            _protocol_segment(
                3,
                "Cooling-down",
                "10",
                1,
                2,
                IntensityBucket.LOW,
                protocol_id="start23_bike_fthr_20min_v1",
                segment_id="cooldown",
                purpose="Zeer rustig uitfietsen en sessie-RPE registreren.",
            ),
        ),
    ),
)


def _canonical_protocol_version(
    template: WorkoutTemplate,
    *,
    id: str,
) -> WorkoutTemplate:
    """Create an immutable successor whose targets use reviewed RPE zones."""
    segments: list[WorkoutSegment] = []
    for segment in template.segments:
        assert segment.protocol_target is not None
        target = segment.protocol_target
        zone = (
            TrainingZone.ZONE_2
            if (target.target_rpe_min, target.target_rpe_max) == (3, 4)
            else zone_for_rpe_value(segment.expected_rpe)
        )
        guidance = rpe_zone(template.discipline, zone)
        segments.append(
            replace(
                segment,
                instructions=(
                    f"{segment.instructions} {guidance.display_label}: "
                    f"{guidance.description}"
                ),
                expected_rpe=min(
                    max(segment.expected_rpe, guidance.rpe_min), guidance.rpe_max
                ),
                protocol_target=replace(
                    target,
                    target_rpe_min=guidance.rpe_min,
                    target_rpe_max=guidance.rpe_max,
                ),
            )
        )
    return _template(
        id=id,
        key=str(template.template_key),
        version=template.version + 1,
        discipline=template.discipline,
        name=template.name,
        description=template.description,
        phases=template.training_phases,
        requirements=template.zone_requirements,
        fallback=template.fallback_compatibility,
        segments=tuple(segments),
        distance_meters=template.distance_meters,
        explicit_scheduling_only=template.explicit_scheduling_only,
    )


MVP_CATALOG_ADDITIONS: tuple[WorkoutTemplate, ...] = (
    _template(
        id="52000000-0000-0000-0000-000000000001",
        key="50000000-0000-0000-0000-000000000001",
        version=2,
        discipline=Discipline.SWIM,
        name="Aerobic swim",
        description="Relaxed continuous swimming for aerobic endurance.",
        phases=(TrainingPhase.BASE, TrainingPhase.RECOVERY),
        requirements=(ZoneRequirement.PACE,),
        fallback=FallbackCompatibility.INCOMPATIBLE,
        segments=(
            _segment(1, "Easy warm-up", "10", 1, 2, distance=400),
            _segment(2, "Aerobic swimming", "20", 2, 4, distance=800),
            _segment(3, "Easy finish", "10", 1, 2, distance=400),
        ),
        distance_meters=1600,
    ),
    _canonical_protocol_version(
        PHASE_8_5_PROTOCOL_ADDITIONS[0],
        id="56000000-0000-0000-0000-000000000008",
    ),
    _canonical_protocol_version(
        PHASE_11_FIELD_TEST_ADDITIONS[0],
        id="56000000-0000-0000-0000-000000000009",
    ),
    _canonical_protocol_version(
        PHASE_11_FIELD_TEST_ADDITIONS[1],
        id="56000000-0000-0000-0000-000000000010",
    ),
    _canonical_protocol_version(
        PHASE_11_FIELD_TEST_ADDITIONS[2],
        id="56000000-0000-0000-0000-000000000011",
    ),
)

CURRENT_CATALOG = (
    REVIEWED_CATALOG
    + MVP_CATALOG_ADDITIONS
    + PHASE_6_CATALOG_ADDITIONS
    + PHASE_8_5_PROTOCOL_ADDITIONS
    + PHASE_11_FIELD_TEST_ADDITIONS
)


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
