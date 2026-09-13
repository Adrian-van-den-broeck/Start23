"""Static gates for the forward-only R2/R3 migration when Postgres is absent."""

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260912072232_phase_r2_r3_identity_onboarding_calibration.sql"
)


def test_all_documented_owner_tables_receive_an_opaque_key() -> None:
    sql = _MIGRATION.read_text(encoding="utf-8")
    expected = {
        "public.athlete_profiles",
        "public.onboarding_sessions",
        "public.training_history_entries",
        "public.goals",
        "public.zone_profile_versions",
        "public.zone_metrics",
        "public.zone_boundaries",
        "public.change_proposals",
        "public.initial_plan_requests",
        "public.weekly_plans",
        "public.plan_revisions",
        "public.planned_workouts",
        "public.plan_warnings",
        "private.planned_workout_loads",
        "private.plan_revision_loads",
        "public.activities",
        "public.activity_metrics",
        "private.activity_loads",
        "public.weekly_checkins",
        "public.weekly_checkin_contexts",
        "public.injury_restrictions",
        "public.planned_external_activities",
        "public.goal_maintenance_states",
        "public.activity_rpe_revisions",
        "public.discipline_zone_setups",
        "public.calibration_observations",
        "public.calibration_evaluations",
        "public.calibration_threshold_decisions",
        "public.provider_connections",
        "private.provider_tokens",
        "private.integration_oauth_states",
        "public.import_runs",
        "private.webhook_receipts",
        "private.provider_activity_imports",
        "public.activity_files",
        "public.discipline_test_assignments",
        "public.swipe_week_drafts",
        "private.phase_13_activity_load_history",
        "public.onboarding_completion_records",
    }
    owner_loop = re.search(
        r"foreach v_table in array array\[(.*?)\]\s*loop",
        sql,
        flags=re.DOTALL,
    )
    assert owner_loop is not None
    assert (
        set(re.findall(r"'((?:public|private)\.[^']+)'", owner_loop.group(1)))
        == expected
    )
    assert "alter column internal_athlete_id set not null" in sql
    assert (
        "references private.athlete_identity_map (athlete_id) on delete cascade" in sql
    )
    assert "v_table <> 'private.webhook_receipts'" in sql
    assert "webhook_receipts_opaque_owner_pair_valid" in sql
    assert "activity_files_path_dual_owner_valid" in sql
    assert "storage.foldername(name))[1] = (select private.current_athlete_id())" in sql


def test_identity_profile_and_planner_security_contracts_are_present() -> None:
    sql = _MIGRATION.read_text(encoding="utf-8").lower()
    assert "auth_user_id uuid not null unique" in sql
    assert "create function private.backfill_split_athlete_profiles()" in sql
    assert "on conflict (athlete_id) do nothing" in sql
    assert (
        "alter table public.athlete_identifying_profiles force row level security"
        in sql
    )
    assert (
        "alter table public.athlete_physiology_profiles force row level security" in sql
    )
    assert "revoke execute on function public.complete_onboarding()" in sql
    assert (
        "public.complete_current_onboarding(\n  p_expected_session_revision bigint"
        in sql
    )
    assert "create function private.assert_current_planning_eligibility" in sql
    assert "public.get_current_planning_eligibility_context" in sql
    assert "to service_role" in sql
    assert "calibration_observations_r2_10_current_contract" in sql
    assert "current run/bike calibration requires measured average hr" in sql
    assert "current swim calibration requires elapsed time and distance" in sql
    assert "weekly_plans_r3_10_require_current_onboarding" in sql
    assert "plan_revisions_r3_10_require_current_onboarding" in sql
    assert "swipe_week_drafts_r3_10_require_current_onboarding" in sql
    assert "set search_path = ''" in sql
