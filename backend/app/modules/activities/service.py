"""Application orchestration for canonical activity and RPE feedback."""

import hashlib
import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.physiology.activity import (
    PlannedActivityExpectation,
    classify_activity_match,
)
from app.modules.physiology.joren import (
    VERSION,
    ZoneLoad,
    average_hr_zone_load,
    zone_load,
)
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    IntensityBucket,
    InternalLoad,
    RulesetVersion,
    TrainingZone,
)
from app.modules.physiology.specification import PHASE_3_RULESET_V3
from app.modules.physiology.zones import (
    CalculatedZoneBoundary,
    CalculatedZoneMetricProfile,
    ZoneBoundary,
    ZoneMetric,
    ZoneMetricKind,
    classify_calculated_zone_value,
    classify_zone_value,
)

from .repository import ActivityRepository, JsonObject
from .schemas import (
    ActivityMatchConfirmation,
    ActivityResponse,
    ActivityRpeSubmission,
    ActivitySummaryInput,
)


class ActivityDomainError(ValueError):
    """Stored or submitted activity state is inconsistent."""


class ActivityService:
    """Coordinate validation, pure decisions, and owner-scoped persistence."""

    def __init__(self, repository: ActivityRepository) -> None:
        self._repository = repository

    @staticmethod
    def _response(row: Mapping[str, Any]) -> ActivityResponse:
        try:
            return ActivityResponse.model_validate(row)
        except (KeyError, ValueError) as error:
            raise ActivityDomainError("Stored activity data is invalid.") from error

    @staticmethod
    def _fingerprint(payload: JsonObject) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def create(
        self,
        access_token: str,
        idempotency_key: UUID,
        summary: ActivitySummaryInput,
    ) -> ActivityResponse:
        payload = summary.model_dump(mode="json", exclude_none=True)
        row = await self._repository.create_activity(
            access_token,
            idempotency_key,
            self._fingerprint(payload),
            payload,
        )
        return self._response(row)

    async def get(self, access_token: str, activity_id: UUID) -> ActivityResponse:
        return self._response(
            await self._repository.fetch_activity(access_token, activity_id)
        )

    async def list(
        self,
        access_token: str,
        *,
        pending_rpe: bool = False,
    ) -> tuple[ActivityResponse, ...]:
        return tuple(
            self._response(row)
            for row in await self._repository.list_activities(
                access_token,
                pending_rpe=pending_rpe,
            )
        )

    @staticmethod
    def _expectation(context: Mapping[str, Any]) -> PlannedActivityExpectation | None:
        planned = context.get("planned")
        if planned is None:
            return None
        if not isinstance(planned, dict):
            raise ActivityDomainError("Stored planned workout context is invalid.")
        try:
            return PlannedActivityExpectation(
                load=(
                    InternalLoad(Decimal(str(planned["planned_tss"])))
                    if planned.get("planned_tss") is not None
                    else None
                ),
                expected_rpe_min=int(planned["expected_rpe_min"]),
                expected_rpe_max=int(planned["expected_rpe_max"]),
                intensity_bucket=IntensityBucket(str(planned["intensity_bucket"])),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ActivityDomainError(
                "Stored planned workout context is invalid."
            ) from error

    async def submit_rpe(
        self,
        athlete_id: UUID,
        activity_id: UUID,
        submission: ActivityRpeSubmission,
    ) -> ActivityResponse:
        if submission.average_heart_rate_bpm is not None:
            await self._repository.save_rpe_heart_rate_observation(
                athlete_id,
                activity_id,
                submission.average_heart_rate_bpm,
            )
        context = await self._repository.fetch_processing_context(
            athlete_id,
            activity_id,
        )
        if (
            context.get("requires_heart_rate_observation")
            and context.get("average_heart_rate_bpm") is None
        ):
            raise ActivityDomainError(
                "An assigned RPE-guided workout requires an average heart-rate "
                "observation in bpm before session RPE can be completed."
            )
        try:
            duration = DurationMinutes(Decimal(str(context["duration_minutes"] or 0)))
        except (KeyError, TypeError, ValueError) as error:
            raise ActivityDomainError("Stored activity duration is invalid.") from error
        legacy_revision = (
            context.get("rpe") is not None
            and context.get("load_ruleset_version") != VERSION.value
        )
        stored = context.get("private_load_snapshot")
        preserve_measurement = (
            context.get("rpe") is not None
            and isinstance(stored, dict)
            and stored.get("ruleset_version") == VERSION.value
        )
        raw_zones = context.get("zone_minutes")
        measurement = (
            None
            if legacy_revision
            else zone_load(
                discipline=Discipline(str(context["discipline"])),
                total_minutes=(
                    duration.value
                    if context.get("duration_minutes") is not None
                    else None
                ),
                minutes_by_zone=(
                    tuple(Decimal(str(value)) for value in raw_zones)
                    if isinstance(raw_zones, list)
                    else None
                ),
            )
        )
        # Observed zone time, including partial coverage, always takes precedence.
        if (
            not legacy_revision
            and not preserve_measurement
            and raw_zones is None
            and duration.value > 0
        ):
            profile_data = context.get("known_hr_profile")
            average_hr = context.get("average_heart_rate_bpm")
            if isinstance(profile_data, dict) and average_hr is not None:
                try:
                    profile = CalculatedZoneMetricProfile(
                        metric=ZoneMetric(
                            Discipline(str(context["discipline"])),
                            ZoneMetricKind(str(profile_data["metric_kind"])),
                            Decimal(str(profile_data["source_value"])),
                        ),
                        boundaries=tuple(
                            CalculatedZoneBoundary(
                                TrainingZone(int(boundary["zone_number"])),
                                Decimal(str(boundary["lower_value"]))
                                if boundary.get("lower_value") is not None
                                else None,
                                Decimal(str(boundary["upper_value"]))
                                if boundary.get("upper_value") is not None
                                else None,
                            )
                            for boundary in profile_data["boundaries"]
                        ),
                        is_primary=True,
                        zone_model_version=RulesetVersion(
                            str(profile_data["zone_model_version"])
                        ),
                    )
                    assigned_zone = (
                        classify_zone_value(
                            metric_kind=profile.metric.kind,
                            value=Decimal(str(average_hr)),
                            boundaries=tuple(
                                ZoneBoundary(
                                    boundary.zone, boundary.lower, boundary.upper
                                )
                                for boundary in profile.boundaries
                                if boundary.lower is not None
                                and boundary.upper is not None
                            ),
                        )
                        if profile_data.get("boundary_kind") == "manual"
                        else classify_calculated_zone_value(
                            profile=profile, value=Decimal(str(average_hr))
                        ).zone
                    )
                    measurement = average_hr_zone_load(
                        discipline=profile.metric.discipline,
                        total_minutes=duration.value,
                        zone=assigned_zone.value,
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise ActivityDomainError(
                        "Stored heart-rate zone context is invalid."
                    ) from error
        if preserve_measurement and isinstance(stored, dict):
            measurement = ZoneLoad(
                InternalLoad(Decimal(str(stored["realized_tss"])))
                if stored.get("realized_tss") is not None
                else None,
                Decimal(str(stored["total_minutes"]))
                if stored.get("total_minutes") is not None
                else None,
                Decimal(str(stored["valid_minutes"])),
                Decimal(str(stored["coverage_ratio"]))
                if stored.get("coverage_ratio") is not None
                else None,
                str(stored["load_status"]),
                str(stored["calculation_method"]),
                VERSION,
                int(stored["assigned_zone"])
                if stored.get("assigned_zone") is not None
                else None,
            )
        result = classify_activity_match(
            duration=duration,
            rpe=submission.rpe,
            planned=self._expectation(context),
            measurement=measurement,
        )
        payload = {
            "rpe": submission.rpe,
            "qualitative_result": result.result.value,
            "public_message": result.public_message,
            "correction_reason": (
                result.correction_reason.value
                if result.correction_reason is not None
                else None
            ),
            "realized_tss": str(result.realized_load.value)
            if result.realized_load is not None
            else None,
            "calculation_method": "actual_rpe_times_duration_hours"
            if legacy_revision
            else measurement.calculation_method
            if measurement is not None
            else "observed_zone_minutes",
            "ruleset_version": str(
                context.get("load_ruleset_version") or PHASE_3_RULESET_V3.version.value
            )
            if legacy_revision
            else VERSION.value,
            **(
                {
                    "total_minutes": str(measurement.total_minutes)
                    if measurement.total_minutes is not None
                    else None,
                    "valid_minutes": str(measurement.valid_minutes),
                    "coverage_ratio": str(measurement.coverage_ratio)
                    if measurement.coverage_ratio is not None
                    else None,
                    "load_status": measurement.status,
                    "assigned_zone": measurement.assigned_zone,
                    "zone_profile_id": (
                        stored.get("zone_profile_id")
                        if isinstance(stored, dict)
                        else context.get("known_hr_profile_id")
                    )
                    if measurement.assigned_zone is not None
                    else None,
                    "average_heart_rate_bpm": str(
                        stored.get("average_heart_rate_bpm")
                        if isinstance(stored, dict)
                        else context["average_heart_rate_bpm"]
                    )
                    if measurement.assigned_zone is not None
                    else None,
                }
                if measurement is not None
                else {}
            ),
        }
        row = (
            await self._repository.revise_activity_rpe(
                athlete_id,
                activity_id,
                payload,
            )
            if context.get("rpe") is not None
            else await self._repository.complete_activity_rpe(
                athlete_id,
                activity_id,
                payload,
            )
        )
        return self._response(row)

    async def confirm_match(
        self,
        access_token: str,
        activity_id: UUID,
        confirmation: ActivityMatchConfirmation,
    ) -> ActivityResponse:
        """Apply only the exact planned-workout match chosen by the athlete."""
        return self._response(
            await self._repository.confirm_planned_workout_match(
                access_token,
                activity_id,
                confirmation.planned_workout_id,
            )
        )
