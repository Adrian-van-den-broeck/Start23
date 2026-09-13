"""Static R4/R5 migration gates for environments without PostgreSQL."""

import re
from pathlib import Path

_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260912180000_phase_r4_r5_onboarding_race_activity.sql"
)
_MIGRATIONS = _MIGRATION.parent


def _sql() -> str:
    return _MIGRATION.read_text(encoding="utf-8").lower()


def test_migration_version_is_unique_and_after_r2_r3() -> None:
    versions = sorted(path.name.split("_", 1)[0] for path in _MIGRATIONS.glob("*.sql"))
    assert len(versions) == len(set(versions))
    assert "20260912072232" in versions
    assert "20260912180000" in versions
    assert versions.index("20260912072232") < versions.index("20260912180000")


def test_r4_adds_explicit_operational_confirmations_without_backfilling_them() -> None:
    sql = _sql()
    assert "add column timezone_source text" in sql
    assert "add column timezone_confirmed_at timestamptz" in sql
    assert "add column heart_rate_monitor_confirmed_at timestamptz" in sql
    assert "timezone_source in ('device', 'manual')" in sql
    assert "from pg_catalog.pg_timezone_names" in sql
    assert "'heart_rate_monitor_confirmed'" in sql
    assert "drop constraint onboarding_sessions_current_step_valid" in sql
    assert "drop constraint onboarding_sessions_completed_steps_valid" in sql
    assert (
        "'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones'" in sql
    )
    assert not re.search(
        r"update\s+public\.athlete_profiles\s+set\s+timezone_confirmed_at",
        sql,
    )


def test_r4_structured_races_cover_exactly_the_current_five_shapes() -> None:
    sql = _sql()
    assert "race_type in ('run', 'bike', 'swim', 'triathlon', 'duathlon')" in sql
    for field in (
        "race_name",
        "race_date",
        "swim_distance_meters",
        "bike_distance_meters",
        "run_distance_meters",
        "total_target_time_seconds",
        "swim_target_time_seconds",
        "bike_target_time_seconds",
        "run_target_time_seconds",
        "specific_focus",
    ):
        assert f"add column {field}" in sql
    assert "when 'run' then run_distance_meters is not null" in sql
    assert "when 'bike' then bike_distance_meters is not null" in sql
    assert "when 'swim' then swim_distance_meters is not null" in sql
    assert "when 'triathlon' then swim_distance_meters is not null" in sql
    assert "when 'duathlon' then bike_distance_meters is not null" in sql
    assert "alter column title drop not null" in sql
    assert "alter column specific_description drop not null" in sql
    assert "delete from public.goals" not in sql
    assert "status = 'active' and race_type is null" in sql
    assert "retain its historical generic values" in sql


def test_r4_current_version_is_enforced_in_completion_and_planner_paths() -> None:
    sql = _sql()
    required = "'profile', 'heart_rate_monitor', 'timezone', 'history', 'goal', 'zones'"
    assert "'phase-14-onboarding-v2'" in sql
    assert required in sql
    assert "create or replace function public.complete_current_onboarding" in sql
    assert (
        "create or replace function private.assert_current_planning_eligibility" in sql
    )
    assert "before insert or update on public.weekly_plans" not in sql
    # R3 owns the triggers; replacing the called function preserves direct-write
    # coverage.
    assert "rename to build_planning_input_snapshot_r3" in sql
    assert "'target_date', goal.race_date" in sql
    assert "'race_discipline_profile', case goal.race_type" in sql
    assert "activities_r4_10_require_confirmed_timezone" in sql
    assert "new.timezone is distinct from v_timezone" in sql


def test_r5_hr_protection_and_correction_are_owner_locked_and_stale_safe() -> None:
    sql = _sql()
    assert "before update of average_heart_rate_bpm on public.activity_metrics" in sql
    assert (
        "new.average_heart_rate_bpm is distinct from old.average_heart_rate_bpm" in sql
    )
    assert "load.ruleset_version = 'phase-13-joren-ruleset-1'" in sql
    assert "rename to revise_activity_rpe_r5_base" in sql
    wrapper = sql[sql.index("create function public.revise_activity_rpe(") :]
    assert (
        "where id = p_activity_id and athlete_id = p_athlete_id for update" in wrapper
    )
    assert "submitted_average_heart_rate_bpm" in wrapper
    assert "expected_current_rpe" in wrapper
    assert "activity correction is stale" in wrapper
    assert wrapper.index("average heart rate is immutable") < wrapper.index(
        "return public.revise_activity_rpe_r5_base"
    )
    assert "revoke execute on function public.revise_activity_rpe_r5_base" in sql
    assert (
        "grant execute on function public.revise_activity_rpe"
        "(uuid, uuid, jsonb)\nto service_role" in sql
    )
