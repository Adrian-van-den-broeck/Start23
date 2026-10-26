"""Verify the A5 PostgreSQL race on a disposable LOCAL database only.

Requires migrated local Supabase and psql on PATH. Uses synthetic committed
fixtures and removes only those synthetic users in finally. Never accepts a
hosted database URL. This is integration evidence, not a mocked backend test.
"""

import concurrent.futures
import json
import os
import shutil
import subprocess
import time
from urllib.parse import urlsplit
from uuid import uuid4


def main() -> None:
    database_url = os.environ.get(
        "START23_A5_LOCAL_DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    )
    if urlsplit(database_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("A5 verification requires a disposable local database.")
    psql = shutil.which("psql")
    if psql is None:
        raise SystemExit(
            "psql is unavailable; PostgreSQL concurrency gate remains open."
        )

    def query(sql: str) -> str:
        # Input and credentials are never printed, including on failure.
        result = subprocess.run(
            [psql, "-X", "-qAt", "-v", "ON_ERROR_STOP=1", database_url],
            input=sql,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Local A5 PostgreSQL verification query failed.")
        return result.stdout.strip()

    owner, checkin = str(uuid4()), str(uuid4())
    first_name = f"a5-race-{uuid4()}"
    payload = {
        "checkin_id": checkin,
        "expected_base_revision": 0,
        "week_start": "2026-08-03",
        "timezone": "Europe/Amsterdam",
        "phase": "base",
        "target_basis": "injury_rest_only",
        "input_fingerprint": "a" * 64,
        "generation_fingerprint": "b" * 64,
        "total_duration_minutes": 0,
        "low_intensity_percent": 0,
        "high_intensity_percent": 0,
        "confirmed_injuries": ["run"],
        "low_only_disciplines": [],
        "goal_disciplines": ["run"],
        "availability": [],
        "available_dates": [],
        "availability_source": "checkin",
        "workouts": [],
        "warnings": [],
        "target_tss": 0,
        "planned_tss": 0,
        "ruleset_version": "phase-13-joren-ruleset-1",
        "planning_ruleset_version": "joren-planning-ruleset-2",
    }
    # Only generated UUIDs and a fixed synthetic payload enter this SQL.
    create = (
        f"select public.create_weekly_plan_proposal_v3('{owner}', "
        f"'{json.dumps(payload)}'::jsonb);"
    )
    service = 'set local request.jwt.claims = \'{"role":"service_role"}\';'
    try:
        query(f"""
          begin;
          insert into auth.users (id) values ('{owner}');
          insert into public.athlete_profiles (athlete_id, timezone,
            timezone_source, timezone_confirmed_at, onboarding_status)
          values ('{owner}', 'Europe/Amsterdam', 'manual', now(), 'in_progress');
          set local start23.checkin_write = 'on';
          insert into public.weekly_checkins (id, athlete_id, week_start, timezone)
          values ('{checkin}', '{owner}', '2026-08-03', 'Europe/Amsterdam');
          commit;
        """)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                query,
                f"""
              begin;
              set local application_name = '{first_name}';
              {service}
              do $$ begin
                perform 1 from public.weekly_checkins where id = '{checkin}' for update;
                perform pg_sleep(2);
              end $$;
              {create}
              commit;
            """,
            )
            deadline = time.monotonic() + 10
            while (
                query(
                    "select count(*) from pg_stat_activity "
                    f"where application_name = '{first_name}' "
                    "and wait_event = 'PgSleep';"
                )
                != "1"
            ):
                if first.done() or time.monotonic() >= deadline:
                    raise RuntimeError(
                        "Could not establish overlapping A5 transactions."
                    )
                time.sleep(0.05)
            second = pool.submit(query, f"begin; {service} {create} commit;")
            result_a = json.loads(first.result())
            result_b = json.loads(second.result())
        assert result_a == result_b, (
            "Concurrent requests returned different identities."
        )
        state = query(f"""
          select jsonb_build_object(
            'status', checkin.status,
            'proposal_id', checkin.plan_proposal_id,
            'revisions', (select count(*) from public.plan_revisions
              where checkin_id = checkin.id),
            'active_revision', plan.active_revision,
            'proposal_state', proposal.state)
          from public.weekly_checkins checkin
          join public.change_proposals proposal
            on proposal.id = checkin.plan_proposal_id
          join public.plan_revisions revision
            on revision.id = proposal.target_plan_revision_id
          join public.weekly_plans plan on plan.id = revision.plan_id
          where checkin.id = '{checkin}';
        """)
        persisted = json.loads(state)
        assert persisted == {
            "status": "completed",
            "proposal_id": result_a["proposal_id"],
            "revisions": 1,
            "active_revision": None,
            "proposal_state": "pending",
        }
        replay = query(f"""
          begin;
          set local request.jwt.claims = '{{"sub":"{owner}","role":"authenticated"}}';
          set local request.jwt.claim.sub = '{owner}';
          set local role authenticated;
          select public.get_checkin_plan_proposal('{checkin}');
          commit;
        """)
        attached = json.loads(replay)
        assert attached["proposal"]["id"] == result_a["proposal_id"]
        assert attached["plan"]["id"] == result_a["plan_id"]
        assert attached["plan"]["revision"] == result_a["revision"]
        print(
            "PASS: overlapping PostgreSQL creates, "
            "one pending attachment, exact replay."
        )
    finally:
        query(f"delete from auth.users where id = '{owner}';")


if __name__ == "__main__":
    main()
