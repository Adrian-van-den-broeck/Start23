"""Synthetic constant-work timings and actual A9 catalog eligibility inventory.

No hosted I/O. Output contains counts, source IDs and timings, never load values.
Run from backend: python -m benchmarks.realized_v2 --output ../.runtime/v2.json
"""

import argparse
import json
import platform
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.modules.activities.realized_context import single_planned_zone
from app.modules.physiology.models import Discipline
from app.modules.physiology.realized_v2 import estimate_realized
from benchmarks.planning import full_catalog


def catalog_coverage() -> dict[str, Any]:
    catalog = full_catalog()
    result = {}
    for sport in Discipline:
        templates = [row for row in catalog if row.discipline is sport]
        reasons: Counter[str] = Counter()
        eligible_ids = []
        source_total = source_eligible = 0
        for template in templates:
            source_total += template.source_catalog is not None
            segments = [
                {"zone_target": row.zone_target.value if row.zone_target else None}
                for row in template.segments
            ]
            if single_planned_zone(segments) is None:
                reasons["mixed_or_non_zone_prescription"] += 1
            elif (
                template.duration_minutes is None
                or template.internal_planned_load is None
            ):
                reasons["missing_duration_or_load"] += 1
            else:
                eligible_ids.append(template.source_workout_id or str(template.id))
                source_eligible += template.source_catalog is not None
        result[sport.value] = {
            "total": len(templates),
            "structurally_eligible": len(eligible_ids),
            "source_total": source_total,
            "source_eligible": source_eligible,
            "eligible_source_or_template_ids": sorted(eligible_ids),
            "excluded": dict(reasons),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10000)
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("iterations must be positive")
    samples = []
    for _ in range(3):
        started = time.perf_counter()
        for index in range(args.iterations):
            estimate_realized(
                planned_load=Decimal(120),
                planned_minutes=Decimal(120),
                actual_minutes=Decimal(60 if index % 2 else 180),
                planned_zone=2,
                rpe=index % 10 + 1,
            )
        samples.append((time.perf_counter() - started) / args.iterations)
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "iterations_per_sample": args.iterations,
        "seconds_per_calculation": samples,
        "catalog": catalog_coverage(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
