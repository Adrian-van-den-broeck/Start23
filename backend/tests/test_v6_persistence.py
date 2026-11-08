"""Lossless/static/transport evidence only. These are NOT PostgreSQL/RLS passes."""

import asyncio
import json
import re
import subprocess
import sys
from copy import deepcopy
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest
from test_planning_repository import _settings

from app.modules.physiology.planned_v6 import sum_official
from app.modules.planning.repository import (
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
    PlanningRepositoryUnavailableError,
)
from app.modules.planning.v6_repository import (
    InactiveSupabaseV6CatalogProvider,
    InactiveSupabaseV6Repository,
)
from app.modules.workouts.joren_v6_official import official_catalog
from app.modules.workouts.v6_storage import (
    canonical_document,
    catalog_document,
    parse_catalog_document,
)

ROOT = Path(__file__).parents[2]
SCHEMA = ROOT / "supabase/migrations/20261105120000_inactive_v6_persistence.sql"
CATALOG = ROOT / "supabase/migrations/20261105120100_inactive_v6_catalog.sql"


def rows() -> list[dict[str, Any]]:
    match = re.search(
        r"\$v6_catalog\$(.*?)\$v6_catalog\$", CATALOG.read_text(encoding="utf-8"), re.S
    )
    assert match
    result: list[dict[str, Any]] = json.loads(match[1])
    return result


@pytest.mark.parametrize("index", range(77))
def test_all_official_sources_lossless_and_independently_recomputed(index: int) -> None:
    original = official_catalog()[index]
    row = rows()[index]
    restored = parse_catalog_document(json.loads(json.dumps(row["document"])))
    assert restored == original
    assert canonical_document(row["document"]) == canonical_document(
        catalog_document(original)
    )
    assert (
        sha256(canonical_document(row["document"]).encode()).hexdigest()
        == row["document_sha256"]
    )
    assert restored.source_revision.source_sha256 == row["source_sha256"]
    assert restored.source_revision.source_row == row["source_row"]
    assert (
        restored.source_revision.predecessor.original_cells
        == original.source_revision.predecessor.original_cells
    )
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        independently_converted = Decimal(row["numerator"]) / Decimal(
            row["denominator"]
        )
    assert (
        independently_converted
        == restored.official.value
        == Decimal(row["official_decimal"])
    )
    assert str(restored.official.value) == row["official_decimal"]


def test_sql_preparation_reproduces_exact_migration() -> None:
    from scripts.prepare_v6_catalog_sql import prepare

    assert prepare() == CATALOG.read_text(encoding="utf-8")
    assert len({r["logical_key"] for r in rows()}) == 77
    assert len({r["template_id"] for r in rows()}) == 77


def test_catalog_can_reload_in_a_new_process_without_reading_workbooks(
    tmp_path: Path,
) -> None:
    source = tmp_path / "private-catalog.json"
    source.write_text(json.dumps([r["document"] for r in rows()]), encoding="utf-8")
    code = """
import json, sys
from pathlib import Path
from unittest.mock import patch
from app.modules.workouts.v6_storage import (
    parse_catalog_document, canonical_document, catalog_document,
)
docs = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
with patch('zipfile.ZipFile', side_effect=AssertionError('workbook unavailable')):
    restored = [parse_catalog_document(d) for d in docs]
assert [canonical_document(catalog_document(t)) for t in restored] == [
    canonical_document(d) for d in docs
]
print(len(restored))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "77"


@pytest.mark.parametrize("change", ["activation", "format", "decimal", "unknown_type"])
def test_corrupt_durable_document_fails_closed(change: str) -> None:
    doc = deepcopy(rows()[0]["document"])
    if change == "activation":
        doc["template"]["fields"]["activation_status"] = "ACTIVE"
    elif change == "format":
        doc["format"] = "future-unapproved-format"
    elif change == "decimal":
        doc["template"]["fields"]["official"]["fields"]["value"]["value"] = "NaN"
    else:
        doc["template"]["type"] = "arbitrary.import.Class"
    with pytest.raises((KeyError, ValueError)):
        parse_catalog_document(doc)


def test_storage_precision_and_aggregate_comparison_are_not_quantized() -> None:
    values = tuple(Decimal(r["official_decimal"]) for r in rows())
    with localcontext(Context(prec=5)):
        total = sum_official(values)
    from fractions import Fraction

    assert Fraction(total) == sum(map(Fraction, values))
    tiny_over = Decimal("45.000000000000000000000000000000000000000000000001")
    assert sum_official((Decimal(45), tiny_over - Decimal(45))) > 45
    sql = SCHEMA.read_text(encoding="utf-8")
    assert "planned_tss numeric not null" in sql
    assert "round(" not in sql and "numeric(" not in sql


@pytest.mark.parametrize("operation", ["write", "context", "retry", "read", "catalog"])
def test_v6_transport_scopes_credentials_and_recreates_repository(
    operation: str,
) -> None:
    athlete, plan = uuid4(), uuid4()
    requests: list[httpx.Request] = []
    documents = [r["document"] for r in rows()]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("resolve_legacy_auth_user_id"):
            return httpx.Response(200, json=str(athlete))
        if request.url.path.endswith("get_inactive_v6_catalog_for_planning"):
            return httpx.Response(200, json=documents)
        if request.url.path.endswith("get_v6_mobile_weekly_plan"):
            assert request.headers["authorization"] == "Bearer caller-a"
            assert request.headers["apikey"] == "sb_publishable_test"
            return httpx.Response(
                200, content=b'{"duration_minutes":0.12345678901234567890123456789}'
            )
        assert request.headers["apikey"] == "sb_secret_test"
        assert "authorization" not in request.headers
        body = json.loads(request.content)
        assert body["p_athlete_id"] == str(athlete)
        return httpx.Response(200, json={"persisted": True})

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            for _ in range(2):
                repo = InactiveSupabaseV6Repository(_settings(), client=client)
                if operation == "write":
                    assert await repo.create_plan_proposal(
                        athlete, {"exact": "0.12345678901234567890123456789"}
                    ) == {"persisted": True}
                elif operation == "context":
                    assert (await repo.fetch_plan_revision_context(athlete, plan, 2))[
                        "persisted"
                    ]
                elif operation == "retry":
                    assert await repo.fetch_v6_edit_retry(athlete, "a" * 64) == {
                        "persisted": True
                    }
                elif operation == "read":
                    assert (await repo.fetch_plan("caller-a", plan, 2))[
                        "duration_minutes"
                    ] == Decimal("0.12345678901234567890123456789")
                else:
                    assert (
                        len(
                            await InactiveSupabaseV6CatalogProvider(
                                repo
                            ).fetch_catalog()
                        )
                        == 77
                    )

    asyncio.run(run())
    assert requests


@pytest.mark.parametrize("evidence", [None, [{"week_start": "2026-10-19"}]])
def test_v6_write_preserves_registration_evidence_or_sends_empty_history(
    evidence: list[dict[str, Any]] | None,
) -> None:
    athlete = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("resolve_legacy_auth_user_id"):
            return httpx.Response(200, json=str(athlete))
        payload = json.loads(request.content)["p_payload"]
        assert payload["weekly_registration_evidence"] == (evidence or [])
        return httpx.Response(200, json={"persisted": True})

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            payload = (
                {} if evidence is None else {"weekly_registration_evidence": evidence}
            )
            await InactiveSupabaseV6Repository(
                _settings(), client=client
            ).create_plan_proposal(athlete, payload)

    asyncio.run(run())


def test_sql_runner_uses_explicit_utf8_for_postgres_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import verify_v6_postgres as runner

    monkeypatch.setenv(
        "WOMBO_V6_DISPOSABLE_PG_DSN", "postgresql://postgres@127.0.0.1/disposable"
    )
    monkeypatch.setattr("scripts.verify_v6_postgres.shutil.which", lambda _: "psql")

    def execute(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["env"]["PGCLIENTENCODING"] == "UTF8"
        return subprocess.CompletedProcess(args, 0, '{"source":"durée · bron"}', "")

    monkeypatch.setattr("scripts.verify_v6_postgres.subprocess.run", execute)
    assert runner.LocalPostgres().execute("select source") == {"source": "durée · bron"}


@pytest.mark.parametrize(
    "code,expected",
    [
        ("PT409", PlanningRepositoryConflictError),
        ("P0002", PlanningRepositoryNotFoundError),
        ("08006", PlanningRepositoryUnavailableError),
    ],
)
def test_database_errors_never_expose_private_diagnostics(
    code: str, expected: type[Exception]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("resolve_legacy_auth_user_id"):
            return httpx.Response(200, json=str(uuid4()))
        return httpx.Response(
            503 if code == "08006" else 409,
            json={"code": code, "message": "private planned_tss details"},
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(expected) as error:
                await InactiveSupabaseV6Repository(
                    _settings(), client=client
                ).create_plan_proposal(uuid4(), {})
            assert "planned_tss" not in str(error.value)

    asyncio.run(run())


def test_postgres_syntax_and_security_structure_only() -> None:
    parser = pytest.importorskip("pglast")
    assert parser.parse_sql(SCHEMA.read_text(encoding="utf-8"))
    assert parser.parse_sql(CATALOG.read_text(encoding="utf-8"))
    sql = SCHEMA.read_text(encoding="utf-8").lower()
    for name in ("v6_plan_snapshots", "v6_occurrence_snapshots", "v6_edit_results"):
        assert name in sql
    assert "force row level security" in sql
    assert "pg_advisory_xact_lock" in sql and "for update of p" in sql
    assert "expected_pending_revision" in sql and "expected_proposal_id" in sql
    assert "foreign key (revision_id, athlete_id)" in sql
    assert "foreign key (planned_workout_id, athlete_id)" in sql
    assert "from public, anon, authenticated, service_role" in sql
    assert "update private.activity_loads" not in sql
    assert "create or replace function public.approve_plan_proposal" not in sql
    assert "v6_repository" not in (ROOT / "backend/app/main.py").read_text()


def test_only_exact_reviewed_import_is_an_intentional_identity_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.jobs import joren_catalog_dry_run as job
    from app.modules.workouts.joren_draft import SourceError, build_manifest

    directory = tmp_path / "supabase/migrations"
    directory.mkdir(parents=True)
    prepared = directory / CATALOG.name
    prepared.write_bytes(CATALOG.read_bytes())
    monkeypatch.setattr(job, "ROOT", tmp_path)
    assert not job.offline_reserved_ids()
    prepared.write_bytes(prepared.read_bytes() + b"\n-- unreviewed mutation\n")
    with pytest.raises(SourceError, match="provisional_uuid_collision"):
        build_manifest(reserved=job.offline_reserved_ids())
    prepared.write_bytes(CATALOG.read_bytes())
    identity = build_manifest().records[0].provisional_key
    (directory / "future_collision.sql").write_text(str(identity), encoding="utf-8")
    assert identity in job.offline_reserved_ids()
    with pytest.raises(SourceError, match="provisional_uuid_collision"):
        build_manifest(reserved=job.offline_reserved_ids())


def test_stored_controls_survive_restart_and_current_restrictions_can_tighten() -> None:
    from dataclasses import replace
    from datetime import date

    from app.modules.planning.v6_selection import V6Controls
    from app.modules.planning.v6_service import controls_json, effective_controls

    athlete, template = uuid4(), uuid4()
    controls = V6Controls(
        athlete_scope=athlete,
        week_scope=date(2026, 10, 26),
        duration_evidence=((template, "approved-individual-evidence-reference"),),
        maximum_uses=((template, 2),),
    )
    stored = json.loads(controls_json(controls))
    assert effective_controls(stored, V6Controls()) == controls
    assert effective_controls(
        stored, replace(controls, maximum_uses=((template, 1),))
    ).maximum_uses == ((template, 1),)
    assert effective_controls(
        stored, replace(controls, maximum_uses=((template, 3),))
    ).maximum_uses == ((template, 2),)


def test_shared_service_interleaved_initial_requests_do_not_cross_bind_athletes() -> (
    None
):
    from datetime import date, timedelta

    from v6_repository_fixture import V6MemoryRepository

    from app.modules.coach.weekly_plan import DisabledWeeklyPlanCoach
    from app.modules.planning.schemas import WeeklyPlanProposalRequest
    from app.modules.planning.v6_service import V6PlanningService

    async def exercise() -> None:
        catalog = official_catalog()
        owners = {"athlete-a": uuid4(), "athlete-b": uuid4()}
        repository = V6MemoryRepository(owners, catalog)
        gate = asyncio.Event()

        class Provider:
            calls = 0

            async def fetch_catalog(self) -> tuple[Any, ...]:
                self.calls += 1
                if self.calls == 2:
                    gate.set()
                await gate.wait()
                return catalog

        class Computation:
            async def run(self, function: Any, **kwargs: Any) -> Any:
                return function(**kwargs)

        planner = V6PlanningService(
            repository, Provider(), DisabledWeeklyPlanCoach(), Computation()
        )
        start = date(2026, 10, 26)
        request = WeeklyPlanProposalRequest(
            week_start=start,
            available_dates=(
                start,
                start + timedelta(days=2),
                start + timedelta(days=5),
            ),
        )
        first, second = await asyncio.gather(
            *(
                planner.generate_initial_proposal(token, owner, request)
                for token, owner in owners.items()
            )
        )
        assert {w.id for w in first.plan.workouts}.isdisjoint(
            w.id for w in second.plan.workouts
        )
        assert len(first.plan.workouts) == len(second.plan.workouts) == 3

    asyncio.run(exercise())
