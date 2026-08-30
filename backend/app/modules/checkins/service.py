"""Application orchestration for structured weekly check-ins."""

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from app.modules.coach.context import (
    CheckInContextCoach,
    CheckInContextFacts,
    ContextCoachProviderError,
    DisabledCheckInContextCoach,
    deterministic_context_fallback,
)
from app.modules.physiology.injury import RestrictionStatus
from app.modules.physiology.models import Discipline
from app.modules.planning.schemas import WeeklyPlanProposalResponse
from app.modules.planning.service import PlanningService

from .domain import (
    AthletePlanChoice,
    RestrictionDecision,
    athlete_local_week_start,
    available_dates_from_blocked_dates,
    confirmed_restriction_sets,
    context_fingerprint,
)
from .repository import CheckInRepository
from .schemas import (
    CheckInContextCandidateResponse,
    CheckInContextConfirmation,
    CheckInContextExtractionRequest,
    CheckInContextUpdate,
    GoalAchievementRequest,
    GoalMaintenanceResponse,
    InjuryRestrictionResponse,
    PlannedExternalActivityResponse,
    WeeklyCheckInResponse,
)


class CheckInDomainError(ValueError):
    """Stored or submitted structured weekly context is inconsistent."""


class CheckInService:
    def __init__(
        self,
        repository: CheckInRepository,
        planning_service: PlanningService,
        context_coach: CheckInContextCoach,
    ) -> None:
        self._repository = repository
        self._planning_service = planning_service
        self._context_coach = context_coach

    @staticmethod
    def _response(row: Mapping[str, Any]) -> WeeklyCheckInResponse:
        try:
            return WeeklyCheckInResponse.model_validate(row)
        except (KeyError, ValueError) as error:
            raise CheckInDomainError(
                "Stored weekly check-in data is invalid."
            ) from error

    async def start(
        self,
        access_token: str,
        *,
        week_start: date,
    ) -> WeeklyCheckInResponse:
        return self._response(
            await self._repository.start_or_resume(access_token, week_start)
        )

    async def current(
        self,
        access_token: str,
        *,
        now: datetime,
        timezone_name: str,
    ) -> WeeklyCheckInResponse:
        week_start = athlete_local_week_start(
            instant=now,
            timezone_name=timezone_name,
        )
        return await self.start(access_token, week_start=week_start)

    async def get(
        self,
        access_token: str,
        checkin_id: UUID,
    ) -> WeeklyCheckInResponse:
        return self._response(await self._repository.fetch(access_token, checkin_id))

    async def extract_context_candidate(
        self,
        access_token: str,
        checkin_id: UUID,
        request: CheckInContextExtractionRequest,
    ) -> CheckInContextCandidateResponse:
        """Return an inert candidate; never save or confirm check-in context."""

        checkin = await self.get(access_token, checkin_id)
        source = (
            "deterministic_fallback"
            if isinstance(self._context_coach, DisabledCheckInContextCoach)
            else "llm"
        )
        try:
            candidate = await self._context_coach.extract(
                CheckInContextFacts(
                    week_start=checkin.week_start,
                    timezone=checkin.timezone,
                    athlete_text=request.athlete_text,
                )
            )
            week_dates = {
                checkin.week_start + timedelta(days=offset) for offset in range(7)
            }
            if (
                not set(candidate.blocked_dates) <= week_dates
                or len(set(candidate.blocked_dates)) != len(candidate.blocked_dates)
                or len(set(candidate.possible_injury_disciplines))
                != len(candidate.possible_injury_disciplines)
            ):
                raise ContextCoachProviderError(
                    "The extracted candidate falls outside the confirmed week."
                )
        except ContextCoachProviderError:
            candidate = deterministic_context_fallback()
            source = "deterministic_fallback"
        return CheckInContextCandidateResponse(
            source=source,
            candidate=candidate,
        )

    @staticmethod
    def _restriction(input_value: Any) -> RestrictionDecision:
        return RestrictionDecision(
            discipline=input_value.discipline,
            status=input_value.status,
            source=input_value.source,
            athlete_plan_choice=input_value.athlete_plan_choice,
            professional_advice=input_value.professional_advice,
            professional_advice_at=input_value.professional_advice_at,
        )

    async def save_context(
        self,
        access_token: str,
        checkin_id: UUID,
        update: CheckInContextUpdate,
    ) -> WeeklyCheckInResponse:
        checkin = await self.get(access_token, checkin_id)
        week_dates = {
            checkin.week_start + timedelta(days=offset) for offset in range(7)
        }
        if not update.blocked_dates <= week_dates:
            raise CheckInDomainError(
                "Blocked dates must fall inside the check-in week."
            )
        timezone = ZoneInfo(checkin.timezone)
        for activity in update.external_activities:
            local_date = activity.scheduled_at.astimezone(timezone).date()
            if local_date not in week_dates:
                raise CheckInDomainError(
                    "External activities must fall inside the check-in week."
                )
        decisions = tuple(self._restriction(item) for item in update.restrictions)
        confirmed_restriction_sets(decisions)
        payload = update.model_dump(
            mode="json",
            exclude={"expected_revision"},
            exclude_none=True,
        )
        fingerprint = context_fingerprint(payload)
        return self._response(
            await self._repository.save_context(
                access_token,
                checkin_id,
                update.expected_revision,
                fingerprint,
                payload,
            )
        )

    async def confirm_context(
        self,
        access_token: str,
        checkin_id: UUID,
        confirmation: CheckInContextConfirmation,
    ) -> WeeklyCheckInResponse:
        return self._response(
            await self._repository.confirm_context(
                access_token,
                checkin_id,
                confirmation.expected_revision,
                confirmation.context_fingerprint,
            )
        )

    @staticmethod
    def _planning_inputs(
        context: Mapping[str, Any],
    ) -> tuple[
        date,
        tuple[date, ...],
        frozenset[Discipline],
        frozenset[Discipline],
    ]:
        try:
            week_start = date.fromisoformat(str(context["week_start"]))
            timezone_name = str(context["timezone"])
            payload = context["confirmed_context"]
            if not isinstance(payload, dict):
                raise ValueError
            restrictions = tuple(
                RestrictionDecision(
                    discipline=Discipline(str(item["discipline"])),
                    status=RestrictionStatus(str(item["status"])),
                    source=str(item["source"]),
                    athlete_plan_choice=AthletePlanChoice(
                        str(item["athlete_plan_choice"])
                    ),
                    professional_advice=item.get("professional_advice"),
                    professional_advice_at=(
                        datetime.fromisoformat(str(item["professional_advice_at"]))
                        if item.get("professional_advice_at") is not None
                        else None
                    ),
                )
                for item in payload.get("restrictions", [])
            )
            blocked, low_only = confirmed_restriction_sets(restrictions)
            strenuous_dates = frozenset(
                datetime.fromisoformat(str(item["scheduled_at"]))
                .astimezone(ZoneInfo(timezone_name))
                .date()
                for item in payload.get("external_activities", [])
                if item.get("strenuous") is True
            )
            available_dates = available_dates_from_blocked_dates(
                week_start=week_start,
                blocked_dates=frozenset(
                    date.fromisoformat(str(value))
                    for value in payload.get("blocked_dates", [])
                ),
                strenuous_dates=strenuous_dates,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise CheckInDomainError(
                "Confirmed check-in context cannot drive planning."
            ) from error
        if not available_dates and blocked != frozenset(Discipline):
            raise CheckInDomainError(
                "At least one available date is required unless every discipline "
                "is blocked."
            )
        return week_start, available_dates, blocked, low_only

    async def generate_plan_proposal(
        self,
        access_token: str,
        athlete_id: UUID,
        checkin_id: UUID,
    ) -> WeeklyPlanProposalResponse:
        context = await self._repository.fetch_planning_context(
            athlete_id,
            checkin_id,
        )
        week_start, available_dates, blocked, low_only = self._planning_inputs(context)
        result = await self._planning_service.generate_checkin_proposal(
            access_token,
            athlete_id,
            checkin_id=checkin_id,
            input_source=context,
            week_start=week_start,
            available_dates=available_dates,
            blocked_disciplines=blocked,
            low_only_disciplines=low_only,
        )
        await self._repository.attach_plan_proposal(
            athlete_id,
            checkin_id,
            result.proposal.id,
        )
        return result

    async def list_restrictions(
        self,
        access_token: str,
    ) -> tuple[InjuryRestrictionResponse, ...]:
        return tuple(
            InjuryRestrictionResponse.model_validate(row)
            for row in await self._repository.list_restrictions(access_token)
        )

    async def list_external_activities(
        self,
        access_token: str,
        week_start: date | None,
    ) -> tuple[PlannedExternalActivityResponse, ...]:
        return tuple(
            PlannedExternalActivityResponse.model_validate(row)
            for row in await self._repository.list_external_activities(
                access_token,
                week_start,
            )
        )

    async def mark_goal_achieved(
        self,
        access_token: str,
        goal_id: UUID,
        achievement: GoalAchievementRequest,
    ) -> GoalMaintenanceResponse:
        return GoalMaintenanceResponse.model_validate(
            await self._repository.mark_goal_achieved(
                access_token,
                goal_id,
                achievement.achieved_at,
            )
        )
