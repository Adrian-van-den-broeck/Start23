"""Phase 4 application service over deterministic physiology and persistence."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.calibration.schemas import DisciplineSetupResponse
from app.modules.onboarding.repository import JsonObject, OnboardingRepository
from app.modules.onboarding.schemas import (
    AthleteProfileResponse,
    AthleteProfileUpdate,
    CalculatedZoneSubmission,
    FallbackZoneSubmission,
    GoalPlanningOptionResponse,
    ManualZoneSubmission,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
    OnboardingStep,
    PrimaryRaceGoalInput,
    PrimaryRaceGoalResponse,
    TrainingHistoryEntryResponse,
    TrainingHistoryReplace,
    ZoneMetricResponse,
    ZoneProfileResponse,
    ZoneProposalDecisionResponse,
    ZoneSubmission,
    ZoneSubmissionResponse,
)
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.zones import (
    ZONE_MODEL_VERSION,
    CalculatedZoneMetricProfile,
    ZoneBoundary,
    ZoneMetric,
    assess_metric_with_soft_limits,
    calculate_karvonen_fallback,
    calculate_zone_profiles,
    validate_zone_profile,
)


class OnboardingDomainError(Exception):
    """Persisted or submitted onboarding state is invalid."""


class OnboardingService:
    """Coordinate owner-scoped Phase 4 use cases."""

    def __init__(self, repository: OnboardingRepository) -> None:
        self._repository = repository

    @staticmethod
    def goal_planning_options() -> tuple[GoalPlanningOptionResponse, ...]:
        """Expose only reviewed planning capability; unsupported modes fail closed."""
        return (
            GoalPlanningOptionResponse(
                goal_kind="race_event",
                goal_family="race_event",
                label="Wedstrijd of evenement",
                availability="available",
                requires_target_date=True,
                cycle_anchor="race_date",
                unavailable_reason=None,
            ),
            GoalPlanningOptionResponse(
                goal_kind="personal_goal",
                goal_family="general_fitness",
                label="Algemene fitheid",
                availability="coming_later",
                requires_target_date=False,
                cycle_anchor="cycle_week_1",
                unavailable_reason="deterministic_rules_not_approved",
            ),
            GoalPlanningOptionResponse(
                goal_kind="personal_goal",
                goal_family="weight_loss",
                label="Gewichtsverlies",
                availability="coming_later",
                requires_target_date=False,
                cycle_anchor="cycle_week_1",
                unavailable_reason="deterministic_rules_not_approved",
            ),
            GoalPlanningOptionResponse(
                goal_kind="personal_goal",
                goal_family="muscle_gain",
                label="Spieropbouw",
                availability="coming_later",
                requires_target_date=False,
                cycle_anchor="cycle_week_1",
                unavailable_reason="deterministic_rules_not_approved",
            ),
        )

    @staticmethod
    def _profile(row: JsonObject | None) -> AthleteProfileResponse | None:
        return AthleteProfileResponse.model_validate(row) if row is not None else None

    @staticmethod
    def _goal(row: JsonObject | None) -> PrimaryRaceGoalResponse | None:
        if row is None:
            return None
        return PrimaryRaceGoalResponse.model_validate(
            {key: row[key] for key in PrimaryRaceGoalResponse.model_fields}
        )

    @staticmethod
    def _history(row: JsonObject) -> TrainingHistoryEntryResponse:
        return TrainingHistoryEntryResponse.model_validate(
            {key: row[key] for key in TrainingHistoryEntryResponse.model_fields}
        )

    @staticmethod
    def _discipline_setup(row: JsonObject) -> DisciplineSetupResponse:
        return DisciplineSetupResponse.model_validate(
            {key: row[key] for key in DisciplineSetupResponse.model_fields}
        )

    @staticmethod
    def _zone_profiles(state: JsonObject) -> tuple[ZoneProfileResponse, ...]:
        metric_by_profile = {
            str(row["zone_profile_id"]): row for row in state["zone_metrics"]
        }
        boundaries_by_profile: dict[str, list[JsonObject]] = {}
        for row in state["zone_boundaries"]:
            boundaries_by_profile.setdefault(
                str(row["zone_profile_id"]),
                [],
            ).append(row)
        proposal_by_profile = {
            str(row["target_zone_profile_id"]): row
            for row in state.get("zone_proposals", [])
            if row.get("target_zone_profile_id") is not None
        }

        profiles: list[ZoneProfileResponse] = []
        for row in state["zone_profiles"]:
            profile_id = str(row["id"])
            metric_row = metric_by_profile.get(profile_id)
            metric_profiles = list(row.get("metric_profiles") or [])
            primary_profile = next(
                (
                    profile
                    for profile in metric_profiles
                    if bool(profile.get("is_primary"))
                ),
                metric_profiles[0] if metric_profiles else None,
            )
            metric: ZoneMetricResponse | None = None
            if primary_profile is not None:
                metric = ZoneMetricResponse.model_validate(
                    {
                        "metric_kind": primary_profile["metric_kind"],
                        "value": primary_profile["source_value"],
                    }
                )
            elif metric_row is not None:
                metric = ZoneMetricResponse.model_validate(
                    {
                        "metric_kind": metric_row["metric_kind"],
                        "value": metric_row["value"],
                    }
                )
            raw_boundaries = (
                list(primary_profile["boundaries"])
                if primary_profile is not None
                else boundaries_by_profile.get(profile_id, [])
            )
            boundaries = tuple(
                {
                    "zone_number": boundary["zone_number"],
                    "lower_value": boundary.get("lower_value"),
                    "upper_value": boundary.get("upper_value"),
                }
                for boundary in sorted(
                    raw_boundaries,
                    key=lambda value: int(value["zone_number"]),
                )
            )
            proposal = proposal_by_profile.get(profile_id)
            stored_values = {
                key: row[key]
                for key in ZoneProfileResponse.model_fields
                if key in row
                and key
                not in {
                    "metric",
                    "boundaries",
                    "metric_profiles",
                    "source",
                    "validation_status",
                    "proposal_id",
                    "base_zone_profile_id",
                }
            }
            profiles.append(
                ZoneProfileResponse.model_validate(
                    {
                        **stored_values,
                        "metric": metric,
                        "boundaries": boundaries,
                        "metric_profiles": metric_profiles,
                        "proposal_id": (
                            proposal.get("id") if proposal is not None else None
                        ),
                        "base_zone_profile_id": (
                            proposal.get("base_zone_profile_id")
                            if proposal is not None
                            else None
                        ),
                    }
                )
            )
        return tuple(profiles)

    @staticmethod
    def _profile_is_complete(profile: AthleteProfileResponse | None) -> bool:
        return profile is not None and all(
            value is not None
            for value in (
                profile.date_of_birth,
                profile.height_cm,
                profile.weight_kg,
                profile.resting_heart_rate_bpm,
                profile.motivation_text,
            )
        )

    @classmethod
    def _state(cls, raw: JsonObject) -> OnboardingStateResponse:
        profile = cls._profile(raw["profile"])
        history = tuple(cls._history(row) for row in raw["training_history"])
        goal_rows = raw["goals"]
        goal = cls._goal(goal_rows[0] if goal_rows else None)
        zones = cls._zone_profiles(raw)
        discipline_setups = tuple(
            cls._discipline_setup(row) for row in raw.get("discipline_setups", [])
        )
        active_disciplines = {
            zone.discipline for zone in zones if zone.status == "active"
        }
        configured_disciplines = active_disciplines | {
            setup.discipline for setup in discipline_setups
        }

        derived_steps: list[OnboardingStep] = []
        if cls._profile_is_complete(profile):
            derived_steps.append("profile")
        if {entry.discipline for entry in history} == set(Discipline):
            derived_steps.append("history")
        if goal is not None:
            derived_steps.append("goal")
        if configured_disciplines == set(Discipline):
            derived_steps.append("zones")

        session = raw["session"]
        persisted_status = (
            str(session["status"])
            if session is not None
            else (profile.onboarding_status if profile is not None else "not_started")
        )
        if persisted_status == "completed":
            completed_steps: tuple[OnboardingStep, ...] = (
                "profile",
                "history",
                "goal",
                "zones",
                "review",
            )
            current_step: OnboardingStep = "completed"
        else:
            completed_steps = tuple(derived_steps)
            step_order: tuple[OnboardingStep, ...] = (
                "profile",
                "history",
                "goal",
                "zones",
                "review",
            )
            current_step = next(
                (step for step in step_order if step not in completed_steps),
                "review",
            )

        can_complete = all(
            step in derived_steps for step in ("profile", "history", "goal", "zones")
        )
        request_id = (
            session.get("initial_plan_request_id") if session is not None else None
        )
        return OnboardingStateResponse(
            status=persisted_status,
            current_step=current_step,
            completed_steps=completed_steps,
            profile=profile,
            training_history=history,
            primary_goal=goal,
            zones=zones,
            discipline_setups=discipline_setups,
            can_complete=can_complete,
            initial_plan_request_id=request_id,
        )

    async def get_state(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> OnboardingStateResponse:
        """Return resumable state derived from persisted owner-scoped rows."""
        return self._state(await self._repository.fetch_state(access_token, athlete_id))

    async def get_profile(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> AthleteProfileResponse | None:
        """Return the athlete profile when one has been started."""
        return (await self.get_state(access_token, athlete_id)).profile

    async def update_profile(
        self,
        access_token: str,
        athlete_id: UUID,
        update: AthleteProfileUpdate,
    ) -> AthleteProfileResponse:
        """Validate timezone and persist only explicitly supplied fields."""
        values = update.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=False,
        )
        timezone_name = values.get("timezone")
        if timezone_name is not None:
            try:
                ZoneInfo(str(timezone_name))
            except ZoneInfoNotFoundError as error:
                raise OnboardingDomainError(
                    "timezone must be a valid IANA name"
                ) from error
        row = await self._repository.upsert_profile(
            access_token,
            athlete_id,
            values,
        )
        return AthleteProfileResponse.model_validate(row)

    async def replace_training_history(
        self,
        access_token: str,
        replacement: TrainingHistoryReplace,
    ) -> tuple[TrainingHistoryEntryResponse, ...]:
        """Atomically replace athlete-confirmed swim, bike, and run history."""
        rows = await self._repository.replace_training_history(
            access_token,
            [entry.model_dump(mode="json") for entry in replacement.entries],
        )
        return tuple(self._history(row) for row in rows)

    async def save_primary_goal(
        self,
        access_token: str,
        goal: PrimaryRaceGoalInput,
        *,
        goal_id: UUID | None = None,
    ) -> PrimaryRaceGoalResponse:
        """Create or update the one active primary race goal."""
        row = await self._repository.save_primary_goal(
            access_token,
            goal_id,
            goal.model_dump(mode="json"),
        )
        goal_response = self._goal(row)
        if goal_response is None:
            raise OnboardingDomainError("Saved goal could not be read back.")
        return goal_response

    @staticmethod
    def _manual_zone_values(
        discipline: Discipline,
        submission: ManualZoneSubmission,
    ) -> JsonObject:
        metric = ZoneMetric(
            discipline=discipline,
            kind=submission.metric_kind,
            value=submission.metric_value,
        )
        boundaries = tuple(
            ZoneBoundary(
                zone=TrainingZone(boundary.zone_number),
                lower=boundary.lower_value,
                upper=boundary.upper_value,
            )
            for boundary in submission.boundaries
        )
        validate_zone_profile(
            metric_kind=metric.kind,
            boundaries=boundaries,
        )
        assessment = assess_metric_with_soft_limits(metric, {})
        return {
            "discipline": discipline.value,
            "setup_method": "manual",
            "metric_kind": metric.kind.value,
            "metric_value": str(metric.value),
            "boundaries": [
                {
                    "zone_number": boundary.zone.value,
                    "lower_value": str(boundary.lower),
                    "upper_value": str(boundary.upper),
                }
                for boundary in boundaries
            ],
            "requires_review": assessment.requires_review,
            "review_reason": assessment.reason.value,
            "ruleset_version": assessment.ruleset_version.value,
        }

    @staticmethod
    def _calculated_profile_payload(
        profiles: tuple[CalculatedZoneMetricProfile, ...],
        submission: CalculatedZoneSubmission,
    ) -> list[JsonObject]:
        overrides = {
            profile.metric_kind: profile for profile in submission.boundary_overrides
        }
        if not set(overrides).issubset(
            {threshold.metric_kind for threshold in submission.thresholds}
        ):
            raise OnboardingDomainError(
                "Boundary overrides require the same confirmed threshold metric."
            )
        payload: list[JsonObject] = []
        for profile in profiles:
            override = overrides.get(profile.metric.kind)
            boundaries: tuple[JsonObject, ...]
            if override is not None:
                manual_boundaries = tuple(
                    ZoneBoundary(
                        zone=TrainingZone(boundary.zone_number),
                        lower=boundary.lower_value,
                        upper=boundary.upper_value,
                    )
                    for boundary in override.boundaries
                )
                validate_zone_profile(
                    metric_kind=profile.metric.kind,
                    boundaries=manual_boundaries,
                )
                boundaries = tuple(
                    {
                        "zone_number": boundary.zone.value,
                        "lower_value": str(boundary.lower),
                        "upper_value": str(boundary.upper),
                    }
                    for boundary in manual_boundaries
                )
                boundary_source = "athlete_entered"
            else:
                boundaries = tuple(
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
                )
                boundary_source = "model_derived"
            payload.append(
                {
                    "metric_kind": profile.metric.kind.value,
                    "source_value": str(profile.metric.value),
                    "is_primary": profile.is_primary,
                    "boundary_source": boundary_source,
                    "zone_model_version": profile.zone_model_version.value,
                    "boundaries": list(boundaries),
                }
            )
        return payload

    @classmethod
    def _calculated_zone_values(
        cls,
        discipline: Discipline,
        submission: CalculatedZoneSubmission,
    ) -> JsonObject:
        kinds = [threshold.metric_kind for threshold in submission.thresholds]
        if len(set(kinds)) != len(kinds):
            raise OnboardingDomainError("Known threshold metrics must be unique.")
        try:
            profiles = calculate_zone_profiles(
                tuple(
                    ZoneMetric(
                        discipline=discipline,
                        kind=threshold.metric_kind,
                        value=threshold.value,
                    )
                    for threshold in submission.thresholds
                )
            )
            metric_profiles = cls._calculated_profile_payload(profiles, submission)
        except ValueError as error:
            raise OnboardingDomainError(str(error)) from error
        fingerprint_source = {
            "discipline": discipline.value,
            "source_quality": submission.source_quality,
            "zone_model_version": ZONE_MODEL_VERSION.value,
            "metric_profiles": metric_profiles,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_source,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            "discipline": discipline.value,
            "source_method": (
                "physician_or_lab_reported"
                if submission.source_quality == "measured_lab"
                else "athlete_entered"
            ),
            "source_quality": submission.source_quality,
            "metric_profiles": metric_profiles,
            "input_fingerprint": fingerprint,
            "calibration_evaluation_id": None,
        }

    @staticmethod
    def _age_on(date_of_birth: date, today: date) -> int:
        return (
            today.year
            - date_of_birth.year
            - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        )

    @classmethod
    def _fallback_zone_values(
        cls,
        discipline: Discipline,
        submission: FallbackZoneSubmission,
        profile: AthleteProfileResponse | None,
    ) -> JsonObject:
        del submission
        if discipline is Discipline.SWIM:
            raise OnboardingDomainError(
                "The approved fallback is heart-rate based and unavailable for swim."
            )
        if (
            profile is None
            or profile.date_of_birth is None
            or profile.resting_heart_rate_bpm is None
        ):
            raise OnboardingDomainError(
                "Fallback zones require date_of_birth and resting_heart_rate_bpm."
            )
        result = calculate_karvonen_fallback(
            age_years=cls._age_on(profile.date_of_birth, date.today()),
            resting_heart_rate_bpm=Decimal(profile.resting_heart_rate_bpm),
        )
        return {
            "discipline": discipline.value,
            "setup_method": "fallback",
            "metric_kind": None,
            "metric_value": None,
            "boundaries": [
                {
                    "zone_number": boundary.zone.value,
                    "lower_value": str(boundary.lower),
                    "upper_value": str(boundary.upper),
                }
                for boundary in result.boundaries
            ],
            "requires_review": True,
            "review_reason": "fallback_unvalidated",
            "ruleset_version": result.ruleset_version.value,
        }

    async def save_zone_profile(
        self,
        access_token: str,
        athlete_id: UUID,
        discipline: Discipline,
        submission: ZoneSubmission,
    ) -> ZoneSubmissionResponse:
        """Validate a zone profile and preserve approval semantics."""
        if isinstance(submission, ManualZoneSubmission):
            values = self._manual_zone_values(discipline, submission)
            result = await self._repository.save_zone_profile(access_token, values)
        elif isinstance(submission, FallbackZoneSubmission):
            profile = await self.get_profile(access_token, athlete_id)
            values = self._fallback_zone_values(
                discipline,
                submission,
                profile,
            )
            result = await self._repository.save_fallback_zone_profile(
                athlete_id,
                values,
            )
        else:
            values = self._calculated_zone_values(discipline, submission)
            result = await self._repository.save_calculated_zone_profile(
                athlete_id,
                values,
            )
        state = await self.get_state(access_token, athlete_id)
        profile_id = UUID(str(result["profile_id"]))
        zone_profile = next(
            (zone for zone in state.zones if zone.id == profile_id),
            None,
        )
        if zone_profile is None:
            raise OnboardingDomainError("Saved zone profile could not be read back.")
        proposal_id = result.get("proposal_id")
        return ZoneSubmissionResponse(
            profile=zone_profile,
            proposal_id=UUID(str(proposal_id)) if proposal_id is not None else None,
        )

    async def complete(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> OnboardingCompleteResponse:
        """Complete onboarding and persist an idempotent planning trigger."""
        state = await self.get_state(access_token, athlete_id)
        if not state.can_complete:
            raise OnboardingDomainError(
                "Profile, history, primary goal, and discipline guidance are required."
            )
        request_id = await self._repository.complete_onboarding(access_token)
        completed = await self.get_state(access_token, athlete_id)
        return OnboardingCompleteResponse(
            onboarding=completed,
            initial_plan_request_id=request_id,
        )

    async def approve_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_zone_profile_id: UUID | None,
    ) -> ZoneProposalDecisionResponse:
        """Apply one pending profile against its exact active-or-empty base."""
        result = await self._repository.approve_zone_proposal(
            access_token,
            proposal_id,
            expected_base_zone_profile_id,
        )
        return ZoneProposalDecisionResponse.model_validate(result)

    async def reject_zone_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> ZoneProposalDecisionResponse:
        """Reject a pending replacement without changing active zones."""
        result = await self._repository.reject_zone_proposal(
            access_token,
            proposal_id,
        )
        return ZoneProposalDecisionResponse.model_validate(result)
