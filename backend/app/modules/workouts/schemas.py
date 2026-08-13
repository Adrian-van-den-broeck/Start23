"""Public TSS-free workout catalog schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.physiology.models import Discipline, IntensityBucket, TrainingZone
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
)


class PublicWorkoutModel(BaseModel):
    """Reject accidental internal fields in public catalog models."""

    model_config = ConfigDict(extra="forbid")


class WorkoutSegmentResponse(PublicWorkoutModel):
    """Athlete-facing ordered workout instruction."""

    sequence: int = Field(ge=1)
    name: str
    instructions: str
    duration_minutes: Decimal = Field(gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    zone: TrainingZone
    expected_rpe: int = Field(ge=1, le=10)
    is_swim_technique: bool


class WorkoutTemplateResponse(PublicWorkoutModel):
    """Athlete-facing immutable catalog version without hidden load."""

    id: UUID
    template_key: UUID
    version: int = Field(ge=1)
    discipline: Discipline
    name: str
    description: str
    duration_minutes: Decimal = Field(gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    intensity_bucket: IntensityBucket
    expected_rpe_min: int = Field(ge=1, le=10)
    expected_rpe_max: int = Field(ge=1, le=10)
    training_phases: tuple[TrainingPhase, ...]
    zone_requirements: tuple[ZoneRequirement, ...]
    fallback_compatibility: FallbackCompatibility
    segments: tuple[WorkoutSegmentResponse, ...]

    @classmethod
    def from_domain(cls, template: WorkoutTemplate) -> "WorkoutTemplateResponse":
        """Map an internal template field-by-field across the TSS boundary."""
        values = {
            field: getattr(template, field)
            for field in cls.model_fields
            if field != "segments"
        }
        values["segments"] = tuple(
            {
                field: getattr(segment, field)
                for field in WorkoutSegmentResponse.model_fields
            }
            for segment in template.segments
        )
        return cls.model_validate(values)


class WorkoutCatalogResponse(PublicWorkoutModel):
    """Current reviewed catalog versions."""

    templates: tuple[WorkoutTemplateResponse, ...]
