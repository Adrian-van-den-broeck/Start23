"""Offline synthetic policy probes using the unchanged deterministic planner.

No activation path. Only the three easiest rows and the long-bike hazard witness
are projected; revised swimming rows 015-020 never enter this synthetic deck.
Displayed source P is a declared counterfactual, not approved operational load.
Run: python -m benchmarks.joren_c2 --private-output PATH
"""

import argparse
import json
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
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
from app.modules.workouts.joren_draft import SwimDistance, TimedZone, build_manifest

START = date(2026, 10, 26)


def synthetic_deck() -> tuple[WorkoutTemplate, ...]:
    manifest = build_manifest()
    assert not manifest.errors
    swim = swim_rows(read_revision())[0]
    assert swim.structure_status == "CONSISTENT"
    templates = []
    for record in manifest.records:
        if record.original_workout_id not in (
            "TR-RUN-001",
            "TR-BIKE-001",
            "TR-SWIM-001",
            "TR-BIKE-013",
        ):
            continue
        sport = Discipline(record.sport)
        segments = tuple(
            WorkoutSegment(
                sequence=e.sequence,
                name=e.raw_token,
                instructions=e.raw_token,
                duration_minutes=e.seconds / 60 if isinstance(e, TimedZone) else None,
                distance_meters=int(e.meters) if isinstance(e, SwimDistance) else None,
                expected_rpe=e.zone * 2 - 1,
                zone_target=TrainingZone(e.zone),
            )
            for e in record.events
            if isinstance(e, (SwimDistance, TimedZone))
        )
        templates.append(
            WorkoutTemplate(
                id=record.provisional_id,
                template_key=record.provisional_key,
                version=1,
                discipline=sport,
                name=record.original_workout_id,
                description="SYNTHETIC C2 COUNTERFACTUAL ONLY",
                duration_minutes=record.original_measure
                if record.sport != "swim"
                else None,
                distance_meters=int(record.original_measure)
                if record.sport == "swim"
                else None,
                intensity_bucket=IntensityBucket.LOW,
                expected_rpe_min=min(e.expected_rpe for e in segments),
                expected_rpe_max=max(e.expected_rpe for e in segments) + 1,
                training_phases=tuple(TrainingPhase),
                zone_requirements=(
                    ZoneRequirement.PACE
                    if record.sport == "swim"
                    else ZoneRequirement.HEART_RATE,
                ),
                fallback_compatibility=FallbackCompatibility.INCOMPATIBLE
                if record.sport == "swim"
                else FallbackCompatibility.COMPATIBLE,
                segments=segments,
                internal_planned_load=InternalLoad(
                    Decimal(
                        swim.source_display_p
                        if record.sport == "swim"
                        else record.load.original_displayed_value
                    )
                ),
                source_catalog="C2-SYNTHETIC-INACTIVE",
                source_workout_id=record.original_workout_id,
            )
        )
    return tuple(templates)


def inputs(deck: tuple[WorkoutTemplate, ...]) -> dict[str, Any]:
    return dict(
        week_start=START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2027, 3, 15),
        catalog=deck,
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            s: ZoneCapability(
                frozenset(
                    {
                        ZoneRequirement.PACE
                        if s is Discipline.SWIM
                        else ZoneRequirement.HEART_RATE
                    }
                )
            )
            for s in Discipline
        },
        available_dates=tuple(START + timedelta(days=i) for i in range(7)),
        onboarding_baseline=starting_baseline({s: Decimal(0) for s in Discipline}),
    )


def probe(values: dict[str, Any]) -> dict[str, Any]:
    try:
        plan = build_weekly_plan(**values)
    except PlanningConstraintError as exc:
        return {"outcome": "REJECTED", "code": exc.code}
    loads = {
        s.value: sum(
            (
                w.snapshot.internal_planned_load.value
                for w in plan.workouts
                if w.discipline is s and w.snapshot.internal_planned_load is not None
            ),
            Decimal(0),
        )
        for s in Discipline
    }
    return {
        "outcome": "PENDING_DRAFT_ONLY",
        "target": str(plan.target.target.value),
        "basis": plan.target.basis.value,
        "phase": plan.target.phase.value,
        "planned_p": str(plan.planned_load.value),
        "count": len(plan.workouts),
        "sport_loads": {s: str(v) for s, v in loads.items()},
        "sport_percentages": {
            s: str(v / plan.planned_load.value * 100)
            if plan.planned_load.value
            else None
            for s, v in loads.items()
        },
        "known_minutes": str(plan.total_duration_minutes),
        "unknown_swim_duration": any(
            w.discipline is Discipline.SWIM and w.snapshot.duration_minutes is None
            for w in plan.workouts
        ),
        "source_ids": [w.snapshot.name for w in plan.workouts],
        "dates": [w.scheduled_date.isoformat() for w in plan.workouts],
        "warnings": [w.code for w in plan.warnings],
    }


def registration_sample(
    week: date, planned: Decimal, *, swim_status: str
) -> PlanLoadSample:
    # Independently SUPPLIED hypothetical observed loads, not derived from source P.
    registrations = [
        WorkoutRegistration(
            s,
            s,
            "measured",
            v,
            "observed_zone_minutes",
            "phase-13-joren-ruleset-1",
            True,
            f"{week}:{s}",
        )
        for s, v in (("bike", Decimal("30.2")), ("run", Decimal("17.4")))
    ]
    if swim_status == "measured":
        registrations.append(
            WorkoutRegistration(
                "swim",
                "swim",
                "measured",
                Decimal("16.9"),
                "observed_zone_minutes",
                "phase-13-joren-ruleset-1",
                True,
                f"{week}:swim",
            )
        )
    elif swim_status == "skipped":
        registrations.append(
            WorkoutRegistration(None, "swim", "skipped", calculation_id=f"{week}:skip")
        )
    quality = aggregate_week(
        expected_occurrences=("bike", "run", "swim"),
        registrations=tuple(registrations),
        expected_known=True,
    )
    return PlanLoadSample(
        week_start=week,
        load=InternalLoad(planned),
        phase=TrainingPhase.BASE,
        realized_load=InternalLoad(quality.planner_usable_load)
        if quality.planner_usable_load is not None
        else None,
        weekly_registration=quality,
        has_prior_approved_plan=True,
    )


def evidence() -> dict[str, Any]:
    deck = synthetic_deck()
    starter = tuple(t for t in deck if t.source_workout_id != "TR-BIKE-013")
    base = inputs(starter)
    starter_ids = tuple(t.id for t in starter)
    results = {
        "baseline_45_automatic": probe(base),
        "baseline_45_explicit_three": probe(
            {**base, "selected_template_ids": starter_ids}
        ),
    }
    # Counterfactual exception ONLY in local input, never the actual starting rule.
    exception = {
        **base,
        "onboarding_baseline": replace(
            base["onboarding_baseline"], total=InternalLoad(Decimal("64.5"))
        ),
        "selected_template_ids": starter_ids,
    }
    results["exception_64_5"] = probe(exception)
    results["exception_one_date"] = probe({**exception, "available_dates": (START,)})
    results["exception_no_dates"] = probe({**exception, "available_dates": ()})
    results["injured_run_zero"] = probe(
        {**base, "confirmed_injuries": frozenset({Discipline.RUN})}
    )
    results["all_injured"] = probe(
        {**base, "confirmed_injuries": frozenset(Discipline)}
    )
    results["missing_swim_capability"] = probe(
        {
            **base,
            "zone_capabilities": {
                s: c
                for s, c in base["zone_capabilities"].items()
                if s is not Discipline.SWIM
            },
        }
    )
    results["unconfirmed_swim_capability"] = probe(
        {
            **base,
            "zone_capabilities": {
                **base["zone_capabilities"],
                Discipline.SWIM: ZoneCapability(frozenset()),
            },
        }
    )
    results["long_bike_only_45"] = probe(
        {
            **base,
            "catalog": tuple(t for t in deck if t.source_workout_id == "TR-BIKE-013"),
            "goal_disciplines": frozenset({Discipline.BIKE}),
        }
    )
    for sport in Discipline:
        results[f"single_{sport.value}_45"] = probe(
            {
                **base,
                "goal_disciplines": frozenset({sport}),
                "catalog": tuple(t for t in starter if t.discipline is sport),
            }
        )
    next_weeks = {}
    for status in ("measured", "missing", "skipped"):
        sample = registration_sample(START, Decimal("64.5"), swim_status=status)
        next_input = {
            **base,
            "week_start": START + timedelta(weeks=1),
            "race_date": START + timedelta(weeks=8),
            "prior_loads": (sample,),
            "available_dates": tuple(START + timedelta(days=7 + i) for i in range(7)),
            "selected_template_ids": starter_ids,
        }
        next_weeks[status] = probe(next_input)
        target = resolve_target(
            week_start=START + timedelta(weeks=1),
            race_date=START + timedelta(weeks=8),
            prior_loads=(sample,),
            initial_catalog_load=InternalLoad(Decimal(45)),
        )
        next_weeks[status]["resolved_target"] = str(target.target.value)
        next_weeks[status]["resolved_basis"] = target.basis.value
        next_weeks[status]["registration_reason"] = (
            sample.weekly_registration.reason if sample.weekly_registration else None
        )
        if status == "measured":
            second = registration_sample(
                START + timedelta(weeks=1), Decimal("64.5"), swim_status="missing"
            )
            next_weeks["third_after_incomplete_second"] = probe(
                {
                    **next_input,
                    "week_start": START + timedelta(weeks=2),
                    "prior_loads": (sample, second),
                    "available_dates": tuple(
                        START + timedelta(days=14 + i) for i in range(7)
                    ),
                }
            )
    sample = registration_sample(
        START - timedelta(weeks=1), Decimal("64.5"), swim_status="measured"
    )
    for phase, weeks in (("build", 9), ("recovery", 10), ("taper", 1)):
        results[phase] = probe(
            {
                **base,
                "prior_loads": (sample,),
                "race_date": START + timedelta(weeks=weeks),
                "selected_template_ids": starter_ids,
            }
        )
        target = resolve_target(
            week_start=START,
            race_date=START + timedelta(weeks=weeks),
            prior_loads=(sample,),
            initial_catalog_load=InternalLoad(Decimal(45)),
        )
        results[phase]["resolved_target"] = str(target.target.value)
        results[phase]["resolved_phase"] = target.phase.value
    return {
        "schema": "joren-c2-policy-probes-1",
        "status": "SYNTHETIC ONLY; UNAPPROVED; INACTIVE",
        "scenarios": results,
        "following_weeks": next_weeks,
    }


def main() -> None:
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    write_immutable(
        args.private_output, json.dumps(evidence(), sort_keys=True, indent=2) + "\n"
    )
    print("C2 synthetic planner probes recorded; activation disabled")


if __name__ == "__main__":
    main()
