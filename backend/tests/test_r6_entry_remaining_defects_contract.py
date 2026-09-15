"""Static gates for H-01/H-04 and the forward-only R6 remediations."""

import re
from pathlib import Path

from app.modules.calibration.domain import PROTOCOLS

_ROOT = Path(__file__).parents[2]
_MIGRATIONS = _ROOT / "supabase" / "migrations"
_CREATION_MIGRATION = (
    _MIGRATIONS / "20260914080000_close_historical_calibration_writes.sql"
)
_ACTIVATION_MIGRATION = (
    _MIGRATIONS / "20260914090000_block_historical_zone_profile_activation.sql"
)
_PGTAP = _ROOT / "supabase" / "tests"
_R6_FORWARD_MIGRATIONS = {
    "20260912070000_r6_allow_opaque_owner_backfill_for_immutable_calibration.sql",
    "20260914162430_r6_preserve_critical_context_for_submaximal_zone_provenance.sql",
    "20260914162711_r6_order_plan_revision_owner_before_eligibility.sql",
    "20260914163325_r6_restore_activity_idempotency_preflight.sql",
    "20260914170134_r6_increment_structured_race_goal_revision.sql",
    "20260914172000_r6_refresh_planning_snapshot_after_input_change.sql",
    "20260914172500_r6_refresh_extended_planning_snapshot_after_input_change.sql",
    "20260914173000_r6_refresh_planning_snapshot_after_goal_rpc.sql",
    "20260914173500_r6_force_distinct_post_rpc_snapshot_refresh.sql",
    "20260914174000_r6_disambiguate_activity_processing_load_source.sql",
    "20260914175000_r6_cover_foreign_key_access_paths.sql",
    "20260914180000_r6_preserve_account_deletion_cascades.sql",
}


def _sql(path: Path = _CREATION_MIGRATION) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_h01_and_r6_use_unique_forward_only_migrations() -> None:
    migration_paths = list(_MIGRATIONS.glob("*.sql"))
    versions = [path.name.split("_", 1)[0] for path in migration_paths]
    assert len(versions) == len(set(versions))
    names = {path.name for path in migration_paths}
    assert _R6_FORWARD_MIGRATIONS <= names
    assert _CREATION_MIGRATION.name in names
    assert _ACTIVATION_MIGRATION.name in names
    sql = _sql()
    assert "without starting r6" in sql
    assert "delete from public.calibration_" not in sql
    assert "update public.calibration_" not in sql
    assert "truncate" not in sql
    activation_sql = _sql(_ACTIVATION_MIGRATION)
    assert "delete from public.calibration_" not in activation_sql
    assert "delete from public.zone_profile_versions" not in activation_sql
    assert "truncate" not in activation_sql


def test_python_and_database_lifecycle_registries_are_exactly_aligned() -> None:
    expected = {
        protocol_id: (
            protocol.discipline.value,
            protocol.protocol_type.value,
            protocol.lifecycle.value,
        )
        for protocol_id, protocol in PROTOCOLS.items()
    }
    rows = {
        protocol_id: (discipline, protocol_type, lifecycle)
        for protocol_id, discipline, protocol_type, lifecycle in re.findall(
            r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*"
            r"'([^']+)'\s*\)",
            _sql(),
        )
    }
    assert rows == expected
    assert {
        protocol_id
        for protocol_id, values in rows.items()
        if values[2] == "historical_read_only"
    } == {
        "start23_run_threshold_30min_v1",
        "start23_bike_ftp_30min_v1",
        "start23_bike_fthr_20min_v1",
    }


def test_every_database_creation_boundary_uses_the_lifecycle_registry() -> None:
    sql = _sql()
    for function_name in (
        "private.enforce_current_calibration_setup",
        "private.enforce_current_calibration_observation",
        "private.enforce_current_calibration_evaluation",
        "private.enforce_current_calibration_zone_profile",
        "private.enforce_current_validation_test_assignment",
    ):
        start = sql.index(f"create function {function_name}")
        end = sql.index("$$;", start)
        assert "private.is_current_calibration_protocol" in sql[start:end]
    assert (
        "revoke execute on function public.save_integrated_test_assignment(jsonb)"
        in sql
    )
    assert (
        "grant execute on function private.is_current_calibration_protocol"
        "(text,text,text)\nto authenticated" in sql
    )
    proposal_start = sql.index(
        "create or replace function public.create_validation_test_proposal"
    )
    assert "private.is_current_calibration_protocol" in sql[proposal_start:]
    for table_name in (
        "discipline_zone_setups",
        "calibration_observations",
        "calibration_evaluations",
        "zone_profile_versions",
        "discipline_test_assignments",
    ):
        assert f"on public.{table_name}" in sql


def test_database_rpc_and_transition_both_block_historical_activation() -> None:
    sql = _sql(_ACTIVATION_MIGRATION)
    trigger_start = sql.index(
        "create function private.enforce_current_calibration_zone_activation"
    )
    trigger_end = sql.index("$$;", trigger_start)
    trigger_body = sql[trigger_start:trigger_end]
    assert "old.status is distinct from 'active'" in trigger_body
    assert "new.status = 'active'" in trigger_body
    assert "old.calibration_evaluation_id" in trigger_body
    assert "private.is_current_calibration_protocol" in trigger_body
    assert "historical calibration profile cannot be activated" in trigger_body
    assert "before update on public.zone_profile_versions" in sql

    approval_start = sql.index(
        "create or replace function public.approve_zone_proposal"
    )
    approval_body = sql[approval_start:]
    guard_at = approval_body.index("private.is_current_calibration_protocol")
    activation_at = approval_body.index("status = 'active'")
    assert guard_at < activation_at
    assert "profile.calibration_evaluation_id" in approval_body
    assert "historical calibration profile cannot be activated" in approval_body
    assert "security invoker" in approval_body
    assert "set search_path = ''" in approval_body
    assert (
        "grant execute on function public.approve_zone_proposal(uuid, uuid)\n"
        "to authenticated" in approval_body
    )


def test_phase_13_submaximal_threshold_constraint_matches_current_contract() -> None:
    sql = _sql(_ACTIVATION_MIGRATION)
    assert "drop constraint calibration_evaluations_submaximal_no_threshold" in sql
    assert "or ruleset_version = 'phase-13-joren-ruleset-1'" in sql
    for protocol_id in (
        "start23_week1_run_calibration_v1",
        "start23_week1_bike_calibration_v1",
        "start23_week1_swim_calibration_v1",
    ):
        assert protocol_id in sql


def test_backend_boundaries_share_the_domain_lifecycle_classification() -> None:
    domain = (
        _ROOT / "backend" / "app" / "modules" / "calibration" / "domain.py"
    ).read_text(encoding="utf-8")
    service = (
        _ROOT / "backend" / "app" / "modules" / "calibration" / "service.py"
    ).read_text(encoding="utf-8")
    catalog = (
        _ROOT / "backend" / "app" / "modules" / "workouts" / "catalog.py"
    ).read_text(encoding="utf-8")
    assert "def is_current_protocol(" in domain
    assert "protocol.lifecycle is ProtocolLifecycle.CURRENT_SELECTABLE" in domain
    assert "_current_mvp_protocols" not in service
    assert service.count("is_current_protocol(") >= 4
    assert "if all(" in catalog
    assert "is_current_protocol(" in catalog
    assert "for protocol in PROTOCOLS.values()" in catalog


def test_complete_pgtap_directory_targets_the_final_profile_contract() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(_PGTAP.glob("*.sql"))
    )
    assert "alter table public.athlete_profiles disable trigger" not in combined
    assert "authenticated may select profiles subject to rls" not in combined
    assert "an athlete can update their own supported fields" not in combined
    assert (
        "the final contract denies every authenticated direct profile update"
        in combined
    )
    for phrase in (
        "authenticated direct operational inserts fail",
        "authenticated direct operational updates fail",
        "invalid iana timezones fail",
        "forged timezone confirmation timestamps fail",
        "retired direct physiology writes fail",
        "second owner cannot read the first owner physiology row",
        "rejects attacker-controlled athlete ids",
        "cannot enumerate the private identity map",
        "rpc guards remain enabled",
        "service operations do not regain broad legacy operational-table reads",
    ):
        assert phrase in combined


def test_h01_pgtap_companion_covers_current_history_and_state_boundaries() -> None:
    sql = _sql(_PGTAP / "phase_13_calibration_lifecycle_test.sql")
    for phrase in (
        "current swim, bike, and run observations are newly persistable",
        "current swim, bike, and run observations are newly evaluable",
        "observation api rejects a new historical observation",
        "direct insert with the legacy guard flag",
        "cannot configure a historical field test",
        "historical field tests cannot be newly scheduled",
        "service evaluation persistence rpc rejects historical protocols",
        "current evaluation requires a matching existing observation",
        "no historical protocol can generate a new pending proposal",
        "preserves authenticated owner reads of already-stored history",
    ):
        assert phrase in sql

    activation_sql = _sql(_PGTAP / "phase_13_historical_activation_guard_test.sql")
    for phrase in (
        "historical pending run profile cannot be activated through approval rpc",
        "historical pending bike profile cannot be activated through approval rpc",
        "direct historical pending profile transition to active is rejected",
        "historical pending run profile remains readable and unchanged",
        "already-active historical profile remains readable and is not rewritten",
        "current run pending calibration profile can still be approved",
        "current bike pending calibration profile can still be approved",
        "current swim css pending calibration profile can still be approved",
        "stale current calibration approval still fails",
        "replayed current approval retains the existing terminal behavior",
        "current calculated-profile creation retries remain idempotent",
        "current run bike and swim calibration create pending calculated profiles",
        "rejected historical approvals leave pending history unchanged",
        "all current calibration activations retain their evaluation provenance",
    ):
        assert phrase in activation_sql
    assert "disable trigger" not in activation_sql
