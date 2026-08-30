"""Strict TSS-free Phase 7 activity API contracts."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.physiology.models import Discipline


class PublicActivityModel(BaseModel):
    """Prevent internal persistence fields from entering public responses."""

    model_config = ConfigDict(extra="forbid")


class ActivityMetricInput(PublicActivityModel):
    """Optional canonical summaries; no raw telemetry is accepted in Phase 7."""

    average_heart_rate_bpm: int | None = Field(default=None, ge=20, le=260)
    max_heart_rate_bpm: int | None = Field(default=None, ge=20, le=260)
    normalized_power_watts: int | None = Field(default=None, gt=0, le=3000)
    average_speed_kmh: Decimal | None = Field(default=None, gt=0, le=300)
    max_speed_kmh: Decimal | None = Field(default=None, gt=0, le=300)
    average_pace_seconds_per_km: Decimal | None = Field(
        default=None,
        gt=0,
        le=3600,
    )
    low_intensity_minutes: Decimal | None = Field(default=None, ge=0, le=1440)
    high_intensity_minutes: Decimal | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def validate_metric_relationships(self) -> "ActivityMetricInput":
        if (
            self.average_heart_rate_bpm is not None
            and self.max_heart_rate_bpm is not None
            and self.average_heart_rate_bpm > self.max_heart_rate_bpm
        ):
            raise ValueError("average heart rate cannot exceed maximum heart rate")
        if (
            self.average_speed_kmh is not None
            and self.max_speed_kmh is not None
            and self.average_speed_kmh > self.max_speed_kmh
        ):
            raise ValueError("average speed cannot exceed maximum speed")
        intensity_values = (
            self.low_intensity_minutes,
            self.high_intensity_minutes,
        )
        if (intensity_values[0] is None) != (intensity_values[1] is None):
            raise ValueError("low and high intensity minutes must be supplied together")
        if not any(
            value is not None
            for value in (
                self.average_heart_rate_bpm,
                self.max_heart_rate_bpm,
                self.normalized_power_watts,
                self.average_speed_kmh,
                self.max_speed_kmh,
                self.average_pace_seconds_per_km,
                *intensity_values,
            )
        ):
            raise ValueError("at least one activity metric is required")
        return self


class ActivitySummaryInput(PublicActivityModel):
    """Authenticated phase-one canonical completed-activity summary."""

    planned_workout_id: UUID | None = None
    planned_external_activity_id: UUID | None = None
    discipline: Discipline
    started_at: datetime
    timezone: str = Field(min_length=1, max_length=100)
    duration_minutes: Decimal = Field(gt=0, le=1440, max_digits=8)
    distance_meters: int | None = Field(default=None, gt=0, le=1_000_000)
    elevation_gain_meters: int | None = Field(default=None, ge=0, le=100_000)
    metrics: ActivityMetricInput | None = None

    @model_validator(mode="after")
    def validate_summary(self) -> "ActivitySummaryInput":
        if (
            self.planned_workout_id is not None
            and self.planned_external_activity_id is not None
        ):
            raise ValueError(
                "planned workout and external activity are mutually exclusive"
            )
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be an IANA timezone") from error
        if (
            self.discipline is Discipline.SWIM
            and self.elevation_gain_meters is not None
        ):
            raise ValueError("swim activities cannot include elevation gain")
        if self.metrics is not None:
            if (
                self.metrics.normalized_power_watts is not None
                and self.discipline is not Discipline.BIKE
            ):
                raise ValueError("normalized power is supported only for bike")
            if (
                self.metrics.average_speed_kmh is not None
                or self.metrics.max_speed_kmh is not None
            ) and self.discipline is not Discipline.BIKE:
                raise ValueError("speed telemetry is supported only for bike")
            if (
                self.metrics.average_pace_seconds_per_km is not None
                and self.discipline is Discipline.BIKE
            ):
                raise ValueError("pace is supported only for swim and run")
            low = self.metrics.low_intensity_minutes
            high = self.metrics.high_intensity_minutes
            if (
                low is not None
                and high is not None
                and low + high > self.duration_minutes
            ):
                raise ValueError("classified intensity minutes cannot exceed duration")
        return self


class ActivityMetricResponse(ActivityMetricInput):
    """Persisted safe metric summary."""


class ActivityResponse(PublicActivityModel):
    """Owner-scoped activity without planned or realized load values."""

    id: UUID
    planned_workout_id: UUID | None
    discipline: Discipline
    source: Literal["canonical_summary"]
    started_at: datetime
    timezone: str
    duration_minutes: Decimal
    distance_meters: int | None
    elevation_gain_meters: int | None
    rpe: int | None = Field(default=None, ge=1, le=10)
    rpe_submitted_at: datetime | None
    match_status: Literal["matched", "unmatched"]
    processing_state: Literal["awaiting_rpe", "complete"]
    qualitative_result: Literal[
        "awaiting_rpe",
        "perfect_match",
        "overshoot",
        "hidden_fatigue",
        "deviation",
        "unplanned",
    ]
    public_message: str
    correction_proposal_id: UUID | None
    metrics: ActivityMetricResponse | None
    created_at: datetime
    updated_at: datetime


class ActivityRpeSubmission(PublicActivityModel):
    """Athlete RPE, correctable only during its current local week."""

    rpe: int = Field(ge=1, le=10)
    average_heart_rate_bpm: int | None = Field(default=None, ge=20, le=260)


class ActivityMatchConfirmation(PublicActivityModel):
    """Explicit athlete confirmation for one suggested planned-workout match."""

    planned_workout_id: UUID
