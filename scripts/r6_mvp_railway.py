"""Run the real-token MVP flow against an explicitly supplied staging URL.

Only tagged development Auth users are created. No response bodies or tokens
are logged; failed gates report endpoint/status and always clean up test users.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from r6_real_token_security import (
    ROOT,
    VerificationError,
    assert_no_private_load_keys,
    call,
    create_actor,
    delete_user,
    load_env,
    require_status,
)


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("https://r6-api-"):
        raise VerificationError("provide the explicit r6-api staging HTTPS URL")
    api = sys.argv[1].rstrip("/")
    env = load_env(ROOT / "backend" / ".env")
    db = env["START23_SUPABASE_URL"]
    if db.rstrip("/") != "https://isfumhgqphieoayqahjv.supabase.co":
        raise VerificationError("wrong Supabase target")
    key = env["START23_SUPABASE_PUBLISHABLE_KEY"]
    secret = env["START23_SUPABASE_SECRET_KEY"]
    cli = os.environ.get("R6_SUPABASE_CLI")
    if not cli:
        raise VerificationError(
            "R6_SUPABASE_CLI is required for the guarded legacy fixture"
        )
    users: list[str] = []
    actors: list[tuple[str, str, str, str]] = []

    def request(token, method, path, body=None, statuses=None, headers=None):
        response = call(
            api,
            method,
            "/api/v1" + path,
            api_key=key,
            bearer=token,
            body=body,
            extra_headers=headers,
            timeout_seconds=20,
        )
        if response.status not in (statuses or {200, 201}):
            assert_no_private_load_keys(response.payload)
            error = (
                response.payload.get("error", {})
                if isinstance(response.payload, dict)
                else {}
            )
            if isinstance(error, dict):
                print("Public failure:", error.get("code"), error.get("message"))
        payload = require_status(response, statuses or {200, 201}, method + " " + path)
        assert_no_private_load_keys(payload)
        return payload

    try:
        for label in ("a", "b"):
            auth_id, token = create_actor(db, key, secret, label)
            users.append(auth_id)
            if label == "b":
                fixture = (
                    ROOT / "scripts" / "r6_legacy_onboarding_fixture.sql"
                ).read_text()
                result = subprocess.run(
                    [
                        cli,
                        "db",
                        "query",
                        "--project-ref",
                        "isfumhgqphieoayqahjv",
                        fixture.replace("__R6_AUTH_ID__", str(UUID(auth_id))),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if result.returncode or '"_tag": "Error"' in result.stdout:
                    raise VerificationError("guarded legacy fixture failed")
            initial = request(token, "GET", "/onboarding")
            if label == "b" and not initial["upgrade_required"]:
                raise VerificationError(
                    "legacy completion was incorrectly treated as current"
                )
            request(
                token,
                "PATCH",
                "/me/identifying-profile",
                {
                    "first_name": "R6",
                    "last_name": label,
                },
            )
            request(
                token,
                "PATCH",
                "/me/physiology-profile",
                {
                    "date_of_birth": "1990-01-01",
                    "resting_heart_rate_bpm": 55,
                },
            )
            request(
                token,
                "PATCH",
                "/me/operational-profile",
                {
                    "heart_rate_monitor_confirmed": True,
                    "timezone": "Europe/Amsterdam",
                    "timezone_source": "manual",
                    "timezone_confirmed": True,
                },
            )
            goal_body = {
                "race_type": "run",
                "race_name": "R6 staging race",
                "race_date": (
                    datetime.now(timezone.utc).date() + timedelta(days=180)
                ).isoformat(),
                "run_distance_meters": 10000,
                "total_target_time_seconds": 3600,
            }
            goal = request(token, "POST", "/me/goals", goal_body)
            request(
                token,
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
                token,
                "PUT",
                "/onboarding/disciplines/run/setup",
                {
                    "setup_route": "calibration_week",
                    "guidance_mode": "heart_rate",
                },
            )
            now = datetime.now(timezone.utc).isoformat()
            summary = {
                "discipline": "run",
                "started_at": now,
                "timezone": "Europe/Amsterdam",
                "duration_minutes": 40,
                "distance_meters": 5000,
                "metrics": {
                    "average_heart_rate_bpm": 148,
                    "zone_minutes": [10, 15, 5, 0, 0],
                },
            }
            idem = {"Idempotency-Key": str(uuid4())}
            activity = request(token, "POST", "/activities", summary, headers=idem)
            replay = request(token, "POST", "/activities", summary, headers=idem)
            if activity["id"] != replay["id"]:
                raise VerificationError("activity retry is not idempotent")
            request(
                token,
                "POST",
                "/activities",
                {**summary, "distance_meters": 5100},
                statuses={409},
                headers=idem,
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
                    "performed_at": now,
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
                request(token, "POST", "/calibration/observations", observation)
            evaluation = request(
                token,
                "POST",
                "/calibration/evaluate",
                {
                    "activity_id": activity["id"],
                    "protocol_id": protocol,
                },
            )
            decision = request(
                token,
                "POST",
                f"/calibration/evaluations/{evaluation['id']}/threshold/confirm",
                {"confirmed": True},
            )
            if decision["zone_proposal_state"] != "pending":
                raise VerificationError("calibration did not remain pending")
            proposal_id = decision["zone_proposal_id"]
            request(
                token,
                "POST",
                f"/change-proposals/{proposal_id}/approve",
                {"expected_base_zone_profile_id": str(uuid4())},
                statuses={409},
            )
            request(
                token,
                "POST",
                f"/change-proposals/{proposal_id}/approve",
                {"expected_base_zone_profile_id": decision["base_zone_profile_id"]},
            )
            state = request(token, "GET", "/onboarding")
            if not state["can_complete"]:
                raise VerificationError(
                    "onboarding remains incomplete after approved calibration"
                )
            request(
                token,
                "POST",
                "/onboarding/complete",
                {"expected_onboarding_revision": state["onboarding_revision"]},
            )
            resumed = request(token, "GET", "/onboarding")
            if resumed["upgrade_required"] or resumed["status"] != "completed":
                raise VerificationError("completed onboarding did not resume")
            actors.append((token, goal["id"], activity["id"], evaluation["id"]))
            print(
                f"PASS Railway user {label}: profile/monitor/timezone/race/history/calibration/pending/approval/onboarding"
            )

        for actor, other in ((actors[0], actors[1]), (actors[1], actors[0])):
            token, _, _, _ = actor
            request(token, "GET", f"/activities/{other[2]}", statuses={404})
            request(
                token, "PUT", f"/activities/{other[2]}/rpe", {"rpe": 4}, statuses={404}
            )
            request(
                token,
                "POST",
                f"/calibration/evaluations/{other[3]}/threshold/confirm",
                {"confirmed": True},
                statuses={404},
            )
            request(
                token, "PUT", f"/me/goals/{other[1]}", goal_body, statuses={404, 409}
            )
        print("PASS Railway inverse goal/activity/calibration ownership")

        token = actors[0][0]
        today = datetime.now(timezone.utc).date()
        monday = today - timedelta(days=today.weekday())
        plan = request(
            token,
            "POST",
            "/weekly-plans/proposals",
            {
                "week_start": monday.isoformat(),
                "available_dates": [
                    (monday + timedelta(days=i)).isoformat() for i in range(7)
                ],
            },
        )
        print("PASS Railway pending planning proposal")
        proposal = plan["proposal"]
        request(
            actors[1][0], "GET", f"/weekly-plans/{plan['plan']['id']}", statuses={404}
        )
        request(
            token,
            "POST",
            f"/change-proposals/{proposal['id']}/approve",
            {"expected_base_revision": 999},
            statuses={409},
        )
        request(
            token,
            "POST",
            f"/change-proposals/{proposal['id']}/approve",
            {"expected_base_revision": proposal["base_plan_revision"] or 0},
        )
        processed = request(token, "PUT", f"/activities/{actors[0][2]}/rpe", {"rpe": 4})
        if processed["processing_state"] != "complete":
            raise VerificationError("activity processing incomplete")
        print("PASS Railway plan approval and realized activity processing")
        checkin = request(
            token,
            "POST",
            "/checkins",
            {
                "week_start": (monday + timedelta(days=7)).isoformat(),
            },
        )
        path = f"/checkins/{checkin['id']}"
        context_body = {
            "expected_revision": checkin["context_revision"],
            "recurring_activities_confirmed": True,
        }
        context = request(token, "PUT", path + "/context", context_body)
        request(
            token,
            "PUT",
            path + "/context",
            {**context_body, "fatigue_level": "high"},
            statuses={409},
        )
        request(
            token,
            "POST",
            path + "/context-confirmation",
            {
                "expected_revision": context["context_revision"],
                "context_fingerprint": context["context"]["fingerprint"],
            },
        )
        next_plan = request(token, "POST", path + "/plan-proposals")
        if next_plan["proposal"]["state"] != "pending":
            raise VerificationError("next-week proposal automatically applied")
        print("PASS Railway next-week pending progression and stale context conflict")
        print(
            json.dumps(
                {
                    "status": "pass",
                    "legacy_fixture": "representative legacy completed session, no historical plan",
                }
            )
        )
    finally:
        failures = sum(not delete_user(db, secret, user) for user in reversed(users))
        print(
            f"{'FAIL' if failures else 'PASS'} Railway temporary-user cleanup: {len(users) - failures}/{len(users)}"
        )
        if failures:
            raise VerificationError("temporary-user cleanup failed")


if __name__ == "__main__":
    try:
        main()
    except VerificationError as error:
        print(f"FAIL {error}", file=sys.stderr)
        raise SystemExit(1) from error
