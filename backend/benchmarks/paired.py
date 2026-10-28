"""Interleaved A8/current domain measurements; no snapshots or private values logged."""

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

from app.modules.planning.domain import build_weekly_plan

from .planning import ROOT, digest, full_catalog, scenario


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference-sha", default="d0e726dfd291ffde12a459ec430b11fdc5cddc7a"
    )
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reference_sha = subprocess.check_output(
        ["git", "rev-parse", "--verify", args.reference_sha + "^{commit}"],
        cwd=ROOT,
        text=True,
    ).strip()
    source = subprocess.check_output(
        ["git", "show", reference_sha + ":backend/app/modules/planning/domain.py"],
        cwd=ROOT,
    )
    reference = ModuleType("_a9_reference_domain")
    sys.modules[reference.__name__] = reference
    exec(compile(source, "<A8 domain>", "exec"), reference.__dict__)
    baseline = json.loads(
        (
            ROOT.parent / "docs/audits/remediation/evidence/a9/backend-baseline.json"
        ).read_text(encoding="utf-8")
    )
    catalog = full_catalog()
    result: dict[str, Any] = {}
    for name in ("run_history", "duathlon", "tri_balanced", "tri_zero"):
        inputs = scenario(name, catalog)
        assert digest(inputs) == baseline["cases"][name]["input_sha256"]
        rows: dict[str, list[dict[str, float]]] = {"a8": [], "optimized": []}
        for run in range(args.runs):
            order = ("a8", "optimized") if run % 2 == 0 else ("optimized", "a8")
            for version in order:
                function = (
                    reference.build_weekly_plan
                    if version == "a8"
                    else build_weekly_plan
                )
                start, cpu_start = time.perf_counter(), time.process_time()
                try:
                    output = function(**inputs)
                except ValueError as error:
                    elapsed, cpu = (
                        time.perf_counter() - start,
                        time.process_time() - cpu_start,
                    )
                    output_hash = digest((getattr(error, "code", None), str(error)))
                else:
                    elapsed, cpu = (
                        time.perf_counter() - start,
                        time.process_time() - cpu_start,
                    )
                    output_hash = digest(output)
                assert output_hash == baseline["cases"][name]["output_sha256"]
                rows[version].append({"seconds": elapsed, "cpu_seconds": cpu})
        result[name] = {
            version: {
                "runs": samples,
                "median_seconds": statistics.median(row["seconds"] for row in samples),
                "max_seconds": max(row["seconds"] for row in samples),
            }
            for version, samples in rows.items()
        }
        print(
            json.dumps(
                {
                    "case": name,
                    "medians": {
                        version: row["median_seconds"]
                        for version, row in result[name].items()
                    },
                }
            ),
            flush=True,
        )
    args.output.write_text(
        json.dumps(
            {
                "reference_sha": reference_sha,
                "measurement": (
                    "Interleaved raw domain wall/CPU time; canonical output "
                    "validation outside timing; every result matches A8 golden"
                ),
                "cases": result,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
