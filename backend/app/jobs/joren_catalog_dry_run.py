"""Offline C1 command with load-free summary and explicit private output."""

from __future__ import annotations

import argparse
import json
import re
import time
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    ROOT,
    SourceError,
    build_manifest,
    manifest_json,
)


def offline_reserved_ids() -> frozenset[UUID]:
    """Conservative collision check against every UUID in the offline SQL history.

    No SQL execution or database client. Hosted successor uniqueness is a C8 gate.
    The exact reviewed inactive import contains these same identities and their
    predecessor references intentionally. A byte-changed import is NOT exempt.
    """
    return frozenset(
        UUID(value)
        for path in sorted((ROOT / "supabase/migrations").glob("*.sql"))
        if not (
            path.name == "20261105120100_inactive_v6_catalog.sql"
            and sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
            == "6e77d8d54650c7be554a90bb87cdf339b72a2db334be1a8dd98e82d6e22efe34"
        )
        for value in re.findall(
            r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b",
            path.read_text(encoding="utf-8"),
        )
    )


def write_immutable(path: Path, content: str) -> None:
    """Identical retries are read-only; any differing existing artifact fails closed."""
    payload = content.encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise SourceError("artifact_revision_conflict") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument(
        "--private-output",
        type=Path,
        help="Explicit private developer manifest file; never served by API",
    )
    parser.add_argument("--timings", type=Path, help="Separate local timing report")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        reserved = offline_reserved_ids()
        registry_done = time.perf_counter()
        manifest = build_manifest(args.sources, reserved=reserved)
        parsed = time.perf_counter()
        if manifest.errors:
            print(
                json.dumps(
                    {
                        "status": "INVALID",
                        "errors": [
                            {"document": e.document_id, "row": e.row, "code": e.code}
                            for e in manifest.errors
                        ],
                    },
                    sort_keys=True,
                )
            )
            return 1
        output = manifest_json(manifest)
        generated = time.perf_counter()
        if args.private_output is not None:
            write_immutable(args.private_output, output)
        if args.timings is not None:
            # Timings are explicitly excluded from the reproducible source artifact.
            write_immutable(
                args.timings,
                json.dumps(
                    {
                        "registry_seconds": registry_done - started,
                        "verify_parse_normalize_seconds": parsed - registry_done,
                        "serialize_seconds": generated - parsed,
                        "planner_executed": False,
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
            )
        print(
            json.dumps(
                {
                    "status": manifest.status,
                    "records": len(manifest.records),
                    "sport_counts": {
                        sport: sum(r.sport == sport for r in manifest.records)
                        for sport in ("run", "bike", "swim")
                    },
                    "errors": [],
                    "approval_gaps": manifest.approval_gaps,
                    "activation_status": manifest.activation_status,
                    "operational_method": "UNAVAILABLE",
                    "offline_reserved_uuids": len(reserved),
                    "manifest_sha256": sha256(output.encode("utf-8")).hexdigest(),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except SourceError as exc:
        print(json.dumps({"status": "INVALID", "error_code": str(exc)}, sort_keys=True))
        return 1
    except OSError:
        print(json.dumps({"status": "INVALID", "error_code": "local_io_error"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
