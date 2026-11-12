"""Offline reproducible examples. Every frequency record is explicitly TEST_ONLY."""

import argparse
import json
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import UUID

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.planning.domain import (
    PlanningConstraintError,
    PlanningTarget,
    PlanningTargetBasis,
    ZoneCapability,
)
from app.modules.planning.v6_frequency import SessionFrequency
from app.modules.planning.v6_selection import V6Controls, active_times, build_v6_plan
from app.modules.workouts.catalog import TrainingPhase, ZoneRequirement
from app.modules.workouts.joren_v6_official import official_catalog


def evidence() -> list[dict[str, Any]]:
    start = date(2026, 10, 26)
    catalog = official_catalog()
    results: list[dict[str, Any]] = []
    for label, counts, budget in (
        ("two_run_two_bike_one_swim", (2, 2, 1), "100"),
        ("two_run_one_bike_one_swim", (2, 1, 1), "100"),
        ("single_sport_two_run", (2, 0, 0), "100"),
        ("partial_budget", (2, 2, 1), "45"),
        ("rest", (2, 2, 1), "0"),
        ("bounded_exhaustion", (2, 2, 1), "300"),
    ):
        controls = V6Controls(
            athlete_scope=UUID(int=1),
            week_scope=start,
            authorized_target=PlanningTarget(
                TrainingPhase.BASE,
                PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
                InternalLoad(Decimal(budget)),
            ),
            session_frequency=tuple(
                SessionFrequency(s, n, "TEST_ONLY example frequency v1", n)
                for s, n in zip(
                    (Discipline.RUN, Discipline.BIKE, Discipline.SWIM), counts
                )
            ),
        )
        entry: dict[str, Any] = {
            "case": label,
            "test_only": True,
            "budget": budget,
            "requested_run_bike_swim": counts,
        }
        began = perf_counter()
        try:
            plan = build_v6_plan(
                week_start=start,
                timezone_name="Europe/Amsterdam",
                race_date=start + timedelta(weeks=12),
                catalog=catalog,
                prior_loads=(),
                goal_disciplines=frozenset(
                    r.sport for r in controls.session_frequency if r.requested
                ),
                confirmed_injuries=frozenset(),
                zone_capabilities={
                    s: ZoneCapability(frozenset(ZoneRequirement)) for s in Discipline
                },
                available_dates=tuple(start + timedelta(days=i) for i in range(7)),
                controls=controls,
            )
        except PlanningConstraintError as error:
            entry["outcome"] = error.code
        else:
            by_id = {t.id: t for t in plan.templates}
            entry.update(
                {
                    "outcome": plan.optimality,
                    "selection_version": plan.selection_version,
                    "nodes_including_schedule": plan.examined,
                    "official_total": str(plan.planned_load.value),
                    "workouts": [
                        {
                            "source": by_id[w.snapshot.template_id].source_workout_id,
                            "occurrence": str(w.occurrence_id),
                            "date": w.scheduled_date.isoformat(),
                            "method": by_id[w.snapshot.template_id].official.method,
                        }
                        for w in plan.workouts
                    ],
                    "high_share_by_sport": {
                        s.value: str(
                            sum(
                                (
                                    active_times(t, controls)[1]
                                    for t in plan.templates
                                    if t.discipline is s
                                ),
                                Fraction(0),
                            )
                            / sum(
                                (
                                    sum(active_times(t, controls)[:2])
                                    for t in plan.templates
                                    if t.discipline is s
                                ),
                                Fraction(0),
                            )
                        )
                        for s in Discipline
                        if any(t.discipline is s for t in plan.templates)
                    },
                    "estimated_sports": sorted(s.value for s in plan.estimated_sports),
                    "warnings": [w.code for w in plan.warnings],
                }
            )
        entry["seconds"] = perf_counter() - began
        results.append(entry)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    args.private_output.write_text(
        json.dumps(evidence(), indent=2) + "\n", encoding="utf-8"
    )
    print("Recorded TEST_ONLY multi-session examples; no activation")


if __name__ == "__main__":
    main()
