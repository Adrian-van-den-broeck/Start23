"""Replay migrations and every TAP assertion in a NEW loopback PG17 database.

Never reads .env. Requires an explicitly supplied psql binary, cluster directory,
and port. Only CREATE DATABASE is used; existing databases are never reset.
The historical A5 file stays untouched: its optional overlay is explicit evidence.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
A5 = "wombo_a5_checkin_proposal_recovery_test.sql"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def a5_overlay(source: str) -> str:
    marker = "select set_config('start23.checkin_write', 'on', true);"
    if source.count(marker) != 1:
        raise RuntimeError("A5 insertion point differs from reviewed fixture")
    fixture = ROOT / "supabase/tests/fixtures/a5_current_onboarding.sql"
    fingerprint = "'input_fingerprint', repeat('a', 64)"
    if source.count(fingerprint) != 1:
        raise RuntimeError("A5 fingerprint differs from reviewed fixture")
    return source.replace(fingerprint, "'input_fingerprint', repeat('a', 32)").replace(
        marker, fixture.read_text(encoding="utf-8") + "\n" + marker
    )


class Replay:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.out: Path = args.private_output
        self.out.mkdir(parents=True, exist_ok=False)

    def sql(self, sql: str, database: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(self.args.psql),
                "-X",
                "-qAt",
                "-h",
                "127.0.0.1",
                "-p",
                str(self.args.port),
                "-U",
                "postgres",
                "-d",
                database,
                "-v",
                "ON_ERROR_STOP=1",
                "-v",
                "VERBOSITY=verbose",
            ],
            input=sql,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
            env={**os.environ, "PGCLIENTENCODING": "UTF8"},
        )

    def save(self, name: str, value: Any) -> None:
        (self.out / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def checked(self, sql: str, database: str, name: str) -> str:
        result = self.sql(sql, database)
        (self.out / (name + ".log")).write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        if result.returncode:
            raise RuntimeError("Failed: " + name + "; inspect private log")
        return result.stdout

    def tap(self, path: Path, database: str, overlay: bool = False) -> dict[str, Any]:
        source = path.read_text(encoding="utf-8")
        if overlay:
            source = a5_overlay(source)
        result = self.sql(source, database)
        name = path.stem + ("-overlay" if overlay else "-original")
        transcript = result.stdout + result.stderr
        (self.out / (name + ".log")).write_text(transcript, encoding="utf-8")
        assertions = re.findall(r"^(not ok|ok) (\d+)([^\r\n]*)$", result.stdout, re.M)
        plans = re.findall(r"^1\.\.(\d+)\s*$", result.stdout, re.M)
        failed = [
            line for line in result.stdout.splitlines() if line.startswith("not ok ")
        ]
        executed = len(assertions)
        classified = [
            {
                "number": int(number),
                "description": description.strip().removeprefix("- "),
                "status": "NOT EXECUTED"
                if re.search(r"#\s*(SKIP|TODO)\b", description, re.I)
                else "EXECUTED / PASS"
                if outcome == "ok"
                else "EXECUTED / FAIL",
            }
            for outcome, number, description in assertions
        ]
        skipped = sum(row["status"] == "NOT EXECUTED" for row in classified)
        complete = (
            result.returncode == 0
            and len(plans) == 1
            and int(plans[0]) == executed
            and [int(n) for _, n, _ in assertions] == list(range(1, executed + 1))
            and skipped == 0
        )
        return {
            "file": path.name,
            "source_sha256": digest(path.read_bytes()),
            "executed_sql_sha256": digest(source.encode()),
            "overlay": overlay,
            "exit_code": result.returncode,
            "assertions_executed": executed,
            "assertions": classified,
            "passed": executed - len(failed),
            "failures": failed,
            "plan": plans,
            "complete": complete,
            "status": "EXECUTED / PASS"
            if complete and not failed
            else "EXECUTED / FAIL",
            "transcript_sha256": digest(transcript.encode()),
        }

    def run(self) -> None:
        args = self.args
        server = json.loads(
            self.checked(
                "select json_build_object('data_directory',"
                "current_setting('data_directory'),"
                "'version',version(),'address',inet_server_addr(),'port',inet_server_port(),"
                "'major',current_setting('server_version_num')::integer / 10000)",
                "postgres",
                "server-identity",
            )
        )
        if (
            Path(server["data_directory"]).resolve() != args.cluster_directory.resolve()
            or server["address"] != "127.0.0.1"
            or server["port"] != args.port
            or server["major"] != 17
        ):
            raise RuntimeError("Wrong disposable server identity")
        self.save("server.json", server)
        db: str = args.database
        self.checked("create database " + db, "postgres", "create-database")
        self.checked(
            (
                ROOT / "supabase/tests/fixtures/v6_disposable_supabase_bootstrap.sql"
            ).read_text(encoding="utf-8"),
            db,
            "bootstrap",
        )
        ledger = []
        historical = ""
        for file in sorted((ROOT / "supabase/migrations").glob("*.sql")):
            if file.name.startswith("20261105120000"):
                historical = self.checked(
                    "select jsonb_build_object('templates',"
                    "(select jsonb_agg(to_jsonb(t) order by id) "
                    "from public.workout_templates t),"
                    "'loads',(select jsonb_agg(to_jsonb(t) order by template_id) "
                    "from private.workout_template_loads t))",
                    db,
                    "historical-before-v6",
                )
                self.save(
                    "a5-historical-original.json",
                    self.tap(ROOT / "supabase/tests" / A5, db),
                )
                if args.historical_only:
                    break
            self.checked(
                "begin;\n" + file.read_text(encoding="utf-8") + "\ncommit;",
                db,
                file.stem,
            )
            ledger.append(
                {
                    "file": file.name,
                    "sha256": digest(file.read_bytes()),
                    "status": "EXECUTED / PASS",
                }
            )
            self.save("migration-ledger.json", ledger)
        if args.historical_only:
            return
        self.save("a5-final-original.json", self.tap(ROOT / "supabase/tests" / A5, db))
        results = []
        for file in sorted((ROOT / "supabase/tests").glob("*.sql")):
            result = self.tap(file, db, overlay=file.name == A5)
            results.append(result)
            self.save("pgtap-results.json", results)
            print(
                file.name, result["status"], result["assertions_executed"], flush=True
            )
        current = self.checked(
            "select jsonb_build_object('templates',"
            "(select jsonb_agg(to_jsonb(t) - 'inactive_v6' order by id) "
            "from public.workout_templates t where id not in "
            "(select template_id from private.v6_source_revisions)),"
            "'loads',(select jsonb_agg(to_jsonb(t) order by template_id) "
            "from private.workout_template_loads t where template_id not in "
            "(select template_id from private.v6_source_revisions)))",
            db,
            "historical-after-v6",
        )
        active = self.checked(
            "select jsonb_build_object('source_revisions',count(*),'active',"
            "count(*) filter(where not t.inactive_v6)) "
            "from private.v6_source_revisions s "
            "join public.workout_templates t on t.id = s.template_id",
            db,
            "inactive-inventory",
        )
        self.save(
            "catalog-preservation.json",
            {
                "historical_equal": json.loads(historical) == json.loads(current),
                "historical_templates": len(json.loads(historical)["templates"]),
                "historical_loads": len(json.loads(historical)["loads"]),
                "historical_sha256": digest(historical.encode()),
                "v6": json.loads(active),
            },
        )
        if json.loads(historical) != json.loads(current) or json.loads(active) != {
            "source_revisions": 77,
            "active": 0,
        }:
            raise SystemExit("Catalog preservation failed; inspect evidence")
        if not all(result["status"] == "EXECUTED / PASS" for result in results):
            raise SystemExit("SQL suite incomplete or failed; inspect result ledger")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-disposable-local-only", action="store_true")
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--cluster-directory", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--historical-only", action="store_true")
    args = parser.parse_args()
    if not args.execute_disposable_local_only or not re.fullmatch(
        r"wombo_v6_final_[a-z0-9_]+", args.database
    ):
        raise SystemExit("Explicit disposable database authorization is required")
    Replay(args).run()


if __name__ == "__main__":
    main()
