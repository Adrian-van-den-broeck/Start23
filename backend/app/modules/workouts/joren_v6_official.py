"""Inactive official successor view; never registered in the active repository."""

from dataclasses import dataclass, field
from decimal import Context, Decimal, localcontext
from typing import Literal

from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.physiology.planned_v6 import OfficialPlannedLoad, calculate_v6
from app.modules.physiology.rpe_zones import SESSION_MAPPING_V2, rpe_zone
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    WorkoutSegment,
    WorkoutTemplate,
    ZoneRequirement,
)
from app.modules.workouts.joren_draft import SwimDistance, TimedZone, WallRest
from app.modules.workouts.joren_v6_phase import (
    PhaseCatalog,
    PhaseTemplate,
    build_phase_catalog,
)


@dataclass(frozen=True, slots=True)
class V6Template(WorkoutTemplate):
    source_revision: PhaseTemplate = field(repr=False, kw_only=True)
    official: OfficialPlannedLoad = field(repr=False, kw_only=True)
    activation_status: Literal["INACTIVE"] = field(default="INACTIVE", init=False)


def official_catalog(catalog: PhaseCatalog | None = None) -> tuple[V6Template, ...]:
    with localcontext(Context(prec=50)):
        return _official_catalog(catalog)


def _official_catalog(catalog: PhaseCatalog | None) -> tuple[V6Template, ...]:
    rows = (catalog or build_phase_catalog()).templates
    result = []
    for source in rows:
        record = source.predecessor
        sport = Discipline(record.sport)
        quantities = tuple(
            sum(
                (
                    e.meters if isinstance(e, SwimDistance) else e.seconds
                    for e in record.events
                    if not isinstance(e, WallRest) and e.zone == z
                ),
                Decimal(0),
            )
            for z in range(1, 6)
        )
        official = calculate_v6(sport, quantities)
        segments: list[WorkoutSegment] = []
        for event in record.events:
            if isinstance(event, WallRest):
                # Legacy public segment DTO cannot represent stationary rest.
                # Preserve it verbatim in adjacent instructions and the complete
                # private typed sidecar; never fabricate a zone, RPE or distance.
                from dataclasses import replace

                segments[-1] = replace(
                    segments[-1],
                    instructions=segments[-1].instructions + " | " + event.raw_token,
                )
                continue
            guidance = rpe_zone(
                sport, TrainingZone(event.zone), version=SESSION_MAPPING_V2
            )
            segments.append(
                WorkoutSegment(
                    len(segments) + 1,
                    event.raw_token,
                    event.raw_token,
                    event.seconds / 60 if isinstance(event, TimedZone) else None,
                    guidance.rpe_min,
                    zone_target=TrainingZone(event.zone),
                    distance_meters=int(event.meters)
                    if isinstance(event, SwimDistance)
                    else None,
                )
            )
        result.append(
            V6Template(
                id=source.revision_id,
                template_key=source.logical_key,
                version=source.version,
                discipline=sport,
                name=record.original_training_name,
                description=record.original_training_focus,
                duration_minutes=record.original_measure
                if sport is not Discipline.SWIM
                else None,
                distance_meters=int(record.original_measure)
                if sport is Discipline.SWIM
                else None,
                intensity_bucket=IntensityBucket.HIGH
                if any(e.zone > 2 for e in record.events if not isinstance(e, WallRest))
                else IntensityBucket.LOW,
                expected_rpe_min=min(s.expected_rpe for s in segments),
                expected_rpe_max=max(s.expected_rpe for s in segments) + 1,
                training_phases=source.phases,
                zone_requirements=(
                    ZoneRequirement.PACE
                    if sport is Discipline.SWIM
                    else ZoneRequirement.HEART_RATE,
                ),
                fallback_compatibility=FallbackCompatibility.INCOMPATIBLE
                if sport is Discipline.SWIM
                else FallbackCompatibility.COMPATIBLE,
                segments=tuple(segments),
                internal_planned_load=InternalLoad(official.value),
                source_catalog=source.source_release,
                source_workout_id=record.original_workout_id,
                source_revision=source,
                official=official,
            )
        )
    return tuple(result)
