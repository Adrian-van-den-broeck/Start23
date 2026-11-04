"""Bounded, offline V6 simulations of the unchanged deterministic planner.

Source display P and selection metadata are UNAPPROVED HYPOTHETICAL inputs.
Typed source/rest events stay in the immutable sidecar. Current templates cannot
represent stationary rest: exact rest text is folded into preceding instructions
for this simulation only, never fabricated as a zone or athlete duration.
"""

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
    evaluate_training_week,
)
from app.modules.physiology.weekly_registration import (
    WorkoutRegistration,
    aggregate_week,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    PlanningConstraintError,
    ZoneCapability,
    build_weekly_plan,
    resolve_target,
)
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    TrainingPhase,
    WorkoutSegment,
    WorkoutTemplate,
    ZoneRequirement,
)
from app.modules.workouts.joren_c2_verification import read_revision, swim_rows
from app.modules.workouts.joren_draft import (
    DraftWorkout,
    SwimDistance,
    TimedZone,
    WallRest,
    build_manifest,
    parse_events,
)
from app.modules.workouts.joren_v6 import V6Workout, build_v6_manifest
from benchmarks.joren_c2 import START, inputs
from benchmarks.planning import digest, full_catalog

BOUND_SECONDS = 8  # Same historical diagnostic wall budget, including imports.
MINIMUM = ("TR-BIKE-022", "TR-RUN-021", "TR-SWIM-021")
CANDIDATE = ("TR-BIKE-023", "TR-RUN-024", "TR-SWIM-021")
CASES = (
    "tri_zero",
    "minimum",
    "candidate",
    "candidate_one_day",
    "candidate_no_dates",
    "limited_dates",
    "run_zero",
    "bike_zero",
    "swim_zero",
    "recovery",
    "taper",
    "build_1",
    "build_2",
    "build_3",
    "build_4",
    "repeat_bike",
    "long_bike_only",
    "injury_run",
    "all_injured",
    "missing_swim_capability",
    "candidate_shortage",
    "all_easy_build",
    "beginner_recovery",
    "beginner_taper",
    "repeat_explicit",
    "unconfirmed_swim_capability",
)


def source_records(mode: str = "v6") -> tuple[DraftWorkout, ...]:
    if mode == "v6":
        return build_v6_manifest().records
    baseline = build_manifest()
    assert not baseline.errors
    return baseline.records


def projection(
    records: tuple[DraftWorkout, ...], *, historical: bool = False
) -> tuple[WorkoutTemplate, ...]:
    deck = []
    previous_swims = {s.source_id: s for s in swim_rows(read_revision())}
    for r in records:
        events = r.events
        display = r.load.original_displayed_value
        if r.sport == "swim" and not isinstance(r, V6Workout) and not historical:
            prior = previous_swims[r.original_workout_id]
            prescription = prior.cells[13].value or ""
            if r.original_workout_id in {f"TR-SWIM-{i:03d}" for i in range(15, 21)}:
                prescription = prescription.replace("300m Z3", "300m Z2", 1)
            events = parse_events(prescription, "swim", f"N{r.source_row}")
            display = prior.source_display_p
        segments: list[WorkoutSegment] = []
        for e in events:
            if isinstance(e, WallRest):
                # No fake seconds/distance/RPE in the legacy typed projection.
                segments[-1] = replace(
                    segments[-1],
                    instructions=segments[-1].instructions + "|" + e.raw_token,
                )
                continue
            segments.append(
                WorkoutSegment(
                    sequence=len(segments) + 1,
                    name=e.raw_token,
                    instructions=e.raw_token,
                    duration_minutes=e.seconds / 60
                    if isinstance(e, TimedZone)
                    else None,
                    distance_meters=int(e.meters)
                    if isinstance(e, SwimDistance)
                    else None,
                    expected_rpe=e.zone * 2 - 1,
                    zone_target=TrainingZone(e.zone),
                )
            )
        high = any(e.zone > 2 for e in events if not isinstance(e, WallRest))
        deck.append(
            WorkoutTemplate(
                id=r.provisional_id,
                template_key=r.provisional_key,
                version=r.provisional_template_version,
                discipline=Discipline(r.sport),
                name=r.original_workout_id,
                description="V6 UNAPPROVED HYPOTHETICAL PROJECTION; NO ACTIVATION",
                duration_minutes=r.original_measure if r.sport != "swim" else None,
                distance_meters=int(r.original_measure) if r.sport == "swim" else None,
                intensity_bucket=IntensityBucket.HIGH if high else IntensityBucket.LOW,
                expected_rpe_min=min(s.expected_rpe for s in segments),
                expected_rpe_max=max(s.expected_rpe for s in segments) + 1,
                training_phases=(TrainingPhase.BUILD,)
                if high
                else tuple(TrainingPhase),
                zone_requirements=(
                    ZoneRequirement.PACE
                    if r.sport == "swim"
                    else ZoneRequirement.HEART_RATE,
                ),
                fallback_compatibility=FallbackCompatibility.INCOMPATIBLE
                if r.sport == "swim"
                else FallbackCompatibility.COMPATIBLE,
                segments=tuple(segments),
                internal_planned_load=InternalLoad(Decimal(display)),
                source_catalog="V6-HYPOTHETICAL-INACTIVE",
                source_workout_id=r.original_workout_id,
            )
        )
    return tuple(deck)


def history() -> tuple[PlanLoadSample, ...]:
    return tuple(
        PlanLoadSample(
            week_start=START - timedelta(weeks=i),
            load=InternalLoad(Decimal(500)),
            phase=TrainingPhase.BUILD,
            realized_load=InternalLoad(Decimal(500)),
            has_prior_approved_plan=True,
            discipline_loads={
                Discipline.BIKE: InternalLoad(Decimal(250)),
                Discipline.RUN: InternalLoad(Decimal(150)),
                Discipline.SWIM: InternalLoad(Decimal(100)),
            },
        )
        for i in range(4, 0, -1)
    )


def scenario(case: str, deck: tuple[WorkoutTemplate, ...]) -> dict[str, Any]:
    values = inputs(deck)
    if case.startswith("build_") or case in ("recovery", "taper"):
        weeks = (
            10 - int(case[-1])
            if case.startswith("build_")
            else (10 if case == "recovery" else 1)
        )
        values.update(prior_loads=history(), race_date=START + timedelta(weeks=weeks))
        values["onboarding_baseline"] = starting_baseline(
            {
                Discipline.SWIM: Decimal(60),
                Discipline.BIKE: Decimal(180),
                Discipline.RUN: Decimal(120),
            }
        )
        values["zone_capabilities"] = {
            s: ZoneCapability(frozenset(ZoneRequirement)) for s in Discipline
        }
    if case in ("run_zero", "bike_zero", "swim_zero", "repeat_bike", "long_bike_only"):
        sport = (
            Discipline(case.split("_")[0]) if case.endswith("zero") else Discipline.BIKE
        )
        values["goal_disciplines"] = frozenset({sport})
    if case in ("minimum", "candidate", "candidate_one_day", "candidate_no_dates"):
        ids = MINIMUM if case == "minimum" else CANDIDATE
        values["selected_template_ids"] = tuple(
            t.id for identifier in ids for t in deck if t.name == identifier
        )
        if len(values["selected_template_ids"]) != 3:
            raise ValueError("scenario_source_rows_unavailable")
    if case in ("limited_dates", "candidate_one_day"):
        values["available_dates"] = (
            (START,)
            if case.endswith("one_day")
            else (START, START + timedelta(days=2), START + timedelta(days=5))
        )
    if case == "candidate_no_dates":
        values["available_dates"] = ()
    if case == "missing_swim_capability":
        values["zone_capabilities"].pop(Discipline.SWIM)
    if case == "unconfirmed_swim_capability":
        values["zone_capabilities"][Discipline.SWIM] = ZoneCapability(frozenset())
    if case in ("injury_run", "all_injured"):
        values["confirmed_injuries"] = (
            frozenset(Discipline)
            if case == "all_injured"
            else frozenset({Discipline.RUN})
        )
    if case in ("long_bike_only", "repeat_bike", "candidate_shortage"):
        name = "TR-BIKE-013" if case == "long_bike_only" else "TR-BIKE-022"
        values["catalog"] = (
            tuple(t for t in deck if t.name == name)
            if case != "candidate_shortage"
            else ()
        )
    if case in ("all_easy_build", "beginner_recovery", "beginner_taper"):
        values = scenario("candidate", deck)
        weeks = {"all_easy_build": 9, "beginner_recovery": 10, "beginner_taper": 1}[
            case
        ]
        values["race_date"] = START + timedelta(weeks=weeks)
        values["prior_loads"] = tuple(
            replace(
                s,
                load=InternalLoad(Decimal("43.1")),
                realized_load=InternalLoad(Decimal("43.1")),
            )
            for s in history()
        )
        if case == "all_easy_build":
            values["catalog"] = tuple(
                t for t in deck if t.intensity_bucket == IntensityBucket.LOW
            )
    if case == "repeat_explicit":
        values["goal_disciplines"] = frozenset({Discipline.BIKE})
        template = next(t for t in deck if t.name == "TR-BIKE-023")
        values["selected_template_ids"] = (template.id, template.id)
        values["selected_occurrence_ids"] = tuple(
            uuid5(NAMESPACE_URL, f"v6-repeat:{i}") for i in range(2)
        )
    return values


def inspect_plan(
    values: dict[str, Any], records: tuple[DraftWorkout, ...]
) -> dict[str, Any]:
    try:
        plan = build_weekly_plan(**values)
    except PlanningConstraintError as exc:
        return {"outcome": "FAIL_CLOSED", "code": exc.code}
    lookup = {r.original_workout_id: r for r in records}
    sessions = []
    for w in plan.workouts:
        r = lookup.get(w.snapshot.name)
        if r:
            sessions.append(
                PlannedSession(
                    w.discipline,
                    w.scheduled_date,
                    tuple(
                        PlannedSegment(e.seconds, stationary_rest=True)
                        if isinstance(e, WallRest)
                        else PlannedSegment(
                            e.seconds if isinstance(e, TimedZone) else None,
                            TrainingZone(e.zone),
                        )
                        for e in r.events
                    ),
                )
            )
    compliance = (
        evaluate_training_week(values["week_start"], tuple(sessions)) if lookup else ()
    )
    sport_load = {
        s.value: sum(
            (
                w.snapshot.internal_planned_load.value
                for w in plan.workouts
                if w.discipline == s and w.snapshot.internal_planned_load
            ),
            Decimal(0),
        )
        for s in Discipline
    }
    counts = Counter(w.discipline.value for w in plan.workouts)
    over_budget = plan.planned_load.value > plan.target.target.value
    return {
        "outcome": "PENDING_HYPOTHETICAL_PLAN",
        "fit": "EXACT_LOAD"
        if plan.planned_load == plan.target.target
        else "TARGET_NEAREST_FIT",
        "target": str(plan.target.target.value),
        "selected_p": str(plan.planned_load.value),
        "target_basis": plan.target.basis.value,
        "phase": plan.target.phase.value,
        "count": len(plan.workouts),
        "sport_counts": dict(counts),
        "source_ids": [w.snapshot.name for w in plan.workouts],
        "dates": [w.scheduled_date.isoformat() for w in plan.workouts],
        "one_per_sport": all(
            counts.get(s.value, 0) == 1 for s in values["goal_disciplines"]
        ),
        "sport_p": {s: str(v) for s, v in sport_load.items()},
        "sport_share": {
            s: str(v / plan.planned_load.value) if plan.planned_load.value else None
            for s, v in sport_load.items()
        },
        "known_minutes": str(plan.total_duration_minutes),
        "unknown_swim_time": any(
            w.discipline == Discipline.SWIM and w.snapshot.duration_minutes is None
            for w in plan.workouts
        ),
        "active_time_compliance": {
            c.sport.value: {
                "status": c.status,
                "low_seconds": str(c.known_low_seconds),
                "high_seconds": str(c.known_high_seconds),
                "high_ratio": str(c.high_ratio) if c.high_ratio is not None else None,
            }
            for c in compliance
        },
        "warnings": [w.code for w in plan.warnings],
        "occurrence_identity_status": "UNALLOCATED_DRAFT"
        if any(w.occurrence_id is None for w in plan.workouts)
        else "UNIQUE"
        if len({w.occurrence_id for w in plan.workouts}) == len(plan.workouts)
        else "DUPLICATE",
        "budget_ceiling": "EXCEEDED; UNSUITABLE FOR APPROVED BUDGET"
        if over_budget
        else "WITHIN",
        "policy_result": "FAIL_CLOSED_FOR_V6_POLICY"
        if over_budget or any(c.status == "REJECTED" for c in compliance)
        else "UNVERIFIED_SWIM_TIME"
        if any(c.status == "UNVERIFIED" for c in compliance)
        else "DIAGNOSTIC_PASS; SUITABILITY/OPERATIONAL_P UNAPPROVED",
    }


def combinations(records: tuple[DraftWorkout, ...]) -> dict[str, Any]:
    low = {
        sport: tuple(
            r
            for r in records
            if r.sport == sport
            and not any(v > 0 for v in r.original_zone_distribution[2:])
        )
        for sport in ("bike", "run", "swim")
    }
    fits = []
    for combo in product(*low.values()):
        loads = tuple(Decimal(r.load.original_displayed_value) for r in combo)
        total = sum(loads, Decimal(0))
        if total <= 45:
            shares = tuple(Fraction(v) / Fraction(total) for v in loads)
            # Diagnostic score only; no new selection objective is approved.
            error = sum(
                abs(a - b)
                for a, b in zip(
                    shares, (Fraction(1, 2), Fraction(3, 10), Fraction(1, 5))
                )
            )
            fits.append(
                (
                    error,
                    Decimal(45) - total,
                    tuple(r.original_workout_id for r in combo),
                    total,
                    shares,
                )
            )
    best = sorted(fits)
    return {
        "one_each_all_easy_within_45_count": len(fits),
        "scoring": (
            "UNAPPROVED diagnostic absolute share-error, then budget distance, then IDs"
        ),
        "top_share_fits": [
            {"ids": row[2], "total": str(row[3]), "shares": [str(s) for s in row[4]]}
            for row in best[:10]
        ],
    }


def continuation(
    deck: tuple[WorkoutTemplate, ...], records: tuple[DraftWorkout, ...]
) -> dict[str, Any]:
    result = {}
    for status in ("measured", "skipped", "unknown", "partial_observed"):
        # Independent hypothetical observations; no source P -> actual conversion.
        regs = [
            WorkoutRegistration(
                s,
                s,
                "measured",
                Decimal(v),
                "observed_zone_minutes",
                "phase-13-joren-ruleset-1",
                True,
                f"w1:{s}",
            )
            for s, v in (("bike", "20"), ("run", "14"))
        ]
        if status == "measured":
            regs.append(
                WorkoutRegistration(
                    "swim",
                    "swim",
                    "measured",
                    Decimal(8),
                    "observed_zone_minutes",
                    "phase-13-joren-ruleset-1",
                    True,
                    "w1:swim",
                )
            )
        elif status == "skipped":
            regs.append(
                WorkoutRegistration(None, "swim", "skipped", calculation_id="w1:skip")
            )
        elif status == "partial_observed":
            regs.append(
                WorkoutRegistration(
                    "swim",
                    "swim",
                    "partial_observed",
                    Decimal(3),
                    calculation_id="w1:partial",
                )
            )
        quality = aggregate_week(
            expected_occurrences=("bike", "run", "swim"),
            registrations=tuple(regs),
            expected_known=True,
        )
        sample = PlanLoadSample(
            START,
            InternalLoad(Decimal("43.1")),
            TrainingPhase.BASE,
            realized_load=InternalLoad(quality.planner_usable_load)
            if quality.planner_usable_load is not None
            else None,
            weekly_registration=quality,
            has_prior_approved_plan=True,
        )
        values = scenario("candidate", deck)
        values.update(
            week_start=START + timedelta(weeks=1),
            prior_loads=(sample,),
            available_dates=tuple(START + timedelta(days=i + 7) for i in range(7)),
        )
        target = resolve_target(
            week_start=values["week_start"],
            race_date=values["race_date"],
            prior_loads=(sample,),
            initial_catalog_load=InternalLoad(Decimal(45)),
        )
        result[status] = {
            "registration": {
                "reason": quality.reason,
                "known_subtotal": str(quality.known_subtotal),
                "progression_eligible": quality.progression_eligible,
            },
            "target": str(target.target.value),
            "basis": target.basis.value,
            "planner": inspect_plan(values, records),
        }
        if status == "measured":
            incomplete = aggregate_week(
                expected_occurrences=("bike", "run", "swim"),
                registrations=(),
                expected_known=True,
            )
            second = PlanLoadSample(
                START + timedelta(weeks=1),
                InternalLoad(Decimal("43.1")),
                TrainingPhase.BASE,
                weekly_registration=incomplete,
                has_prior_approved_plan=True,
            )
            values.update(
                week_start=START + timedelta(weeks=2),
                prior_loads=(sample, second),
                available_dates=tuple(START + timedelta(days=i + 14) for i in range(7)),
            )
            result["third_after_incomplete_second"] = inspect_plan(values, records)
    return result


def worker(case: str, mode: str) -> dict[str, Any]:
    records = () if mode == "current" else source_records(mode)
    deck = (
        full_catalog()
        if mode == "current"
        else projection(records, historical=mode == "historical61")
    )
    values = scenario(case, deck)
    return {**inspect_plan(values, records), "input_sha256": digest(values)}


def run_all(output: Path, timings: Path) -> None:
    records = source_records()
    results: dict[str, Any] = {}
    measurements = []
    comparisons = [(case, "v6") for case in CASES]
    # Repeat the eight historical timeout slots without increasing their bound:
    # four CURRENT builds, D61 tri_zero + builds 1-3. V6 counterparts above.
    comparisons += [
        (case, "previous61")
        for case in ("tri_zero", "build_1", "build_2", "build_3", "build_4")
    ]
    comparisons += [(f"build_{i}", "current") for i in range(1, 5)]
    comparisons += [
        (case, "historical61")
        for case in ("tri_zero", "build_1", "build_2", "build_3", "build_4")
    ]
    for case, mode in comparisons:
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "benchmarks.joren_v6",
                    "--case",
                    case,
                    "--mode",
                    mode,
                ],
                capture_output=True,
                text=True,
                timeout=BOUND_SECONDS,
                check=True,
            )
            result = json.loads(completed.stdout)
        except subprocess.TimeoutExpired:
            result = {"outcome": "DIAGNOSTIC_TIMEOUT", "bound_seconds": BOUND_SECONDS}
        except subprocess.CalledProcessError:
            raise RuntimeError(f"simulation_worker_failed:{case}:{mode}") from None
        key = f"{mode}:{case}"
        results[key] = result
        measurements.append(
            {
                "case": case,
                "mode": mode,
                "wall_seconds": time.perf_counter() - started,
                "outcome": result["outcome"],
            }
        )
        print(f"Recorded {key}: {result['outcome']}", flush=True)
    payload = {
        "schema": "joren-v6-planner-probes-2",
        "status": "UNAPPROVED HYPOTHETICAL; INACTIVE",
        "bound_seconds_including_imports": BOUND_SECONDS,
        "scenarios": results,
        "one_each_combinations": combinations(records),
        "continuation": continuation(projection(records), records),
    }
    write_immutable(output, json.dumps(payload, sort_keys=True, indent=2) + "\n")
    write_immutable(
        timings,
        json.dumps(
            {
                "serial_workers": True,
                "host_load_controlled": False,
                "measurements": measurements,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument(
        "--mode", choices=("v6", "previous61", "historical61", "current"), default="v6"
    )
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--timings", type=Path)
    args = parser.parse_args()
    if args.case:
        print(json.dumps(worker(args.case, args.mode), sort_keys=True))
    elif args.private_output and args.timings:
        run_all(args.private_output, args.timings)
    else:
        parser.error("provide --case or both private output paths")


if __name__ == "__main__":
    main()
