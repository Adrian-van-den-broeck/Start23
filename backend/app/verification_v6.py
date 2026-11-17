"""Isolated hosted verification factory. Never imported by production startup.

There is no module-level app, environment toggle, migration/SQL endpoint or
account-creation path. An owner-held two-subject manifest and an independently
queried Management API project identity are mandatory. Production is rejected.
"""

import asyncio
import base64
import hashlib
import json
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, model_validator
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings
from app.core.security import InvalidAccessTokenError, SupabaseAccessTokenVerifier
from app.main import create_app
from app.modules.activities.repository import SupabaseActivityRepository
from app.modules.activities.router import get_activity_service
from app.modules.activities.router import router as activities_router
from app.modules.activities.service import ActivityService
from app.modules.calibration.repository import SupabaseCalibrationRepository
from app.modules.calibration.router import router as calibration_router
from app.modules.checkins.repository import SupabaseCheckInRepository
from app.modules.checkins.router import get_checkin_service
from app.modules.checkins.router import router as checkins_router
from app.modules.checkins.service import CheckInService
from app.modules.coach.context import DisabledCheckInContextCoach
from app.modules.coach.weekly_plan import DisabledWeeklyPlanCoach
from app.modules.identity.repository import (
    AthleteIdentityResolutionError,
    SupabaseAthleteIdentityRepository,
)
from app.modules.identity.router import router as identity_router
from app.modules.onboarding.frequency import PreferenceResponse, PreferenceSave
from app.modules.onboarding.frequency import router as frequency_router
from app.modules.onboarding.repository import SupabaseOnboardingRepository
from app.modules.onboarding.router import router as onboarding_router
from app.modules.planning.router import get_planning_service
from app.modules.planning.router import router as planning_router
from app.modules.planning.schemas import WeeklyPlanProposalResponse
from app.modules.planning.v6_repository import (
    InactiveSupabaseV6CatalogProvider,
    InactiveSupabaseV6Repository,
)
from app.modules.planning.v6_service import V6PlanningService

PRODUCTION_PROJECT = "isfumhgqphieoayqahjv"


class SyntheticOwner(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    label: Literal["A", "B"]
    auth_subject: UUID
    athlete_id: UUID
    email: str

    @model_validator(mode="after")
    def synthetic(self) -> "SyntheticOwner":
        if self.auth_subject == self.athlete_id or not re.fullmatch(
            r"[a-z0-9._+-]+@[a-z0-9.-]+\.invalid", self.email
        ):
            raise ValueError(
                "Manifest requires a distinct opaque ID and synthetic email"
            )
        return self


class VerificationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1]
    run_id: UUID
    project_ref: str
    issuer: str
    audience: Literal["authenticated"]
    hostname: str
    owners: tuple[SyntheticOwner, SyntheticOwner]
    target_kind: Literal["isolated_synthetic"]
    owner_approval_reference: str

    @model_validator(mode="after")
    def exact_target(self) -> "VerificationManifest":
        if (
            not re.fullmatch(r"[a-z]{20}", self.project_ref)
            or self.project_ref == PRODUCTION_PROJECT
            or self.hostname != self.project_ref + ".supabase.co"
            or self.issuer != "https://" + self.hostname + "/auth/v1"
            or not self.owner_approval_reference.strip()
            or {o.label for o in self.owners} != {"A", "B"}
            or len({o.auth_subject for o in self.owners}) != 2
            or len({o.athlete_id for o in self.owners}) != 2
            or {o.auth_subject for o in self.owners}
            & {o.athlete_id for o in self.owners}
            or len({o.email for o in self.owners}) != 2
        ):
            raise ValueError(
                "Exact isolated target and two independent owners required"
            )
        return self

    def digest(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


@dataclass
class RequestCustody:
    owner: SyntheticOwner
    token: str
    reconciliation_only: bool = False
    attempted_write: bool = False


_custody: ContextVar[RequestCustody | None] = ContextVar(
    "v6_verification", default=None
)

# Exact route names are retained from existing typed routes, never prefix matching.
ROUTES = frozenset(
    {
        "get_me",
        "get_onboarding",
        "get_identifying_profile",
        "update_identifying_profile",
        "get_physiology_profile",
        "update_physiology_profile",
        "get_operational_profile",
        "update_operational_profile",
        "replace_training_history",
        "create_primary_goal",
        "update_primary_goal",
        "save_zone_profile",
        "get_goal_planning_options",
        "save_discipline_setup",
        "get_zone_options",
        "get_zone_profile_state",
        "complete_onboarding",
        "get_preferences",
        "save_preferences",
        "report_interruption",
        "approve_change_proposal",
        "reject_change_proposal",
        "discover_planning",
        "create_initial_weekly_plan_proposal",
        "get_weekly_plan",
        "create_swipe_week_draft",
        "get_swipe_week_draft",
        "transition_swipe_week_draft",
        "place_swipe_week_workout",
        "submit_swipe_week_draft",
        "get_pending_workout_alternatives",
        "edit_pending_workout",
        "validate_weekly_plan",
        "move_planned_workout",
        "get_calendar",
        "list_change_proposals",
        "get_change_proposal",
        "start_weekly_checkin",
        "get_weekly_checkin",
        "save_weekly_checkin_context",
        "confirm_weekly_checkin_context",
        "generate_checkin_plan_proposal",
        "list_injury_restrictions",
        "create_activity",
        "list_activities",
        "list_pending_rpe",
        "get_activity",
        "submit_activity_rpe",
        "confirm_activity_planned_workout_match",
        "get_workout_registration",
        "confirm_workout_registration",
    }
)

# POST is also used for read-only PostgREST RPCs. Classify by exact RPC name.
READ_RPCS = frozenset(
    {
        "get_current_athlete_id",
        "resolve_legacy_auth_user_id",
        "resolve_opaque_athlete_id_for_auth_user",
        "get_operational_athlete_profile",
        "get_frequency_preferences",
        "get_v6_frequency_context",
        "get_inactive_v6_catalog_for_planning",
        "get_plan_load_history_for_planning_v16",
        "get_v6_mobile_weekly_plan",
        "get_v6_mobile_calendar",
        "get_calendar_rest_days",
        "get_v6_plan_context_for_planning",
        "get_v6_move_workout_context",
        "get_v6_mobile_edit_retry",
        "get_v6_frequency_swipe_receipt",
        "get_checkin_plan_proposal",
        "get_checkin_context_for_planning",
        "get_weekly_checkin",
        "get_activity",
        "list_activities",
        "get_activity_presentation_v2",
        "get_activity_processing_context_v2",
        "get_workout_registration",
        "get_current_planning_eligibility_context",
        "get_previous_week_available_dates",
    }
)
WRITE_RPCS = frozenset(
    {
        "save_identifying_profile",
        "save_physiology_profile",
        "save_operational_athlete_profile",
        "replace_training_history",
        "save_primary_race_goal",
        "save_discipline_zone_setup",
        "save_zone_profile",
        "complete_current_onboarding",
        "save_frequency_preferences",
        "report_frequency_interruption",
        "approve_plan_proposal",
        "reject_plan_proposal",
        "approve_zone_proposal",
        "reject_zone_proposal",
        "create_v6_weekly_plan_proposal",
        "create_weekly_plan_proposal_v3",
        "create_v6_frequency_swipe_draft",
        "update_v6_frequency_swipe_draft",
        "create_v6_frequency_swipe_proposal",
        "move_v6_planned_workout",
        "set_weekly_plan_proposal_explanation",
        "start_weekly_checkin",
        "save_weekly_checkin_context",
        "confirm_weekly_checkin_context",
        "create_activity_summary_v2",
        "create_activity_summary",
        "complete_activity_rpe_v2",
        "complete_activity_rpe",
        "revise_activity_rpe",
        "save_rpe_heart_rate_observation",
        "confirm_activity_planned_workout_match",
        "confirm_workout_registration",
    }
)
READ_TABLES = frozenset(
    {
        "initial_plan_requests",
        "onboarding_sessions",
        "change_proposals",
        "swipe_week_drafts",
        "athlete_identifying_profiles",
        "athlete_physiology_profiles",
        "discipline_zone_setups",
        "goals",
        "training_history_entries",
        "zone_boundaries",
        "zone_metrics",
        "zone_profile_versions",
        "injury_restrictions",
        "calibration_evaluations",
        "calibration_observations",
        "calibration_threshold_decisions",
        "discipline_test_assignments",
    }
)


class RestrictedDataTransport(httpx.AsyncBaseTransport):
    """No arbitrary HTTP, SQL, Auth admin, migrations, grants or provider calls."""

    def __init__(self, manifest: VerificationManifest, kill_file: Path) -> None:
        self.manifest = manifest
        self.kill_file = kill_file
        self.inner: httpx.AsyncBaseTransport = httpx.AsyncHTTPTransport(retries=0)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        custody = _custody.get()
        if (
            custody is None
            or request.url.scheme != "https"
            or request.url.host != self.manifest.hostname
            or request.url.port not in (None, 443)
            or request.url.username
            or request.url.password
        ):
            raise httpx.RequestError("Verification target or identity denied")
        path = request.url.path.removeprefix("/rest/v1/")
        rpc = path.removeprefix("rpc/")
        if (
            request.method == "POST"
            and path == "rpc/" + rpc
            and rpc in READ_RPCS | WRITE_RPCS
        ):
            payload = json.loads(request.content)
            for key in ("p_athlete_id", "p_auth_user_id"):
                if key in payload:
                    expected = (
                        custody.owner.athlete_id
                        if rpc
                        in {"get_v6_frequency_context", "resolve_legacy_auth_user_id"}
                        else custody.owner.auth_subject
                    )
                    if payload[key] != str(expected):
                        raise httpx.RequestError("Verification owner denied")
            if rpc in WRITE_RPCS:
                if (
                    custody.reconciliation_only
                    or self.kill_file.read_text(encoding="utf-8").strip()
                    != self.manifest.digest()
                ):
                    raise httpx.RequestError(
                        "Uncertain mutation requires read reconciliation"
                    )
                custody.attempted_write = True
        elif request.method == "GET" and path in READ_TABLES:
            owner_column = (
                "athlete_id"
                if path
                in {"athlete_identifying_profiles", "athlete_physiology_profiles"}
                else "internal_athlete_id"
            )
            expected_filter = "eq." + str(custody.owner.athlete_id)
            if request.url.params.get(owner_column, expected_filter) != expected_filter:
                raise httpx.RequestError("Verification table owner filter required")
            request.url = request.url.copy_set_param(owner_column, expected_filter)
        else:
            raise httpx.RequestError("Verification operation denied")
        authorization = request.headers.get("authorization")
        if authorization is not None and authorization != "Bearer " + custody.token:
            raise httpx.RequestError("Verification token substitution denied")
        response = await self.inner.handle_async_request(request)
        if response.is_success and rpc in {
            "resolve_legacy_auth_user_id",
            "resolve_opaque_athlete_id_for_auth_user",
        }:
            await response.aread()
            expected_id = (
                custody.owner.auth_subject
                if rpc == "resolve_legacy_auth_user_id"
                else custody.owner.athlete_id
            )
            if response.json() != str(expected_id):
                raise httpx.RequestError("Verification identity map changed")
        return response

    async def aclose(self) -> None:
        await self.inner.aclose()


def public_only(value: Any) -> None:
    """Fail closed; never echo a rejected value or upstream exception."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            if re.search(
                r"tss|privateload|plannedload|realizedload|provenance|evidence|"
                r"frequencycontext|servicerole|secret|v6frozencontext|"
                r"frozenphysiologicalcontext",
                normalized,
            ):
                raise ValueError("Verification response rejected")
            public_only(child)
    elif isinstance(value, list):
        for child in value:
            public_only(child)
    elif isinstance(value, str) and re.search(
        r"\btss\b|\b(?:planned|realized|private)[ _-]?load\b|"
        r"sb_secret_|eyJ[a-zA-Z0-9_-]+\.",
        value,
        re.I,
    ):
        raise ValueError("Verification response rejected")


class MutationJournal:
    """Write-ahead, durable receipts; no automatic replay of an uncertain write."""

    def __init__(self, directory: Path, manifest: VerificationManifest) -> None:
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.manifest = manifest
        self.lock_path = directory / "process.lock"
        self.lock = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(self.lock, str(os.getpid()).encode())
        os.fsync(self.lock)

    def write(self, operation: UUID, record: dict[str, Any]) -> None:
        path = self.directory / (str(operation) + ".json")
        temporary = path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(record, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def begin(
        self,
        operation: UUID,
        custody: RequestCustody,
        method: str,
        path: str,
        query: bytes,
        body: bytes,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if idempotency_key is not None:
            idempotency_key = str(UUID(idempotency_key))
        values = json.loads(body) if body else {}
        preconditions = {
            key: values[key]
            for key in (
                "operation_id",
                "expected_revision",
                "expected_base_revision",
                "plan_revision_id",
                "expected_registration_revision",
                "expected_current_rpe",
            )
            if isinstance(values, dict) and key in values
        }
        fingerprint = hashlib.sha256(
            method.encode() + b"\0" + path.encode() + b"\0" + query + b"\0" + body
        ).hexdigest()
        identity = {
            "run_id": str(self.manifest.run_id),
            "manifest_sha256": self.manifest.digest(),
            "auth_subject": str(custody.owner.auth_subject),
            "athlete_id": str(custody.owner.athlete_id),
            "request_sha256": fingerprint,
            "method": method,
            "path": path,
            "idempotency_key": idempotency_key,
            "preconditions": preconditions,
        }
        record_path = self.directory / (str(operation) + ".json")
        if record_path.exists():
            record: dict[str, Any] = json.loads(record_path.read_text(encoding="utf-8"))
            if any(record.get(k) != v for k, v in identity.items()):
                raise ValueError("Verification operation identity changed")
            custody.reconciliation_only = record["state"] != "complete"
            return record
        # An unresolved sibling operation blocks new mutations for this owner.
        for existing in self.directory.glob("*.json"):
            old = json.loads(existing.read_text(encoding="utf-8"))
            if (
                old["auth_subject"] == identity["auth_subject"]
                and old["state"] != "complete"
            ):
                raise ValueError(
                    "Uncertain verification mutation requires reconciliation"
                )
        record = {**identity, "state": "dispatching"}
        self.write(operation, record)
        return record

    def close(self) -> None:
        os.close(self.lock)
        self.lock_path.unlink()


class VerificationBoundary:
    """Pure ASGI boundary: authentication, owner map, journal, redaction, kill file."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        manifest: VerificationManifest,
        verifier: SupabaseAccessTokenVerifier,
        identity: SupabaseAthleteIdentityRepository,
        journal: MutationJournal,
        kill_file: Path,
        client: httpx.AsyncClient,
        publishable_key: str,
        api_prefix: str,
    ) -> None:
        self.app, self.manifest, self.verifier = app, manifest, verifier
        self.identity, self.journal, self.kill_file = identity, journal, kill_file
        self.serial = asyncio.Lock()
        self.client, self.publishable_key, self.api_prefix = (
            client,
            publishable_key,
            api_prefix,
        )

    async def reconcile_preference(
        self, request: Request, body: bytes, custody: RequestCustody
    ) -> tuple[int, bytes] | None:
        """Read-only proof of an exact committed preference, never resubmit it."""
        if (
            request.method != "PUT"
            or request.url.path != self.api_prefix + "/me/frequency-preferences"
        ):
            return None
        submitted = PreferenceSave.model_validate_json(body)
        response = await self.client.post(
            "https://"
            + self.manifest.hostname
            + "/rest/v1/rpc/get_frequency_preferences",
            headers={
                "apikey": self.publishable_key,
                "Authorization": "Bearer " + custody.token,
            },
            json={},
        )
        response.raise_for_status()
        current = PreferenceResponse.model_validate(response.json())
        if (
            current.operation_id != submitted.operation_id
            or current.revision != submitted.expected_revision + 1
            or current.preferences != submitted.preferences
        ):
            # A superseded/currently absent receipt cannot prove this operation.
            raise ValueError("Exact read reconciliation unavailable")
        return 200, current.model_dump_json().encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        response: Response = JSONResponse(
            {"error": "verification_denied"}, status_code=403
        )
        token_context = None
        try:
            if (
                self.kill_file.read_text(encoding="utf-8").strip()
                != self.manifest.digest()
            ):
                raise ValueError("Verification process disabled")
            scheme, _, token = request.headers.get("authorization", "").partition(" ")
            if scheme.lower() != "bearer" or not token:
                raise InvalidAccessTokenError
            verified = await run_in_threadpool(self.verifier.verify, token)
            owner = next(
                (o for o in self.manifest.owners if o.auth_subject == verified.user_id),
                None,
            )
            if owner is None:
                raise InvalidAccessTokenError
            custody = RequestCustody(owner, token)
            token_context = _custody.set(custody)
            if (
                await self.identity.resolve_current_athlete_id(token)
                != owner.athlete_id
            ):
                raise InvalidAccessTokenError
            body = b""
            async for chunk in request.stream():
                if len(body) + len(chunk) > 262144:
                    raise ValueError("Verification request exceeds envelope")
                body += chunk
            operation = (
                UUID(request.headers["x-verification-operation"])
                if request.method != "GET"
                else None
            )
            async with self.serial:
                record = (
                    self.journal.begin(
                        operation,
                        custody,
                        request.method,
                        request.url.path,
                        scope["query_string"],
                        body,
                        request.headers.get("idempotency-key"),
                    )
                    if operation
                    else None
                )
                if record is not None and record["state"] == "complete":
                    stored_response = base64.b64decode(
                        record["response"], validate=True
                    )
                    if (
                        hashlib.sha256(stored_response).hexdigest()
                        != record["response_sha256"]
                    ):
                        raise ValueError("Verification receipt changed")
                    public_only(json.loads(stored_response))
                    response = Response(
                        stored_response,
                        status_code=record["status"],
                        media_type="application/json",
                    )
                else:
                    messages: list[Message] = []
                    consumed = False

                    async def replay_body() -> Message:
                        nonlocal consumed
                        if consumed:
                            return {"type": "http.disconnect"}
                        consumed = True
                        return {
                            "type": "http.request",
                            "body": body,
                            "more_body": False,
                        }

                    async def capture(message: Message) -> None:
                        messages.append(message)

                    reconciliation = (
                        await self.reconcile_preference(request, body, custody)
                        if custody.reconciliation_only
                        else None
                    )
                    if reconciliation is None:
                        await self.app(scope, replay_body, capture)
                        status = next(
                            m["status"]
                            for m in messages
                            if m["type"] == "http.response.start"
                        )
                        content = b"".join(
                            m.get("body", b"")
                            for m in messages
                            if m["type"] == "http.response.body"
                        )
                    else:
                        status, content = reconciliation
                    public_only(json.loads(content))
                    response = Response(
                        content, status_code=status, media_type="application/json"
                    )
                    if record is not None and operation is not None:
                        record["state"] = (
                            "uncertain"
                            if status >= 500
                            or (
                                status >= 400
                                and (
                                    custody.attempted_write
                                    or custody.reconciliation_only
                                )
                            )
                            else "complete"
                        )
                        record.update(
                            status=status,
                            response=base64.b64encode(content).decode(),
                            response_sha256=hashlib.sha256(content).hexdigest(),
                        )
                        self.journal.write(operation, record)
        except (InvalidAccessTokenError, AthleteIdentityResolutionError):
            response = JSONResponse(
                {"error": "verification_authentication_denied"}, status_code=401
            )
        except Exception:
            # Includes kill/mapping/transport failures and unexpected private DTOs.
            # A dispatching journal record survives and blocks blind retries.
            response = JSONResponse({"error": "verification_denied"}, status_code=403)
        finally:
            if token_context is not None:
                _custody.reset(token_context)
        await response(scope, receive, send)


def verify_isolated_target(
    manifest: VerificationManifest, settings: Settings, management_token: str
) -> None:
    VerificationManifest.model_validate(manifest.model_dump())
    if (
        str(settings.supabase_url).rstrip("/") != "https://" + manifest.hostname
        or settings.supabase_jwt_issuer != manifest.issuer
        or settings.supabase_jwt_audience != manifest.audience
        or settings.supabase_jwks_url != manifest.issuer + "/.well-known/jwks.json"
        or settings.environment != "staging"
        or not settings.supabase_secret_key.get_secret_value()
        or settings.openai_api_key.get_secret_value()
        or settings.polar_client_id
    ):
        raise ValueError("Independent verification configuration mismatch")
    with httpx.Client(
        base_url="https://api.supabase.com", follow_redirects=False, timeout=10
    ) as client:
        response = client.get(
            "/v1/projects/" + manifest.project_ref,
            headers={"Authorization": "Bearer " + management_token},
        )
        response.raise_for_status()
        project = response.json()
        if (
            project.get("id") != manifest.project_ref
            or project.get("status") != "ACTIVE_HEALTHY"
        ):
            raise ValueError("Independently observed target mismatch")
    # Inspect only the two independently manifested synthetic subjects. No list,
    # creation, mail, refresh, grant or configuration mutation is available here.
    with httpx.Client(
        base_url="https://" + manifest.hostname,
        headers={"apikey": settings.supabase_secret_key.get_secret_value()},
        follow_redirects=False,
        timeout=10,
    ) as client:
        for owner in manifest.owners:
            account = client.get("/auth/v1/admin/users/" + str(owner.auth_subject))
            account.raise_for_status()
            if (
                account.json().get("id") != str(owner.auth_subject)
                or account.json().get("email") != owner.email
            ):
                raise ValueError("Independently observed synthetic account mismatch")
            mapping = client.post(
                "/rest/v1/rpc/resolve_legacy_auth_user_id",
                json={"p_athlete_id": str(owner.athlete_id)},
            )
            mapping.raise_for_status()
            if mapping.json() != str(owner.auth_subject):
                raise ValueError("Independently observed owner map mismatch")


def create_verification_app(
    settings: Settings,
    manifest: VerificationManifest,
    *,
    management_token: str,
    journal_directory: Path,
    kill_file: Path,
) -> FastAPI:
    """Owner must first approve/provision target/accounts and protect local paths.

    Use uvicorn with one worker, no access log, loopback bind, and no reload.
    The Management credential is used for this fixed GET only, never retained.
    """
    verify_isolated_target(manifest, settings, management_token)
    transport = RestrictedDataTransport(manifest, kill_file)
    client = httpx.AsyncClient(
        transport=transport,
        follow_redirects=False,
        timeout=settings.supabase_data_api_timeout_seconds,
    )
    repository = InactiveSupabaseV6Repository(settings, client=client)
    catalog = InactiveSupabaseV6CatalogProvider(repository)
    identity = SupabaseAthleteIdentityRepository(settings, client=client)
    activities = SupabaseActivityRepository(settings, client=client)
    # Confined to this independent factory; ordinary Settings/startup stay closed.
    activities._v2_ready = activities._v2_selection = True
    verifier = SupabaseAccessTokenVerifier(settings)
    app = create_app(
        settings,
        access_token_verifier=verifier,
        planning_repository=repository,
        planning_catalog_provider=catalog,
        athlete_identity_repository=identity,
        activity_repository=activities,
        checkin_repository=SupabaseCheckInRepository(settings, client=client),
        onboarding_repository=SupabaseOnboardingRepository(settings, client=client),
        calibration_repository=SupabaseCalibrationRepository(settings, client=client),
        weekly_plan_coach=DisabledWeeklyPlanCoach(),
        checkin_context_coach=DisabledCheckInContextCoach(),
    )
    app.router.routes.clear()
    selected_routes = APIRouter()
    for source in (
        identity_router,
        onboarding_router,
        frequency_router,
        calibration_router,
        planning_router,
        checkins_router,
        activities_router,
    ):
        selected_routes.routes.extend(
            r for r in source.routes if isinstance(r, APIRoute) and r.name in ROUTES
        )
    app.include_router(selected_routes, prefix=settings.api_v1_prefix)

    async def private_safe_failure(request: Request, error: Exception) -> Response:
        # Override normal traceback logging for this isolated verification process.
        return JSONResponse({"error": "verification_failed"}, status_code=503)

    app.add_exception_handler(Exception, private_safe_failure)

    def planning(request: Request) -> V6PlanningService:
        return V6PlanningService(
            repository,
            catalog,
            app.state.weekly_plan_coach,
            request.app.state.planning_computation,
        )

    class VerificationCheckInService(CheckInService):
        async def generate_plan_proposal(
            self, access_token: str, athlete_id: UUID, checkin_id: UUID
        ) -> WeeklyPlanProposalResponse:
            response = await super().generate_plan_proposal(
                access_token, athlete_id, checkin_id
            )
            response.plan.workouts = await cast(
                V6PlanningService, self._planning_service
            )._present_workouts(response.plan.workouts)
            return response

    def checkins(request: Request) -> CheckInService:
        return VerificationCheckInService(
            request.app.state.checkin_repository,
            planning(request),
            request.app.state.checkin_context_coach,
        )

    app.dependency_overrides[get_planning_service] = planning
    app.dependency_overrides[get_checkin_service] = checkins
    app.dependency_overrides[get_activity_service] = lambda: ActivityService(
        activities, enable_estimates=True
    )
    journal = MutationJournal(journal_directory, manifest)
    app.add_middleware(
        VerificationBoundary,
        manifest=manifest,
        verifier=verifier,
        identity=identity,
        journal=journal,
        kill_file=kill_file,
        client=client,
        publishable_key=settings.supabase_publishable_key,
        api_prefix=settings.api_v1_prefix,
    )
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            async with original_lifespan(application):
                yield
        finally:
            await client.aclose()
            journal.close()

    app.router.lifespan_context = lifespan
    return app
