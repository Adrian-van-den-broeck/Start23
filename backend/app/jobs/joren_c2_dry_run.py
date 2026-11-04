"""Read-only C2 reconciliation. Normal output never contains private load values."""

import argparse
import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.planned_source import SourceMethodError
from app.modules.workouts.joren_c2_verification import private_evidence
from app.modules.workouts.joren_c21_corrections import correction_evidence
from app.modules.workouts.joren_draft import DEFAULT_SOURCES, SourceError


def private_json(evidence: dict[str, object]) -> str:
    def encode(value: object) -> str:
        if isinstance(value, Decimal):
            return str(value)
        raise TypeError("unsupported_evidence_value")

    return (
        json.dumps(
            evidence, default=encode, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", required=True, action="store_true")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--approved-corrections", action="store_true")
    args = parser.parse_args(argv)
    try:
        evidence = (
            correction_evidence if args.approved_corrections else private_evidence
        )
        content = private_json(evidence(args.sources))
        if args.private_output is not None:
            write_immutable(args.private_output, content)
        print(
            json.dumps(
                {
                    "status": "APPROVALS_PENDING",
                    "source_rows": 20,
                    "source_conflicted_rows": 6,
                    **(
                        {"derived_conflicted_rows": 0}
                        if args.approved_corrections
                        else {}
                    ),
                    "activation_status": "INACTIVE",
                    "artifact_sha256": sha256(content.encode()).hexdigest(),
                },
                sort_keys=True,
            )
        )
        return 0
    except (SourceError, SourceMethodError) as exc:
        print(json.dumps({"status": "INVALID", "error_code": str(exc)}))
        return 1
    except OSError:
        print(json.dumps({"status": "INVALID", "error_code": "local_io_error"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
