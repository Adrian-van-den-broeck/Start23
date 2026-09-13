"""Static gates for the final Phase 13/14 audit remediation migration."""

import re
from pathlib import Path

_ROOT = Path(__file__).parents[2]
_MIGRATIONS = _ROOT / "supabase" / "migrations"
_MIGRATION = _MIGRATIONS / "20260913130000_phase_13_14_r6_entry_audit_remediation.sql"
_PGTAP = (
    _ROOT / "supabase" / "tests" / "phase_13_14_r6_entry_audit_remediation_test.sql"
)


def _sql() -> str:
    return _MIGRATION.read_text(encoding="utf-8").lower()


def test_remediation_is_unique_forward_only_and_preserves_historical_rows() -> None:
    versions = [path.name.split("_", 1)[0] for path in _MIGRATIONS.glob("*.sql")]
    assert len(versions) == len(set(versions))
    assert "20260912180000" in versions
    assert "20260913130000" in versions
    assert sorted(versions).index("20260912180000") < sorted(versions).index(
        "20260913130000"
    )
    sql = _sql()
    assert "delete from public.goals" not in sql
    assert "update public.goals" not in sql
    assert "not valid" in sql
    assert "no r6 contract migration is started" in sql


def test_legacy_operational_profile_is_only_exposed_through_narrow_rpcs() -> None:
    sql = _sql()
    assert (
        "revoke all privileges on table public.athlete_profiles\n"
        "from public, anon, authenticated, service_role" in sql
    )
    assert "create or replace function public.get_operational_athlete_profile()" in sql
    assert "create or replace function public.save_operational_athlete_profile" in sql
    assert "v_auth_user_id uuid := (select auth.uid())" in sql
    assert "from pg_catalog.pg_timezone_names" in sql
    assert "excluded.timezone_confirmed_at" in sql
    assert "statement_timestamp()" in sql
    assert "create or replace function public.start_weekly_checkin" in sql
    assert "security invoker" in sql
    assert "v_operational jsonb := public.get_operational_athlete_profile()" in sql
    assert "create or replace function public.create_validation_test_proposal" in sql
    assert (
        "alter function private.enforce_confirmed_activity_timezone() security definer"
        in sql
    )


def test_sql_has_the_exact_current_race_discipline_mapping_and_readiness_rule() -> None:
    sql = _sql()
    mapping_start = (
        "create or replace function private.required_disciplines_for_race_type"
    )
    mapping_end = (
        "revoke execute on function private.required_disciplines_for_race_type"
    )
    mapping = sql[sql.index(mapping_start) : sql.index(mapping_end)]
    assert "when 'run' then array['run']::text[]" in mapping
    assert "when 'bike' then array['bike']::text[]" in mapping
    assert "when 'swim' then array['swim']::text[]" in mapping
    assert "when 'duathlon' then array['bike', 'run']::text[]" in mapping
    assert "when 'triathlon' then array['swim', 'bike', 'run']::text[]" in mapping
    assert (
        "'race_discipline_profile', to_jsonb(\n"
        "      private.required_disciplines_for_race_type(goal.race_type)" in sql
    )

    readiness_start = (
        "create or replace function private.current_onboarding_satisfied_steps"
    )
    readiness_end = (
        "revoke execute on function private.current_onboarding_satisfied_steps"
    )
    readiness = sql[sql.index(readiness_start) : sql.index(readiness_end)]
    assert "profile.status = 'active'" in readiness
    assert "from public.discipline_zone_setups" not in readiness
    assert "from public.training_history_entries" in readiness
    assert re.search(
        r"baseline_model_version\s*=\s*'phase-13-joren-ruleset-1'", readiness
    )
    assert ") = 3 then 'history'" in readiness


def test_sql_race_contract_closes_null_bound_shape_time_and_date_gaps() -> None:
    sql = _sql()
    constraint_start = "add constraint goals_r6_entry_structured_race_valid"
    constraint_end = (
        "create or replace function private.enforce_current_structured_race_goal"
    )
    constraint = sql[sql.index(constraint_start) : sql.index(constraint_end)]
    for field in (
        "race_type",
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
        assert f"{field} is null" in constraint
    assert "race_type in ('run', 'bike', 'swim', 'triathlon', 'duathlon')" in constraint
    assert "between 1 and 1000000" in constraint
    assert "between 1 and 604800" in constraint
    assert "<= total_target_time_seconds" in constraint
    for race_type in ("run", "bike", "swim", "triathlon", "duathlon"):
        assert f"when '{race_type}' then" in constraint
    assert "new.race_date <= current_date" in sql
    assert "before insert or update of" in sql


def test_submaximal_provenance_is_distinct_and_external_bypass_is_revoked() -> None:
    sql = _sql()
    assert "'submaximal_calibration_estimate'" in sql
    assert "evaluation.status = 'threshold_estimated'" in sql
    assert (
        "evaluation.zone_profiles is distinct from "
        "p_profile -> 'metric_profiles'" in sql
    )
    assert "rename to save_calculated_zone_profile_r5" in sql
    assert (
        "revoke execute on function public.save_calculated_zone_profile_r5(uuid, jsonb)"
        in sql
    )
    assert (
        "grant execute on function public.save_calculated_zone_profile(uuid, jsonb)\n"
        "to service_role" in sql
    )


def test_pgtap_companion_covers_runtime_security_and_race_boundaries() -> None:
    sql = _PGTAP.read_text(encoding="utf-8").lower()
    for phrase in (
        "cannot select legacy identity or physiology columns",
        "cannot write operational fields directly",
        "forged confirmation timestamps are rejected",
        "second owner cannot receive the first owner",
        "setup intent alone cannot imply zone readiness",
        "maximum distance",
        "maximum total target time",
        "future-date rule",
    ):
        assert phrase in sql
    for race_type in ("run", "bike", "swim", "duathlon", "triathlon"):
        assert f"valid {race_type} shape" in sql
