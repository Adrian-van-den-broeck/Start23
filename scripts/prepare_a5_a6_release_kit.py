"""Prepare immutable backend/SQL review inputs; never connects to any service."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path

BACKEND_SHA = "e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6"
A5_VERSION = "20261026224844"
A5_FILE = f"supabase/migrations/{A5_VERSION}_wombo_a5_checkin_proposal_recovery.sql"
ROOT = Path(__file__).resolve().parents[1]


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def blob(path: str) -> bytes:
    return git_bytes("show", f"{BACKEND_SHA}:{path}")


def paths(prefix: str) -> list[str]:
    return (
        git_bytes("ls-tree", "-r", "--name-only", BACKEND_SHA, "--", prefix)
        .decode()
        .splitlines()
    )


def catalog_sql(migrations: list[str]) -> str:
    sql = blob(A5_FILE).decode()
    functions = [
        ("get_checkin_plan_proposal(uuid)", False, True, False),
        ("create_weekly_plan_proposal_v3(uuid,jsonb)", True, False, True),
    ]
    rows = []
    for signature, definer, authenticated, service in functions:
        name = signature.split("(", 1)[0]
        match = re.search(
            rf"create(?: or replace)? function public\.{name}\(.*?as \$\$(.*?)\$\$;",
            sql,
            re.S | re.I,
        )
        if match is None:
            raise ValueError(f"Missing pinned function {name}")
        digest = hashlib.md5(
            match[1].replace("\r\n", "\n").encode(), usedforsecurity=False
        ).hexdigest()
        rows.append(
            f"('public.{signature}', {str(definer).lower()}, "
            f"{str(authenticated).lower()}, {str(service).lower()}, '{digest}')"
        )
    versions = ",".join("'" + Path(p).name.split("_", 1)[0] + "'" for p in migrations)
    template = (ROOT / "scripts/a5-a6/a5-catalog-template.sql").read_text()
    return (
        template.replace("__FUNCTION_ROWS__", ",\n".join(rows))
        .replace("__VERSIONS__", versions)
        .replace("__A5_VERSION__", A5_VERSION)
    )


def prepare(output: Path) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise ValueError("Choose a new output directory; existing files are preserved.")
    migrations = paths("supabase/migrations")
    if not migrations or not all(Path(p).name[:14] <= A5_VERSION for p in migrations):
        raise ValueError("Pinned backend unexpectedly contains later migrations.")
    if A5_FILE not in migrations:
        raise ValueError("A5 missing from pinned source.")
    output.mkdir(parents=True)
    archive = git_bytes("archive", "--format=tar", BACKEND_SHA, "backend")
    (output / "backend-source.tar").write_bytes(archive)
    # Keep the tar untouched; do not extract executable/source paths automatically.
    with tarfile.open(output / "backend-source.tar") as tar:
        for member in tar:
            p = Path(member.name)
            if (
                member.issym()
                or member.islnk()
                or p.is_absolute()
                or ".." in p.parts
                or p.parts[0] != "backend"
            ):
                raise ValueError("Unsafe archive member.")
            if p.name == ".env" or "credentials" in p.name:
                raise ValueError("Unexpected credential file.")
    db = output / "isolated-db" / "supabase"
    (db / "migrations").mkdir(parents=True)
    (db / "tests").mkdir()
    for path in migrations:
        (db / "migrations" / Path(path).name).write_bytes(blob(path))
    config = (
        blob("supabase/config.toml")
        .decode()
        .replace('project_id = "start23"', 'project_id = "wombo-a5-a6-verify"')
    )
    for port in range(54320, 54330):
        config = config.replace(str(port), str(port + 1000))
    config = config.replace(
        "enabled = true\n# Specifies an ordered list of seed files",
        "enabled = false\n# Specifies an ordered list of seed files",
    )
    (db / "config.toml").write_text(config, encoding="utf-8", newline="\n")
    (db / "seed.sql").write_bytes(blob("supabase/seed.sql"))
    test = "supabase/tests/wombo_a5_checkin_proposal_recovery_test.sql"
    (db / "tests" / Path(test).name).write_bytes(blob(test))
    (output / "a5-catalog-readonly.sql").write_text(
        catalog_sql(migrations), encoding="utf-8", newline="\n"
    )
    local_sql = output / "local-sql"
    local_sql.mkdir()
    for sql_path in sorted((ROOT / "scripts/a5-a6").glob("isolated-*.sql")):
        (local_sql / sql_path.name).write_bytes(sql_path.read_bytes())
    source_hashes = {
        p: hashlib.sha256(blob(p)).hexdigest()
        for p in paths("backend") + migrations + [test]
    }
    manifest: dict[str, object] = {
        "review_baseline": "abcc800d594e9e46784148cc799c51834daed329",
        "backend_component_sha": BACKEND_SHA,
        "backend_tar_sha256": hashlib.sha256(archive).hexdigest(),
        "required_migrations": migrations,
        "excluded": (
            "All four November Realized TSS V2 migrations "
            "and all new catalog source code"
        ),
        "source_sha256": source_hashes,
        "production_identity_verified": False,
        "database_execution_verified": False,
        "deployment_authorized": False,
        "kit_sql_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(local_sql.glob("*.sql"))
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.output)
    print(
        json.dumps(
            {
                "backend_component_sha": BACKEND_SHA,
                "migration_count": len(paths("supabase/migrations")),
                "deployable": manifest["deployment_authorized"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
