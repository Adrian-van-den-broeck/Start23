"""Private TEST_ONLY exact reproduction of the original frequency review matrix.

Run each measurement in a fresh interpreter; no environment files or services.
Instrumentation observes calls, never changes search decisions. No latency SLA.
"""

import argparse
import builtins
import ctypes
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter, process_time
from typing import Any
from uuid import UUID

from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.planning import v6_search, v6_selection
from app.modules.planning.domain import (
    PlanningConstraintError,
    PlanningTarget,
    PlanningTargetBasis,
    ZoneCapability,
)
from app.modules.planning.v6_frequency import SessionFrequency
from app.modules.workouts.catalog import TrainingPhase, ZoneRequirement
from app.modules.workouts.joren_v6_official import official_catalog

START = date(2026, 10, 26)
SPORTS = (Discipline.RUN, Discipline.BIKE, Discipline.SWIM)
CASES = [
    ("base_221_" + b, (2, 2, 1), b, "base", None)
    for b in ("100", "150", "200", "250", "300")
] + [
    ("base_211_300", (2, 1, 1), "300", "base", None),
    ("base_321_150", (3, 2, 1), "150", "base", None),
    ("base_222_100", (2, 2, 2), "100", "base", None),
    ("base_222_200", (2, 2, 2), "200", "base", None),
    ("run_3_200", (3, 0, 0), "200", "base", None),
    ("run_4_300", (4, 0, 0), "300", "base", None),
    ("build4_221_100", (2, 2, 1), "100", "build", None),
    ("build4_221_150", (2, 2, 1), "150", "build", None),
    ("normal_baseline_35min", (2, 2, 1), None, "base", "35"),
    ("normal_baseline_105min", (2, 2, 1), None, "base", "105"),
]
EXTRA_CASES = [
    ("base_332_300", (3, 3, 2), "300", "base", None),
    ("base_444_500", (4, 4, 4), "500", "base", None),
    ("base_888_1000", (8, 8, 8), "1000", "base", None),
    *[
        ("base_221_300_" + suffix, (2, 2, 1), "300", "base", None)
        for suffix in (
            "retained",
            "two_dates",
            "same_day",
            "repeat_limits",
            "injury",
            "low_only",
            "capability",
            "sport_caps",
        )
    ],
    ("build1_221_300", (2, 2, 1), "300", "build", None),
    ("recovery_221_150", (2, 2, 1), "150", "recovery", None),
    ("taper_221_100", (2, 2, 1), "100", "taper", None),
]


def inputs(label: str) -> dict[str, Any]:
    _, counts, budget, phase_name, minutes = next(
        c for c in CASES + EXTRA_CASES if c[0] == label
    )
    phase = TrainingPhase(phase_name)
    target = (
        None
        if budget is None
        else PlanningTarget(
            phase,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            InternalLoad(Decimal(budget)),
            build_week=4 if phase is TrainingPhase.BUILD else None,
        )
    )
    values: dict[str, Any] = dict(
        week_start=START,
        timezone_name="Europe/Amsterdam",
        race_date=START + timedelta(weeks=12),
        catalog=official_catalog(),
        prior_loads=(),
        goal_disciplines=frozenset(s for s, n in zip(SPORTS, counts) if n),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            s: ZoneCapability(frozenset(ZoneRequirement)) for s in SPORTS
        },
        available_dates=tuple(START + timedelta(days=i) for i in range(7)),
        onboarding_baseline=starting_baseline({s: Decimal(minutes) for s in SPORTS})
        if minutes
        else None,
        controls=v6_selection.V6Controls(
            athlete_scope=UUID(int=1),
            week_scope=START,
            authorized_target=target,
            session_frequency=tuple(
                SessionFrequency(
                    s, n, "TEST_ONLY frequency policy review 2026-11-13", n
                )
                for s, n in zip(SPORTS, counts)
            ),
        ),
    )
    if label == "build1_221_300":
        assert target is not None
        values["controls"] = replace(
            values["controls"], authorized_target=replace(target, build_week=1)
        )
    if label.endswith("_retained"):
        row = next(t for t in values["catalog"] if t.source_workout_id == "TR-RUN-025")
        values.update(
            prefix=(row.id, row.id),
            prefix_occurrence_ids=(UUID(int=101), UUID(int=102)),
            fixed_occurrence_dates={
                UUID(int=101): START + timedelta(days=1),
                UUID(int=102): START + timedelta(days=4),
            },
        )
    if label.endswith("_two_dates"):
        values["available_dates"] = values["available_dates"][:2]
    if label.endswith("_same_day"):
        values["available_dates"] = values["available_dates"][:1]
    if label.endswith("_repeat_limits"):
        values["controls"] = replace(
            values["controls"], maximum_uses=tuple((t.id, 1) for t in values["catalog"])
        )
    if label.endswith("_injury"):
        values["confirmed_injuries"] = frozenset({Discipline.RUN})
    if label.endswith("_low_only"):
        values["low_only_disciplines"] = frozenset({Discipline.RUN, Discipline.BIKE})
    if label.endswith("_capability"):
        values["zone_capabilities"].pop(Discipline.SWIM)
    if label.endswith("_sport_caps"):
        assert target is not None
        values["controls"] = replace(
            values["controls"],
            authorized_target=replace(
                target,
                discipline_caps={
                    Discipline.RUN: InternalLoad(Decimal(20)),
                    Discipline.SWIM: InternalLoad(Decimal(15)),
                },
            ),
        )
    return values


def peak_memory() -> int:
    if sys.platform != "win32":
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            *[
                (name, ctypes.c_size_t)
                for name in (
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ],
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = ctypes.c_void_p
    memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not memory_info(
        get_process(),
        ctypes.byref(counters),
        counters.cb,
    ):
        raise ctypes.WinError()
    return int(counters.PeakWorkingSetSize)


def measure(label: str, instrument: bool, warm: bool) -> dict[str, Any]:
    values = inputs(label)
    if warm:
        try:
            v6_selection.build_v6_plan(**values)
        except PlanningConstraintError:
            pass
    metrics: dict[str, Any] = {
        "steps": Counter(),
        "scheduling_attempts": 0,
        "materialized_combinations": 0,
        "ranking_sort_seconds": 0.0,
        "sport_sort_seconds": 0.0,
        "bound_seconds": 0.0,
        "scheduler_seconds": 0.0,
    }
    original_step = v6_search.SearchWork.step
    original_options = v6_search.multi_options
    original_schedule = getattr(v6_selection, "schedule_workouts")
    original_eligible = v6_selection.eligible_v6
    original_bound = getattr(v6_search, "_bound", None)
    seen_groups: dict[tuple[int, int], int] = {}

    def step(self: v6_search.SearchWork) -> None:
        work = self
        frame = sys._getframe(1)
        stage = frame.f_code.co_name
        metrics["steps"][stage] += 1
        metrics["last_stage"] = stage
        metrics["worknodes"] = work.nodes + 1
        if stage == "join" and "sport_options" not in metrics:
            metrics["sport_options"] = [len(g) for g in frame.f_locals["groups"]]
        if stage == "enqueue":
            metrics["heap_peak"] = max(
                metrics.get("heap_peak", 0), len(frame.f_locals["heap"]) + 1
            )
            for axis, span in enumerate(frame.f_locals["box"]):
                seen_groups[axis, id(span.options)] = len(span.options)
            metrics["sport_options"] = [
                sum(n for (i, _), n in seen_groups.items() if i == axis)
                for axis in range(len(frame.f_locals["box"]))
            ]
        try:
            original_step(work)
        except PlanningConstraintError:
            if stage == "join":
                metrics["materialized_combinations"] = len(frame.f_locals["result"])
            raise

    def options(**kwargs: Any) -> Any:
        result = original_options(**kwargs)
        if isinstance(result, tuple):
            metrics["materialized_combinations"] = len(result)
            return result

        def observed() -> Any:
            for row in result:
                metrics["materialized_combinations"] += 1
                yield row

        return observed()

    def schedule(**kwargs: Any) -> Any:
        metrics["scheduling_attempts"] += 1
        began = perf_counter()
        try:
            return original_schedule(**kwargs)
        finally:
            metrics["scheduler_seconds"] += perf_counter() - began

    def eligible(**kwargs: Any) -> Any:
        deck = original_eligible(**kwargs)
        metrics["eligible_by_sport"] = Counter(t.discipline.value for t in deck)
        return deck

    def bound(*args: Any) -> Any:
        assert original_bound is not None
        began = perf_counter()
        try:
            return original_bound(*args)
        finally:
            metrics["bound_seconds"] += perf_counter() - began

    def sport_sorted(values: Any, **kwargs: Any) -> Any:
        began = perf_counter()
        result = builtins.sorted(values, **kwargs)
        metrics["sport_sort_seconds"] += perf_counter() - began
        return result

    def observed_sorted(values: Any, **kwargs: Any) -> Any:
        began = perf_counter()
        result = builtins.sorted(values, **kwargs)
        if result and isinstance(result[0], tuple):
            metrics["ranking_sort_seconds"] += perf_counter() - began
        return result

    if instrument:
        v6_search.SearchWork.step = step  # type: ignore[method-assign]
        v6_search.multi_options = options
        setattr(v6_selection, "schedule_workouts", schedule)
        v6_selection.eligible_v6 = eligible
        v6_selection.sorted = observed_sorted  # type: ignore[attr-defined]
        setattr(v6_search, "sorted", sport_sorted)
        if original_bound is not None:
            setattr(v6_search, "_bound", bound)
    entry: dict[str, Any] = {
        "case": label,
        "test_only": True,
        "instrumented": instrument,
        "warm": warm,
    }
    began, cpu = perf_counter(), process_time()
    try:
        plan = v6_selection.build_v6_plan(**values)
    except PlanningConstraintError as error:
        entry["outcome"] = error.code
        entry["failure_stage"] = metrics.get("last_stage")
        entry["worknodes"] = metrics.get("worknodes")
    else:
        by_id = {t.id: t for t in plan.templates}
        score = v6_selection.ranking(
            plan.templates, values["goal_disciplines"], plan.controls.session_frequency
        )
        entry.update(
            outcome=plan.optimality,
            worknodes=plan.examined,
            official_total=str(plan.planned_load.value),
            resolved_budget=str(plan.target.target.value),
            ranking=[score[0], score[1], str(score[2]), str(score[3]), list(score[4])],
            workouts=[
                dict(
                    source=by_id[w.snapshot.template_id].source_workout_id,
                    template=str(w.snapshot.template_id),
                    occurrence=str(w.occurrence_id),
                    date=str(w.scheduled_date),
                )
                for w in plan.workouts
            ],
        )
    entry.update(
        wall_seconds=perf_counter() - began,
        cpu_seconds=process_time() - cpu,
        peak_working_set_bytes=peak_memory(),
    )
    if instrument:
        entry["metrics"] = metrics
        v6_search.SearchWork.step = original_step  # type: ignore[method-assign]
        v6_search.multi_options = original_options
        setattr(v6_selection, "schedule_workouts", original_schedule)
        v6_selection.eligible_v6 = original_eligible
        del v6_selection.sorted  # type: ignore[attr-defined]
        delattr(v6_search, "sorted")
        if original_bound is not None:
            setattr(v6_search, "_bound", original_bound)
    return entry


def install_reference() -> None:
    """Fresh-child-only baseline: exact accepted Git blobs, no source mutation."""
    commit = "e85cbaa8b5e702c283186fc61fcadda74ad36faf"
    for module, filename in (
        (v6_search, "v6_search.py"),
        (v6_selection, "v6_selection.py"),
    ):
        source = subprocess.check_output(
            ["git", "show", f"{commit}:backend/app/modules/planning/{filename}"]
        )
        exec(compile(source, str(module.__file__), "exec"), module.__dict__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=[c[0] for c in CASES + EXTRA_CASES])
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--instrument", action="store_true")
    parser.add_argument("--warm", action="store_true")
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args()
    if args.case:
        if args.reference:
            install_reference()
        result: Any = measure(args.case, args.instrument, args.warm)
    else:
        records = []
        cases = EXTRA_CASES if args.extended else CASES
        for label, *_ in cases:
            child = args.output.with_suffix(".child.json")
            command = [
                sys.executable,
                "-m",
                "benchmarks.v6_exact_search",
                "--case",
                label,
                "--output",
                str(child),
            ]
            if args.instrument:
                command.append("--instrument")
            if args.warm:
                command.append("--warm")
            if args.reference:
                command.append("--reference")
            began = perf_counter()
            subprocess.run(command, check=True)
            record = json.loads(child.read_text(encoding="utf-8"))
            record["cold_process_seconds"] = perf_counter() - began
            records.append(record)
            print(label, record["outcome"], flush=True)
            args.output.write_text(
                json.dumps(records, indent=2) + "\n", encoding="utf-8"
            )
        child.unlink()
        result = {
            "machine": platform.platform(),
            "python": sys.version,
            "processor": platform.processor(),
            "cases": records,
            "fixture_sha256": hashlib.sha256(repr(cases).encode()).hexdigest(),
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
