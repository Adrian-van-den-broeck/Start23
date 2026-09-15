"""R6 two-user Supabase Auth/RLS verification against non-production.

The script reads local backend configuration, creates two short-lived confirmed
Auth users, exercises the hosted Data API with their real access tokens, and
deletes both users in a finally block. It never prints keys, passwords, tokens,
email addresses, profile values, or response bodies.
"""

from __future__ import annotations

import json
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]


class VerificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    payload: Any


@dataclass(frozen=True)
class Actor:
    auth_user_id: str
    athlete_id: str
    access_token: str
    goal_id: str
    activity_id: str
    activity_idempotency_key: str
    activity_fingerprint: str


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def call(
    base_url: str,
    method: str,
    path: str,
    *,
    api_key: str,
    bearer: str,
    body: Any | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout_seconds: int = 30,
) -> Response:
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=encoded,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            return Response(response.status, json.loads(raw) if raw else None)
    except HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            payload: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = None
        return Response(error.code, payload)


def require_status(response: Response, allowed: set[int], label: str) -> Any:
    if response.status not in allowed:
        code = (
            response.payload.get("code") if isinstance(response.payload, dict) else None
        )
        raise VerificationError(f"{label}: HTTP {response.status}, code={code!r}")
    return response.payload


def rpc(
    base_url: str,
    publishable_key: str,
    access_token: str,
    name: str,
    body: dict[str, Any],
    *,
    timeout_seconds: int = 30,
) -> Response:
    return call(
        base_url,
        "POST",
        f"/rest/v1/rpc/{name}",
        api_key=publishable_key,
        bearer=access_token,
        body=body,
        timeout_seconds=timeout_seconds,
    )


def assert_no_private_load_keys(value: Any, path: str = "$") -> None:
    forbidden = {"tss", "planned_tss", "realized_tss", "private_load"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in forbidden:
                raise VerificationError(f"private-load key exposed at {path}.{key}")
            assert_no_private_load_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_private_load_keys(child, f"{path}[{index}]")


def create_actor(
    base_url: str,
    publishable_key: str,
    secret_key: str,
    label: str,
) -> tuple[str, str]:
    nonce = secrets.token_hex(10)
    email = f"start23-r6-{label}-{nonce}@example.com"
    password = f"R6!{secrets.token_urlsafe(32)}a9"
    created = call(
        base_url,
        "POST",
        "/auth/v1/admin/users",
        api_key=secret_key,
        bearer=secret_key,
        body={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"purpose": "phase-13-14-r6"},
        },
    )
    created_payload = require_status(created, {200, 201}, f"create Auth user {label}")
    auth_user_id = str(created_payload["id"])

    signed_in = call(
        base_url,
        "POST",
        "/auth/v1/token?grant_type=password",
        api_key=publishable_key,
        bearer=publishable_key,
        body={"email": email, "password": password},
    )
    signed_in_payload = require_status(signed_in, {200}, f"sign in Auth user {label}")
    return auth_user_id, str(signed_in_payload["access_token"])


def provision_actor(
    base_url: str,
    publishable_key: str,
    auth_user_id: str,
    access_token: str,
    label: str,
) -> Actor:
    mapped = rpc(base_url, publishable_key, access_token, "get_current_athlete_id", {})
    athlete_id = str(require_status(mapped, {200}, f"resolve opaque identity {label}"))
    UUID(athlete_id)
    if athlete_id == auth_user_id:
        raise VerificationError(f"{label}: opaque identity equals Auth UUID")

    identifying = rpc(
        base_url,
        publishable_key,
        access_token,
        "save_identifying_profile",
        {"p_profile": {"first_name": f"R6-{label}", "last_name": "Security"}},
    )
    require_status(identifying, {200}, f"save identifying profile {label}")

    physiology = rpc(
        base_url,
        publishable_key,
        access_token,
        "save_physiology_profile",
        {"p_profile": {"date_of_birth": "1990-01-01", "resting_heart_rate_bpm": 55}},
    )
    require_status(physiology, {200}, f"save physiology profile {label}")

    operational = rpc(
        base_url,
        publishable_key,
        access_token,
        "save_operational_athlete_profile",
        {
            "p_profile": {
                "timezone": "Europe/Amsterdam",
                "timezone_source": "manual",
                "timezone_confirmed": True,
                "heart_rate_monitor_confirmed": True,
            }
        },
    )
    require_status(operational, {200}, f"save operational profile {label}")

    history = rpc(
        base_url,
        publishable_key,
        access_token,
        "replace_training_history",
        {
            "p_entries": [
                {"discipline": "swim", "average_hours_per_week": 2},
                {"discipline": "bike", "average_hours_per_week": 4},
                {"discipline": "run", "average_hours_per_week": 3},
            ]
        },
    )
    require_status(history, {200}, f"save previous-month history {label}")

    race_date = (datetime.now(timezone.utc).date() + timedelta(days=365)).isoformat()
    goal = rpc(
        base_url,
        publishable_key,
        access_token,
        "save_primary_race_goal",
        {
            "p_goal_id": None,
            "p_race_type": "run",
            "p_race_name": f"R6 {label} race",
            "p_race_date": race_date,
            "p_swim_distance_meters": None,
            "p_bike_distance_meters": None,
            "p_run_distance_meters": 10000,
            "p_total_target_time_seconds": 3600,
            "p_swim_target_time_seconds": None,
            "p_bike_target_time_seconds": None,
            "p_run_target_time_seconds": 3600,
            "p_specific_focus": "R6 isolation verification",
        },
    )
    goal_payload = require_status(goal, {200}, f"save race goal {label}")
    goal_id = str(goal_payload["id"])
    UUID(goal_id)

    idempotency_key = str(uuid4())
    fingerprint = secrets.token_hex(32)
    activity = rpc(
        base_url,
        publishable_key,
        access_token,
        "create_activity_summary",
        {
            "p_idempotency_key": idempotency_key,
            "p_request_fingerprint": fingerprint,
            "p_payload": {
                "discipline": "run",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "timezone": "Europe/Amsterdam",
                "duration_minutes": 30,
                "distance_meters": 5000,
                "metrics": {
                    "average_heart_rate_bpm": 150,
                    "max_heart_rate_bpm": 170,
                    "low_intensity_minutes": 30,
                    "high_intensity_minutes": 0,
                },
            },
        },
    )
    activity_payload = require_status(activity, {200}, f"create activity {label}")
    assert_no_private_load_keys(activity_payload)
    activity_id = str(activity_payload["id"])
    UUID(activity_id)

    replay = rpc(
        base_url,
        publishable_key,
        access_token,
        "create_activity_summary",
        {
            "p_idempotency_key": idempotency_key,
            "p_request_fingerprint": fingerprint,
            "p_payload": {"retry_payload_is_ignored": True},
        },
    )
    replay_payload = require_status(replay, {200}, f"replay activity {label}")
    assert_no_private_load_keys(replay_payload)
    if str(replay_payload.get("id")) != activity_id:
        raise VerificationError(f"{label}: activity retry created a different row")

    return Actor(
        auth_user_id,
        athlete_id,
        access_token,
        goal_id,
        activity_id,
        idempotency_key,
        fingerprint,
    )


def verify_activity_conflict(
    base_url: str,
    publishable_key: str,
    actor: Actor,
) -> None:
    try:
        conflict = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "create_activity_summary",
            {
                "p_idempotency_key": actor.activity_idempotency_key,
                "p_request_fingerprint": secrets.token_hex(32),
                "p_payload": {"discipline": "run"},
            },
            timeout_seconds=10,
        )
    except TimeoutError as error:
        raise VerificationError(
            "hosted activity idempotency conflict did not return within 10 seconds"
        ) from error
    conflict_code = (
        conflict.payload.get("code") if isinstance(conflict.payload, dict) else None
    )
    if conflict.status != 409 or conflict_code != "PT409":
        raise VerificationError(
            "activity idempotency conflict: "
            f"HTTP {conflict.status}, code={conflict_code!r}"
        )


def rest_rows(
    base_url: str,
    publishable_key: str,
    actor: Actor,
    path: str,
    label: str,
) -> list[dict[str, Any]]:
    response = call(
        base_url,
        "GET",
        f"/rest/v1/{path}",
        api_key=publishable_key,
        bearer=actor.access_token,
    )
    rows = require_status(response, {200}, label)
    if not isinstance(rows, list):
        raise VerificationError(f"{label}: expected row list")
    assert_no_private_load_keys(rows)
    return rows


def verify_actor_surface(
    base_url: str,
    publishable_key: str,
    actor: Actor,
) -> tuple[int, list[str]]:
    owner_tables = [
        "athlete_identifying_profiles",
        "athlete_physiology_profiles",
        "onboarding_sessions",
        "training_history_entries",
        "goals",
        "zone_profile_versions",
        "zone_metrics",
        "zone_boundaries",
        "change_proposals",
        "initial_plan_requests",
        "weekly_plans",
        "plan_revisions",
        "planned_workouts",
        "plan_warnings",
        "activities",
        "activity_metrics",
        "weekly_checkins",
        "weekly_checkin_contexts",
        "injury_restrictions",
        "planned_external_activities",
        "goal_maintenance_states",
        "activity_rpe_revisions",
        "discipline_zone_setups",
        "calibration_observations",
        "calibration_evaluations",
        "calibration_threshold_decisions",
        "provider_connections",
        "import_runs",
        "activity_files",
        "discipline_test_assignments",
        "swipe_week_drafts",
        "onboarding_completion_records",
    ]
    denied: list[str] = []
    checked = 0
    for table in owner_tables:
        response = call(
            base_url,
            "GET",
            f"/rest/v1/{table}?select=*&limit=100",
            api_key=publishable_key,
            bearer=actor.access_token,
        )
        if response.status in {401, 403, 404}:
            denied.append(table)
            continue
        rows = require_status(response, {200}, f"list own surface {table}")
        if not isinstance(rows, list):
            raise VerificationError(f"list own surface {table}: expected row list")
        assert_no_private_load_keys(rows)
        for row in rows:
            legacy_owner = row.get("athlete_id")
            opaque_owner = row.get("internal_athlete_id")
            if legacy_owner is not None and legacy_owner not in {
                actor.auth_user_id,
                actor.athlete_id,
            }:
                raise VerificationError(f"{table}: foreign athlete_id visible")
            if opaque_owner is not None and opaque_owner != actor.athlete_id:
                raise VerificationError(f"{table}: foreign internal_athlete_id visible")
        checked += 1
    return checked, denied


def verify_two_user_boundaries(
    base_url: str,
    publishable_key: str,
    secret_key: str,
    actor_a: Actor,
    actor_b: Actor,
) -> None:
    if actor_a.athlete_id == actor_b.athlete_id:
        raise VerificationError("two Auth users resolved to the same opaque athlete")

    for actor, other, label in (
        (actor_a, actor_b, "A versus B"),
        (actor_b, actor_a, "B versus A"),
    ):
        foreign_identifying = rest_rows(
            base_url,
            publishable_key,
            actor,
            "athlete_identifying_profiles?select=athlete_id&athlete_id=eq."
            + quote(other.athlete_id),
            f"cross-read identifying profile {label}",
        )
        if foreign_identifying:
            raise VerificationError(
                f"cross-read identifying profile succeeded: {label}"
            )

        foreign_physiology = rest_rows(
            base_url,
            publishable_key,
            actor,
            "athlete_physiology_profiles?select=athlete_id&athlete_id=eq."
            + quote(other.athlete_id),
            f"cross-read physiology profile {label}",
        )
        if foreign_physiology:
            raise VerificationError(f"cross-read physiology profile succeeded: {label}")

        foreign_goal = rest_rows(
            base_url,
            publishable_key,
            actor,
            "goals?select=id&id=eq." + quote(other.goal_id),
            f"cross-read goal {label}",
        )
        if foreign_goal:
            raise VerificationError(f"cross-read goal succeeded: {label}")

        foreign_activity = rest_rows(
            base_url,
            publishable_key,
            actor,
            "activities?select=id&id=eq." + quote(other.activity_id),
            f"cross-read activity {label}",
        )
        if foreign_activity:
            raise VerificationError(f"cross-read activity succeeded: {label}")

        foreign_activity_rpc = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "get_activity",
            {"p_activity_id": other.activity_id},
        )
        foreign_activity_code = (
            foreign_activity_rpc.payload.get("code")
            if isinstance(foreign_activity_rpc.payload, dict)
            else None
        )
        if (
            foreign_activity_rpc.status not in {400, 404, 500}
            or foreign_activity_code != "P0002"
        ):
            raise VerificationError(
                f"cross-read activity RPC {label}: "
                f"HTTP {foreign_activity_rpc.status}, code={foreign_activity_code!r}"
            )

        tamper_goal = call(
            base_url,
            "PATCH",
            "/rest/v1/goals?id=eq." + quote(other.goal_id),
            api_key=publishable_key,
            bearer=actor.access_token,
            body={"race_name": "cross-owner mutation"},
            extra_headers={"Prefer": "return=representation"},
        )
        if tamper_goal.status == 200 and tamper_goal.payload:
            raise VerificationError(f"cross-owner goal mutation succeeded: {label}")
        require_status(
            tamper_goal, {200, 401, 403}, f"cross-owner goal mutation {label}"
        )

        forged_owner = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "save_identifying_profile",
            {
                "p_profile": {
                    "athlete_id": other.athlete_id,
                    "first_name": "forged",
                }
            },
        )
        require_status(
            forged_owner, {400}, f"reject supplied authoritative owner {label}"
        )

    for actor in (actor_a, actor_b):
        operational = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "get_operational_athlete_profile",
            {},
        )
        operational_payload = require_status(
            operational, {200}, "read own operational profile"
        )
        assert_no_private_load_keys(operational_payload)
        if operational_payload.get("athlete_id") != actor.athlete_id:
            raise VerificationError("operational RPC returned a foreign owner")

        own_activity = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "get_activity",
            {"p_activity_id": actor.activity_id},
        )
        own_activity_payload = require_status(
            own_activity, {200}, "read own activity RPC"
        )
        assert_no_private_load_keys(own_activity_payload)
        if str(own_activity_payload.get("id")) != actor.activity_id:
            raise VerificationError("activity RPC returned a foreign row")

        activity_list = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "list_activities",
            {"p_pending_rpe": False},
        )
        activity_list_payload = require_status(
            activity_list, {200}, "list own activities RPC"
        )
        assert_no_private_load_keys(activity_list_payload)
        if not any(
            isinstance(row, dict) and str(row.get("id")) == actor.activity_id
            for row in activity_list_payload
        ):
            raise VerificationError("activity list omitted the owner row")

        direct_legacy = call(
            base_url,
            "GET",
            "/rest/v1/athlete_profiles?select=*",
            api_key=publishable_key,
            bearer=actor.access_token,
        )
        require_status(direct_legacy, {401, 403}, "block athlete_profiles bypass")

        private_map = call(
            base_url,
            "GET",
            "/rest/v1/athlete_identity_map?select=*",
            api_key=publishable_key,
            bearer=actor.access_token,
            extra_headers={"Accept-Profile": "private"},
        )
        require_status(
            private_map, {400, 401, 403, 404, 406}, "block identity map enumeration"
        )

        private_load = call(
            base_url,
            "GET",
            "/rest/v1/activity_loads?select=*",
            api_key=publishable_key,
            bearer=actor.access_token,
            extra_headers={"Accept-Profile": "private"},
        )
        require_status(
            private_load, {400, 401, 403, 404, 406}, "block private load table"
        )

        service_rpc_as_user = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "resolve_opaque_athlete_id_for_auth_user",
            {"p_auth_user_id": actor.auth_user_id},
        )
        require_status(
            service_rpc_as_user, {401, 403}, "block service-only identity RPC"
        )

        processing_context_as_user = rpc(
            base_url,
            publishable_key,
            actor.access_token,
            "get_activity_processing_context",
            {
                "p_athlete_id": actor.auth_user_id,
                "p_activity_id": actor.activity_id,
            },
        )
        require_status(
            processing_context_as_user,
            {401, 403},
            "block service-only activity processing RPC",
        )

    service_identity = call(
        base_url,
        "POST",
        "/rest/v1/rpc/resolve_opaque_athlete_id_for_auth_user",
        api_key=secret_key,
        bearer=secret_key,
        body={"p_auth_user_id": actor_a.auth_user_id},
    )
    resolved = str(require_status(service_identity, {200}, "service identity RPC"))
    if resolved != actor_a.athlete_id:
        raise VerificationError("service identity RPC returned the wrong opaque owner")

    service_activity = call(
        base_url,
        "POST",
        "/rest/v1/rpc/get_activity_processing_context",
        api_key=secret_key,
        bearer=secret_key,
        body={
            "p_athlete_id": actor_a.auth_user_id,
            "p_activity_id": actor_a.activity_id,
        },
    )
    service_activity_payload = require_status(
        service_activity, {200}, "service activity processing RPC"
    )
    if service_activity_payload.get("duration_minutes") != 30:
        raise VerificationError("service activity processing RPC returned wrong row")


def delete_user(base_url: str, secret_key: str, auth_user_id: str) -> bool:
    deleted = call(
        base_url,
        "DELETE",
        f"/auth/v1/admin/users/{quote(auth_user_id)}",
        api_key=secret_key,
        bearer=secret_key,
    )
    return deleted.status in {200, 204}


def cleanup_tagged_users(base_url: str, secret_key: str) -> int:
    listed = call(
        base_url,
        "GET",
        "/auth/v1/admin/users?per_page=1000",
        api_key=secret_key,
        bearer=secret_key,
    )
    payload = require_status(listed, {200}, "list tagged R6 Auth users")
    users = payload.get("users", []) if isinstance(payload, dict) else []
    tagged_ids = [
        str(user["id"])
        for user in users
        if isinstance(user, dict)
        and isinstance(user.get("user_metadata"), dict)
        and user["user_metadata"].get("purpose") == "phase-13-14-r6"
    ]
    for auth_user_id in tagged_ids:
        if not delete_user(base_url, secret_key, auth_user_id):
            raise VerificationError("tagged R6 Auth user cleanup failed")
    return len(tagged_ids)


def main() -> int:
    env = load_env(ROOT / "backend" / ".env")
    base_url = env.get("START23_SUPABASE_URL", "")
    publishable_key = env.get("START23_SUPABASE_PUBLISHABLE_KEY", "")
    secret_key = env.get("START23_SUPABASE_SECRET_KEY", "")
    if not all((base_url, publishable_key, secret_key)):
        raise VerificationError("required Supabase configuration is absent")
    if "isfumhgqphieoayqahjv" not in base_url:
        raise VerificationError(
            "configured Supabase target is not the approved start23-dev project"
        )

    stale_count = cleanup_tagged_users(base_url, secret_key)
    if stale_count:
        print(f"PASS stale tagged Auth/data cleanup: {stale_count}/{stale_count}")

    created_user_ids: list[str] = []
    cleanup_ok = True
    try:
        auth_a, token_a = create_actor(base_url, publishable_key, secret_key, "a")
        created_user_ids.append(auth_a)
        auth_b, token_b = create_actor(base_url, publishable_key, secret_key, "b")
        created_user_ids.append(auth_b)
        print("PASS real Auth users created and password tokens issued: 2/2")

        actor_a = provision_actor(base_url, publishable_key, auth_a, token_a, "a")
        actor_b = provision_actor(base_url, publishable_key, auth_b, token_b, "b")
        print(
            "PASS opaque identity and split/operational/profile/history/goal/activity "
            "setup with exact retry checks: 2/2"
        )

        checked_a, denied_a = verify_actor_surface(base_url, publishable_key, actor_a)
        checked_b, denied_b = verify_actor_surface(base_url, publishable_key, actor_b)
        if checked_a != checked_b or denied_a != denied_b:
            raise VerificationError(
                "public table grant surface differs between test users"
            )
        print(
            "PASS owner-table RLS list scans: "
            f"users=2 accessible_surfaces_each={checked_a} "
            f"denied_surfaces={len(denied_a)}"
        )

        verify_two_user_boundaries(
            base_url, publishable_key, secret_key, actor_a, actor_b
        )
        print(
            "PASS inverse two-user read/mutation, identity, RPC, "
            "and private-schema boundaries"
        )
        print(
            "PASS recursive private-load key scan across all successful "
            "public table/RPC responses"
        )
        verify_activity_conflict(base_url, publishable_key, actor_a)
        print("PASS hosted activity idempotency conflict returned promptly")
        return 0
    finally:
        for auth_user_id in reversed(created_user_ids):
            cleanup_ok = delete_user(base_url, secret_key, auth_user_id) and cleanup_ok
        if created_user_ids:
            print(
                "PASS temporary Auth/data cleanup: "
                f"{len(created_user_ids)}/{len(created_user_ids)}"
                if cleanup_ok
                else "FAIL temporary Auth/data cleanup"
            )
        if not cleanup_ok and sys.exc_info()[0] is None:
            raise VerificationError("temporary Auth user cleanup failed")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as error:
        print(f"FAIL {error}", file=sys.stderr)
        raise SystemExit(1) from error
