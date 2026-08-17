"""Phase 4 application service over deterministic physiology and persistence."""

from datetime import date
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.calibration.schemas import DisciplineSetupResponse
from app.modules.onboarding.repository import JsonObject, OnboardingRepository
from app.modules.onboarding.schemas import (
    AthleteProfileResponse,
    AthleteProfileUpdate,
    FallbackZoneSubmission,
    ManualZoneSubmission,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
    OnboardingStep,
    PrimaryRaceGoalInput,
    PrimaryRaceGoalResponse,
    TrainingHistoryEntryResponse,
    TrainingHistoryReplace,
    ZoneBoundaryInput,
    ZoneMetricResponse,
    ZoneProfileResponse,
    ZoneProposalDecisionResponse,
    ZoneSubmission,
    ZoneSubmissionResponse,
)
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.zones import (
    ZoneBoundary,
    ZoneMetric,
    assess_metric_with_soft_limits,
    calculate_karvonen_fallback,
    validate_zone_profile,
)


class OnboardingDomainError(Exception):
    """Persisted or submitted onboarding state is invalid."""


class OnboardingService:
    """Coordinate owner-scoped Phase 4 use cases."""

    def __init__(self, repository: OnboardingRepository) -> None:
        self._repository = repository

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

        profiles: list[ZoneProfileResponse] = []
        for row in state["zone_profiles"]:
            profile_id = str(row["id"])
            metric_row = metric_by_profile.get(profile_id)
            metric = (
                ZoneMetricResponse.model_validate(
                    {
                        "metric_kind": metric_row["metric_kind"],
                        "value": metric_row["value"],
                    }
                )
                if metric_row is not None
                else None
            )
            boundaries = tuple(
                ZoneBoundaryInput.model_validate(
                    {
                        "zone_number": boundary["zone_number"],
                        "lower_value": boundary["lower_value"],
                        "upper_value": boundary["upper_value"],
                    }
                )
                for boundary in sorted(
                    boundaries_by_profile.get(profile_id, []),
                    key=lambda value: int(value["zone_number"]),
                )
            )
            profiles.append(
                ZoneProfileResponse.model_validate(
                    {
                        **{
                            key: row[key]
                            for key in ZoneProfileResponse.model_fields
                            if key
                            not in {
                                "metric",
                                "boundaries",
                                "source",
                                "validation_status",
                            }
                        },
                        "metric": metric,
                        "boundaries": boundaries,
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
        else:
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
        expected_base_zone_profile_id: UUID,
    ) -> ZoneProposalDecisionResponse:
        """Apply exactly one pending replacement against its expected base."""
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
