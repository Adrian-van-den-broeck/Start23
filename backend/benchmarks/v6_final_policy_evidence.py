"""Private reproducible V6 final-policy simulations; no production planner calls."""

import argparse
import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.models import Discipline
from benchmarks.joren_c2 import START
from benchmarks.joren_v6 import source_records
from benchmarks.prospective_planning_policy import (
    RestrictionEvidence,
    SuitabilityDimension,
    SuitabilityEvidence,
)
from benchmarks.v6_final_policy import POLICY_VERSION, PolicyInput, enumerate_weeks
from benchmarks.v6_partial_approval import estimate_swim
from benchmarks.v6_policy_sandbox import candidates, private_json

ASSUMED = RestrictionEvidence(
    "ALLOWED",
    ("synthetic_fixture_only_all_existing_safeguards_assumed_satisfied",),
    "TEST_ONLY:athlete/template/week/phase/injury/recovery/taper/progression/scheduling",
)


def fixture_support(row: PolicyInput) -> PolicyInput:
    """Counterfactual fixture permissions, never real catalog approval."""
    c = row.candidate
    return replace(
        row,
        candidate=replace(
            c,
            restrictions=ASSUMED,
            suitability=tuple(
                SuitabilityEvidence(
                    dimension,
                    "SUPPORTED",
                    f"TEST_ONLY:synthetic-athlete:{c.source_id}:V6:{START}:supplied-phase",
                    "test-only-suitability-assumption-1",
                    "TEST_ONLY:no-Joren-suitability-approval",
                )
                for dimension in SuitabilityDimension
            ),
        ),
    )


def evidence() -> dict[str, Any]:
    records = source_records()
    raw = candidates(records)
    by_id = {r.original_workout_id: r for r in records}
    estimated = tuple(
        PolicyInput(c, estimate_swim(by_id[c.source_id]))
        if c.sport == Discipline.SWIM
        else PolicyInput(c)
        for c in raw
    )
    supported = tuple(fixture_support(r) for r in estimated)
    dates = frozenset(START + timedelta(days=i) for i in range(7))
    results: dict[str, Any] = {}

    def run(label: str, rows: tuple[PolicyInput, ...], budget: str) -> None:
        result = enumerate_weeks(
            rows,
            week_start=START,
            authorized_budget=Decimal(budget),
            available_dates=dates,
            safeguards=ASSUMED,
            maximum_combinations=20000,
        )
        results[label] = {
            "authorized_budget_hypothetical_P": budget,
            "availability": sorted(d.isoformat() for d in dates),
            "suitability_basis": "TEST_ONLY" if rows == supported else "see_inputs",
            "inputs": [
                {
                    "source_id": r.candidate.source_id,
                    "suitability_state": r.candidate.suitability_state,
                    "suitability_scopes": sorted(
                        {e.scope for e in r.candidate.suitability}
                    ),
                    "suitability_rule_versions": sorted(
                        {e.rule_version for e in r.candidate.suitability}
                    ),
                    "suitability_approval_references": sorted(
                        {e.approval_reference for e in r.candidate.suitability}
                    ),
                    "restrictions": private_json(r.candidate.restrictions),
                    "local_date": r.candidate.session.local_date.isoformat(),
                    "estimate_provenance": (
                        r.swim_estimate.status if r.swim_estimate else None
                    ),
                }
                for r in rows
            ],
            "result": private_json(result),
        }

    run("beginner_45_actual_suitability_unknown", estimated, "45")
    run("safe_three_sport_conditional_fixture", supported, "45")
    run("recovery_25.86_two_sport_conditional_fixture", supported, "25.86")
    run("taper_15.085_partial_conditional_fixture", supported, "15.085")
    # This is a supplied scenario restriction, never a sport omission priority.
    one_sport = tuple(
        r
        if r.candidate.sport == Discipline.RUN
        else replace(
            r,
            candidate=replace(
                r.candidate,
                restrictions=RestrictionEvidence(
                    "BLOCKED", ("fixture_individually_unsuitable",), "TEST_ONLY"
                ),
            ),
        )
        for r in supported
    )
    run("safe_one_sport_conditional_fixture", one_sport, "15.085")
    for label, sport, reason in (
        ("partial_missing_swim_capability", Discipline.SWIM, "missing_capability"),
        ("partial_run_injury", Discipline.RUN, "confirmed_injury_no_redistribution"),
    ):
        rows = tuple(
            replace(
                r,
                candidate=replace(
                    r.candidate,
                    restrictions=RestrictionEvidence("BLOCKED", (reason,), "TEST_ONLY"),
                ),
            )
            if r.candidate.sport == sport
            else r
            for r in supported
        )
        run(label, rows, "45")
    run(
        "no_suitable_workout",
        tuple(
            replace(
                r,
                candidate=replace(
                    r.candidate,
                    restrictions=RestrictionEvidence(
                        "BLOCKED", ("fixture_individually_unsuitable",), "TEST_ONLY"
                    ),
                ),
            )
            for r in supported
        ),
        "45",
    )
    easy = tuple(r for r in supported if r.candidate.all_easy)
    run("all_easy_BUILD_zero_high_conditional_fixture", easy, "45")
    for label, identifier in (
        ("compliant_mixed_BUILD", "TR-BIKE-020"),
        ("exceeded_20_percent_BUILD", "TR-RUN-017"),
        ("swim_approved_reference_estimate", "TR-SWIM-021"),
    ):
        run(
            label,
            tuple(r for r in supported if r.candidate.source_id == identifier),
            "550",
        )
    run(
        "missing_swim_time",
        tuple(PolicyInput(r.candidate) for r in supported),
        "45",
    )
    return {
        "policy_version": POLICY_VERSION,
        "base_sha": "7dc3f22595d4b9e22e1e84abaf148d9bd791fd33",
        "catalog_rows": len(records),
        "source_methods_unchanged": True,
        "no_operational_approval_or_default": True,
        "test_only_suitability_is_not_Joren_approval": True,
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", required=True, type=Path)
    args = parser.parse_args()
    write_immutable(
        args.private_output, json.dumps(evidence(), indent=2, sort_keys=True) + "\n"
    )
    print("Recorded private conditional witnesses; no selection or activation")


if __name__ == "__main__":
    main()
