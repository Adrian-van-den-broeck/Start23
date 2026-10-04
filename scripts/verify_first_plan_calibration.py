"""Reproduce the first-plan calibration regression on start23-dev only.

Creates exactly one disposable athlete through the normal API lifecycle, verifies
private provenance locally without logging load, then reads the hosted swipe deck.
Always revokes its session and deletes the owned athlete. No historical writes.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

sys.dont_write_bytecode = True

from r6_real_token_security import (
    assert_no_private_load_keys,
    call,
    delete_user,
    load_env,
    require_status,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
API = "https://r6-api-r6-staging.up.railway.app"
DB = "https://isfumhgqphieoayqahjv.supabase.co"
WEEK = date(2026, 10, 5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path)
    args = parser.parse_args()
    env = load_env(args.env_file)
    assert env["START23_SUPABASE_URL"].rstrip("/") == DB
    public = env["START23_SUPABASE_PUBLISHABLE_KEY"]
    secret = env["START23_SUPABASE_SECRET_KEY"]
    purpose = "first-plan-calibration-" + secrets.token_hex(10)
    email = purpose + "@example.com"
    password = "Regression!" + secrets.token_hex(24) + "A9"
    auth_id: str | None = None
    token: str | None = None

    def request(method: str, path: str, body: Any = None, **kwargs: Any) -> Any:
        assert token is not None
        response = call(
            API,
            method,
            "/api/v1" + path,
            api_key=public,
            bearer=token,
            body=body,
            **kwargs,
        )
        assert_no_private_load_keys(response.payload)
        return require_status(response, {200, 201}, method + " " + path)

    try:
        created = require_status(
            call(
                DB,
                "POST",
                "/auth/v1/admin/users",
                api_key=secret,
                bearer=secret,
                body={
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"purpose": purpose},
                },
            ),
            {200, 201},
            "create one disposable athlete",
        )
        auth_id = created["id"]
        signed = require_status(
            call(
                DB,
                "POST",
                "/auth/v1/token?grant_type=password",
                api_key=public,
                bearer=public,
                body={"email": email, "password": password},
            ),
            {200},
            "sign in disposable athlete",
        )
        token = signed["access_token"]
        request(
            "PATCH",
            "/me/identifying-profile",
            {"first_name": "Regression", "last_name": "Calibration"},
        )
        request(
            "PATCH",
            "/me/physiology-profile",
            {"date_of_birth": "1990-01-01", "resting_heart_rate_bpm": 55},
        )
        request(
            "PATCH",
            "/me/operational-profile",
            {
                "heart_rate_monitor_confirmed": True,
                "timezone": "Europe/Amsterdam",
                "timezone_source": "manual",
                "timezone_confirmed": True,
            },
        )
        request(
            "POST",
            "/me/goals",
            {
                "race_type": "run",
                "race_name": "Disposable regression",
                "race_date": "2027-04-04",
                "run_distance_meters": 10000,
                "total_target_time_seconds": 3600,
            },
        )
        request(
            "PUT",
            "/me/training-history",
            {
                "entries": [
                    {"discipline": sport, "average_hours_per_week": hours}
                    for sport, hours in (("swim", 0), ("bike", 0), ("run", 3))
                ]
            },
        )
        request(
            "PUT",
            "/onboarding/disciplines/run/setup",
            {
                "setup_route": "calibration_week",
                "guidance_mode": "heart_rate",
            },
        )
        # Fixed local week reproduces the original history/race-anchor sequence.
        performed = "2026-10-02T10:00:00+00:00"
        activity = request(
            "POST",
            "/activities",
            {
                "discipline": "run",
                "started_at": performed,
                "timezone": "Europe/Amsterdam",
                "duration_minutes": 40,
                "distance_meters": 5000,
                "metrics": {
                    "average_heart_rate_bpm": 148,
                    "zone_minutes": [10, 15, 5, 0, 0],
                },
            },
            extra_headers={"Idempotency-Key": str(uuid4())},
        )
        protocol = "start23_week1_run_calibration_v1"
        for segment, rpe, duration in (
            ("warmup", 3, 600),
            ("comfortable_20min", 4, 1200),
            ("cooldown", 2, 600),
        ):
            observation = {
                "activity_id": activity["id"],
                "protocol_id": protocol,
                "discipline": "run",
                "segment_id": segment,
                "performed_at": performed,
                "completed": True,
                "quality_status": "sufficient",
                "target_rpe": rpe,
                "duration_seconds": duration,
            }
            if segment == "comfortable_20min":
                observation.update(
                    reported_block_rpe=4,
                    steady_execution="yes",
                    average_heart_rate_bpm=148,
                )
            request("POST", "/calibration/observations", observation)
        evaluation = request(
            "POST",
            "/calibration/evaluate",
            {
                "activity_id": activity["id"],
                "protocol_id": protocol,
            },
        )
        decision = request(
            "POST",
            f"/calibration/evaluations/{evaluation['id']}/threshold/confirm",
            {"confirmed": True},
        )
        assert decision["zone_proposal_state"] == "pending"
        request(
            "POST",
            f"/change-proposals/{decision['zone_proposal_id']}/approve",
            {"expected_base_zone_profile_id": decision["base_zone_profile_id"]},
        )
        state = request("GET", "/onboarding")
        assert state["can_complete"]
        request(
            "POST",
            "/onboarding/complete",
            {"expected_onboarding_revision": state["onboarding_revision"]},
        )
        state = request("GET", "/onboarding")
        assert state["status"] == "completed" and not state["upgrade_required"]
        athlete_id = UUID(state["profile"]["athlete_id"])

        async def verify_private_context() -> None:
            from app.core.config import Settings
            from app.modules.coach.weekly_plan import DisabledWeeklyPlanCoach
            from app.modules.planning.domain import PlanningTargetBasis
            from app.modules.planning.repository import SupabasePlanningRepository
            from app.modules.planning.service import (
                PlanningService,
                SupabasePlanningCatalogProvider,
            )
            from app.modules.workouts.catalog import TrainingPhase
            from app.modules.workouts.repository import SupabaseWorkoutCatalogRepository

            settings = Settings(
                _env_file=None,
                environment="local",
                supabase_url=DB,
                supabase_publishable_key=public,
                supabase_secret_key=secret,
                openai_api_key="",
            )
            repository = SupabasePlanningRepository(settings)
            catalog = SupabasePlanningCatalogProvider(
                SupabaseWorkoutCatalogRepository(settings)
            )
            try:
                history = await repository.fetch_load_history(athlete_id, WEEK)
                assert history and any(r["completed_activity_count"] for r in history)
                assert all(r["has_prior_approved_plan"] is False for r in history)
                source = await repository.fetch_initial_request(token, athlete_id)
                assert source is not None
                context = await PlanningService(
                    repository, catalog, DisabledWeeklyPlanCoach()
                )._prepare_swipe_context(
                    athlete_id=athlete_id,
                    input_source=source,
                    initial_plan_request_id=UUID(source["id"]),
                    plan_id=None,
                    base_plan_revision=0,
                    context_plan_revision=None,
                    week_start=WEEK,
                    available_dates=tuple(WEEK + timedelta(days=d) for d in (0, 2, 5)),
                    availability_source="explicit",
                    injuries=frozenset(),
                    low_only_disciplines=frozenset(),
                )
                assert context.target.phase is TrainingPhase.BASE
                assert (
                    context.target.basis is PlanningTargetBasis.INITIAL_CATALOG_BASELINE
                )
                assert context.automatic_template_ids and context.eligible_deck
                print(
                    "PASS private provenance: activity history present; no approved "
                    "plan; onboarding BASE; valid workout combination",
                    flush=True,
                )
            finally:
                await repository.aclose()
                await catalog.aclose()

        asyncio.run(verify_private_context())
        response = call(
            API,
            "POST",
            "/api/v1/weekly-plans/swipe-drafts",
            api_key=public,
            bearer=token,
            body={
                "week_start": WEEK.isoformat(),
                "available_dates": [
                    (WEEK + timedelta(days=d)).isoformat() for d in (0, 2, 5)
                ],
                "confirmed_injuries": [],
                "cross_training_opt_ins": [],
            },
        )
        assert_no_private_load_keys(response.payload)
        draft = require_status(response, {201}, "first weekly swipe draft")
        loaded = request("GET", f"/weekly-plans/swipe-drafts/{draft['id']}")
        assert loaded["current_candidate"] is not None
        assert loaded["target_workout_count"] > 0
        assert "tss" not in str(loaded).casefold()
        assert "planned_load" not in str(loaded).casefold()
        print(
            "PASS hosted first swipe draft: HTTP 201; deck GET 200; workouts "
            "available; no capacity error or private-load leak",
            flush=True,
        )
        proposal = request(
            "POST",
            "/weekly-plans/proposals",
            {
                "week_start": WEEK.isoformat(),
                "available_dates": [
                    (WEEK + timedelta(days=d)).isoformat() for d in (0, 2, 5)
                ],
            },
        )
        assert proposal["plan"]["workouts"]
        request(
            "POST",
            f"/change-proposals/{proposal['proposal']['id']}/approve",
            {"expected_base_revision": 0},
        )

        async def verify_returning_context() -> None:
            from decimal import Decimal

            from app.core.config import Settings
            from app.modules.physiology.models import InternalLoad
            from app.modules.planning.domain import PlanningTargetBasis, resolve_target
            from app.modules.planning.repository import SupabasePlanningRepository
            from app.modules.planning.service import PlanningService
            from app.modules.workouts.catalog import TrainingPhase

            repository = SupabasePlanningRepository(
                Settings(
                    _env_file=None,
                    environment="local",
                    supabase_url=DB,
                    supabase_publishable_key=public,
                    supabase_secret_key=secret,
                    openai_api_key="",
                )
            )
            try:
                history = await repository.fetch_load_history(
                    athlete_id, WEEK + timedelta(days=7)
                )
                assert history and all(r["has_prior_approved_plan"] for r in history)
                target = resolve_target(
                    week_start=WEEK + timedelta(days=7),
                    race_date=date(2027, 4, 4),
                    prior_loads=PlanningService._load_samples(history),
                    initial_catalog_load=InternalLoad(Decimal("194.1")),
                )
                assert target.phase is TrainingPhase.BUILD
                assert target.basis is PlanningTargetBasis.REALIZED_PROGRESSION
                print(
                    "PASS returning athlete: persisted approved revision; "
                    "BUILD/missed-week progression, not first-plan BASE",
                    flush=True,
                )
            finally:
                await repository.aclose()

        asyncio.run(verify_returning_context())
    finally:
        if auth_id is not None:
            owner = require_status(
                call(
                    DB,
                    "GET",
                    "/auth/v1/admin/users/" + auth_id,
                    api_key=secret,
                    bearer=secret,
                ),
                {200},
                "guard disposable cleanup",
            )
            assert owner["user_metadata"]["purpose"] == purpose
            assert owner["email"] == email
            if token is not None:
                require_status(
                    call(
                        DB,
                        "POST",
                        "/auth/v1/logout?scope=global",
                        api_key=public,
                        bearer=token,
                    ),
                    {200, 204},
                    "revoke sessions",
                )
            assert delete_user(DB, secret, auth_id)
            absent = call(
                DB,
                "GET",
                "/auth/v1/admin/users/" + auth_id,
                api_key=secret,
                bearer=secret,
            )
            assert absent.status == 404
            print(
                "PASS cleanup: one created/one deleted; sessions revoked; Auth GET 404",
                flush=True,
            )


if __name__ == "__main__":
    main()
