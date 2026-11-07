"""Opt-in real SQL integration runner. Requires an already migrated disposable DB.

Never reads .env, never connects to a non-loopback host, never applies migrations.
Each request uses a NEW psql process/connection and a real database transaction.
The parent destroys the create-stage Python process before starting resume.
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx

from app.core.config import Settings
from app.modules.coach.weekly_plan import DisabledWeeklyPlanCoach
from app.modules.physiology.planned_v6 import sum_official
from app.modules.planning.repository import (
    PlanningRepositoryConflictError,
    PlanningRepositoryNotFoundError,
    PlanningRepositoryUnavailableError,
)
from app.modules.planning.schemas import (
    PendingWorkoutEditRequest,
    WeeklyPlanProposalRequest,
)
from app.modules.planning.v6_repository import (
    InactiveSupabaseV6CatalogProvider,
    InactiveSupabaseV6Repository,
)
from app.modules.planning.v6_selection import V6Controls
from app.modules.planning.v6_service import V6PlanningService, private_json
from app.modules.workouts.joren_v6_official import official_catalog
from app.modules.workouts.v6_storage import catalog_document, parse_catalog_document

ROOT = Path(__file__).resolve().parents[2]
USERS = (
    UUID("a6000000-0000-0000-0000-000000000006"),
    UUID("b6000000-0000-0000-0000-000000000006"),
)


def literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (dict, list)):
        return "'" + json.dumps(value).replace("'", "''") + "'::jsonb"
    return "'" + str(value).replace("'", "''") + "'"


class TransitionBarrier:
    """Both clients finish validation before either sends its competing RPC."""

    def __init__(self) -> None:
        self.arrivals = 0
        self.ready = asyncio.Event()

    async def wait(self) -> None:
        self.arrivals += 1
        if self.arrivals == 2:
            self.ready.set()
        await asyncio.wait_for(self.ready.wait(), timeout=30)


class LocalPostgres:
    def __init__(self) -> None:
        self.dsn = os.environ.get("WOMBO_V6_DISPOSABLE_PG_DSN", "")
        parsed = urlparse(self.dsn)
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.query
            or parsed.fragment
            or not shutil.which("psql")
        ):
            raise RuntimeError("NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE")

    def execute(
        self,
        sql: str,
        *,
        user: UUID | None = None,
        service: bool = False,
        rollback: bool = False,
    ) -> Any:
        claims = {"role": "service_role" if service else "authenticated"}
        if user:
            claims["sub"] = str(user)
        prefix = "begin; set local statement_timeout = '20s';"
        if user or service:
            prefix += (
                "set local request.jwt.claims = " + literal(json.dumps(claims)) + ";"
            )
            prefix += (
                "set local request.jwt.claim.sub = "
                + literal(str(user) if user else "")
                + ";"
            )
            prefix += (
                "set local role "
                + ("service_role" if service else "authenticated")
                + ";"
            )
        result = subprocess.run(
            [
                "psql",
                "--no-psqlrc",
                "--quiet",
                "--tuples-only",
                "--no-align",
                "--set=ON_ERROR_STOP=1",
                "--set=VERBOSITY=verbose",
                "--dbname",
                self.dsn,
            ],
            input=prefix + sql + (";rollback;" if rollback else ";commit;"),
            encoding="utf-8",
            env={**os.environ, "PGCLIENTENCODING": "UTF8"},
            capture_output=True,
            timeout=30,
        )
        if result.returncode:
            code = re.search(r"ERROR:\s+([A-Z0-9]{5}):", result.stderr)
            state = code[1] if code else "unavailable"
            if state == "P0002":
                raise PlanningRepositoryNotFoundError
            if state in {"PT409", "40001", "23514", "23503", "23505", "42501", "55000"}:
                raise PlanningRepositoryConflictError(state)
            raise PlanningRepositoryUnavailableError(
                "Disposable SQL verification failed: " + state
            )
        output = result.stdout.strip()
        return json.loads(output, parse_float=Decimal) if output else None


class InlineComputation:
    async def run(self, function: Callable[..., Any], **kwargs: Any) -> Any:
        return function(**kwargs)


class SqlRepository(InactiveSupabaseV6Repository):
    """Use the actual repository methods, replacing only HTTP with local SQL.

    Data API transport/auth verification is a separate gate; SQL roles, JWT GUCs,
    grants, RLS, constraints and nested RPC transactions are real in this runner.
    """

    def __init__(self, db: LocalPostgres) -> None:
        def no_network(request: httpx.Request) -> httpx.Response:
            raise AssertionError("Network calls are forbidden in the SQL runner")

        super().__init__(
            Settings(environment="test", _env_file=None),
            client=httpx.AsyncClient(transport=httpx.MockTransport(no_network)),
        )
        self.db = db
        self.rollback_write = False
        self.transition_barrier: TransitionBarrier | None = None

    async def _rpc_athlete_id(self, athlete_id: UUID) -> UUID:
        return UUID(
            await asyncio.to_thread(
                self.db.execute,
                "select to_jsonb(public.resolve_legacy_auth_user_id("
                + literal(athlete_id)
                + "))",
                service=True,
            )
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str = "",
        service: bool = False,
        params: Mapping[str, str] | None = None,
        json: Any = None,
    ) -> Any:
        user = UUID(access_token) if access_token else None
        if self.transition_barrier is not None and path in {
            "rpc/create_v6_weekly_plan_proposal",
            "rpc/approve_plan_proposal",
        }:
            await self.transition_barrier.wait()
        if method == "POST" and path.startswith("rpc/"):
            name = path.removeprefix("rpc/")
            if not re.fullmatch("[a-z_0-9]+", name):
                raise AssertionError("invalid SQL test function")
            arguments = ",".join(
                k + " => " + literal(v) for k, v in (json or {}).items()
            )
            call = "public." + name + "(" + arguments + ")"
            sql = (
                "select coalesce(jsonb_agg(r), '[]') from " + call + " r"
                if name == "get_plan_load_history_for_planning_v16"
                else "select to_jsonb(" + call + ")"
            )
        elif (
            method == "GET"
            and params is not None
            and path
            in {
                "initial_plan_requests",
                "onboarding_sessions",
                "change_proposals",
                "swipe_week_drafts",
            }
        ):
            columns = params["select"]
            assert re.fullmatch("[a-z_,0-9]+", columns)
            where = []
            for key in ("id", "internal_athlete_id"):
                if key in params:
                    where.append(
                        key + " = " + literal(UUID(params[key].removeprefix("eq.")))
                    )
            sql = (
                "select coalesce(jsonb_agg(r), '[]') from (select "
                + columns
                + " from public."
                + path
            )
            sql += " where " + (" and ".join(where) or "true") + " limit 1) r"
        else:
            raise AssertionError(
                "Unsupported local SQL adapter operation: " + method + " " + path
            )
        return await asyncio.to_thread(
            self.db.execute,
            sql,
            user=user,
            service=service,
            rollback=self.rollback_write
            and path == "rpc/create_v6_weekly_plan_proposal",
        )


def service(db: LocalPostgres) -> tuple[SqlRepository, V6PlanningService]:
    repository = SqlRepository(db)
    return repository, V6PlanningService(
        repository,
        InactiveSupabaseV6CatalogProvider(repository),
        DisabledWeeklyPlanCoach(),
        InlineComputation(),
    )


def identity(db: LocalPostgres, user: UUID) -> UUID:
    return UUID(
        db.execute(
            "select to_jsonb(athlete_id) from private.athlete_identity_map "
            "where auth_user_id = " + literal(user)
        )
    )


def verify_numeric_round_trips(db: LocalPostgres) -> None:
    expected = {str(template.id): template for template in official_catalog()}
    stored = db.execute(
        "select jsonb_agg(to_jsonb(s) order by template_id) "
        "from private.v6_source_revisions s"
    )
    assert len(stored) == len(expected) == 77
    for row in stored:
        template = expected[row["template_id"]]
        assert row["official_decimal"] == str(template.official.value)
        assert Decimal(str(row["planned_tss"])) == template.official.value
        assert row["numerator"] == str(template.official.numerator)
        assert row["denominator"] == str(template.official.denominator)
        assert row["planned_method"] == template.official.method
        assert row["reference_version"] == template.official.parameters
        assert row["source_sha256"] == template.source_revision.source_sha256
        assert row["activation"] == "INACTIVE"
        assert row["source_snapshot"] == json.loads(private_json(asdict(template)))
        assert row["public_snapshot"] == V6PlanningService._deck_item(
            template
        ).model_dump(mode="json")
        assert parse_catalog_document(row["document"]) == template
        assert row["document"] == catalog_document(template)
    assert db.execute(
        "select to_jsonb(sum(planned_tss)) from private.v6_source_revisions"
    ) == sum_official(tuple(template.official.value for template in expected.values()))
    over_budget = Decimal("45.000000000000000000000000000000000000000000000001")
    assert db.execute(
        "create temporary table v6_budget_numeric_probe(value numeric); "
        "insert into v6_budget_numeric_probe values ("
        + literal(over_budget)
        + "::numeric); select jsonb_build_object('value',value,'within',value<=45) "
        "from v6_budget_numeric_probe",
        rollback=True,
    ) == {"value": over_budget, "within": False}
    assert (
        db.execute(
            "select to_jsonb(atttypmod) from pg_attribute "
            "where attrelid='private.v6_source_revisions'::regclass "
            "and attname='planned_tss'"
        )
        == -1
    )
    try:
        db.execute(
            "insert into private.v6_source_revisions select "
            "(jsonb_populate_record(null::private.v6_source_revisions, "
            "to_jsonb(s) || jsonb_build_object('planned_tss', s.planned_tss + "
            "'0.000000000000000000000000000000000000000000000001'::numeric))).* "
            "from private.v6_source_revisions s limit 1",
            rollback=True,
        )
    except PlanningRepositoryConflictError as error:
        assert error.code == "23514"
    else:
        raise AssertionError("Numeric equality constraint accepted a rounded value")
    print("77 exact Decimal/rational/source/workbook round trips passed.", flush=True)


def verify_composite_ownership(db: LocalPostgres, revision_id: UUID) -> None:
    before = db.execute("select to_jsonb(count(*)) from public.plan_revisions")
    for table in ("v6_plan_snapshots", "v6_occurrence_snapshots", "v6_edit_results"):
        revision, workout = uuid4(), uuid4()
        prefix = (
            "set local start23.critical_write='on'; "
            "insert into public.plan_revisions select (jsonb_populate_record("
            "null::public.plan_revisions, to_jsonb(r) || jsonb_build_object('id',"
            + literal(revision)
            + ",'revision_number',1000,'generation_fingerprint',"
            + literal(sha256(str(revision).encode()).hexdigest())
            + ",'state','pending_approval'))).* from public.plan_revisions r where id="
            + literal(revision_id)
            + "; "
        )
        if table == "v6_plan_snapshots":
            mutation = (
                "insert into private.v6_plan_snapshots"
                "(revision_id,athlete_id,payload,input_snapshot) values ("
                + literal(revision)
                + ","
                + literal(USERS[1])
                + ",'{}','{}')"
            )
        elif table == "v6_edit_results":
            mutation = (
                "insert into private.v6_edit_results"
                "(revision_id,athlete_id,operation_key,result) values ("
                + literal(revision)
                + ","
                + literal(USERS[1])
                + ","
                + literal(sha256(str(revision).encode()).hexdigest())
                + ",'{}')"
            )
        else:
            prefix += (
                "insert into public.planned_workouts select (jsonb_populate_record("
                "null::public.planned_workouts,to_jsonb(w)||jsonb_build_object('id',"
                + literal(workout)
                + ",'revision_id',"
                + literal(revision)
                + "))).* from public.planned_workouts w where revision_id="
                + literal(revision_id)
                + " limit 1; "
            )
            mutation = (
                "insert into private.v6_occurrence_snapshots"
                "(planned_workout_id,revision_id,athlete_id,occurrence_id,ordinal) "
                "values ("
                + literal(workout)
                + ","
                + literal(revision)
                + ","
                + literal(USERS[1])
                + ","
                + literal(uuid4())
                + ",1)"
            )
        try:
            db.execute(prefix + mutation, rollback=True)
        except PlanningRepositoryConflictError as error:
            assert error.code == "23503", table
        else:
            raise AssertionError(
                "Composite owner FK accepted a foreign owner: " + table
            )
        assert (
            db.execute("select to_jsonb(count(*)) from public.plan_revisions") == before
        )
    print(
        "Three composite owner FK violations rolled back all preceding writes.",
        flush=True,
    )


async def create_stage(db: LocalPostgres, output: Path) -> None:
    verify_numeric_round_trips(db)
    repository, planner = service(db)
    start = date(2026, 10, 26)
    request = WeeklyPlanProposalRequest(
        week_start=start,
        available_dates=(start, start + timedelta(days=2), start + timedelta(days=5)),
    )
    snapshots = []
    for user in USERS:
        result = await planner.generate_initial_proposal(
            str(user), identity(db, user), request
        )
        snapshots.append(result.model_dump(mode="json"))
    output.write_text(json.dumps(snapshots), encoding="utf-8")
    await repository._client.aclose()


async def resume_stage(db: LocalPostgres, output: Path) -> None:
    old = json.loads(output.read_text(encoding="utf-8"))
    repo, planner = service(db)
    athlete = identity(db, USERS[0])
    plan = await planner.get_plan(str(USERS[0]), UUID(old[0]["plan"]["id"]), 1)
    assert plan.model_dump(mode="json") == old[0]["plan"]
    assert plan.proposal is not None
    for table, key, foreign_id in (
        ("weekly_plans", "id", old[1]["plan"]["id"]),
        ("plan_revisions", "id", old[1]["plan"]["revision_id"]),
        ("change_proposals", "id", old[1]["proposal"]["id"]),
        ("planned_workouts", "plan_id", old[1]["plan"]["id"]),
    ):
        assert (
            db.execute(
                "select to_jsonb(count(*)) from public."
                + table
                + " where "
                + key
                + " = "
                + literal(foreign_id),
                user=USERS[0],
            )
            == 0
        )
    assert (
        db.execute(
            "set local start23.critical_write = 'on'; with changed as ("
            "update public.planned_workouts set description = 'foreign tamper' "
            "where plan_id = "
            + literal(old[1]["plan"]["id"])
            + " returning id) select to_jsonb(count(*)) from changed",
            user=USERS[0],
        )
        == 0
    )
    catalog = await InactiveSupabaseV6CatalogProvider(repo).fetch_catalog()
    kept = {w.template_id for w in plan.workouts}
    exhausted = V6PlanningService(
        repo,
        InactiveSupabaseV6CatalogProvider(repo),
        DisabledWeeklyPlanCoach(),
        InlineComputation(),
        controls=V6Controls(
            maximum_uses=tuple((t.id, 0) for t in catalog if t.id not in kept)
        ),
    )
    exhausted_slot = plan.workouts[0]
    no_choices = await exhausted.get_pending_workout_alternatives(
        str(USERS[0]), athlete, plan.id, exhausted_slot.id, plan.revision
    )
    assert not no_choices.alternatives
    assert await planner.get_plan(str(USERS[0]), plan.id, plan.revision) == plan
    payload = db.execute(
        "select payload from private.v6_plan_snapshots where revision_id = "
        + literal(plan.revision_id)
    )
    payload.update(
        plan_id=str(plan.id),
        expected_pending_revision=plan.revision,
        expected_proposal_id=str(plan.proposal.id),
    )
    mutations: dict[str, Callable[[Any], None]] = {
        "plan": lambda p: p.update(plan_id=old[1]["plan"]["id"]),
        "revision": lambda p: p.update(expected_pending_revision=None),
        "proposal": lambda p: p.update(expected_proposal_id=old[1]["proposal"]["id"]),
        "athlete_context": lambda p: p["v6_frozen_snapshot"]["controls"].update(
            athlete_scope=str(identity(db, USERS[1]))
        ),
        "week_context": lambda p: p["v6_frozen_snapshot"]["controls"].update(
            week_scope="2026-11-02"
        ),
        "foreign_occurrence": lambda p: p["workouts"][0].update(
            occurrence_id=old[1]["plan"]["workouts"][0]["id"]
        ),
        "missing_source": lambda p: p["workouts"][0].update(template_id=str(uuid4())),
        "invalid_source_hash": lambda p: p["workouts"][0].update(
            source_revision_sha256="0" * 64
        ),
    }
    for label, mutate in mutations.items():
        altered = deepcopy(payload)
        altered["generation_fingerprint"] = sha256(label.encode()).hexdigest()
        altered["v6_edit_operation_key"] = sha256(
            (label + "-retry").encode()
        ).hexdigest()
        mutate(altered)
        try:
            await repo.create_plan_proposal(athlete, altered)
        except (PlanningRepositoryConflictError, PlanningRepositoryNotFoundError):
            pass
        else:
            raise AssertionError("Tampered database input accepted: " + label)
        assert (await planner.get_plan(str(USERS[0]), plan.id, 1)) == plan
        assert (
            db.execute(
                "select to_jsonb(count(*)) from public.plan_revisions where plan_id = "
                + literal(plan.id)
            )
            == 1
        )
    for action in (
        lambda: planner.get_plan(str(USERS[1]), plan.id, plan.revision),
        lambda: planner.approve_plan_proposal(str(USERS[1]), plan.proposal.id, 0),
        lambda: repo.fetch_plan_revision_context(
            identity(db, USERS[1]), plan.id, plan.revision
        ),
    ):
        try:
            await action()
        except PlanningRepositoryNotFoundError:
            pass
        else:
            raise AssertionError("Cross-account operation succeeded")
    requests = []
    for sport in ("run", "bike"):
        w = next(w for w in plan.workouts if w.discipline.value == sport)
        alternatives = await planner.get_pending_workout_alternatives(
            str(USERS[0]), athlete, plan.id, w.id, plan.revision
        )
        assert alternatives.alternatives
        requests.append(
            (
                w.id,
                PendingWorkoutEditRequest(
                    expected_revision=plan.revision,
                    expected_proposal_id=plan.proposal.id,
                    replacement_template_id=alternatives.alternatives[0].id,
                ),
            )
        )

    async def edit(
        item: tuple[UUID, PendingWorkoutEditRequest],
        barrier: TransitionBarrier | None = None,
    ) -> Any:
        worker_repo, worker = service(db)
        worker_repo.transition_barrier = barrier
        try:
            return await worker.edit_pending_workout(
                str(USERS[0]), athlete, plan.id, item[0], item[1]
            )
        finally:
            await worker_repo._client.aclose()

    interrupted_repo, interrupted_worker = service(db)
    interrupted_repo.rollback_write = True
    try:
        await interrupted_worker.edit_pending_workout(
            str(USERS[0]), athlete, plan.id, requests[0][0], requests[0][1]
        )
    except PlanningRepositoryUnavailableError:
        pass  # No immutable receipt can exist after rollback.
    else:
        raise AssertionError("Rolled-back edit unexpectedly returned a receipt")
    assert await planner.get_plan(str(USERS[0]), plan.id, plan.revision) == plan
    await interrupted_repo._client.aclose()

    swipe_barrier = TransitionBarrier()
    outcomes = await asyncio.gather(
        *(edit(r, swipe_barrier) for r in requests), return_exceptions=True
    )
    assert swipe_barrier.arrivals == 2
    winners = [
        i for i, result in enumerate(outcomes) if not isinstance(result, BaseException)
    ]
    assert len(winners) == 1 and isinstance(
        outcomes[1 - winners[0]], PlanningRepositoryConflictError
    )
    winner = outcomes[winners[0]]
    assert not isinstance(winner, BaseException)
    retried = await edit(requests[winners[0]])
    assert retried == winner
    retained = {w.id: w for w in plan.workouts if w.id != requests[winners[0]][0]}
    assert all(w == retained[w.id] for w in winner.plan.workouts if w.id in retained)
    winning_workout_id = requests[winners[0]][0]
    original_template = next(
        w.template_id for w in plan.workouts if w.id == winning_workout_id
    )
    plan = winner.plan
    # Duplicate worker messages race on the same key and return one immutable result.
    # Reverse the actual winner: this restores the previously validated week,
    # regardless of which sport won or whether other sports are now exhausted.
    w = next(w for w in plan.workouts if w.id == winning_workout_id)
    winning_template = w.template_id
    choices = await planner.get_pending_workout_alternatives(
        str(USERS[0]), athlete, plan.id, w.id, plan.revision
    )
    assert original_template in {choice.id for choice in choices.alternatives}
    duplicate = (
        w.id,
        PendingWorkoutEditRequest(
            expected_revision=plan.revision,
            expected_proposal_id=plan.proposal.id,
            replacement_template_id=original_template,
        ),
    )
    duplicate_barrier = TransitionBarrier()
    first, second = await asyncio.gather(
        edit(duplicate, duplicate_barrier), edit(duplicate, duplicate_barrier)
    )
    assert duplicate_barrier.arrivals == 2
    assert first == second
    plan = first.plan
    # Confirmation races with an edit of the same exact pending proposal.
    # Reapply the actual winner, again restoring a validated complete week.
    w = next(w for w in plan.workouts if w.id == winning_workout_id)
    choices = await planner.get_pending_workout_alternatives(
        str(USERS[0]), athlete, plan.id, w.id, plan.revision
    )
    assert winning_template in {choice.id for choice in choices.alternatives}
    competing = (
        w.id,
        PendingWorkoutEditRequest(
            expected_revision=plan.revision,
            expected_proposal_id=plan.proposal.id,
            replacement_template_id=winning_template,
        ),
    )
    decision_barrier = TransitionBarrier()
    repo.transition_barrier = decision_barrier
    decision_outcomes = await asyncio.gather(
        edit(competing, decision_barrier),
        planner.approve_plan_proposal(str(USERS[0]), plan.proposal.id, 0),
        return_exceptions=True,
    )
    repo.transition_barrier = None
    assert decision_barrier.arrivals == 2
    assert sum(not isinstance(r, BaseException) for r in decision_outcomes) == 1
    assert any(
        isinstance(r, PlanningRepositoryConflictError) for r in decision_outcomes
    )
    if not isinstance(decision_outcomes[0], BaseException):
        plan = decision_outcomes[0].plan
        await planner.approve_plan_proposal(str(USERS[0]), plan.proposal.id, 0)
    confirmed = await planner.get_plan(str(USERS[0]), plan.id, plan.revision)
    assert confirmed.revision_state == "active"
    assert confirmed.proposal is not None
    verify_composite_ownership(db, confirmed.revision_id)
    again = await planner.approve_plan_proposal(str(USERS[0]), confirmed.proposal.id, 0)
    assert again.state == "applied"
    for mutation in (
        "update public.planned_workouts set description = 'tampered' "
        "where revision_id = " + literal(confirmed.revision_id),
        "update private.plan_revision_loads set planned_tss = 0 where revision_id = "
        + literal(confirmed.revision_id),
        "insert into public.planned_workouts select "
        "(jsonb_populate_record(null::public.planned_workouts, to_jsonb(w) || "
        "jsonb_build_object('id',gen_random_uuid()))).* "
        "from public.planned_workouts w where revision_id = "
        + literal(confirmed.revision_id)
        + " limit 1",
    ):
        try:
            db.execute("set local start23.critical_write = 'on'; " + mutation)
        except PlanningRepositoryConflictError:
            pass
        else:
            raise AssertionError("Confirmed snapshot mutation was accepted")
    assert await planner.get_plan(str(USERS[0]), plan.id, plan.revision) == confirmed
    for mutation in (
        "insert into public.planned_workouts select "
        "(jsonb_populate_record(null::public.planned_workouts, to_jsonb(w) || "
        "jsonb_build_object('id',gen_random_uuid()))).* "
        "from public.planned_workouts w where revision_id = "
        + literal(confirmed.revision_id)
        + " limit 1",
        "insert into public.plan_revisions select "
        "(jsonb_populate_record(null::public.plan_revisions, to_jsonb(r) || "
        "jsonb_build_object('id',gen_random_uuid(),'revision_number',1000))).* "
        "from public.plan_revisions r where id = " + literal(confirmed.revision_id),
    ):
        try:
            db.execute(
                "set local start23.critical_write='on'; " + mutation,
                user=USERS[0],
                rollback=True,
            )
        except PlanningRepositoryConflictError as error:
            assert error.code == "42501"
        else:
            raise AssertionError("Authenticated V6 insert custody was bypassed")
    assert (
        await edit(duplicate)
    ) == first  # immutable retry survives later confirmation
    db.execute(
        "select public.approve_plan_proposal("
        + literal(old[1]["proposal"]["id"])
        + ",0)",
        user=USERS[1],
        rollback=True,
    )
    assert (
        await planner.get_plan(str(USERS[1]), UUID(old[1]["plan"]["id"]), 1)
    ).revision_state == "pending_approval"
    rejected, retried_rejection = await asyncio.gather(
        *(
            planner.reject_plan_proposal(str(USERS[1]), UUID(old[1]["proposal"]["id"]))
            for _ in range(2)
        )
    )
    assert rejected == retried_rejection
    assert (
        await planner.get_plan(str(USERS[1]), UUID(old[1]["plan"]["id"]), 1)
    ).revision_state == "rejected"
    # A successful nested write followed by rollback leaves no proposal or plan.
    interrupted_repo, interrupted = service(db)
    interrupted_repo.rollback_write = True
    start = date(2026, 11, 9)
    try:
        await interrupted.generate_initial_proposal(
            str(USERS[0]),
            athlete,
            WeeklyPlanProposalRequest(
                week_start=start,
                available_dates=(
                    start,
                    start + timedelta(days=2),
                    start + timedelta(days=5),
                ),
            ),
        )
    except PlanningRepositoryNotFoundError:
        pass  # Write outcome is rolled back before the subsequent public read.
    assert (
        db.execute(
            "select to_jsonb(count(*)) from public.weekly_plans where athlete_id = "
            + literal(USERS[0])
            + " and week_start = '2026-11-09'"
        )
        == 0
    )
    await repo._client.aclose()
    output.write_text(json.dumps(confirmed.model_dump(mode="json")), encoding="utf-8")


async def reload_stage(db: LocalPostgres, output: Path) -> None:
    expected = json.loads(output.read_text(encoding="utf-8"))
    repo, planner = service(db)
    actual = await planner.get_plan(
        str(USERS[0]), UUID(expected["id"]), expected["revision"]
    )
    assert actual.model_dump(mode="json") == expected
    await repo._client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("all", "create", "resume", "reload"), default="all"
    )
    args = parser.parse_args()
    if not args.execute_disposable_local_only:
        raise SystemExit("NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE")
    db = LocalPostgres()
    if args.stage == "all":
        fixture = (ROOT / "supabase/tests/fixtures/v6_persistence_users.sql").read_text(
            encoding="utf-8"
        )
        # Fixture has its own transaction; execute it without the query wrapper.
        result = subprocess.run(
            ["psql", "--no-psqlrc", "--set=ON_ERROR_STOP=1", "--dbname", db.dsn],
            input=fixture,
            encoding="utf-8",
            env={**os.environ, "PGCLIENTENCODING": "UTF8"},
            capture_output=True,
            timeout=30,
        )
        if result.returncode:
            raise SystemExit(
                "Disposable onboarding fixture failed; inspect locally "
                "without publishing diagnostics."
            )
        args.private_output.mkdir(parents=True, exist_ok=False)
        output = args.private_output / "snapshot.json"
        for stage in ("create", "resume", "reload"):
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.verify_v6_postgres",
                    "--execute-disposable-local-only",
                    "--private-output",
                    str(output),
                    "--stage",
                    stage,
                ],
                check=True,
            )
        print(
            "Real PostgreSQL lifecycle, restart, concurrency, retry, "
            "cancellation and rollback checks passed."
        )
    else:
        operation = {
            "create": create_stage,
            "resume": resume_stage,
            "reload": reload_stage,
        }[args.stage]
        asyncio.run(operation(db, args.private_output))


if __name__ == "__main__":
    main()
