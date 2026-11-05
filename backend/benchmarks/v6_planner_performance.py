"""Offline paired V6 profiling. No catalog/method activation or persistent state.

The frozen accepted search is an oracle, not an alternative runtime planner.
AST counters and stage wrappers are optional and installed only in child workers.
Uninstrumented cold/preloaded measurements remain separate from profiling overhead.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/fixtures/planner_performance/bounded_selection_99c03b1.py.txt"
REFERENCE_SHA = "ebff78029d9fdad5314fb8846072fff31dd07967940c0f9de91c1f00509f8d30"
BOUND = 8


class Counters:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.counts: Counter[str] = Counter()
        self.layers: list[dict[str, int]] = []
        self.stages: dict[str, dict[str, float | int]] = {}
        self.filters: list[dict[str, Any]] = []
        self.stack: list[list[float]] = []
        self.started = time.perf_counter()
        self.setup: dict[str, float] = {}
        self.plan_started: float | None = None
        self.active_names: list[str] = []

    def transition(self) -> None:
        self.counts["candidate_transitions"] += 1
        if self.counts["candidate_transitions"] % 65536 == 0:
            self.checkpoint()

    def layer(self, count: int, size: int, options: int) -> None:
        self.layers.append({"count": count, "states": size, "options": options})
        self.checkpoint()

    def checkpoint(self) -> None:
        if self.path:
            # Private checkpoint survives an owned child-process timeout.
            self.path.write_text(
                json.dumps(self.snapshot(), sort_keys=True), encoding="utf-8"
            )

    def snapshot(self) -> dict[str, Any]:
        return {
            "counts": dict(self.counts),
            "layers": self.layers,
            "stages": self.stages,
            "filters": self.filters,
            "setup_seconds": self.setup,
            "elapsed_since_worker_setup": time.perf_counter() - self.started,
            "open_stage_depth": len(self.stack),
            "active_stages": {
                name: time.perf_counter() - frame[0]
                for name, frame in zip(self.active_names, self.stack)
            },
        }


class ScheduleCounters(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        if node.name == "find_schedule":
            node.body.insert(0, _statement("_perf.counts['date_recursion_calls'] += 1"))
        return node

    def visit_For(self, node: ast.For) -> ast.For:
        self.generic_visit(node)
        if ast.unparse(node.iter) == "candidate_dates":
            node.body.insert(0, _statement("_perf.counts['date_branches'] += 1"))
        return node


def _statement(source: str) -> ast.stmt:
    return ast.parse(source).body[0]


class SearchCounters(ast.NodeTransformer):
    """Observe the same branches and values; never reorder or replace expressions."""

    def visit_For(self, node: ast.For) -> ast.For:
        self.generic_visit(node)
        iterator = ast.unparse(node.iter)
        if iterator == "option_facts":
            node.body.insert(0, _statement("_perf.transition()"))
        elif iterator == "states.items()":
            node.body.insert(0, _statement("_perf.counts['state_visits'] += 1"))
            evaluating = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == "_selection_policy_valid"
                for n in ast.walk(node)
            )
            label = "states_evaluated" if evaluating else "states_expanded"
            node.body.insert(0, _statement(f"_perf.counts[{label!r}] += 1"))
        elif isinstance(node.target, ast.Name) and node.target.id == "count":
            node.body.insert(
                0, _statement("_perf.layer(count, len(states), len(options))")
            )
        return node

    def visit_If(self, node: ast.If) -> ast.If:
        self.generic_visit(node)
        if any(isinstance(stmt, ast.Continue) for stmt in node.body):
            label = "reject:" + ast.unparse(node.test)[:110]
            node.body.insert(0, _statement(f"_perf.counts[{label!r}] += 1"))
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign | list[ast.stmt]:
        if ast.unparse(node.value) == "next_states.get(state)":
            return [
                node,
                _statement("_perf.counts['repeated_states'] += previous is not None"),
            ]
        return node


@contextmanager
def search_variant(variant: str, counters: Counters | None = None) -> Iterator[None]:
    from app.modules.planning import domain

    original = domain._bounded_selection
    source = REFERENCE.read_bytes()
    if sha256(source).hexdigest() != REFERENCE_SHA:
        raise ValueError("reference_revision_mismatch")
    if variant == "optimized":
        source = inspect.getsource(original).encode()
    namespace = dict(vars(domain))
    tree = ast.parse(source)
    if counters:
        tree = SearchCounters().visit(tree)
        namespace["_perf"] = counters
    exec(compile(ast.fix_missing_locations(tree), str(REFERENCE), "exec"), namespace)
    wrapped: dict[str, Any] = {}
    names = (
        "resolve_target",
        "_injury_adjusted_target",
        "eligible_workouts",
        "select_workouts",
        "_selection_policy_valid",
        "_schedule_is_feasible",
        "schedule_workouts",
        "find_anti_stack_violations",
    )
    if counters:
        for name in names:
            saved = getattr(domain, name)
            wrapped[name] = saved
            if name == "schedule_workouts":
                schedule_tree = ScheduleCounters().visit(
                    ast.parse(inspect.getsource(saved))
                )
                namespace["_perf"] = counters
                exec(
                    compile(
                        ast.fix_missing_locations(schedule_tree),
                        "<profile-schedule>",
                        "exec",
                    ),
                    namespace,
                )
                saved = namespace[name]

            def traced(
                *args: Any, _name: str = name, _fn: Any = saved, **kwargs: Any
            ) -> Any:
                started = time.perf_counter()
                frame = [started, 0.0]
                if (
                    _name == "resolve_target"
                    and counters.plan_started is not None
                    and "initial_candidate_capability_filter" not in counters.stages
                ):
                    elapsed = started - counters.plan_started
                    counters.stages["initial_candidate_capability_filter"] = {
                        "calls": 1,
                        "inclusive_seconds": elapsed,
                        "exclusive_seconds": elapsed,
                    }
                counters.stack.append(frame)
                counters.active_names.append(_name)
                try:
                    result = _fn(*args, **kwargs)
                    if _name == "eligible_workouts":
                        counters.filters.append(
                            {
                                "phase": kwargs["phase"].value,
                                "count": len(result),
                                "sports": dict(
                                    Counter(t.discipline.value for t in result)
                                ),
                            }
                        )
                    return result
                finally:
                    elapsed = time.perf_counter() - started
                    counters.stack.pop()
                    counters.active_names.pop()
                    if counters.stack:
                        counters.stack[-1][1] += elapsed
                    entry = counters.stages.setdefault(
                        _name,
                        {
                            "calls": 0,
                            "inclusive_seconds": 0.0,
                            "exclusive_seconds": 0.0,
                        },
                    )
                    entry["calls"] += 1
                    entry["inclusive_seconds"] += elapsed
                    entry["exclusive_seconds"] += elapsed - frame[1]

            setattr(domain, name, traced)
            namespace[name] = traced
    compiled_search = namespace["_bounded_selection"]
    if counters:

        def measured_search(**kwargs: Any) -> Any:
            started = time.perf_counter()
            frame = [started, 0.0]
            counters.stack.append(frame)
            counters.active_names.append("combination_search")
            try:
                return compiled_search(**kwargs)
            finally:
                elapsed = time.perf_counter() - started
                counters.stack.pop()
                counters.active_names.pop()
                if counters.stack:
                    counters.stack[-1][1] += elapsed
                counters.stages["combination_search"] = {
                    "calls": 1,
                    "inclusive_seconds": elapsed,
                    "exclusive_seconds": elapsed - frame[1],
                }

        domain._bounded_selection = measured_search
    else:
        domain._bounded_selection = compiled_search
    try:
        yield
    finally:
        domain._bounded_selection = original
        for name, saved in wrapped.items():
            setattr(domain, name, saved)


def pairs() -> list[tuple[str, str]]:
    from benchmarks.joren_v6 import CASES

    return [(case, "v6") for case in CASES] + [
        (case, mode)
        for mode in ("previous61", "current", "historical61")
        for case in (
            ("build_1", "build_2", "build_3", "build_4")
            if mode == "current"
            else ("tri_zero", "build_1", "build_2", "build_3", "build_4")
        )
    ]


def independent_checks(values: dict[str, Any], plan: Any) -> dict[str, Any]:
    """Check returned values directly, without reusing selection/scheduling predicates.

    Preserved legacy constraints and prospective V6 diagnostics are separate.
    A faster historical selection is never promoted to an approved V6 plan.
    """
    from datetime import datetime, timedelta, timezone
    from datetime import time as day_time
    from decimal import Decimal
    from fractions import Fraction
    from zoneinfo import ZoneInfo

    from app.modules.physiology.models import Discipline, IntensityBucket, TrainingZone
    from app.modules.workouts.catalog import TrainingPhase

    errors = []
    selected = plan.workouts
    templates = {t.id: t for t in values["catalog"]}
    total = sum((w.snapshot.internal_planned_load.value for w in selected), Decimal(0))
    if total != plan.planned_load.value:
        errors.append("load_sum")
    goals = values["goal_disciplines"] - values["confirmed_injuries"]
    if selected and {w.discipline for w in selected} != goals:
        errors.append("sport_coverage")
    for w in selected:
        template = templates[w.snapshot.template_id]
        if w.discipline in values["confirmed_injuries"]:
            errors.append("injury")
        if w.scheduled_date not in values["available_dates"]:
            errors.append("availability")
        if (
            w.snapshot.template_version != template.version
            or w.snapshot.template_key != template.template_key
        ):
            errors.append("immutable_template_identity")
        if w.snapshot.internal_planned_load != template.internal_planned_load:
            errors.append("immutable_load")
        if w.snapshot.segments != template.segments:
            errors.append("immutable_prescription")
        capability = values["zone_capabilities"].get(w.discipline)
        if capability is None or not capability.requirements:
            errors.append("capability")
        zone5 = any(s.zone_target == TrainingZone.ZONE_5 for s in template.segments)
        if (
            plan.target.phase == TrainingPhase.BUILD
            and zone5
            and plan.target.build_week != 4
        ):
            errors.append("z5_phase")
        if (
            plan.target.phase != TrainingPhase.BUILD
            and template.intensity_bucket == IntensityBucket.HIGH
        ):
            errors.append("low_only_phase")
    high = [w for w in selected if w.snapshot.intensity_bucket == IntensityBucket.HIGH]
    for i, a in enumerate(high):
        for b in high[i + 1 :]:
            if a.discipline != b.discipline:
                continue
            instants = [
                datetime.combine(
                    w.scheduled_date, day_time(12), ZoneInfo(values["timezone_name"])
                ).astimezone(timezone.utc)
                for w in (a, b)
            ]
            hours = abs((instants[1] - instants[0]).total_seconds()) / 3600
            if hours < (72 if a.discipline == Discipline.RUN else 48):
                errors.append("high_spacing")
    for sport, cap in plan.target.discipline_caps.items():
        if (
            sum(
                (
                    w.snapshot.internal_planned_load.value
                    for w in selected
                    if w.discipline == sport
                ),
                Decimal(0),
            )
            > cap.value
        ):
            errors.append("discipline_cap")
    eligible = []
    for template in templates.values():
        if (
            template.discipline not in goals
            or template.internal_planned_load is None
            or template.explicit_scheduling_only
        ):
            continue
        phase = plan.target.phase
        zones = {s.zone_target for s in template.segments if s.zone_target is not None}
        if phase not in template.training_phases and not (
            phase == TrainingPhase.TAPER
            and template.source_catalog == "start23-v0.1"
            and template.intensity_bucket == IntensityBucket.LOW
        ):
            continue
        if phase != TrainingPhase.BUILD and (
            template.intensity_bucket == IntensityBucket.HIGH
            or any(z.value > 2 for z in zones)
        ):
            continue
        if (
            phase == TrainingPhase.BUILD
            and plan.target.build_week != 4
            and TrainingZone.ZONE_5 in zones
        ):
            continue
        if template.discipline not in values["zone_capabilities"]:
            continue
        eligible.append(template)
    if selected and eligible:
        minimum = min(t.internal_planned_load.value for t in eligible)
        if abs(plan.target.target.value - total) >= minimum:
            errors.append("legacy_target_fit")
        if plan.target.phase == TrainingPhase.BUILD:
            budget = plan.target.target.value * plan.target.desired_high_fraction.value
            high_load = sum(
                (w.snapshot.internal_planned_load.value for w in high), Decimal(0)
            )
            high_candidates = [
                t
                for t in eligible
                if t.intensity_bucket == IntensityBucket.HIGH
                and t.internal_planned_load.value <= budget
            ]
            if high_load > budget:
                errors.append("legacy_high_budget")
            if (
                high_candidates
                and plan.target.build_week != 4
                and not budget * Decimal(".70") <= high_load <= budget * Decimal(".90")
            ):
                errors.append("legacy_build_high_range")
            if high_candidates and plan.target.build_week == 4:
                z5_available = any(
                    any(s.zone_target == TrainingZone.ZONE_5 for s in t.segments)
                    for t in high_candidates
                )
                z5_selected = any(
                    any(
                        s.zone_target == TrainingZone.ZONE_5
                        for s in w.snapshot.segments
                    )
                    for w in selected
                )
                if high_load <= 0 or (z5_available and not z5_selected):
                    errors.append("legacy_build4_high")
    if (
        selected
        and not values.get("fixed_template_dates")
        and not values.get("fixed_occurrence_dates")
    ):
        from itertools import combinations

        def rest_run(days: set[Any]) -> int:
            bits = "".join(
                "1" if values["week_start"] + timedelta(days=i) in days else "0"
                for i in range(7)
            )
            return max(map(len, bits.split("1")))

        available = values["available_dates"]
        rest_possible = any(
            rest_run(set(days)) <= 3
            for size in range(1, min(len(selected), len(available)) + 1)
            for days in combinations(available, size)
        )
        if rest_possible and rest_run({w.scheduled_date for w in selected}) > 3:
            errors.append("rest_spacing")
    active: dict[str, Any] = {}
    for sport in Discipline:
        low_seconds, high_seconds, unknown = Fraction(0), Fraction(0), False
        sport_workouts = [w for w in selected if w.discipline == sport]
        for w in sport_workouts:
            for segment in w.snapshot.segments:
                if segment.duration_minutes is None:
                    unknown = True
                    continue
                seconds = Fraction(segment.duration_minutes) * 60
                is_high = (
                    (segment.zone_target > TrainingZone.ZONE_2)
                    if segment.zone_target is not None
                    else (
                        (segment.rpe_target or segment.protocol_target).intensity_bucket
                        == IntensityBucket.HIGH
                    )
                )
                if is_high:
                    high_seconds += seconds
                else:
                    low_seconds += seconds
        denominator = low_seconds + high_seconds
        active[sport.value] = {
            "status": "UNVERIFIED"
            if unknown
            else "NOT_APPLICABLE"
            if denominator == 0
            else "PASS"
            if high_seconds * 5 <= denominator
            else "FAIL",
            "high_ratio": None
            if unknown or not denominator
            else str(high_seconds / denominator),
            "known_low_seconds": str(low_seconds),
            "known_high_seconds": str(high_seconds),
        }
    beginner = not values["prior_loads"] and len(goals) == 3
    return {
        "legacy_independent_constraints": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "prospective_v6_diagnostics": {
            "within_target_budget": total <= plan.target.target.value,
            "beginner_one_each": all(
                sum(w.discipline == s for w in selected) == 1 for s in goals
            )
            if beginner
            else None,
            "per_sport_active_time": active,
            "policy_and_method_approval": "NOT GRANTED BY PERFORMANCE WORK",
        },
    }


def child(args: argparse.Namespace) -> None:
    # Module import and catalog setup are deliberately outside measured warm calls.
    from app.modules.planning import domain
    from benchmarks.joren_v6 import projection, scenario, source_records
    from benchmarks.planning import canonical, digest, full_catalog

    imported = time.perf_counter()
    records = () if args.mode == "current" else source_records(args.mode)
    deck = (
        full_catalog()
        if args.mode == "current"
        else projection(records, historical=args.mode == "historical61")
    )
    built = time.perf_counter()
    values = scenario(args.case, deck)
    prepared = time.perf_counter()
    counters = Counters(args.checkpoint) if args.instrument else None
    setup = {
        "python_imports": imported - STARTED,
        "catalog_construction": built - imported,
        "scenario_preparation": prepared - built,
    }
    if counters:
        counters.setup = setup
        counters.checkpoint()
    with search_variant(args.variant, counters):
        print(
            json.dumps(
                {
                    "stage": "ready",
                    "setup_seconds": setup,
                    "input_sha256": digest(values),
                }
            ),
            flush=True,
        )
        if args.preloaded:
            input()
        started = time.perf_counter()
        if counters:
            counters.plan_started = started
        try:
            plan = domain.build_weekly_plan(**values)
            outcome = {"outcome": "PENDING_HYPOTHETICAL_PLAN", "plan": canonical(plan)}
        except domain.PlanningConstraintError as exc:
            outcome = {"outcome": "FAIL_CLOSED", "code": exc.code, "message": str(exc)}
        finished = time.perf_counter()
        checks = (
            independent_checks(values, plan)
            if outcome["outcome"] == "PENDING_HYPOTHETICAL_PLAN"
            else None
        )
        if counters:
            counters.checkpoint()
        serialization_started = time.perf_counter()
        payload = json.dumps(outcome, sort_keys=True)
        serialized = time.perf_counter()
        result = {
            "stage": "result",
            "result": outcome,
            "output_sha256": sha256(payload.encode()).hexdigest(),
            "planner_seconds": finished - started,
            "serialization_seconds": serialized - serialization_started,
            "independent_checks": checks,
            "profile": counters.snapshot() if counters else None,
        }
        print(json.dumps(result, sort_keys=True), flush=True)


def attempt(
    case: str,
    mode: str,
    variant: str,
    *,
    preloaded: bool,
    instrument: bool,
    checkpoint: Path,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-B",
        "-m",
        "benchmarks.v6_planner_performance",
        "--case",
        case,
        "--mode",
        mode,
        "--variant",
        variant,
        "--checkpoint",
        str(checkpoint),
    ]
    if preloaded:
        command.append("--preloaded")
    if instrument:
        command.append("--instrument")
    started = time.perf_counter()
    with subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        ready = None
        setup_wall = None
        clock = started
        try:
            # Read readiness for both modes. The cold deadline still starts
            # before process launch; preloaded gets a separate eight-second call.
            import concurrent.futures

            assert process.stdout is not None
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(process.stdout.readline)
                try:
                    ready = json.loads(future.result(timeout=BOUND))
                except concurrent.futures.TimeoutError:
                    process.kill()
                    raise subprocess.TimeoutExpired(command, BOUND) from None
            setup_wall = time.perf_counter() - started
            if preloaded:
                clock = time.perf_counter()
                stdout, stderr = process.communicate("go\n", timeout=BOUND)
            else:
                stdout, stderr = process.communicate(
                    timeout=max(0.0001, BOUND - setup_wall)
                )
            elapsed = time.perf_counter() - clock
            if process.returncode:
                raise RuntimeError(stderr)
            lines = [json.loads(line) for line in stdout.splitlines() if line]
            ready = ready or next(row for row in lines if row["stage"] == "ready")
            result = next(row for row in lines if row["stage"] == "result")
            return {
                **result,
                "ready": ready,
                "wall_seconds": elapsed,
                "setup_wall_seconds": setup_wall,
                "process_and_harness_setup_seconds": setup_wall
                - sum(ready["setup_seconds"].values()),
            }
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            progress = (
                json.loads(checkpoint.read_text()) if checkpoint.exists() else None
            )
            return {
                "result": {"outcome": "DIAGNOSTIC_TIMEOUT"},
                "wall_seconds": time.perf_counter() - clock,
                "setup_wall_seconds": setup_wall,
                "ready": ready,
                "profile": progress,
                "bound_seconds": BOUND,
            }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case")
    parser.add_argument("--mode", default="v6")
    parser.add_argument(
        "--variant", choices=("reference", "optimized"), default="reference"
    )
    parser.add_argument("--preloaded", action="store_true")
    parser.add_argument("--instrument", action="store_true")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    if args.case:
        child(args)
        return
    if not args.output:
        parser.error("output required")
    from app.jobs.joren_catalog_dry_run import write_immutable

    results = {}
    for case, mode in pairs():
        key = f"{mode}:{case}"
        if args.only and key not in args.only:
            continue
        checkpoint = args.output.with_name(args.output.stem + "-checkpoint.json")
        if checkpoint.exists():
            checkpoint.unlink()
        results[key] = attempt(
            case,
            mode,
            args.variant,
            preloaded=args.preloaded,
            instrument=args.instrument,
            checkpoint=checkpoint,
        )
        print(f"{args.variant} {key}: {results[key]['result']['outcome']}", flush=True)
    write_immutable(
        args.output,
        json.dumps(
            {
                "variant": args.variant,
                "preloaded": args.preloaded,
                "instrumented": args.instrument,
                "bound_seconds": BOUND,
                "cases": results,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
    )


if __name__ == "__main__":
    main()
