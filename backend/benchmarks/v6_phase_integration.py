"""Real phase revisions, source arithmetic and unchanged search diagnostics.

No winning recommendation or operational approval. Existing legacy search is
reused with the new phase projection, never relabeled as the prospective selector.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, replace
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.models import Discipline
from app.modules.planning.v6_phase_review import (
    DIMENSIONS,
    ReviewOccurrence,
    ReviewScope,
    SafeguardEvidence,
    review_week,
    scope_digest,
)
from app.modules.workouts.catalog import TrainingPhase, WorkoutTemplate
from app.modules.workouts.joren_draft import SourceError
from app.modules.workouts.joren_v6_phase import PhaseCatalog, build_phase_catalog
from benchmarks.joren_v6 import inspect_plan, projection, scenario
from benchmarks.planning import canonical, digest

START = date(2026, 10, 26)
NAMESPACE = UUID("ab5dd01f-359e-5375-bddb-0e529972f9f9")
BOUND_SECONDS = 8
WITNESSES: dict[str, tuple[str, ...]] = {
    "43.1_manual": ("TR-BIKE-023", "TR-RUN-024", "TR-SWIM-021"),
    "40.2_allocation": ("TR-BIKE-023", "TR-RUN-023", "TR-SWIM-021"),
    "44.8_utilization": ("TR-BIKE-023", "TR-RUN-026", "TR-SWIM-021"),
    "45.1_legacy_overshoot": ("TR-BIKE-022", "TR-RUN-027", "TR-SWIM-021"),
}


def phase_projection(catalog: PhaseCatalog) -> tuple[WorkoutTemplate, ...]:
    """Legacy diagnostic projection only; full typed rest remains in sidecar."""
    old = projection(tuple(r.predecessor for r in catalog.templates))
    return tuple(
        replace(
            t,
            id=r.revision_id,
            version=r.version,
            training_phases=r.phases,
            source_catalog="V6-PHASE-REVIEW-INACTIVE",
        )
        for r, t in zip(catalog.templates, old)
    )


def make_scope(
    catalog: PhaseCatalog,
    ids: tuple[str, ...],
    *,
    phase: TrainingPhase = TrainingPhase.BASE,
    budget: str = "45",
    goals: frozenset[Discipline] = frozenset(Discipline),
) -> ReviewScope:
    lookup = {t.predecessor.original_workout_id: t for t in catalog.templates}
    return ReviewScope(
        uuid5(NAMESPACE, "TEST_ONLY:athlete"),
        uuid5(NAMESPACE, "TEST_ONLY:revision"),
        START,
        phase,
        Decimal(budget),
        goals,
        frozenset(START + timedelta(days=i) for i in range(7)),
        proposed=tuple(
            ReviewOccurrence(
                uuid5(NAMESPACE, f"TEST_ONLY:occurrence:{i}:{identifier}"),
                lookup[identifier],
                START + timedelta(days=i % 7),
            )
            for i, identifier in enumerate(ids)
        ),
    )


def conditional_evidence(scope: ReviewScope) -> tuple[SafeguardEvidence, ...]:
    return tuple(
        SafeguardEvidence(
            dimension,
            scope_digest(scope),
            "SUPPORTED",
            "TEST_ONLY:assumption-1",
            "TEST_ONLY:conditional-contract-test;not-athlete-suitability-evidence",
        )
        for dimension in sorted(DIMENSIONS)
    )


def encode_private(value: Any) -> Any:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, frozenset):
        return sorted(encode_private(v) for v in value)
    if isinstance(value, dict):
        return {k: encode_private(v) for k, v in value.items()}
    if isinstance(value, tuple | list):
        return [encode_private(v) for v in value]
    return canonical(value)


def evidence() -> dict[str, Any]:
    catalog = build_phase_catalog()
    arithmetic: dict[str, Any] = {}
    for phase, budget in (
        (TrainingPhase.BASE, "45"),
        (TrainingPhase.BUILD, "45"),
        (TrainingPhase.RECOVERY, "25.86"),
        (TrainingPhase.TAPER, "15.085"),
    ):
        groups = tuple(
            tuple(
                r
                for r in catalog.templates
                if phase in r.phases and r.predecessor.sport == sport
            )
            for sport in ("bike", "run", "swim")
        )
        combos = tuple(
            {
                "ids": [r.predecessor.original_workout_id for r in combo],
                "private_total": str(total),
            }
            for combo in product(*groups)
            if (
                total := sum(
                    (
                        Fraction(r.predecessor.load.original_displayed_value)
                        for r in combo
                    ),
                    Fraction(0),
                )
            )
            <= Fraction(budget)
        )
        arithmetic[phase.value] = {
            "authorized_budget": budget,
            "groups": [len(g) for g in groups],
            "count": len(combos),
            "combinations": combos,
            "meaning": (
                "SOURCE_DISPLAY_ARITHMETIC_ONLY; suitability/scheduling unverified"
            ),
        }
    results: dict[str, Any] = {}
    for label, ids in WITNESSES.items():
        for phase in TrainingPhase:
            scope = make_scope(catalog, ids, phase=phase)
            results[label + ":" + phase.value] = encode_private(
                asdict(review_week(scope))
            )
    conditional = {
        "three_sport_build_all_easy": (
            TrainingPhase.BUILD,
            "45",
            WITNESSES["44.8_utilization"],
        ),
        "two_sport_recovery": (
            TrainingPhase.RECOVERY,
            "25.86",
            ("TR-RUN-021", "TR-BIKE-022"),
        ),
        "one_sport_taper": (TrainingPhase.TAPER, "15.085", ("TR-RUN-021",)),
        "zero_sport": (TrainingPhase.BASE, "0", ()),
        "long_duration": (TrainingPhase.TAPER, "500", ("TR-BIKE-013",)),
        "mixed_zone": (TrainingPhase.BASE, "100", ("TR-RUN-017",)),
    }
    for label, (phase, budget, ids) in conditional.items():
        scope = make_scope(catalog, ids, phase=phase, budget=budget)
        results[label] = encode_private(
            asdict(review_week(scope, conditional_evidence(scope)))
        )
    return {
        "schema": "joren-v6-phase-integration-simulation-1",
        "source_release": catalog.release,
        "rows": len(catalog.templates),
        "source_only_arithmetic": arithmetic,
        "review_cases": results,
        "authority": "INACTIVE; no official method or automatic recommendation",
    }


def search_case(case: str) -> dict[str, Any]:
    catalog = build_phase_catalog()
    deck = phase_projection(catalog)
    values = scenario(case, deck)
    print(json.dumps({"input_sha256": digest(values)}), flush=True)
    started = time.perf_counter()
    result = inspect_plan(values, tuple(t.predecessor for t in catalog.templates))
    return {
        "result": result,
        "planner_seconds": time.perf_counter() - started,
        "input_sha256": digest(values),
        "semantics": (
            "UNCHANGED_LEGACY_SEARCH_WITH_REAL_PHASE_PROJECTION;"
            "NOT_PROSPECTIVE_APPROVAL"
        ),
    }


def search_matrix() -> dict[str, Any]:
    cases = (
        "tri_zero",
        "candidate",
        "all_easy_build",
        "build_1",
        "build_2",
        "build_3",
        "build_4",
        "beginner_recovery",
        "beginner_taper",
        "run_zero",
        "bike_zero",
        "swim_zero",
        "injury_run",
        "all_injured",
        "missing_swim_capability",
        "candidate_no_dates",
        "limited_dates",
        "repeat_bike",
        "repeat_explicit",
        "long_bike_only",
    )
    results = {}
    for case in cases:
        started = time.perf_counter()
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "benchmarks.v6_phase_integration",
                    "--case",
                    case,
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=BOUND_SECONDS,
            )
            result = json.loads(process.stdout.splitlines()[-1])
        except subprocess.TimeoutExpired:
            result = {"result": {"outcome": "DIAGNOSTIC_TIMEOUT"}}
        results[case] = {**result, "wall_seconds": time.perf_counter() - started}
        print("Phase projection diagnostic: " + case, flush=True)
    return {"bound_seconds_including_imports": BOUND_SECONDS, "cases": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--search-output", type=Path)
    parser.add_argument("--case")
    args = parser.parse_args()
    if args.case:
        print(json.dumps(search_case(args.case), sort_keys=True))
        return
    if args.private_output:
        write_immutable(
            args.private_output, json.dumps(evidence(), sort_keys=True, indent=2) + "\n"
        )
    if args.search_output:
        write_immutable(
            args.search_output,
            json.dumps(search_matrix(), sort_keys=True, indent=2) + "\n",
        )
    if not args.private_output and not args.search_output:
        raise SourceError("explicit_private_output_required")


if __name__ == "__main__":
    main()
