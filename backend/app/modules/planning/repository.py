"""Supabase persistence boundary for weekly planning."""

from collections.abc import Mapping
from datetime import date
from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings

JsonObject = dict[str, Any]


class PlanningRepositoryError(Exception):
    """Base planning persistence failure."""


class PlanningRepositoryNotFoundError(PlanningRepositoryError):
    """An owner-scoped planning resource does not exist."""


class PlanningRepositoryConflictError(PlanningRepositoryError):
    """A planning revision or proposal precondition is stale."""

    def __init__(
        self,
        code: str = "state_conflict",
        message: str = "The planning state changed. Refresh and try again.",
    ) -> None:
        super().__init__(message)
        self.code = code


class PlanningRepositoryUnavailableError(PlanningRepositoryError):
    """The planning persistence dependency is temporarily unavailable."""


class PlanningRepository(Protocol):
    """Persistence operations required by the Phase 6 service."""

    async def fetch_initial_request(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject | None:
        """Fetch the owner's current pending onboarding planning input."""

    async def fetch_plan_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
    ) -> JsonObject:
        """Fetch private generation context for a follow-up revision."""

    async def fetch_plan_revision_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
        revision: int,
    ) -> JsonObject:
        """Fetch private context for one exact pending revision."""

    async def fetch_previous_available_dates(
        self,
        athlete_id: UUID,
        week_start: date,
    ) -> tuple[date, ...]:
        """Copy the prior active week's availability only on explicit request."""

    async def fetch_load_history(
        self,
        athlete_id: UUID,
        before_week: date,
    ) -> tuple[JsonObject, ...]:
        """Fetch private active-plan load snapshots before one week."""

    async def create_plan_proposal(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        """Persist a deterministic plan as a typed pending proposal."""

    async def create_swipe_draft(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        """Create or replace one server-authoritative open week draft."""

    async def fetch_swipe_draft(
        self,
        access_token: str,
        draft_id: UUID,
    ) -> JsonObject:
        """Read one exact owner-visible swipe draft through RLS."""

    async def update_swipe_draft(
        self,
        athlete_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        payload: JsonObject,
    ) -> JsonObject:
        """Persist one stale-safe backend-calculated draft transition."""

    async def set_plan_proposal_explanation(
        self,
        athlete_id: UUID,
        proposal_id: UUID,
        explanation: str,
    ) -> str:
        """Set qualitative text on an owned pending proposal, once."""

    async def fetch_plan(
        self,
        access_token: str,
        plan_id: UUID,
        revision: int | None = None,
    ) -> JsonObject:
        """Fetch one owner-visible public plan representation."""

    async def fetch_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        """Fetch a common owner-visible proposal envelope."""

    async def list_proposals(
        self,
        access_token: str,
        state: str | None = None,
    ) -> tuple[JsonObject, ...]:
        """List common owner-visible proposal envelopes."""

    async def approve_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_revision: int,
    ) -> JsonObject:
        """Atomically apply one owned current plan revision."""

    async def reject_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        """Reject one pending plan revision."""

    async def move_planned_workout(
        self,
        athlete_id: UUID,
        workout_id: UUID,
        expected_revision: int,
        scheduled_date: date,
        warnings: list[JsonObject],
    ) -> JsonObject:
        """Apply one explicit owner move as a new active revision."""

    async def fetch_workout_context(
        self,
        access_token: str,
        workout_id: UUID,
    ) -> JsonObject:
        """Fetch the active public plan containing one owned workout."""

    async def fetch_calendar(
        self,
        access_token: str,
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        """Fetch owner-visible active calendar workout snapshots."""

    async def fetch_calendar_rest_days(
        self,
        access_token: str,
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        """Fetch intentionally empty dates from owned active plans."""

    async def aclose(self) -> None:
        """Release repository resources."""


class SupabasePlanningRepository:
    """Use caller tokens for RLS and the backend secret for generated writes."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._publishable_key = settings.supabase_publishable_key
        self._secret_key = settings.supabase_secret_key.get_secret_value()
        self._base_url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.supabase_data_api_timeout_seconds,
        )

    def _headers(self, access_token: str, *, service: bool) -> dict[str, str]:
        key = self._secret_key if service else self._publishable_key
        if not key:
            raise PlanningRepositoryUnavailableError("Supabase key is not configured.")
        headers = {
            "apikey": key,
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }
        if not service:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str = "",
        service: bool = False,
        params: Mapping[str, str] | None = None,
        json: Any = None,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                f"{self._base_url}/{path}",
                headers=self._headers(access_token, service=service),
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PlanningRepositoryUnavailableError from error
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return None
            return response.json()

        error_code: str | None = None
        error_message: str | None = None
        try:
            payload = response.json()
            if isinstance(payload, dict):
                error_code = str(payload.get("code"))
                raw_message = payload.get("message")
                if isinstance(raw_message, str):
                    error_message = raw_message
        except ValueError:
            pass
        if error_code == "P0002":
            raise PlanningRepositoryNotFoundError
        if response.status_code == 404 and not (
            error_code and error_code.startswith("PGRST")
        ):
            raise PlanningRepositoryNotFoundError
        if response.status_code in {400, 409, 422} or error_code in {
            "23505",
            "23514",
            "40001",
            "P0001",
        }:
            conflict_codes = {
                "plan proposal is stale": "proposal_stale",
                "plan revision is stale": "plan_revision_stale",
                "plan proposal is not pending": "proposal_not_pending",
                "plan revision is not pending": "proposal_not_pending",
                "swipe draft is stale": "swipe_draft_stale",
                "swipe draft is closed": "swipe_draft_closed",
            }
            public_code = conflict_codes.get(error_message or "", "state_conflict")
            public_messages = {
                "proposal_stale": ("This proposal is based on an older plan revision."),
                "plan_revision_stale": (
                    "The plan changed after this operation was prepared."
                ),
                "proposal_not_pending": "This proposal was already decided.",
                "swipe_draft_stale": (
                    "The swipe draft changed after this action was prepared."
                ),
                "swipe_draft_closed": "This swipe draft is already closed.",
                "state_conflict": "The planning state changed. Refresh and try again.",
            }
            raise PlanningRepositoryConflictError(
                public_code,
                public_messages[public_code],
            )
        raise PlanningRepositoryUnavailableError

    async def fetch_initial_request(
        self,
        access_token: str,
        athlete_id: UUID,
    ) -> JsonObject | None:
        payload = await self._request(
            "GET",
            "initial_plan_requests",
            access_token=access_token,
            params={
                "select": (
                    "id,athlete_id,status,onboarding_revision,ruleset_version,"
                    "input_snapshot,input_fingerprint,created_at,refreshed_at"
                ),
                "athlete_id": f"eq.{athlete_id}",
                "status": "in.(pending,consumed)",
                "order": "status.desc,refreshed_at.desc",
                "limit": "1",
            },
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return dict(payload[0]) if payload else None

    async def fetch_plan_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/get_plan_context_for_planning",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_plan_id": str(plan_id),
            },
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryUnavailableError
        return dict(payload)

    async def fetch_plan_revision_context(
        self,
        athlete_id: UUID,
        plan_id: UUID,
        revision: int,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/get_plan_revision_context_for_planning",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_plan_id": str(plan_id),
                "p_revision": revision,
            },
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryNotFoundError
        return dict(payload)

    async def fetch_previous_available_dates(
        self,
        athlete_id: UUID,
        week_start: date,
    ) -> tuple[date, ...]:
        payload = await self._request(
            "POST",
            "rpc/get_previous_week_available_dates",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_week_start": week_start.isoformat(),
            },
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return tuple(date.fromisoformat(str(value)) for value in payload)

    async def fetch_load_history(
        self,
        athlete_id: UUID,
        before_week: date,
    ) -> tuple[JsonObject, ...]:
        payload = await self._request(
            "POST",
            "rpc/get_plan_load_history_for_planning",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_before_week": before_week.isoformat(),
            },
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return tuple(dict(row) for row in payload if isinstance(row, dict))

    async def create_plan_proposal(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/create_weekly_plan_proposal_v2",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def create_swipe_draft(
        self,
        athlete_id: UUID,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/create_swipe_week_draft",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def fetch_swipe_draft(
        self,
        access_token: str,
        draft_id: UUID,
    ) -> JsonObject:
        payload = await self._request(
            "GET",
            "swipe_week_drafts",
            access_token=access_token,
            params={
                "select": (
                    "id,athlete_id,plan_id,initial_plan_request_id,"
                    "base_plan_revision,context_plan_revision,week_start,timezone,"
                    "available_dates,availability_source,confirmed_injuries,"
                    "low_only_disciplines,input_fingerprint,context_fingerprint,"
                    "ruleset_version,target_workout_count,target_composition,"
                    "accepted_template_ids,passed_template_ids,current_template_id,"
                    "decision_history,placements,state,revision,proposal_id,"
                    "created_at,updated_at,submitted_at"
                ),
                "id": f"eq.{draft_id}",
                "limit": "1",
            },
        )
        if not isinstance(payload, list) or not payload:
            raise PlanningRepositoryNotFoundError
        return dict(payload[0])

    async def update_swipe_draft(
        self,
        athlete_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        payload: JsonObject,
    ) -> JsonObject:
        result = await self._request(
            "POST",
            "rpc/update_swipe_week_draft",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_draft_id": str(draft_id),
                "p_expected_revision": expected_revision,
                "p_payload": payload,
            },
        )
        if not isinstance(result, dict):
            raise PlanningRepositoryUnavailableError
        return dict(result)

    async def set_plan_proposal_explanation(
        self,
        athlete_id: UUID,
        proposal_id: UUID,
        explanation: str,
    ) -> str:
        result = await self._request(
            "POST",
            "rpc/set_weekly_plan_proposal_explanation",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_proposal_id": str(proposal_id),
                "p_explanation": explanation,
            },
        )
        if not isinstance(result, str):
            raise PlanningRepositoryUnavailableError
        return result

    async def fetch_plan(
        self,
        access_token: str,
        plan_id: UUID,
        revision: int | None = None,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/get_weekly_plan",
            access_token=access_token,
            json={
                "p_plan_id": str(plan_id),
                "p_revision": revision,
            },
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryNotFoundError
        return dict(payload)

    async def fetch_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        payload = await self._request(
            "GET",
            "change_proposals",
            access_token=access_token,
            params={
                "select": (
                    "id,kind,state,reason_codes,public_explanation,ruleset_version,"
                    "created_at,decided_at,applied_at,target_plan_revision_id,"
                    "decision_actor,base_plan_revision,target_zone_profile_id,"
                    "base_zone_profile_id,target_test_assignment_id"
                ),
                "id": f"eq.{proposal_id}",
                "limit": "1",
            },
        )
        if not isinstance(payload, list) or not payload:
            raise PlanningRepositoryNotFoundError
        return dict(payload[0])

    async def list_proposals(
        self,
        access_token: str,
        state: str | None = None,
    ) -> tuple[JsonObject, ...]:
        params = {
            "select": (
                "id,kind,state,reason_codes,public_explanation,ruleset_version,"
                "created_at,decided_at,applied_at,target_plan_revision_id,"
                "decision_actor,base_plan_revision,target_zone_profile_id,"
                "base_zone_profile_id,target_test_assignment_id"
            ),
            "order": "created_at.desc",
        }
        if state is not None:
            params["state"] = f"eq.{state}"
        payload = await self._request(
            "GET",
            "change_proposals",
            access_token=access_token,
            params=params,
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return tuple(dict(row) for row in payload if isinstance(row, dict))

    async def approve_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
        expected_base_revision: int,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/approve_plan_proposal",
            access_token=access_token,
            json={
                "p_proposal_id": str(proposal_id),
                "p_expected_base_revision": expected_base_revision,
            },
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryUnavailableError
        return dict(payload)

    async def reject_plan_proposal(
        self,
        access_token: str,
        proposal_id: UUID,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/reject_plan_proposal",
            access_token=access_token,
            json={"p_proposal_id": str(proposal_id)},
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryUnavailableError
        return dict(payload)

    async def move_planned_workout(
        self,
        athlete_id: UUID,
        workout_id: UUID,
        expected_revision: int,
        scheduled_date: date,
        warnings: list[JsonObject],
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/move_planned_workout",
            service=True,
            json={
                "p_athlete_id": str(athlete_id),
                "p_workout_id": str(workout_id),
                "p_expected_revision": expected_revision,
                "p_scheduled_date": scheduled_date.isoformat(),
                "p_warnings": warnings,
            },
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryUnavailableError
        return dict(payload)

    async def fetch_workout_context(
        self,
        access_token: str,
        workout_id: UUID,
    ) -> JsonObject:
        payload = await self._request(
            "POST",
            "rpc/get_planned_workout_context",
            access_token=access_token,
            json={"p_workout_id": str(workout_id)},
        )
        if not isinstance(payload, dict):
            raise PlanningRepositoryNotFoundError
        return dict(payload)

    async def fetch_calendar(
        self,
        access_token: str,
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        payload = await self._request(
            "POST",
            "rpc/get_calendar",
            access_token=access_token,
            json={
                "p_from": from_date.isoformat(),
                "p_to": to_date.isoformat(),
            },
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return tuple(dict(row) for row in payload if isinstance(row, dict))

    async def fetch_calendar_rest_days(
        self,
        access_token: str,
        from_date: date,
        to_date: date,
    ) -> tuple[JsonObject, ...]:
        payload = await self._request(
            "POST",
            "rpc/get_calendar_rest_days",
            access_token=access_token,
            json={
                "p_from": from_date.isoformat(),
                "p_to": to_date.isoformat(),
            },
        )
        if not isinstance(payload, list):
            raise PlanningRepositoryUnavailableError
        return tuple(dict(row) for row in payload if isinstance(row, dict))

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
