"""Private immutable V6 evidence writer; default stdout contains no load values."""

import argparse
from hashlib import sha256
from pathlib import Path

from app.jobs.joren_catalog_dry_run import offline_reserved_ids, write_immutable
from app.modules.workouts.joren_draft import DEFAULT_SOURCES, SourceError
from app.modules.workouts.joren_v6 import (
    build_v6_manifest,
    private_evidence,
    private_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = build_v6_manifest(args.sources, reserved=offline_reserved_ids())
        payload = private_json(private_evidence(manifest))
        if args.private_output:
            write_immutable(args.private_output, payload)
        print(
            f"INACTIVE; structures validated: {len(manifest.records)}; "
            f"evidence sha256: {sha256(payload.encode()).hexdigest()}; "
            "operational method unavailable"
        )
        return 0
    except (SourceError, OSError):
        print("INVALID; V6 intake rejected; inspect private source evidence")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
