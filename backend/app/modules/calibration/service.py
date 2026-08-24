"""Application service for owner-scoped zone setup and calibration."""

import hashlib
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.calibration.domain import (
    CALIBRATION_RULESET_VERSION,
    PROTOCOLS,
    CalibrationObservation,
    DataQuality,
    GuidanceMode,
    ProtocolType,
    SetupRoute,
    SteadyExecution,
    SwimRepetition,
    evaluate_protocol,
    protocols_for_discipline,
)
from app.modules.calibration.repository import CalibrationRepository, JsonObject
from app.modules.calibration.schemas import (
    CalibrationEvaluationRequest,
    CalibrationEvaluationResponse,
    CalibrationObservationCreate,
    CalibrationObservationResponse,
    CalibrationProtocolResponse,
    CalibrationStatusResponse,
    DisciplineSetupInput,
    DisciplineSetupResponse,
    FieldTestSetup,
    KnownValuesSetup,
    ProtocolSegmentResponse,
    RpeOnlySetup,
    ThresholdDecisionResponse,
    ZoneOptionResponse,
)
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.zones import (
    ZONE_MODEL_VERSION,
    CalculatedZoneMetricProfile,
    ZoneBoundary,
    ZoneMetric,
    calculate_zone_profiles,
    validate_zone_profile,
)


class CalibrationDomainError(Exception):
    """Submitted setup or observation violates a deterministic contract."""


_GUIDANCE_BY_DISCIPLINE = {
    Discipline.SWIM: {GuidanceMode.PACE, GuidanceMode.RPE_ONLY},
    Discipline.BIKE: {
        GuidanceMode.POWER,
        GuidanceMode.HEART_RATE,
        GuidanceMode.COMBINED,
        GuidanceMode.RPE_ONLY,
    },
    Discipline.RUN: {
        GuidanceMode.HEART_RATE,
        GuidanceMode.PACE,
        GuidanceMode.COMBINED,
        GuidanceMode.RPE_ONLY,
    },
}
_CALIBRATION_PROTOCOL_BY_DISCIPLINE = {
    Discipline.SWIM: "start23_week1_swim_calibration_v1",
    Discipline.BIKE: "start23_week1_bike_calibration_v1",
    Discipline.RUN: "start23_week1_run_calibration_v1",
}


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CalibrationService:
    """Coordinate strict API models, pure evaluation, and persistence."""

    def __init__(self, repository: CalibrationRepository) -> None:
        self._repository = repository

    @staticmethod
    def zone_options() -> tuple[ZoneOptionResponse, ...]:
        return (
            ZoneOptionResponse(
                setup_route=SetupRoute.KNOWN_VALUES,
                label="Ik ken mijn waarden",
                creates_threshold=False,
                creates_zones=True,
            ),
            ZoneOptionResponse(
                setup_route=SetupRoute.FIELD_TEST,
                label="Ik wil mijn waarden testen",
                creates_threshold=True,
                creates_zones=True,
            ),
            ZoneOptionResponse(
                setup_route=SetupRoute.CALIBRATION_WEEK,
                label="Ik wil rustig beginnen en laten kalibreren",
                creates_threshold=False,
                creates_zones=False,
            ),
            ZoneOptionResponse(
                setup_route=SetupRoute.RPE_ONLY,
                label="Ik wil voorlopig alleen op gevoel trainen",
                creates_threshold=False,
                creates_zones=False,
            ),
        )

    @staticmethod
    def protocols(discipline: Discipline) -> tuple[CalibrationProtocolResponse, ...]:
        return tuple(
            CalibrationProtocolResponse(
                protocol_id=protocol.protocol_id,
                discipline=protocol.discipline,
                protocol_type=protocol.protocol_type,
                version=protocol.version,
                review_status=protocol.review_status,
                result_status_on_success=protocol.result_status_on_success,
                guidance_modes=protocol.guidance_modes,
                segments=tuple(
                    ProtocolSegmentResponse(
                        order=segment.order,
                        segment_id=segment.segment_id,
                        purpose=segment.purpose,
                        duration_seconds=segment.duration_seconds,
                        distance_meters=segment.distance_meters,
                        target_rpe_min=segment.target_rpe_min,
                        target_rpe_max=segment.target_rpe_max,
                        optional=segment.optional,
                    )
                    for segment in protocol.segments
                ),
            )
            for protocol in protocols_for_discipline(discipline)
        )

    @staticmethod
    def _validate_known_values(
        discipline: Discipline,
        setup: KnownValuesSetup,
    ) -> None:
        threshold_kinds = [threshold.metric_kind for threshold in setup.thresholds]
        profile_kinds = [profile.metric_kind for profile in setup.zone_profiles]
        if len(set(threshold_kinds)) != len(threshold_kinds):
            raise CalibrationDomainError("Known threshold metrics must be unique.")
        if len(set(profile_kinds)) != len(profile_kinds):
            raise CalibrationDomainError("Known zone profile metrics must be unique.")
        for threshold in setup.thresholds:
            try:
                ZoneMetric(
                    discipline=discipline,
                    kind=threshold.metric_kind,
                    value=threshold.value,
                )
            except ValueError as error:
                raise CalibrationDomainError(str(error)) from error
        for profile in setup.zone_profiles:
            try:
                metric = ZoneMetric(
                    discipline=discipline,
                    kind=profile.metric_kind,
                    value=next(
                        (
                            threshold.value
                            for threshold in setup.thresholds
                            if threshold.metric_kind is profile.metric_kind
                        ),
                        Decimal(1),
                    ),
                )
                boundaries = tuple(
                    ZoneBoundary(
                        zone=TrainingZone(boundary.zone_number),
                        lower=boundary.lower_value,
                        upper=boundary.upper_value,
                    )
                    for boundary in profile.boundaries
                )
                validate_zone_profile(
                    metric_kind=metric.kind,
                    boundaries=boundaries,
                )
            except ValueError as error:
                raise CalibrationDomainError(str(error)) from error

    @staticmethod
    def _setup_values(
        discipline: Discipline,
        setup: DisciplineSetupInput,
    ) -> JsonObject:
        if setup.guidance_mode not in _GUIDANCE_BY_DISCIPLINE[discipline]:
            raise CalibrationDomainError(
                "Guidance mode is not supported for this discipline."
            )
        protocol_id: str | None = None
        setup_status = "configured"
        threshold_status = "unknown"
        zone_status = "unknown"
        source = "none"
        validation_status = "not_assessed"
        confidence = "not_assessed"
        known_thresholds: list[JsonObject] = []
        known_zone_profiles: list[JsonObject] = []
        pool_length = getattr(setup, "pool_length_meters", None)

        if isinstance(setup, KnownValuesSetup):
            CalibrationService._validate_known_values(discipline, setup)
            threshold_status = "user_provided" if setup.thresholds else "unknown"
            zone_status = (
                "pending_athlete_confirmation" if setup.thresholds else "user_provided"
            )
            source = "user_provided"
            validation_status = "self_reported"
            known_thresholds = [
                threshold.model_dump(mode="json") for threshold in setup.thresholds
            ]
            known_zone_profiles = [
                profile.model_dump(mode="json") for profile in setup.zone_profiles
            ]
        elif isinstance(setup, FieldTestSetup):
            protocol = PROTOCOLS.get(setup.protocol_id)
            if (
                protocol is None
                or protocol.discipline is not discipline
                or protocol.protocol_type is not ProtocolType.FIELD_TEST
            ):
                raise CalibrationDomainError(
                    "Selected field-test protocol is not active for this discipline."
                )
            if setup.guidance_mode.value not in protocol.guidance_modes:
                raise CalibrationDomainError(
                    "Guidance mode is not supported by the selected protocol."
                )
            protocol_id = protocol.protocol_id
            setup_status = "test_pending"
            source = "field_test"
        elif setup.setup_route is SetupRoute.CALIBRATION_WEEK:
            protocol_id = _CALIBRATION_PROTOCOL_BY_DISCIPLINE[discipline]
            setup_status = "calibration_pending"
            source = "week1_calibration"
        elif isinstance(setup, RpeOnlySetup):
            source = "none"

        if (
            discipline is Discipline.SWIM
            and setup.setup_route
            in {SetupRoute.FIELD_TEST, SetupRoute.CALIBRATION_WEEK}
            and pool_length not in {25, 50}
        ):
            raise CalibrationDomainError(
                "Swim field tests and calibration require a 25 m or 50 m pool."
            )
        return {
            "discipline": discipline.value,
            "setup_route": setup.setup_route.value,
            "guidance_mode": setup.guidance_mode.value,
            "setup_status": setup_status,
            "protocol_id": protocol_id,
            "pool_length_meters": pool_length,
            "threshold_status": threshold_status,
            "zone_status": zone_status,
            "source": source,
            "validation_status": validation_status,
            "confidence": confidence,
            "known_thresholds": known_thresholds,
            "known_zone_profiles": known_zone_profiles,
        }

    async def save_setup(
        self,
        access_token: str,
        discipline: Discipline,
        setup: DisciplineSetupInput,
    ) -> DisciplineSetupResponse:
        values = self._setup_values(discipline, setup)
        row = await self._repository.save_setup(access_token, values)
        return self._discipline_setup_response(row)

    @staticmethod
    def _discipline_setup_response(row: JsonObject) -> DisciplineSetupResponse:
        return DisciplineSetupResponse.model_validate(
            {key: row[key] for key in DisciplineSetupResponse.model_fields}
        )

    @staticmethod
    def _evaluation_response(row: JsonObject) -> CalibrationEvaluationResponse:
        values = {
            key: row[key]
            for key in CalibrationEvaluationResponse.model_fields
            if key in row
        }
        values.setdefault("zone_model_version", None)
        values.setdefault("zone_profiles", [])
        return CalibrationEvaluationResponse.model_validate(values)

    @staticmethod
    def _threshold_decision_response(row: JsonObject) -> ThresholdDecisionResponse:
        return ThresholdDecisionResponse.model_validate(
            {
                key: row[key]
                for key in ThresholdDecisionResponse.model_fields
                if key in row
            }
        )

    @staticmethod
    def _zone_profile_values(
        profiles: tuple[CalculatedZoneMetricProfile, ...],
    ) -> list[JsonObject]:
        return [
            {
                "metric_kind": profile.metric.kind.value,
                "source_value": str(profile.metric.value),
                "is_primary": profile.is_primary,
                "boundary_source": "model_derived",
                "zone_model_version": profile.zone_model_version.value,
                "boundaries": [
                    {
                        "zone_number": boundary.zone.value,
                        "lower_value": (
                            str(boundary.lower) if boundary.lower is not None else None
                        ),
                        "upper_value": (
                            str(boundary.upper) if boundary.upper is not None else None
                        ),
                    }
                    for boundary in profile.boundaries
                ],
            }
            for profile in profiles
        ]

    @staticmethod
    def _observation_response(row: JsonObject) -> CalibrationObservationResponse:
        return CalibrationObservationResponse.model_validate(
            {key: row[key] for key in CalibrationObservationResponse.model_fields}
        )

    @staticmethod
    def _domain_observation(values: JsonObject) -> CalibrationObservation:
        return CalibrationObservation(
            protocol_id=str(values["protocol_id"]),
            discipline=Discipline(str(values["discipline"])),
            segment_id=str(values["segment_id"]),
            completed=bool(values["completed"]),
            interrupted=bool(values["interrupted"]),
            quality_status=DataQuality(str(values["quality_status"])),
            target_rpe=values.get("target_rpe"),
            reported_block_rpe=values.get("reported_block_rpe"),
            reported_session_rpe=values.get("reported_session_rpe"),
            steady_execution=(
                SteadyExecution(str(values["steady_execution"]))
                if values.get("steady_execution") is not None
                else None
            ),
            duration_seconds=values.get("duration_seconds"),
            distance_meters=values.get("distance_meters"),
            average_heart_rate_bpm=_decimal(values.get("average_heart_rate_bpm")),
            ending_heart_rate_bpm=_decimal(values.get("ending_heart_rate_bpm")),
            average_heart_rate_last_20min_bpm=_decimal(
                values.get("average_heart_rate_last_20min_bpm")
            ),
            average_power_watts=_decimal(values.get("average_power_watts")),
            average_power_last_20min_watts=_decimal(
                values.get("average_power_last_20min_watts")
            ),
            average_pace_seconds_per_km=_decimal(
                values.get("average_pace_seconds_per_km")
            ),
            elapsed_time_seconds=_decimal(values.get("elapsed_time_seconds")),
            pool_length_meters=values.get("pool_length_meters"),
            stroke=values.get("stroke"),
            equipment=values.get("equipment"),
            rest_time_seconds=values.get("rest_time_seconds"),
            data_completeness=_decimal(values.get("data_completeness")),
            stable_segment=values.get("stable_segment"),
            power_source_calibrated=values.get("power_source_calibrated"),
            repetitions=tuple(
                SwimRepetition(
                    distance_meters=int(repetition["distance_meters"]),
                    elapsed_time_seconds=Decimal(
                        str(repetition["elapsed_time_seconds"])
                    ),
                    rest_time_seconds=int(repetition["rest_time_seconds"]),
                    completed=bool(repetition["completed"]),
                )
                for repetition in values.get("repetitions", [])
            ),
        )

    @staticmethod
    def _validate_observation_protocol(
        observation: CalibrationObservationCreate,
    ) -> None:
        protocol = PROTOCOLS.get(observation.protocol_id)
        if protocol is None or protocol.discipline is not observation.discipline:
            raise CalibrationDomainError(
                "Observation protocol does not match the discipline."
            )
        definition = next(
            (
                segment
                for segment in protocol.segments
                if segment.segment_id == observation.segment_id
            ),
            None,
        )
        if definition is None:
            raise CalibrationDomainError(
                "Observation segment is not part of the selected protocol."
            )
        if not (
            definition.target_rpe_min
            <= observation.target_rpe
            <= definition.target_rpe_max
        ):
            raise CalibrationDomainError(
                "target_rpe does not match the reviewed protocol segment."
            )

    async def save_observation(
        self,
        access_token: str,
        observation: CalibrationObservationCreate,
    ) -> CalibrationObservationResponse:
        self._validate_observation_protocol(observation)
        values = observation.model_dump(mode="json")
        fingerprint = _fingerprint(values)
        row = await self._repository.save_observation(
            access_token,
            values,
            fingerprint,
        )
        return self._observation_response(row)

    async def evaluate(
        self,
        access_token: str,
        athlete_id: UUID,
        request: CalibrationEvaluationRequest,
    ) -> CalibrationEvaluationResponse:
        rows = await self._repository.list_observations(
            access_token,
            athlete_id,
            request.protocol_id,
            request.activity_id,
        )
        result = evaluate_protocol(
            protocol_id=request.protocol_id,
            observations=tuple(self._domain_observation(row) for row in rows),
        )
        payload: JsonObject = {
            "activity_id": str(request.activity_id),
            "protocol_id": result.protocol_id,
            "discipline": result.discipline.value,
            "ruleset_version": CALIBRATION_RULESET_VERSION,
            "status": result.status.value,
            "threshold_status": result.threshold_status.value,
            "zone_status": result.zone_status.value,
            "confidence": result.confidence.value,
            "reason_codes": list(result.reason_codes),
            "thresholds": [
                {
                    "metric_kind": estimate.metric_kind.value,
                    "value": str(estimate.value),
                }
                for estimate in result.thresholds
            ],
            "zone_model_version": (
                ZONE_MODEL_VERSION.value if result.zone_profiles else None
            ),
            "zone_profiles": self._zone_profile_values(result.zone_profiles),
            "requires_athlete_confirmation": result.requires_athlete_confirmation,
            "review_status": (
                "pending_athlete_confirmation"
                if result.requires_athlete_confirmation
                else "not_applicable"
            ),
        }
        fingerprint = _fingerprint(
            {
                "evaluation": payload,
                "observation_fingerprints": sorted(
                    str(row["fingerprint"]) for row in rows
                ),
            }
        )
        saved = await self._repository.save_evaluation(
            athlete_id,
            payload,
            fingerprint,
        )
        return self._evaluation_response(saved)

    async def confirm_threshold(
        self,
        access_token: str,
        athlete_id: UUID,
        evaluation_id: UUID,
    ) -> ThresholdDecisionResponse:
        """Confirm an owned threshold and create a still-pending zone profile."""
        row = await self._repository.get_evaluation(
            access_token,
            athlete_id,
            evaluation_id,
        )
        evaluation = self._evaluation_response(row)
        if (
            evaluation.status.value != "threshold_estimated"
            or not evaluation.requires_athlete_confirmation
            or not evaluation.thresholds
        ):
            raise CalibrationDomainError(
                "Only a pending field-test threshold can be confirmed."
            )
        profiles = calculate_zone_profiles(
            tuple(
                ZoneMetric(
                    discipline=evaluation.discipline,
                    kind=threshold.metric_kind,
                    value=threshold.value,
                )
                for threshold in evaluation.thresholds
            )
        )
        profile_values = self._zone_profile_values(profiles)
        fingerprint = _fingerprint(
            {
                "evaluation_id": str(evaluation.id),
                "zone_model_version": ZONE_MODEL_VERSION.value,
                "metric_profiles": profile_values,
            }
        )
        saved = await self._repository.save_calculated_zone_profile(
            athlete_id,
            {
                "discipline": evaluation.discipline.value,
                "source_method": evaluation.protocol_id,
                "source_quality": "reviewed_field_threshold",
                "metric_profiles": profile_values,
                "input_fingerprint": fingerprint,
                "calibration_evaluation_id": str(evaluation.id),
            },
        )
        return self._threshold_decision_response(
            {"zone_proposal_state": "pending", **saved}
        )

    async def reject_threshold(
        self,
        athlete_id: UUID,
        evaluation_id: UUID,
    ) -> ThresholdDecisionResponse:
        """Reject one pending field-test threshold without creating zones."""
        saved = await self._repository.reject_threshold(
            athlete_id,
            evaluation_id,
        )
        return self._threshold_decision_response(saved)

    async def status(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> CalibrationStatusResponse:
        raw = await self._repository.fetch_status(access_token, athlete_id)
        proposal_states = {
            str(row["id"]): row["state"] for row in raw.get("zone_proposals", [])
        }
        return CalibrationStatusResponse(
            setups=tuple(self._discipline_setup_response(row) for row in raw["setups"]),
            evaluations=tuple(
                self._evaluation_response(row) for row in raw["evaluations"]
            ),
            threshold_decisions=tuple(
                self._threshold_decision_response(
                    {
                        **row,
                        "zone_proposal_state": proposal_states.get(
                            str(row.get("zone_proposal_id"))
                        ),
                    }
                )
                for row in raw.get("threshold_decisions", [])
            ),
        )


def _decimal(value: object) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None
