"""Public TSS-free workout catalog schemas."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.modules.physiology.models import Discipline, IntensityBucket, TrainingZone
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    ProtocolTarget,
    RpeTarget,
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
)


class PublicWorkoutModel(BaseModel):
    """Reject accidental internal fields in public catalog models."""

    model_config = ConfigDict(extra="forbid")


class ProtocolTargetResponse(PublicWorkoutModel):
    """Reviewed protocol instruction that deliberately does not imply a zone."""

    protocol_id: str
    segment_id: str
    target_rpe_min: int = Field(ge=1, le=10)
    target_rpe_max: int = Field(ge=1, le=10)
    intensity_bucket: IntensityBucket
    optional: bool


class RpeTargetResponse(PublicWorkoutModel):
    """Zone-free target for a discipline without a confirmed profile."""

    target_rpe_min: int = Field(ge=1, le=10)
    target_rpe_max: int = Field(ge=1, le=10)
    intensity_bucket: IntensityBucket
    heart_rate_observation_required: Literal[True] = True


class WorkoutSegmentResponse(PublicWorkoutModel):
    """Athlete-facing ordered workout instruction."""

    sequence: int = Field(ge=1)
    name: str
    instructions: str
    duration_minutes: Decimal = Field(gt=0)
    distance_meters: int | None = Field(default=None, gt=0)
    zone_target: TrainingZone | None = Field(
        default=None,
        validation_alias=AliasChoices("zone_target", "zone"),
    )
    protocol_target: ProtocolTargetResponse | None = None
    rpe_target: RpeTargetResponse | None = None
    expected_rpe: int = Field(ge=1, le=10)
    is_swim_technique: bool

    @model_validator(mode="after")
    def require_exactly_one_target(self) -> "WorkoutSegmentResponse":
        if (
            sum(
                target is not None
                for target in (self.zone_target, self.protocol_target, self.rpe_target)
            )
            != 1
        ):
            raise ValueError("A segment requires exactly one target.")
        return self


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
                field: (
                    ProtocolTargetResponse.model_validate(
                        {
                            target_field: getattr(segment.protocol_target, target_field)
                            for target_field in ProtocolTargetResponse.model_fields
                        }
                    )
                    if field == "protocol_target"
                    and isinstance(segment.protocol_target, ProtocolTarget)
                    else RpeTargetResponse.model_validate(
                        {
                            target_field: getattr(segment.rpe_target, target_field)
                            for target_field in RpeTargetResponse.model_fields
                        }
                    )
                    if field == "rpe_target"
                    and isinstance(segment.rpe_target, RpeTarget)
                    else getattr(segment, field)
                )
                for field in WorkoutSegmentResponse.model_fields
            }
            for segment in template.segments
        )
        return cls.model_validate(values)


class WorkoutCatalogResponse(PublicWorkoutModel):
    """Current reviewed catalog versions."""

    templates: tuple[WorkoutTemplateResponse, ...]
