"""Reproduce actual 63-file failure, then prove the forward projection correction."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from app.modules.activities.service import ActivityDomainError, ActivityService
from scripts.rehearse_v6_migration_boundary import snapshots
from scripts.v6_rollout_policy import CORRECTIONS
from scripts.verify_v6_blocker_sql import activity_probe, historical_consumer
from scripts.verify_v6_final_sql import ROOT, Replay


def run(args: argparse.Namespace) -> None:
    replay = Replay(args)
    identity = json.loads(
        replay.checked(
            "select jsonb_build_object('directory',current_setting('data_directory'),"
            "'address',inet_server_addr(),'port',inet_server_port())",
            "postgres",
            "identity",
        )
    )
    if (
        Path(identity["directory"]).resolve() != args.cluster_directory.resolve()
        or identity["address"] != "127.0.0.1"
        or identity["port"] != args.port
    ):
        raise RuntimeError("Wrong disposable cluster")
    files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    accepted = [p for p in files if p.name not in CORRECTIONS]
    expected = json.loads(
        (
            ROOT
            / "docs/catalog/implementation/migration-readiness-20261116"
            / "hosted-before.json"
        ).read_text()
    )["migration_comparison"]["accepted_sha256"]
    if {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in accepted
    } != expected:
        raise RuntimeError("Accepted 63-file chain changed")
    db = args.database
    replay.checked("create database " + db, "postgres", "create")
    replay.checked(
        (
            ROOT / "supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql"
        ).read_text(encoding="utf-8"),
        db,
        "bootstrap",
    )
    for file in accepted:
        replay.checked(
            "begin;" + file.read_text(encoding="utf-8") + "commit;", db, file.stem
        )
    replay.checked(
        (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text(
            encoding="utf-8"
        ),
        db,
        "synthetic-users",
    )
    claims = json.dumps(
        {"role": "authenticated", "sub": "a6000000-0000-0000-0000-000000000006"}
    )
    payload = json.dumps(
        {
            "discipline": "run",
            "source": "manual",
            "started_at": "2026-08-03T08:00:00+02:00",
            "timezone": "Europe/Amsterdam",
            "duration_minutes": 30,
            "metrics": {"average_heart_rate_bpm": 140},
        }
    )
    response = json.loads(
        replay.checked(
            "begin;set local role authenticated;set local request.jwt.claims='"
            + claims
            + "';select public.create_activity_summary("
            "'ac190000-0000-0000-0000-000000000001','"
            + "a" * 64
            + "','"
            + payload
            + "');commit;",
            db,
            "actual-63-activity",
        )
    )
    old, hashes = historical_consumer()
    assert ActivityService._response(response).session_rpe_version == "legacy"
    try:
        old(response)
    except ActivityDomainError as error:
        assert error.__cause__ is not None and "session_rpe_version" in str(
            error.__cause__
        )
    else:
        raise RuntimeError("Original strict-model incompatibility was not reproduced")
    before = snapshots(replay, db, "before-correction")
    replay.checked(
        "begin;"
        + "\n".join(
            (ROOT / "supabase/migrations" / p).read_text(encoding="utf-8")
            for p in CORRECTIONS
        )
        + "commit;",
        db,
        "forward-corrections",
    )
    assert snapshots(replay, db, "after-correction") == before
    activity_probe(replay, db, "corrected-65", versioned=True)
    replay.save(
        "boundary-results.json",
        {
            "hosted_execution": False,
            "historical_source_sha256": hashes,
            "actual_63_projection": {
                "historical_model": "EXPECTED extra_forbidden(session_rpe_version)",
                "current_model": "PASS",
            },
            "corrected_65_projection": {
                "historical_model": "PASS",
                "current_model": "PASS",
                "explicit_v2": "PASS",
            },
            "preserved_tables": len(before),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--cluster-directory", type=Path, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute_disposable_local_only or not re.fullmatch(
        r"wombo_v6_boundary_[a-z0-9_]+", args.database
    ):
        parser.error("New disposable local database required")
    run(args)


if __name__ == "__main__":
    main()
