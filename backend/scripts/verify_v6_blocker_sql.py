"""Synthetic PG-only compatibility probes and exact observed-ACL reproduction."""

import ast
import hashlib
import json
import subprocess
import sys
from types import ModuleType
from typing import Any
from uuid import uuid4

from app.modules.activities.service import ActivityDomainError, ActivityService
from scripts.verify_v6_final_sql import ROOT, Replay

HISTORICAL_SHA = "5d71c688deb610bf5ec79c0f6fac77c835be6b51"


def historical_consumer() -> tuple[Any, dict[str, str]]:
    sources = {}
    for name in ("schemas", "service"):
        sources[name] = subprocess.check_output(
            [
                "git",
                "show",
                HISTORICAL_SHA + ":backend/app/modules/activities/" + name + ".py",
            ],
            cwd=ROOT,
            encoding="utf-8",
        )
    module = ModuleType("historical_activity_schemas_blocker_probe")
    sys.modules[module.__name__] = module
    exec(
        compile(sources["schemas"], "historical_activity_schemas.py", "exec"),
        module.__dict__,
    )
    tree = ast.parse(sources["service"])
    cls = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "ActivityService"
    )
    response = next(
        n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_response"
    )
    namespace = {
        **module.__dict__,
        "Mapping": dict,
        "Any": Any,
        "ActivityDomainError": ActivityDomainError,
    }
    exec(
        compile(
            ast.Module(body=[response], type_ignores=[]),
            "historical_response.py",
            "exec",
        ),
        namespace,
    )
    return namespace["_response"].__func__, {
        name: hashlib.sha256(value.encode()).hexdigest()
        for name, value in sources.items()
    }


def activity_probe(
    replay: Replay, database: str, stage: str, *, versioned: bool
) -> None:
    old_response, source_hashes = historical_consumer()
    activities = json.loads(
        replay.checked(
            "select jsonb_agg(jsonb_build_object('id',id,'owner',athlete_id) "
            "order by id) from public.activities",
            database,
            stage + "-activity-ids",
        )
    )
    outcomes = []
    for row in activities:
        owner, activity = row["owner"], row["id"]
        sql = (
            "begin;set local role authenticated;set local request.jwt.claims='"
            + json.dumps({"sub": owner, "role": "authenticated"})
            + "';select public.get_activity('"
            + activity
            + "');rollback;"
        )
        value = json.loads(replay.checked(sql, database, stage + "-get-" + activity))
        old = old_response(value)
        new = ActivityService._response(value)
        if set(value) != set(old.model_dump()) or new.session_rpe_version != "legacy":
            raise RuntimeError("Historical projection changed")
        listed = json.loads(
            replay.checked(
                sql.replace(
                    "select public.get_activity('" + activity + "')",
                    "select jsonb_agg(r) from public.list_activities(false) r",
                ),
                database,
                stage + "-list-" + activity,
            )
        )
        for item in listed:
            old_response(item)
            ActivityService._response(item)
        if versioned:
            metadata = json.loads(
                replay.checked(
                    "begin;set local role service_role;set local request.jwt.claims="
                    '\'{"role":"service_role"}\';'
                    "select public.get_activity_presentation_v2('"
                    + activity
                    + "');rollback;",
                    database,
                    stage + "-metadata-" + activity,
                )
            )
            assert metadata == {"session_rpe_version": "legacy"}
            ActivityService._response({**value, **metadata})
        outcomes.append(
            {
                "activity_id": activity,
                "historical_model": "PASS",
                "historical_response_method": "PASS",
                "current_model": "PASS",
                "owner_list": "PASS",
                "versioned_metadata": versioned,
            }
        )
    if versioned:
        configured = json.loads(
            replay.checked(
                "select jsonb_build_object('owner',athlete_id,'timezone',timezone) "
                "from public.athlete_profiles where timezone_confirmed_at is not null "
                "and heart_rate_monitor_confirmed_at is not null "
                "order by athlete_id limit 1",
                database,
                stage + "-synthetic-configured-owner",
            )
        )
        owner = configured["owner"]
        key = str(uuid4())
        claims = json.dumps({"sub": owner, "role": "authenticated"})
        payload = json.dumps(
            {
                "discipline": "run",
                "source": "manual",
                "started_at": "2026-08-03T08:00:00+02:00",
                "timezone": configured["timezone"],
                "duration_minutes": 30,
                "performed_duration_confirmed": True,
                "metrics": {"average_heart_rate_bpm": 140},
            }
        )
        v2_sql = (
            "begin;set local role authenticated;set local request.jwt.claims='"
            + claims
            + "';select public.create_activity_summary_v2('"
            + key
            + "','"
            + "e" * 64
            + "','"
            + payload
            + "');reset role;"
            + (
                "select private.activity_public_json_v2(id,athlete_id) from p"
                "ublic.activities "
            )
            + "where idempotency_key='"
            + key
            + "';rollback;"
        )
        lines = replay.checked(v2_sql, database, stage + "-explicit-v2").splitlines()
        legacy, explicit = (json.loads(line) for line in lines if line.startswith("{"))
        old_response(legacy)
        assert "session_rpe_version" not in legacy
        assert explicit["session_rpe_version"] == "2"
        presented = ActivityService._response(explicit)
        assert (
            presented.session_rpe_guidance and len(presented.session_rpe_guidance) == 10
        )
        try:
            old_response(explicit)
        except ActivityDomainError:
            pass
        else:
            raise RuntimeError("Historical model should stay strict on explicit V2")
        outcomes.append(
            {
                "case": "new_v2_activity",
                "historical_projection": "PASS",
                "explicit_v2_projection": "PASS",
                "new_guidance": 10,
                "historical_model_remains_strict": True,
                "transaction": "rolled_back",
            }
        )
    replay.save(
        stage + "-activity-compatibility.json",
        {
            "historical_source_sha": HISTORICAL_SHA,
            "historical_file_sha256": source_hashes,
            "postgres_generated": True,
            "hosted_execution": False,
            "outcomes": outcomes,
        },
    )


def reproduce_hosted_acls(
    replay: Replay, database: str, details: dict[str, Any]
) -> None:
    """Metadata-only recreation in an already verified disposable local cluster.

    Include every observed default ACL (including untouched provider schemas),
    plus the four observed historical service privileges. Never run hosted.
    """
    defaults = details["metadata"]["default_privileges"]
    identifiers = {r["rolname"] for r in defaults} | {"dashboard_user"}
    schemas = {r["nspname"] for r in defaults if r["nspname"]}
    if not all(x.replace("_", "").isalnum() for x in identifiers | schemas):
        raise ValueError("Unexpected identifier in observed metadata")
    sql = "begin;"
    for role in sorted(identifiers):
        sql += (
            "do $$begin if not exists(select 1 from pg_roles where rolname='"
            + role
            + "') then create role "
            + role
            + " nologin;end if;end;$$;"
        )
    for schema in sorted(schemas):
        sql += "create schema if not exists " + schema + ";"
    for row in defaults:
        # aclitem grants retain grant options; recreate from PostgreSQL's parser.
        acl = row["acl"].replace("'", "''")
        target = {"S": "sequences", "f": "functions", "r": "tables"}[
            row["defaclobjtype"]
        ]
        prefix = (
            "alter default privileges for role "
            + row["rolname"]
            + " in schema "
            + row["nspname"]
        )
        sql += (
            prefix
            + " revoke all on "
            + target
            + " from public,postgres,anon,authenticated,service_role,dashboard_user;"
        )
        sql += (
            "do $acl$ declare a record;begin for a in select * from aclexplode('"
            + acl
            + "'::aclitem[]) loop execute '"
            + prefix
            + " grant '||a.privilege_type||' on "
            + target
            + " to '||case when a.grantee=0 then 'public' else "
            "quote_ident(pg_get_userbyid(a.grantee)) end||case when "
            "a.is_grantable then ' with grant option' else '' end;end loop;end;$acl$;"
        )
    for table in (
        "workout_templates",
        "workout_segments",
        "workout_template_phase_tags",
        "workout_template_zone_requirements",
    ):
        sql += (
            "grant truncate,references,trigger,maintain on public."
            + table
            + " to service_role;"
        )
    replay.checked(sql + "commit;", database, "reproduced-observed-hosted-acls")
