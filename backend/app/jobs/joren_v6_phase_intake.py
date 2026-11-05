"""Private inactive catalog artifact, with no database or activation option."""

import argparse
from dataclasses import asdict
from pathlib import Path

from app.jobs.joren_catalog_dry_run import offline_reserved_ids, write_immutable
from app.modules.workouts.joren_draft import SourceError
from app.modules.workouts.joren_v6 import calculation_evidence, private_json
from app.modules.workouts.joren_v6_phase import (
    EXPORT_LEXEME_CHANGES,
    build_phase_catalog,
)


def artifact() -> str:
    catalog = build_phase_catalog(reserved=offline_reserved_ids())
    return private_json(
        {
            "catalog": asdict(catalog),
            "source_value_changes": [
                {
                    "sport": sport,
                    "coordinate": coordinate,
                    "historical_numeric_lexeme": before,
                    "phase_numeric_lexeme": after,
                }
                for (sport, coordinate), (
                    before,
                    after,
                ) in EXPORT_LEXEME_CHANGES.items()
            ],
            "calculations": {
                r.predecessor.original_workout_id: calculation_evidence(r.predecessor)
                for r in catalog.templates
            },
            "authority_decision": "joren-v6-phase-tss-owner-intake-1",
            "method_approval": (
                "OWNER_CONFIRMED_JOREN_APPROVAL; EXACT_PROPOSAL_BINDING_OPEN"
            ),
            "operational_planned_load": None,
            "internal_official_comparison_storage_precision": None,
            "candidate_precision": (
                "exact rational plus Decimal50 HALF_EVEN; no intermediate rounding"
            ),
            "candidate_display_precision": "0.1 HALF_EVEN; not an authority decision",
            "input_reference": "joren-v6-partial-approval-1",
            "active_template_rows_emitted": 0,
            "persistence_status": (
                "PREPARED_PRIVATE_ARTIFACT; NO_MIGRATION_OR_ACTIVE_READER"
            ),
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        write_immutable(args.private_output, artifact())
    except SourceError as exc:
        print("Inactive intake rejected: " + str(exc))
        return 1
    except OSError:
        print("Inactive intake rejected: local_io_error")
        return 1
    print("Validated 77 inactive phase revisions; private review artifact retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
