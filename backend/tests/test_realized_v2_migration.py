"""Static contracts only; these do not prove PostgreSQL/RLS/RPC execution."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
MIGRATION = (
    ROOT
    / "supabase/migrations/20261103134520_joren_realized_tss_v2_private_provenance.sql"
)


def test_private_schema_and_least_privilege() -> None:
    sql = MIGRATION.read_text().lower()
    for table in ("realized_v2_activity_inputs", "realized_v2_calculations"):
        assert f"alter table private.{table} enable row level security" in sql
        assert f"alter table private.{table} force row level security" in sql
    assert "grant select, insert" in sql
    assert "from public, anon, authenticated, service_role" in sql
    assert "foreign key (activity_id, athlete_id)" in sql
    assert "private.sync_dual_athlete_owner_keys()" in sql
    assert "for update" in sql
    assert "v_activity.rpe = (p_payload ->> 'rpe')" in sql
    assert "v_previous.revision, 0) + 1" in sql
    assert "v_activity.rpe is not null and v_previous.id is null" in sql
    assert "pg_trigger_depth() > 1" in sql


def test_no_historical_rewrite_or_legacy_constraint_weakening() -> None:
    sql = MIGRATION.read_text().lower()
    assert "update private.activity_loads" not in sql
    assert "alter table private.activity_loads" not in sql
    assert "delete from" not in sql
    assert "public.revise_activity_rpe(p_athlete_id, p_activity_id" in sql
    assert "is distinct from v_basis" in sql
    assert "order by revision desc limit 1" in sql
    assert "template.id = workout.template_id" in sql


def test_sql_syntax_with_existing_parser() -> None:
    # Optional development parser, never install a database tool for this check.
    import pytest

    parser = pytest.importorskip("pglast")
    assert parser.parse_sql(MIGRATION.read_text())
    assert parser.parse_sql(
        (
            MIGRATION.parent / "20261103135735_realized_v2_weekly_registration.sql"
        ).read_text()
    )
    assert parser.parse_sql(
        (
            MIGRATION.parent
            / "20261103140959_realized_v2_planning_evidence_preconditions.sql"
        ).read_text()
    )


def test_new_pending_plans_freeze_evidence_and_guard_approval() -> None:
    sql = (
        (
            MIGRATION.parent
            / "20261103140959_realized_v2_planning_evidence_preconditions.sql"
        )
        .read_text()
        .lower()
    )
    assert "create table private.realized_v2_plan_evidence" in sql
    assert "force row level security" in sql
    assert (
        "v_evidence is distinct from p_payload -> 'weekly_registration_evidence'" in sql
    )
    assert "old.state = 'pending_approval' and new.state = 'active'" in sql
    assert "before update of state on public.plan_revisions" in sql
    assert "v_evidence.evidence is distinct from" in sql
    assert "update private.activity_loads" not in sql


def test_weekly_registration_is_explicit_owned_and_stale_safe() -> None:
    sql = (
        (MIGRATION.parent / "20261103135735_realized_v2_weekly_registration.sql")
        .read_text()
        .lower()
    )
    assert "create table private.workout_registration_events" in sql
    assert "force row level security" in sql
    assert "(select auth.uid())" in sql
    assert "p_expected_registration_revision" in sql
    assert "v_context ->> 'status' = p_status then return v_context" in sql
    assert "for update of plan" in sql
    assert "workout_registration_immutable" in sql
    assert "guard_skipped_workout_activity" in sql
    assert "get_plan_load_history_for_planning_v16" in sql
    assert "'expected_known', revision.id is not null" in sql
    assert "workout.status <> 'cancelled'" in sql
    assert "get_plan_load_history_for_planning_v15" in sql
    assert "delete from" not in sql
