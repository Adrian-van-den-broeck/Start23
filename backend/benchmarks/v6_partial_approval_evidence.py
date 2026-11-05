"""Write private, immutable partial-approval evidence; no operational integration."""

import argparse
import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.planned_source import SWIM_IF2, TIMED_IF2, calculate_source
from app.modules.workouts.joren_draft import SwimDistance, TimedZone
from app.modules.workouts.joren_v6 import build_v6_manifest, private_json
from benchmarks.v6_partial_approval import (
    CONFIRMED_IF,
    DECISION_VERSION,
    ESTIMATOR_VERSION,
    REFERENCE_MINUTES,
    REFERENCE_SECONDS,
    SELECTION_PRIORITIES,
    EstimatedSwimSession,
    evaluate_swim_week,
)


def evidence() -> dict[str, Any]:
    manifest = build_v6_manifest()
    start = date(2026, 11, 2)
    swims = {}
    candidates = {}
    for r in manifest.records:
        quantities = (
            r.original_zone_distribution
            if r.sport == "swim"
            else tuple(
                sum(
                    (
                        e.seconds
                        for e in r.events
                        if isinstance(e, TimedZone) and e.zone == z
                    ),
                    Decimal(0),
                )
                for z in range(1, 6)
            )
        )
        calculation = calculate_source(
            method=SWIM_IF2 if r.sport == "swim" else TIMED_IF2,
            quantities=quantities,
            if_values=CONFIRMED_IF,
            sport_factor=Decimal(r.original_cells[6].value or "NaN"),
            reference_seconds_per_100m=REFERENCE_SECONDS if r.sport == "swim" else None,
            stationary_rest_seconds=r.stationary_rest_seconds,
        )
        candidates[r.original_workout_id] = {
            **asdict(calculation),
            "parameter_version": DECISION_VERSION,
            "parameter_status": "CONFIRMED_VALUES_ONLY",
            "complete_formula_rounding_and_operational_method": "UNAPPROVED",
            "raw_source_lexeme": r.load.source_numeric_lexeme,
            "source_sha256": r.source_sha256,
        }
        if r.sport != "swim":
            continue
        week = evaluate_swim_week(
            start,
            (
                EstimatedSwimSession(
                    f"offline-single:{r.original_workout_id}", start, r
                ),
            ),
            sensitivity_half_width=Fraction(1, 200),
        )
        estimate = week.estimates[0]
        swims[r.original_workout_id] = {
            "source_sha256": r.source_sha256,
            "template_version": r.provisional_template_version,
            "source_row": r.source_row,
            "source_execution_cell": asdict(r.original_cells[13]),
            "original_distance_meters": str(r.planned_distance_meters),
            "original_prescribed_duration_seconds": r.planned_duration_seconds,
            "status": estimate.status,
            "segments": [
                {
                    "original": asdict(s.original),
                    "estimated_active_minutes": str(s.estimated_active_minutes),
                }
                for s in estimate.segments
            ],
            "estimated_low_minutes": str(week.low_minutes),
            "estimated_high_minutes": str(week.high_minutes),
            "estimated_high_ratio": str(week.high_ratio),
            "estimated_compliance": week.status,
            "authoritative_duration_compliance": week.authoritative_duration_compliance,
            "operational_safety_gate_approved": week.operational_safety_gate_approved,
            "sensitivity_scenario_half_width_min_per_100m": str(
                week.sensitivity_half_width
            ),
            "sensitivity_ratio_min": str(week.sensitivity_ratio_min),
            "sensitivity_ratio_max": str(week.sensitivity_ratio_max),
            "boundary_sensitive_in_this_scenario": week.boundary_sensitive,
            "individual_prescribed_segment_durations": [
                e.duration_seconds for e in r.events if isinstance(e, SwimDistance)
            ],
        }
    return {
        "decision_version": DECISION_VERSION,
        "estimator_version": ESTIMATOR_VERSION,
        "classification": "PRIVATE OFFLINE EVIDENCE; INACTIVE",
        "confirmed_if": [str(v) for v in CONFIRMED_IF],
        "confirmed_reference_minutes_per_100m": [str(v) for v in REFERENCE_MINUTES],
        "prospective_selection_priorities": SELECTION_PRIORITIES,
        "partial_plan_versus_no_plan": "CLARIFICATION_REQUIRED",
        "source_method_status": "UNAPPROVED",
        "realized_v2_compatibility": "UNCHANGED; NOT GRANTED",
        "sensitivity_limitation": (
            "Illustrative +/- .005 quantization-scale scenario; "
            "no empirical pace uncertainty supplied"
        ),
        "if2_candidates": candidates,
        "single_workout_swim_week_diagnostics": swims,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    write_immutable(args.private_output, private_json(evidence()))
    print(json.dumps({"status": "RECORDED_OFFLINE_PARTIAL_APPROVAL_EVIDENCE"}))


if __name__ == "__main__":
    main()
