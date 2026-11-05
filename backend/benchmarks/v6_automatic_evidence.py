"""Reproducible private evidence from the actual official V6 selector."""

import argparse
from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.jobs.joren_catalog_dry_run import write_immutable
from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.physiology.planned_v6 import METHOD
from app.modules.planning.domain import (
    PlanningConstraintError,
    PlanningTarget,
    PlanningTargetBasis,
    ZoneCapability,
)
from app.modules.planning.v6_selection import (
    V6Controls,
    V6Plan,
    active_times,
    build_v6_plan,
    ranking,
)
from app.modules.planning.v6_service import private_json
from app.modules.workouts.catalog import TrainingPhase, ZoneRequirement
from app.modules.workouts.joren_v6_official import official_catalog

START = date(2026, 10, 26)


def summarize(plan: V6Plan) -> dict[str, object]:
    return {
        "authorized_budget": str(plan.target.target.value),
        "phase": plan.target.phase.value,
        "official_total": str(plan.planned_load.value),
        "optimality": plan.optimality,
        "examined": plan.examined,
        "scope": "at_most_one_new_per_present_goal_sport",
        "ranking": [str(v) for v in ranking(plan.templates, frozenset(Discipline))],
        "workouts": [
            {
                "source_id": t.source_workout_id,
                "template_id": str(t.id),
                "version": t.version,
                "source_sha256": t.source_revision.source_sha256,
                "official_value": str(t.official.value),
                "low_seconds": str(active_times(t, plan.controls)[0]),
                "high_seconds": str(active_times(t, plan.controls)[1]),
                "time_provenance": "ESTIMATED_FROM_APPROVED_REFERENCE_PACE"
                if active_times(t, plan.controls)[2]
                else "SOURCE_OR_AUTHORITATIVE_PRESCRIBED_TIME",
            }
            for t in plan.templates
        ],
        "placements": [
            {
                "template_id": str(w.snapshot.template_id),
                "occurrence_id": str(w.occurrence_id),
                "date": w.scheduled_date.isoformat(),
            }
            for w in plan.workouts
        ],
        "warning_codes": [w.code for w in plan.warnings],
        "individual_suitability": (
            "conditional_on_existing_authorized_context;not_physical_readiness_proof"
        ),
        "activation": "INACTIVE_PREVIEW",
    }


def evidence() -> dict[str, object]:
    catalog = official_catalog()
    common: dict[str, Any] = dict(
        week_start=START,
        timezone_name="Europe/Amsterdam",
        race_date=START + timedelta(weeks=12),
        catalog=catalog,
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            s: ZoneCapability(frozenset(ZoneRequirement)) for s in Discipline
        },
        available_dates=tuple(START + timedelta(days=i) for i in range(7)),
    )
    cases = {}
    for phase, budget in (
        (TrainingPhase.BASE, "45"),
        (TrainingPhase.BUILD, "45"),
        (TrainingPhase.RECOVERY, "25.86"),
        (TrainingPhase.TAPER, "15.085"),
        (TrainingPhase.BASE, "10"),
        (TrainingPhase.BASE, "0"),
    ):
        target = PlanningTarget(
            phase,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            InternalLoad(Decimal(budget)),
            build_week=4 if phase is TrainingPhase.BUILD else None,
        )
        controls = V6Controls(authorized_target=target)
        plan = build_v6_plan(**common, controls=controls)
        cases[phase.value + ":" + budget] = summarize(plan)
    initial = build_v6_plan(
        **common,
        controls=V6Controls(
            authorized_target=PlanningTarget(
                TrainingPhase.BASE,
                PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
                InternalLoad(Decimal(45)),
            )
        ),
    )
    alternatives = {}
    for current in initial.workouts:
        valid = []
        for candidate in catalog:
            if (
                candidate.discipline is not current.discipline
                or candidate.id == current.snapshot.template_id
            ):
                continue
            ids = tuple(
                candidate.id
                if w.occurrence_id == current.occurrence_id
                else w.snapshot.template_id
                for w in initial.workouts
            )
            try:
                changed = build_v6_plan(
                    **common,
                    controls=V6Controls(authorized_target=initial.target),
                    selected_template_ids=ids,
                    selected_occurrence_ids=tuple(
                        w.occurrence_id
                        for w in initial.workouts
                        if w.occurrence_id is not None
                    ),
                    fixed_occurrence_dates={
                        w.occurrence_id: w.scheduled_date
                        for w in initial.workouts
                        if w.occurrence_id is not None
                    },
                )
            except PlanningConstraintError:
                continue
            valid.append(summarize(changed))
        alternatives[current.discipline.value] = valid
    return {
        "schema": "joren-v6-automatic-evidence-1",
        "official_method": METHOD,
        "source_rows": len(catalog),
        "official_ledger": [
            {
                "source_id": t.source_workout_id,
                "template_id": str(t.id),
                "version": t.version,
                "source_sha256": t.source_revision.source_sha256,
                "phase_labels": [p.value for p in t.source_revision.phases],
                "phase_cell_text": t.source_revision.phase_cell.value,
                "original_source_numeric_lexeme": (
                    t.source_revision.predecessor.load.source_numeric_lexeme
                ),
                "phase_source_numeric_lexeme": t.source_revision.source_cells[
                    12
                ].numeric_lexeme,
                "source_display": (
                    t.source_revision.predecessor.load.original_displayed_value
                ),
                "official": asdict(t.official),
            }
            for t in catalog
        ],
        "actual_selected_plans": cases,
        "whole_week_validated_alternatives": alternatives,
        "estimated_time_release_approval": False,
        "production_access": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    write_immutable(args.private_output, private_json(evidence()) + "\n")
    print("Recorded official V6 selection and complete-week alternatives; inactive")


if __name__ == "__main__":
    main()
