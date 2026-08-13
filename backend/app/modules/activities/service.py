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
from app.modules.physiology.models import DurationMinutes, IntensityBucket, InternalLoad
from app.modules.physiology.specification import PHASE_3_RULESET_V3

from .repository import ActivityRepository, JsonObject
from .schemas import ActivityResponse, ActivityRpeSubmission, ActivitySummaryInput


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
                load=InternalLoad(Decimal(str(planned["planned_tss"]))),
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
        context = await self._repository.fetch_processing_context(
            athlete_id,
            activity_id,
        )
        try:
            duration = DurationMinutes(Decimal(str(context["duration_minutes"])))
        except (KeyError, TypeError, ValueError) as error:
            raise ActivityDomainError("Stored activity duration is invalid.") from error
        result = classify_activity_match(
            duration=duration,
            rpe=submission.rpe,
            planned=self._expectation(context),
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
            "realized_tss": str(result.realized_load.value),
            "calculation_method": "actual_rpe_times_duration_hours",
            "ruleset_version": PHASE_3_RULESET_V3.version.value,
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
