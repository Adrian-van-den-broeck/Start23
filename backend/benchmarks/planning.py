"""Reproducible A9 full-source timings and deterministic output fingerprints.

Run from backend: python -m benchmarks.planning --runs 3 --output PATH
Only aggregate timings, scenario labels and hashes leave the calculation.
"""

import argparse
import cProfile
import dataclasses
import hashlib
import json
import platform
import re
import statistics
import time
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.planning import domain
from app.modules.planning.domain import PlanLoadSample, ZoneCapability
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
    active_catalog,
)
from app.modules.workouts.repository import parse_planning_catalog

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 10, 26)
SCENARIOS = (
    "run_zero",
    "run_history",
    "swim_history",
    "duathlon",
    "tri_balanced",
    "tri_zero",
    "tri_one_sport_history",
    "run_no_days",
    "constrained",
    "repeated_occurrences",
    "build_week",
    "recovery_week",
    "taper_week",
    "restriction",
    "partial_taper",
)


def canonical(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonical(getattr(value, field.name))
            for field in dataclasses.fields(value)
            # The additive v2 field is absent in the pinned A8/A9 corpus.
            # Preserve those original input hashes; populated new evidence is
            # still serialized and compared in full.
            if not (
                field.name == "weekly_registration"
                and getattr(value, field.name) is None
            )
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(canonical(key)): canonical(item) for key, item in value.items()}
    if isinstance(value, (frozenset, set)):
        return sorted((canonical(item) for item in value), key=str)
    if isinstance(value, (tuple, list)):
        return [canonical(item) for item in value]
    return value


def digest(value: Any) -> str:
    encoded = json.dumps(canonical(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def full_catalog() -> tuple[WorkoutTemplate, ...]:
    """Same forward-migration projection as audit, with stable source UUIDs."""
    sql = (
        ROOT.parent
        / "supabase/migrations/20260903074359_add_source_catalog_training_options.sql"
    ).read_text(encoding="utf-8")
    match = re.search(r"\$catalog\$(.*?)\$catalog\$::jsonb", sql, re.DOTALL)
    assert match is not None
    source = json.loads(match.group(1))
    rows = tuple(
        {
            **row,
            "version": 2,
            "fallback_compatibility": "compatible",
            "explicit_scheduling_only": False,
            "athlete_selection_only": False,
            "source_catalog": "start23-v0.1",
            "zone_requirements": [],
            "training_phases": ["build"]
            if any(segment.get("zone_number", 0) > 2 for segment in row["segments"])
            else ["base", "build", "recovery", "taper"],
            "segments": [
                {**segment, "is_swim_technique": False} for segment in row["segments"]
            ],
        }
        for row in source
    )
    return active_catalog((*CURRENT_CATALOG, *parse_planning_catalog(rows)))


def scenario(name: str, catalog: tuple[WorkoutTemplate, ...]) -> dict[str, Any]:
    hours = ("0", "0", "3")
    sports = frozenset({Discipline.RUN})
    if name.startswith("tri"):
        sports = frozenset(Discipline)
        hours = (
            ("2", "5", "3")
            if name == "tri_balanced"
            else ("0", "0", "0")
            if name == "tri_zero"
            else hours
        )
    elif name == "duathlon":
        sports, hours = frozenset({Discipline.BIKE, Discipline.RUN}), ("0", "5", "3")
    elif name == "swim_history":
        sports, hours = frozenset({Discipline.SWIM}), ("2", "0", "0")
    elif name == "run_zero":
        hours = ("0", "0", "0")
    days = (
        ()
        if name == "run_no_days"
        else (0, 2, 5)
        if name == "constrained"
        else tuple(range(7))
    )
    race = date(2027, 3, 15)
    history: tuple[PlanLoadSample, ...] = ()
    if name in {"build_week", "recovery_week", "taper_week", "partial_taper"}:
        history = tuple(
            PlanLoadSample(
                week_start=START - timedelta(days=7 * (index + 1)),
                load=InternalLoad(Decimal("100")),
                phase=TrainingPhase.BUILD,
                realized_load=InternalLoad(Decimal("100")),
                has_prior_approved_plan=True,
                discipline_loads={Discipline.RUN: InternalLoad(Decimal("100"))},
            )
            for index in range(4)
        )
        race = START + timedelta(
            days={
                "build_week": 49,
                "recovery_week": 70,
                "taper_week": 7,
                "partial_taper": 10,
            }[name]
        )
    result: dict[str, Any] = {
        "week_start": START,
        "timezone_name": "Europe/Amsterdam",
        "race_date": race,
        "catalog": catalog,
        "prior_loads": history,
        "goal_disciplines": sports,
        "confirmed_injuries": frozenset({Discipline.RUN})
        if name == "restriction"
        else frozenset(),
        "zone_capabilities": {
            sport: ZoneCapability(frozenset(ZoneRequirement)) for sport in Discipline
        },
        "available_dates": tuple(START + timedelta(days=day) for day in days),
        "onboarding_baseline": starting_baseline(
            {
                sport: Decimal(hour) * 60
                for sport, hour in zip(Discipline, hours, strict=True)
            }
        ),
    }
    if name == "repeated_occurrences":
        item = next(
            row
            for row in catalog
            if row.discipline is Discipline.RUN
            and row.duration_minutes is not None
            and row.intensity_bucket.value == "low"
            and TrainingPhase.BASE in row.training_phases
            and not row.explicit_scheduling_only
            and not row.athlete_selection_only
        )
        result["catalog"] = (item,)
        automatic = domain.build_weekly_plan(**result)
        assert len(automatic.workouts) > 1
        result["selected_template_ids"] = tuple(
            row.snapshot.template_id for row in automatic.workouts
        )
        result["selected_occurrence_ids"] = tuple(
            UUID(int=101 + index) for index in range(len(automatic.workouts))
        )
    return result


def calculate(inputs: dict[str, Any]) -> dict[str, Any]:
    trace: dict[str, list[str]] = {}
    originals: dict[str, Any] = {}
    for name in (
        "resolve_target",
        "eligible_workouts",
        "_injury_adjusted_target",
        "_bounded_selection",
        "schedule_workouts",
    ):
        original = getattr(domain, name)
        originals[name] = original

        def traced(
            *args: Any, _function: Any = original, _name: str = name, **kwargs: Any
        ) -> Any:
            value = _function(*args, **kwargs)
            trace.setdefault(_name, []).append(digest(value))
            return value

        setattr(domain, name, traced)
    try:
        draft = domain.build_weekly_plan(**inputs)
        return {"outcome": "success", "output_sha256": digest(draft), "trace": trace}
    except domain.PlanningConstraintError as error:
        return {
            "outcome": "fail_closed",
            "code": error.code,
            "output_sha256": digest((error.code, str(error))),
            "trace": trace,
        }
    finally:
        for name, original in originals.items():
            setattr(domain, name, original)


def multiweek(builder: Any = None) -> list[dict[str, str]]:
    """Ten adjacent weeks, carrying only successfully planned historical inputs."""
    build = builder or domain.build_weekly_plan
    catalog = full_catalog()
    history: tuple[PlanLoadSample, ...] = ()
    results = []
    for index in range(10):
        inputs = scenario("run_history", catalog)
        start = START + timedelta(days=7 * index)
        inputs.update(
            week_start=start,
            race_date=START + timedelta(days=70),
            prior_loads=history,
            available_dates=tuple(start + timedelta(days=day) for day in range(7)),
        )
        entry = {"input_sha256": digest(inputs)}
        try:
            draft = build(**inputs)
        except ValueError as error:
            entry.update(
                outcome="fail_closed",
                output_sha256=digest((getattr(error, "code", None), str(error))),
            )
        else:
            entry.update(outcome="success", output_sha256=digest(draft))
            history += (
                PlanLoadSample(
                    week_start=start,
                    load=draft.planned_load,
                    realized_load=draft.planned_load,
                    phase=draft.target.phase,
                    target_basis=draft.target.basis,
                    has_prior_approved_plan=True,
                    discipline_loads={
                        sport: InternalLoad(
                            sum(
                                (
                                    row.snapshot.internal_planned_load.value
                                    for row in draft.workouts
                                    if row.discipline is sport
                                    and row.snapshot.internal_planned_load is not None
                                ),
                                Decimal(0),
                            )
                        )
                        for sport in Discipline
                    },
                ),
            )
        results.append(entry)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--cases", nargs="+", default=list(SCENARIOS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    catalog = full_catalog()
    measurements: dict[str, Any] = {}
    for name in args.cases:
        inputs = scenario(name, catalog)
        elapsed = []
        expected = calculate(inputs)
        for _ in range(args.runs):
            started = time.perf_counter()
            actual = calculate(inputs)
            elapsed.append(time.perf_counter() - started)
            assert actual == expected, "Nondeterministic synthetic result"
        measurements[name] = {
            **expected,
            "input_sha256": digest(inputs),
            "seconds": elapsed,
            "median_seconds": statistics.median(elapsed),
            "max_seconds": max(elapsed),
        }
        print(
            json.dumps(
                {
                    "case": name,
                    "outcome": expected["outcome"],
                    "median_seconds": statistics.median(elapsed),
                }
            ),
            flush=True,
        )
    if args.profile:
        profiler = cProfile.Profile()
        profiler.runcall(calculate, scenario("tri_balanced", catalog))
        profiler.dump_stats(args.profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "catalog_sha256": digest(catalog),
                "cases": measurements,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
