"""Private offline policy evidence. Real planner calls are never monkeypatched."""

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
)
from app.modules.planning.domain import PlanningConstraintError, build_weekly_plan
from app.modules.workouts.joren_draft import DraftWorkout, TimedZone, WallRest
from benchmarks.joren_c2 import START
from benchmarks.joren_v6 import BOUND_SECONDS, projection, scenario, source_records
from benchmarks.planning import canonical, digest, full_catalog
from benchmarks.prospective_planning_policy import (
    POLICY_VERSION,
    SOURCE_METHOD,
    TRIATHLON,
    Candidate,
    LegacyEvidence,
    RestrictionEvidence,
    enumerate_one_per_sport,
    evaluate,
    rank_experiment,
)
from benchmarks.v6_planner_performance import independent_checks, pairs

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/catalog/implementation"


def private_json(value: Any) -> Any:
    if isinstance(value, Fraction):
        return str(value)
    converted = canonical(value)
    if isinstance(converted, dict):
        return {k: private_json(v) for k, v in converted.items()}
    if isinstance(converted, list):
        return [private_json(v) for v in converted]
    return converted


def candidates(records: tuple[DraftWorkout, ...]) -> tuple[Candidate, ...]:
    return tuple(
        Candidate(
            r.original_workout_id,
            Discipline(r.sport),
            Decimal(r.load.original_displayed_value),
            PlannedSession(
                Discipline(r.sport),
                START,
                tuple(
                    PlannedSegment(e.seconds, stationary_rest=True)
                    if isinstance(e, WallRest)
                    else PlannedSegment(
                        e.seconds if isinstance(e, TimedZone) else None,
                        TrainingZone(e.zone),
                    )
                    for e in r.events
                ),
            ),
            not any(v > 0 for v in r.original_zone_distribution[2:]),
        )
        for r in records
    )


def independent_fits(
    records: tuple[DraftWorkout, ...], budget: Decimal, *, easy_only: bool
) -> set[tuple[str, ...]]:
    """Independent rational nested-loop oracle; no sandbox arithmetic or ranking."""
    rows = {
        sport: tuple(
            r
            for r in records
            if r.sport == sport
            and (not easy_only or all(v == 0 for v in r.original_zone_distribution[2:]))
        )
        for sport in ("bike", "run", "swim")
    }
    found = set()
    for bike in rows["bike"]:
        for run in rows["run"]:
            for swim in rows["swim"]:
                if sum(
                    (
                        Fraction(r.load.original_displayed_value)
                        for r in (bike, run, swim)
                    ),
                    Fraction(0),
                ) <= Fraction(budget):
                    found.add(tuple(r.original_workout_id for r in (bike, run, swim)))
    return found


def experiments() -> dict[str, Any]:
    records = source_records()
    deck = projection(records)
    rows = candidates(records)
    ids = tuple((t.name, str(t.id)) for t in deck)
    minimum = min(c.private_load for c in rows)
    results: dict[str, Any] = {}
    for label, subset in (
        ("all77", rows),
        ("all_easy", tuple(c for c in rows if c.all_easy)),
    ):
        result = enumerate_one_per_sport(
            subset,
            required_sports=TRIATHLON,
            budget=Decimal(45),
            legacy_minimum=minimum,
            maximum_combinations=20000,
            evidence_mode="ARITHMETIC_ONLY",
            deterministic_ids=ids,
        )
        assert result.status == "COMPLETE"
        assert {c.source_ids for c in result.within_budget} == independent_fits(
            records, Decimal(45), easy_only=label == "all_easy"
        )
        fit = tuple(c for c in result.within_budget if c.legacy_fit)
        results[label] = {
            "feasibility": private_json(result),
            "independent_set_equality": True,
            "legacy_fit_count": len(fit),
            "allocation_first": private_json(
                rank_experiment(fit, "ALLOCATION_FIRST")[:5]
            ),
            "utilization_first": private_json(
                rank_experiment(fit, "UTILIZATION_FIRST")[:5]
            ),
        }
    results["supported_suitability"] = private_json(
        enumerate_one_per_sport(
            rows,
            required_sports=TRIATHLON,
            budget=Decimal(45),
            legacy_minimum=minimum,
            maximum_combinations=20000,
            evidence_mode="SUPPORTED_SUITABILITY",
            deterministic_ids=ids,
        )
    )
    # Infeasibility is confined to exactly one occurrence per sport, not every
    # conceivable week, altered workout, repetition pattern or future catalog.
    for label, budget in (("recovery_25.86", "25.86"), ("taper_15.085", "15.085")):
        result = enumerate_one_per_sport(
            rows,
            required_sports=TRIATHLON,
            budget=Decimal(budget),
            legacy_minimum=minimum,
            maximum_combinations=20000,
            evidence_mode="ARITHMETIC_ONLY",
            deterministic_ids=ids,
        )
        assert not result.within_budget
        assert not independent_fits(records, Decimal(budget), easy_only=False)
        results[label] = private_json(result)
    # These are supplied plans, never represented as automatic selection.
    witnesses = {
        "manual_43.1": ("TR-BIKE-023", "TR-RUN-024", "TR-SWIM-021"),
        "unselected_allocation_40.2": ("TR-BIKE-023", "TR-RUN-023", "TR-SWIM-021"),
        "minimum_29.3": ("TR-BIKE-022", "TR-RUN-021", "TR-SWIM-021"),
        "mixed_bike_020": ("TR-BIKE-020",),
        "mixed_run_017": ("TR-RUN-017",),
    }
    for label, selected_ids in witnesses.items():
        selected = tuple(
            next(c for c in rows if c.source_id == k) for k in selected_ids
        )
        is_triathlon = len(selected) == 3
        results[label] = private_json(
            evaluate(
                week_start=START,
                selected=selected,
                authorized_budget=Decimal(45),
                required_sports=TRIATHLON
                if is_triathlon
                else frozenset(c.sport for c in selected),
                goal="TRIATHLON" if is_triathlon else "OTHER",
                legacy=LegacyEvidence("NOT_RUN", "OFFLINE_UNSELECTED", label),
            )
        )
    return {
        "schema": POLICY_VERSION,
        "method": SOURCE_METHOD,
        "classification": "TESTED OFFLINE BEHAVIOR; NO OPERATIONAL APPROVAL",
        "results": results,
    }


def actual_case(case: str, mode: str) -> dict[str, Any]:
    records = () if mode == "current" else source_records(mode)
    deck = (
        full_catalog()
        if mode == "current"
        else projection(records, historical=mode == "historical61")
    )
    values = scenario(case, deck)
    fingerprint = digest(values)
    print(json.dumps({"input_sha256": fingerprint}), flush=True)
    try:
        plan = build_weekly_plan(**values)
    except PlanningConstraintError as exc:
        return {
            "input_sha256": fingerprint,
            "result": {"outcome": "FAIL_CLOSED", "code": exc.code, "message": str(exc)},
        }
    outcome = {"outcome": "PENDING_HYPOTHETICAL_PLAN", "plan": canonical(plan)}
    checks = independent_checks(values, plan)
    assert checks["legacy_independent_constraints"] == "PASS"
    result = {
        "input_sha256": fingerprint,
        "result": outcome,
        "independent_checks": checks,
    }
    if mode == "v6":
        lookup = {c.source_id: c for c in candidates(records)}
        selected = tuple(
            replace(
                lookup[w.snapshot.name],
                session=replace(
                    lookup[w.snapshot.name].session, local_date=w.scheduled_date
                ),
                restrictions=RestrictionEvidence(
                    "ALLOWED",
                    ("unchanged_planner_and_independent_legacy_checks",),
                    f"40-case:{mode}:{case}",
                ),
            )
            for w in plan.workouts
        )
        result["prospective"] = private_json(
            evaluate(
                week_start=START,
                selected=selected,
                authorized_budget=plan.target.target.value,
                required_sports=values["goal_disciplines"],
                goal="TRIATHLON"
                if values["goal_disciplines"] == TRIATHLON
                else "OTHER",
                legacy=LegacyEvidence(
                    "RETURNED_PENDING",
                    "EXPLICIT_MANUAL"
                    if values.get("selected_template_ids")
                    else "AUTOMATIC_PLANNER",
                    f"40-case:{mode}:{case}",
                ),
            )
        )
    return result


def regression() -> dict[str, Any]:
    reference = json.loads((EVIDENCE / "build-search/optimized_cold.json").read_text())
    accepted = json.loads((EVIDENCE / "build-search/accepted_cold.json").read_text())
    results = {}
    reference_completions = 0
    for case, mode in pairs():
        key = f"{mode}:{case}"
        command = [
            sys.executable,
            "-B",
            "-m",
            "benchmarks.v6_policy_sandbox",
            "--case",
            case,
            "--mode",
            mode,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=BOUND_SECONDS,
                check=True,
            )
            lines = completed.stdout.splitlines()
            result = json.loads(lines[-1])
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout or b""
            line = partial.decode() if isinstance(partial, bytes) else partial
            ready = json.loads(line.splitlines()[0])
            result = {**ready, "result": {"outcome": "DIAGNOSTIC_TIMEOUT"}}
        old = reference["cases"][key]
        assert result["input_sha256"] == old["ready"]["input_sha256"], key
        assert result["result"] == old["result"], key
        prior = accepted["cases"][key]["result"]
        if prior["outcome"] != "DIAGNOSTIC_TIMEOUT":
            assert result["result"] == prior, key
            reference_completions += 1
        results[key] = result
        print(f"Verified {key}: {result['result']['outcome']}", flush=True)
    assert len(results) == 40 and reference_completions == 26
    return {
        "schema": "joren-v6-policy-unmodified-planner-regression-1",
        "bound_seconds_including_imports": BOUND_SECONDS,
        "planner_monkeypatched": False,
        "serial_workers": True,
        "host_load_controlled": False,
        "all_40_input_fingerprints_and_outcomes_equal_delivery": True,
        "accepted_complete_outcomes_preserved": reference_completions,
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--regression-output", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--mode", default="v6")
    args = parser.parse_args()
    if args.case:
        print(json.dumps(actual_case(args.case, args.mode), sort_keys=True))
        return
    if not args.private_output and not args.regression_output:
        parser.error("provide private evidence output")
    if args.private_output:
        write_immutable(
            args.private_output,
            json.dumps(experiments(), sort_keys=True, indent=2) + "\n",
        )
        print("Recorded private offline policy experiments; no activation")
    if args.regression_output:
        write_immutable(
            args.regression_output,
            json.dumps(regression(), sort_keys=True, indent=2) + "\n",
        )


if __name__ == "__main__":
    main()
