"""Sequential synthetic-only historical lifecycle against real hosted gateways.

Starts the unchanged backend on IPv4 loopback with real repositories/verifier.
No V6 dependency injection, SQL writes, migration or permission changes exist.
Every mutation is journaled privately before dispatch; uncertain writes stop.
"""

import argparse
import hashlib
import json
import logging
import socket
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import httpx
import uvicorn

from app.core.config import Settings
from app.main import create_app
from scripts.verify_v6_hosted_accounts import HostedAccounts, credentials
from scripts.verify_v6_hosted_auth import PROJECT_URL, write_json


def private_free(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = rekey(key)
            if normalized in {
                "tss",
                "plannedtss",
                "realizedtss",
                "plannedload",
                "realizedload",
                "privateload",
                "v6frozencontext",
                "frozenphysiologicalcontext",
            }:
                raise RuntimeError(
                    "Private field in public response; stop immediately."
                )
            private_free(item)
    elif isinstance(value, list):
        for item in value:
            private_free(item)


def rekey(value: str) -> str:
    return "".join(c for c in value.lower() if c.isalnum())


class Lifecycle:
    def __init__(self, accounts: HostedAccounts, client: httpx.Client) -> None:
        self.accounts, self.client = accounts, client
        self.today = datetime.now(ZoneInfo("Europe/Amsterdam")).date()
        self.week = self.today - timedelta(days=self.today.weekday())
        self.rows: list[dict[str, Any]] = []
        previous = accounts.directory / "lifecycle-results.json"
        if previous.exists():
            self.rows = json.loads(previous.read_text(encoding="utf-8"))

    def auth_negatives(self) -> None:
        account = self.accounts.manifest["accounts"]["A"]
        token = account["current_session"]["access_token"]
        parts = token.split(".")
        parts[1] = ("A" if parts[1][0] != "A" else "B") + parts[1][1:]
        for label, headers in (
            ("missing", {}),
            ("invalid", {"Authorization": "Bearer invalid"}),
            ("tampered_real_token", {"Authorization": "Bearer " + ".".join(parts)}),
        ):
            response = self.client.get("/api/v1/onboarding", headers=headers)
            private_free(response.json())
            self.rows.append(
                {"case": "local_backend:" + label, "http_status": response.status_code}
            )
            write_json(self.accounts.directory / "lifecycle-results.json", self.rows)
            if response.status_code != 401:
                raise RuntimeError("Local backend accepted invalid credentials.")

    def call(
        self,
        label: str,
        account: dict[str, Any],
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        expected: tuple[int, ...] = (200,),
        foreign: bool = False,
        headers: dict[str, str] | None = None,
    ) -> Any:
        allowed_prefixes = (
            "/api/v1/onboarding",
            "/api/v1/me/",
            "/api/v1/checkins",
            "/api/v1/weekly-plans",
            "/api/v1/change-proposals/",
            "/api/v1/planned-workouts/",
            "/api/v1/calendar",
            "/api/v1/activities",
        )
        if not path.startswith(allowed_prefixes) or method not in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
        }:
            raise ValueError("Unapproved local verification route.")
        journal = account.setdefault("operation_journal", {})
        if method != "GET":
            if label in journal:
                raise RuntimeError(
                    "Already attempted mutation; inspect private journal."
                )
            journal[label] = {
                "method": method,
                "path": path,
                "request": body,
                "outcome": "pending",
            }
            self.accounts.persist()
        response = self.client.request(
            method,
            path,
            json=body,
            headers={
                "Authorization": "Bearer " + account["current_session"]["access_token"],
                **(headers or {}),
            },
            timeout=125,
        )
        payload = response.json()
        private_free(payload)
        if method != "GET":
            journal[label].update(
                http_status=response.status_code, response=payload, outcome="received"
            )
        row = {
            "case": label,
            "http_status": response.status_code,
            "foreign": foreign,
            "classification": "historical_planner_only",
        }
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            row["code"] = payload["error"].get("code")
        self.rows.append(row)
        self.accounts.persist()
        write_json(self.accounts.directory / "lifecycle-results.json", self.rows)
        if foreign and response.is_success:
            raise RuntimeError("Cross-account operation unexpectedly succeeded; stop.")
        if response.status_code not in expected:
            raise RuntimeError(
                "Unexpected lifecycle status; inspect the private journal."
            )
        return payload

    def onboarding(self, label: str, account: dict[str, Any]) -> None:
        if account.get("onboarding_completed"):
            return
        if account.get("onboarding_attempted"):
            raise RuntimeError("Partial onboarding exists; inspect before any retry.")
        account["onboarding_attempted"] = True
        self.accounts.persist()
        self.call(label + ":onboarding_before", account, "GET", "/api/v1/onboarding")
        self.call(
            label + ":physiology",
            account,
            "PATCH",
            "/api/v1/me/physiology-profile",
            {"date_of_birth": "1990-05-20", "resting_heart_rate_bpm": 52},
        )
        self.call(
            label + ":operational",
            account,
            "PATCH",
            "/api/v1/me/operational-profile",
            {
                "heart_rate_monitor_confirmed": True,
                "timezone": "Europe/Amsterdam",
                "timezone_source": "manual",
                "timezone_confirmed": True,
            },
        )
        # Accepted synthetic history/goal fixtures, not real athlete observations.
        self.call(
            label + ":history",
            account,
            "PUT",
            "/api/v1/me/training-history",
            {
                "entries": [
                    {"discipline": sport, "average_hours_per_week": hours}
                    for sport, hours in (("swim", "2"), ("bike", "4"), ("run", "3"))
                ]
            },
        )
        goal = self.call(
            label + ":goal",
            account,
            "POST",
            "/api/v1/me/goals",
            {
                "race_type": "triathlon",
                "race_name": "Synthetic hosted verification triathlon",
                "race_date": (self.today + timedelta(days=120)).isoformat(),
                "swim_distance_meters": 1500,
                "bike_distance_meters": 40000,
                "run_distance_meters": 10000,
                "total_target_time_seconds": 10800,
            },
            expected=(201,),
        )
        account["goal_id"] = str(UUID(goal["id"]))
        for sport, metric, value in (
            ("run", "run_lthr_bpm", 172),
            ("bike", "bike_ftp_watts", 250),
            ("swim", "swim_css_seconds_per_100m", 100),
        ):
            self.call(
                label + ":setup:" + sport,
                account,
                "PUT",
                f"/api/v1/onboarding/disciplines/{sport}/setup",
                {
                    "setup_route": "known_values",
                    "guidance_mode": "pace"
                    if sport == "swim"
                    else "heart_rate"
                    if sport == "run"
                    else "power",
                    "thresholds": [{"metric_kind": metric, "value": value}],
                    **({"pool_length_meters": 25} if sport == "swim" else {}),
                },
            )
            zones = self.call(
                label + ":zones:" + sport,
                account,
                "PUT",
                f"/api/v1/me/zones/{sport}",
                {
                    "setup_method": "calculated",
                    "confirmed": True,
                    "thresholds": [{"metric_kind": metric, "value": value}],
                },
            )
            proposal = str(UUID(zones["proposal_id"]))
            account.setdefault("zone_proposals", []).append(proposal)
            self.accounts.persist()
            self.call(
                label + ":zone_confirm:" + sport,
                account,
                "POST",
                f"/api/v1/change-proposals/{proposal}/approve",
                {"expected_base_zone_profile_id": None},
            )
        ready = self.call(
            label + ":onboarding_ready", account, "GET", "/api/v1/onboarding"
        )
        if not ready["can_complete"]:
            raise RuntimeError(
                "Current onboarding remains incomplete; no bypass permitted."
            )
        complete = self.call(
            label + ":onboarding_complete",
            account,
            "POST",
            "/api/v1/onboarding/complete",
            {
                "expected_onboarding_revision": ready["onboarding_revision"],
            },
        )
        account["onboarding_completed"] = True
        account["onboarding_receipt"] = complete
        self.accounts.persist()

    def checkin(self, label: str, account: dict[str, Any]) -> None:
        if account.get("checkin_confirmed"):
            return
        started = self.call(
            label + ":checkin_start",
            account,
            "POST",
            "/api/v1/checkins",
            {"week_start": self.week.isoformat()},
        )
        cid = str(UUID(started["id"]))
        account["checkin_id"] = cid
        self.accounts.persist()
        saved = self.call(
            label + ":checkin_save",
            account,
            "PUT",
            f"/api/v1/checkins/{cid}/context",
            {
                "expected_revision": started["context_revision"],
                "recurring_activities_confirmed": True,
            },
        )
        self.call(
            label + ":checkin_confirm",
            account,
            "POST",
            f"/api/v1/checkins/{cid}/context-confirmation",
            {
                "expected_revision": saved["context"]["revision"],
                "context_fingerprint": saved["context"]["fingerprint"],
            },
        )
        account["checkin_confirmed"] = True
        self.accounts.persist()

    def proposal(self, label: str, account: dict[str, Any]) -> None:
        if account.get("plan"):
            return
        generated = self.call(
            label + ":historical_initial_proposal",
            account,
            "POST",
            "/api/v1/weekly-plans/proposals",
            {
                "week_start": self.week.isoformat(),
                "available_dates": [
                    (self.week + timedelta(days=i)).isoformat() for i in range(7)
                ],
            },
            expected=(201,),
        )
        if generated["plan"]["revision_state"] != "pending_approval":
            raise RuntimeError("A generated plan was not pending.")
        account["plan"], account["plan_proposal"] = (
            generated["plan"],
            generated["proposal"],
        )
        self.accounts.persist()

    def foreign_checks(self) -> None:
        accounts = self.accounts.manifest["accounts"]
        for caller, target in (("A", "B"), ("B", "A")):
            source, victim = accounts[caller], accounts[target]
            plan, proposal = victim["plan"], victim["plan_proposal"]
            self.call(
                caller + ":foreign_plan",
                source,
                "GET",
                f"/api/v1/weekly-plans/{plan['id']}",
                expected=(404,),
                foreign=True,
            )
            self.call(
                caller + ":foreign_confirm",
                source,
                "POST",
                f"/api/v1/change-proposals/{proposal['id']}/approve",
                {"expected_base_revision": proposal["base_plan_revision"]},
                expected=(404,),
                foreign=True,
            )
            if plan["workouts"]:
                workout = plan["workouts"][0]
                self.call(
                    caller + ":foreign_alternatives",
                    source,
                    "GET",
                    f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/{workout['id']}/alternatives?expected_revision={plan['revision']}",
                    expected=(404,),
                    foreign=True,
                )
                self.call(
                    caller + ":foreign_move",
                    source,
                    "PATCH",
                    f"/api/v1/planned-workouts/{workout['id']}",
                    {
                        "expected_revision": plan["revision"],
                        "scheduled_date": (self.week + timedelta(days=6)).isoformat(),
                    },
                    expected=(404,),
                    foreign=True,
                )
                self.call(
                    caller + ":foreign_attach",
                    source,
                    "POST",
                    "/api/v1/activities",
                    {
                        "planned_workout_id": workout["id"],
                        "discipline": workout["discipline"],
                        "started_at": self.week.isoformat() + "T12:00:00+01:00",
                        "timezone": "Europe/Amsterdam",
                        "duration_minutes": "30",
                        "metrics": {"average_heart_rate_bpm": 140},
                    },
                    headers={"Idempotency-Key": str(uuid4())},
                    expected=(404,),
                    foreign=True,
                )
            own = self.call(
                target + ":unchanged_pending_after_foreign",
                victim,
                "GET",
                f"/api/v1/weekly-plans/{plan['id']}",
            )
            if (
                own["revision"] != plan["revision"]
                or own["revision_state"] != "pending_approval"
            ):
                raise RuntimeError(
                    "A foreign operation changed the victim state; stop."
                )

    def gates(self) -> None:
        for label, account in self.accounts.manifest["accounts"].items():
            self.call(
                label + ":missing_frequency_gate",
                account,
                "GET",
                "/api/v1/me/frequency-preferences",
                expected=(404,),
            )
            self.call(
                label + ":missing_a5_recovery_gate",
                account,
                "POST",
                f"/api/v1/checkins/{account['checkin_id']}/plan-proposals",
                expected=(404,),
            )

    def swipe(self) -> None:
        account = self.accounts.manifest["accounts"]["A"]
        if account.get("swipe_attempted") and not account.get("swipe_draft_id"):
            raise RuntimeError("A swipe attempt is already journaled; do not recreate.")
        account["swipe_attempted"] = True
        self.accounts.persist()
        week = self.week + timedelta(days=7)
        if account.get("swipe_draft_id"):
            draft = self.call(
                "A:historical_swipe_resume",
                account,
                "GET",
                f"/api/v1/weekly-plans/swipe-drafts/{account['swipe_draft_id']}",
            )
        else:
            draft = self.call(
                "A:historical_swipe_create",
                account,
                "POST",
                "/api/v1/weekly-plans/swipe-drafts",
                {
                    "week_start": week.isoformat(),
                    "available_dates": [
                        (week + timedelta(days=i)).isoformat() for i in range(7)
                    ],
                },
                expected=(201, 409),
            )
        if "error" in draft:
            account["swipe_blocked_code"] = draft["error"]["code"]
            self.accounts.persist()
            return
        account["swipe_draft_id"] = str(UUID(draft["id"]))
        self.accounts.persist()
        for index in range(24):
            if draft["state"] == "placement":
                break
            candidate = draft["current_candidate"]
            draft = self.call(
                f"A:swipe_accept:revision:{draft['revision']}",
                account,
                "POST",
                f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/transitions",
                {
                    "expected_revision": draft["revision"],
                    "action": "accept",
                    "candidate_template_id": candidate["id"],
                    "candidate_occurrence_id": candidate["occurrence_id"],
                },
            )
        if draft["state"] != "placement":
            raise RuntimeError(
                "The normal swipe flow did not complete within its existing bound."
            )
        submitted = self.call(
            "A:historical_swipe_submit",
            account,
            "POST",
            f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}/submit",
            {
                "expected_revision": draft["revision"],
                "placement_mode": "automatic",
            },
            expected=(200, 201),
        )
        if submitted["plan"]["revision_state"] != "pending_approval":
            raise RuntimeError("Swipe submission did not remain pending.")
        account["swipe_submission"] = submitted
        self.accounts.persist()
        other = self.accounts.manifest["accounts"]["B"]
        self.call(
            "B:foreign_swipe_draft",
            other,
            "GET",
            f"/api/v1/weekly-plans/swipe-drafts/{draft['id']}",
            expected=(404,),
            foreign=True,
        )

    def restore(self) -> None:
        from concurrent.futures import ThreadPoolExecutor

        for label, account in self.accounts.manifest["accounts"].items():
            plan = self.call(
                label + ":after_login_plan_restore",
                account,
                "GET",
                f"/api/v1/weekly-plans/{account['plan']['id']}",
            )
            if plan["revision"] != account["latest_plan"]["revision"]:
                raise RuntimeError("Login restored a different plan revision.")
            if submitted := account.get("swipe_submission"):
                pending = self.call(
                    label + ":after_login_pending_restore",
                    account,
                    "GET",
                    f"/api/v1/weekly-plans/{submitted['plan']['id']}",
                )
                if (
                    pending["revision_state"] != "pending_approval"
                    or pending["id"] != submitted["plan"]["id"]
                ):
                    raise RuntimeError("Pending swipe state was not restored exactly.")
                self.call(
                    label + ":after_login_submitted_draft",
                    account,
                    "GET",
                    f"/api/v1/weekly-plans/swipe-drafts/{account['swipe_draft_id']}",
                )
            self.call(
                label + ":after_login_calendar",
                account,
                "GET",
                f"/api/v1/calendar?from={self.week}&to={self.week + timedelta(days=7)}",
            )
        pairs = list(self.accounts.manifest["accounts"].items())

        def read(pair: tuple[str, dict[str, Any]]) -> bool:
            _, account = pair
            response = self.client.get(
                f"/api/v1/weekly-plans/{account['plan']['id']}",
                headers={
                    "Authorization": "Bearer "
                    + account["current_session"]["access_token"]
                },
            )
            return (
                response.status_code == 200
                and response.json()["id"] == account["plan"]["id"]
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            if not all(pool.map(read, pairs)):
                raise RuntimeError("Two ordinary concurrent owner reads failed.")
        self.rows.append(
            {"case": "two_concurrent_owner_reads", "status": "PASS", "requests": 2}
        )
        write_json(self.accounts.directory / "lifecycle-results.json", self.rows)

    def audit_legacy_move(self) -> None:
        for label, account in self.accounts.manifest["accounts"].items():
            journal = account.get("operation_journal", {})
            if account.get("legacy_move_audit"):
                continue
            if label + ":move_unfinished" not in journal:
                continue
            before = journal[label + ":attach_owned_activity"]["response"]
            after = self.call(
                label + ":legacy_move_activity_audit",
                account,
                "GET",
                f"/api/v1/activities/{account['activity_id']}",
            )
            if before != after:
                raise RuntimeError("Completed activity evidence changed; stop.")
            plan = self.call(
                label + ":legacy_move_plan_audit",
                account,
                "GET",
                f"/api/v1/weekly-plans/{account['plan']['id']}",
            )
            original = before["planned_workout_id"]
            account["legacy_move_audit"] = {
                "activity_evidence_equal": True,
                "physical_locator_in_active_plan": any(
                    w["id"] == original for w in plan["workouts"]
                ),
                "activity_evidence_sha256": hashlib.sha256(
                    json.dumps(after, sort_keys=True).encode()
                ).hexdigest(),
            }
            current = next(w for w in plan["workouts"] if w["status"] != "completed")
            old_revision = journal[label + ":move_unfinished"]["request"][
                "expected_revision"
            ]
            self.call(
                label + ":stale_revision_current_locator",
                account,
                "PATCH",
                f"/api/v1/planned-workouts/{current['id']}",
                {
                    "expected_revision": old_revision,
                    "scheduled_date": current["scheduled_date"],
                },
                expected=(409,),
            )
            account["latest_plan"] = plan
            account["historical_finished"] = True
            self.accounts.persist()

    def finish(self) -> None:
        for label, account in self.accounts.manifest["accounts"].items():
            plan, proposal = account["plan"], account["plan_proposal"]
            if account.get("historical_finished"):
                continue
            if account.get("historical_finish_attempted"):
                raise RuntimeError("Partial finish exists; inspect before retry.")
            account["historical_finish_attempted"] = True
            self.accounts.persist()
            if plan["workouts"]:
                workout = plan["workouts"][0]
                self.call(
                    label + ":owned_pending_alternatives",
                    account,
                    "GET",
                    f"/api/v1/weekly-plans/{plan['id']}/pending-workouts/{workout['id']}/alternatives?expected_revision={plan['revision']}",
                )
            self.call(
                label + ":separate_plan_confirmation",
                account,
                "POST",
                f"/api/v1/change-proposals/{proposal['id']}/approve",
                {"expected_base_revision": proposal["base_plan_revision"]},
            )
            active = self.call(
                label + ":active_reload",
                account,
                "GET",
                f"/api/v1/weekly-plans/{plan['id']}",
            )
            if active["revision_state"] != "active":
                raise RuntimeError("Explicit confirmation did not activate the plan.")
            self.call(
                label + ":calendar",
                account,
                "GET",
                f"/api/v1/calendar?from={self.week}&to={self.week + timedelta(days=7)}",
            )
            candidates = [
                w
                for w in active["workouts"]
                if w["discipline"] == "run"
                and w["scheduled_date"] <= self.today.isoformat()
            ]
            if not candidates:
                raise RuntimeError(
                    "No past synthetic RUN occurrence; no fabricated evidence."
                )
            completed = candidates[0]
            body = {
                "planned_workout_id": completed["id"],
                "discipline": "run",
                "started_at": completed["scheduled_date"] + "T12:00:00+01:00",
                "timezone": "Europe/Amsterdam",
                "duration_minutes": "30",
                "metrics": {"average_heart_rate_bpm": 140},
            }
            idem = str(uuid4())
            account["activity_idempotency_key"] = idem
            account["activity_request"] = body
            self.accounts.persist()
            activity = self.call(
                label + ":attach_owned_activity",
                account,
                "POST",
                "/api/v1/activities",
                body,
                expected=(201,),
                headers={"Idempotency-Key": idem},
            )
            account["activity_id"] = str(UUID(activity["id"]))
            repeated = self.call(
                label + ":activity_exact_retry",
                account,
                "POST",
                "/api/v1/activities",
                body,
                expected=(200, 201),
                headers={"Idempotency-Key": idem},
            )
            if repeated["id"] != activity["id"]:
                raise RuntimeError("An exact activity retry created a duplicate.")
            evidence_before = self.call(
                label + ":activity_before_move",
                account,
                "GET",
                f"/api/v1/activities/{activity['id']}",
            )
            refreshed = self.call(
                label + ":plan_before_move",
                account,
                "GET",
                f"/api/v1/weekly-plans/{plan['id']}",
            )
            remaining = [
                w
                for w in refreshed["workouts"]
                if w["id"] != completed["id"] and w["status"] != "completed"
            ]
            if not remaining:
                raise RuntimeError(
                    "No unfinished synthetic workout; do not invent one."
                )
            unfinished = remaining[0]
            old_day = unfinished["scheduled_date"]
            new_day = next(
                (self.week + timedelta(days=i)).isoformat()
                for i in range(7)
                if (self.week + timedelta(days=i)).isoformat() != old_day
            )
            moved = self.call(
                label + ":move_unfinished",
                account,
                "PATCH",
                f"/api/v1/planned-workouts/{unfinished['id']}",
                {
                    "expected_revision": refreshed["revision"],
                    "scheduled_date": new_day,
                },
            )
            self.call(
                label + ":stale_move",
                account,
                "PATCH",
                f"/api/v1/planned-workouts/{unfinished['id']}",
                {
                    "expected_revision": refreshed["revision"],
                    "scheduled_date": old_day,
                },
                # Legacy revisions replace physical locators. Distinguish an old
                # missing locator from CAS on a still-current locator explicitly.
                expected=(409,)
                if any(w["id"] == unfinished["id"] for w in moved["workouts"])
                else (404,),
            )
            evidence_after = self.call(
                label + ":activity_after_move",
                account,
                "GET",
                f"/api/v1/activities/{activity['id']}",
            )
            if evidence_before != evidence_after:
                raise RuntimeError(
                    "Completed activity evidence changed during another move."
                )
            account["activity_evidence_sha256"] = hashlib.sha256(
                json.dumps(evidence_after, sort_keys=True).encode()
            ).hexdigest()
            account["latest_plan"] = moved
            account["historical_finished"] = True
            self.accounts.persist()
        accounts = self.accounts.manifest["accounts"]
        for caller, target in (("A", "B"), ("B", "A")):
            source, victim = accounts[caller], accounts[target]
            self.call(
                caller + ":foreign_activity_read",
                source,
                "GET",
                f"/api/v1/activities/{victim['activity_id']}",
                expected=(404,),
                foreign=True,
            )
            self.call(
                caller + ":foreign_receipt_reuse",
                source,
                "POST",
                "/api/v1/activities",
                victim["activity_request"],
                headers={"Idempotency-Key": victim["activity_idempotency_key"]},
                expected=(404,),
                foreign=True,
            )


def run(
    accounts: HostedAccounts, public_key: str, secret_key: str, phase: str = "prefix"
) -> None:
    settings = Settings(
        environment="local",
        log_level="ERROR",
        supabase_url=PROJECT_URL,
        supabase_publishable_key=public_key,
        supabase_secret_key=secret_key,
        openai_api_key="",
        realized_v2_storage_ready=False,
        realized_v2_selection_enabled=False,
        _env_file=None,
    )
    app = create_app(settings)
    logging.disable(logging.CRITICAL)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_config=None))
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [listener]}, daemon=True
    )
    thread.start()
    try:
        limit = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= limit:
                raise RuntimeError("Local loopback backend did not start.")
            time.sleep(0.05)
        with httpx.Client(base_url=f"http://127.0.0.1:{port}") as client:
            flow = Lifecycle(accounts, client)
            if phase == "prefix":
                for label, account in accounts.manifest["accounts"].items():
                    flow.onboarding(label, account)
                    flow.checkin(label, account)
                    flow.proposal(label, account)
                flow.foreign_checks()
            elif phase == "audit":
                flow.audit_legacy_move()
            elif phase == "gates":
                flow.gates()
            elif phase == "swipe":
                flow.swipe()
            elif phase == "restore":
                flow.restore()
            elif phase == "auth-negatives":
                flow.auth_negatives()
            else:
                flow.finish()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-synthetic-lifecycle", action="store_true")
    parser.add_argument("--credential-file", type=Path, required=True)
    parser.add_argument("--private-directory", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=(
            "prefix",
            "finish",
            "audit",
            "gates",
            "swipe",
            "restore",
            "auth-negatives",
        ),
        default="prefix",
    )
    args = parser.parse_args()
    if not args.execute_synthetic_lifecycle:
        parser.error("Explicit synthetic-only execution is required.")
    public_key, secret_key = credentials(args.credential_file)
    accounts = HostedAccounts(args.private_directory, public_key, secret_key)
    if not all(a.get("athlete_id") for a in accounts.manifest["accounts"].values()):
        raise RuntimeError("Authenticate the exact two manifested accounts first.")
    run(accounts, public_key, secret_key, args.phase)
    print("Scoped historical lifecycle phase completed:", args.phase)


if __name__ == "__main__":
    main()
