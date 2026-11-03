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
