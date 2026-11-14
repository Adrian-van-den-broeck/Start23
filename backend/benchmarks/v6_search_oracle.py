"""Independent exhaustive reference, only for offline TEST_ONLY verification.

No selector ranking, enumeration, bounds, eligibility, validation or scheduler.
Integer arithmetic over the exact official Decimal operands, and exhaustive date
feasibility over source buckets. This is deliberately not a production engine.
"""

from collections import Counter
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta, timezone
from fractions import Fraction
from itertools import combinations, combinations_with_replacement, product
from math import lcm
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.planning.domain import PlanningTarget, ZoneCapability
from app.modules.planning.v6_selection import V6Controls
from app.modules.workouts.catalog import FallbackCompatibility, TrainingPhase
from app.modules.workouts.joren_draft import TimedZone, WallRest
from app.modules.workouts.joren_v6_official import V6Template


def source_times(t: V6Template, c: V6Controls) -> tuple[Fraction, Fraction]:
    prescribed = {k: values for k, values, _ in c.prescribed_swim_seconds}
    low = high = Fraction(0)
    for i, event in enumerate(t.source_revision.predecessor.events):
        if isinstance(event, WallRest):
            continue
        if t.id in prescribed:
            seconds = Fraction(prescribed[t.id][i])
        elif isinstance(event, TimedZone):
            seconds = Fraction(event.seconds)
        else:
            seconds = (
                Fraction(event.meters)
                * (
                    Fraction("130.2"),
                    Fraction(120),
                    Fraction("109.8"),
                    Fraction("100.2"),
                    Fraction(90),
                )[event.zone - 1]
                / 100
            )
        if event.zone <= 2:
            low += seconds
        else:
            high += seconds
    return low, high


def date_feasible(
    rows: tuple[V6Template, ...],
    *,
    controls: V6Controls,
    week_start: date,
    timezone_name: str,
    dates: tuple[date, ...],
    prefix_ids: tuple[UUID, ...],
    prefix_count: int,
    fixed: Mapping[UUID, date],
) -> bool:
    if not rows:
        return True
    if not dates or len(set(dates)) != len(dates):
        return False
    week = tuple(week_start + timedelta(days=i) for i in range(7))
    if not set(dates) <= set(week) or not set(fixed.values()) <= set(dates):
        return False
    ordered = (
        rows
        if prefix_count
        else tuple(sorted(rows, key=lambda t: (t.discipline.value, str(t.id))))
    )
    version = "joren-v6-automatic-selection-1"
    namespace = controls.occurrence_namespace or (
        uuid5(controls.athlete_scope, f"{version}:{week_start}")
        if controls.athlete_scope
        else NAMESPACE_URL
    )
    ids = tuple(
        prefix_ids[i]
        if i < len(prefix_ids)
        else uuid5(namespace, f"{version}:{week_start}:{i}:{t.id}")
        for i, t in enumerate(ordered)
    )
    if not set(fixed) <= set(ids) | {t.id for t in ordered}:
        return False

    def rest_gap(days: set[date]) -> int:
        gap = longest = 0
        for day in week:
            gap = 0 if day in days else gap + 1
            longest = max(longest, gap)
        return longest

    enforce_rest = not fixed and any(
        rest_gap(set(subset)) <= 3
        for n in range(1, min(len(ordered), len(dates)) + 1)
        for subset in combinations(dates, n)
    )
    # The proof of feasibility needs existence, not production placement order.
    assignments: list[tuple[V6Template, date]] = []
    zone = ZoneInfo(timezone_name)

    def assign(i: int) -> bool:
        if i == len(ordered):
            return not enforce_rest or rest_gap({d for _, d in assignments}) <= 3
        row = ordered[i]
        pinned = fixed.get(ids[i], fixed.get(row.id))
        for day in (pinned,) if pinned is not None else dates:
            instant = datetime.combine(day, time(12), zone).astimezone(timezone.utc)
            if row.intensity_bucket is IntensityBucket.HIGH and any(
                other.discipline is row.discipline
                and other.intensity_bucket is IntensityBucket.HIGH
                and abs(
                    (
                        instant
                        - datetime.combine(when, time(12), zone).astimezone(
                            timezone.utc
                        )
                    ).total_seconds()
                )
                < {Discipline.RUN: 72, Discipline.BIKE: 48, Discipline.SWIM: 48}[
                    row.discipline
                ]
                * 3600
                for other, when in assignments
            ):
                continue
            assignments.append((row, day))
            found = assign(i + 1)
            assignments.pop()
            if found:
                return True
        return False

    return assign(0)


def exhaustive(
    *,
    catalog: tuple[V6Template, ...],
    target: PlanningTarget,
    controls: V6Controls,
    goals: frozenset[Discipline],
    capabilities: Mapping[Discipline, ZoneCapability],
    week_start: date,
    timezone_name: str,
    dates: tuple[date, ...],
    injuries: frozenset[Discipline] = frozenset(),
    low_only: frozenset[Discipline] = frozenset(),
    prefix: tuple[UUID, ...] = (),
    prefix_ids: tuple[UUID, ...] = (),
    fixed: Mapping[UUID, date] | None = None,
    excluded: frozenset[UUID] = frozenset(),
    required: Mapping[Discipline, int] | None = None,
) -> dict[str, Any]:
    eligible = []
    for row in catalog:
        cap = capabilities.get(row.discipline)
        if row.discipline not in goals or row.discipline in injuries:
            continue
        if target.phase not in row.source_revision.phases:
            continue
        if cap is None or not (cap.requirements or cap.rpe_guided):
            continue
        if (
            cap.fallback_active
            and not cap.rpe_guided
            and row.fallback_compatibility is FallbackCompatibility.INCOMPATIBLE
        ):
            continue
        if row.discipline in low_only and row.intensity_bucket is IntensityBucket.HIGH:
            continue
        if (
            target.phase is TrainingPhase.BUILD
            and target.build_week != 4
            and any(
                not isinstance(e, WallRest) and e.zone == 5
                for e in row.source_revision.predecessor.events
            )
        ):
            continue
        if row.source_workout_id == "TR-BIKE-013" and row.id not in dict(
            controls.duration_evidence
        ):
            continue
        if (
            row.discipline is Discipline.SWIM
            and not controls.estimate_swim_for_preview
            and row.id not in {v[0] for v in controls.prescribed_swim_seconds}
        ):
            continue
        eligible.append(row)
    by_id = {t.id: t for t in eligible}
    if not set(prefix) <= set(by_id):
        return {"outcome": "ineligible_prefix"}
    retained = tuple(by_id[k] for k in prefix)
    frequency = {r.sport: r for r in controls.session_frequency}
    limits = dict(controls.maximum_uses)
    # A single common integer unit is lossless; no rounded grid is used.
    operands = [Fraction(t.official.value) for t in eligible] + [
        Fraction(target.target.value),
        *(Fraction(c.value) for c in target.discipline_caps.values()),
    ]
    scale = lcm(*(v.denominator for v in operands))
    loads = {t.id: int(Fraction(t.official.value) * scale) for t in eligible}
    budget = int(Fraction(target.target.value) * scale)
    times = {t.id: source_times(t, controls) for t in eligible}
    sports = sorted(goals, key=lambda s: s.value)
    groups = []
    for sport in sports:
        existing = tuple(t for t in retained if t.discipline is sport)
        desired = max(
            len(existing), frequency[sport].requested if sport in frequency else 1
        )
        choices = tuple(
            sorted(
                (t for t in eligible if t.discipline is sport and t.id not in excluded),
                key=lambda t: str(t.id),
            )
        )
        options = []
        for n in range(desired - len(existing) + 1):
            for added in combinations_with_replacement(choices, n):
                members = existing + added
                count = len(members)
                if sport in frequency and count > frequency[sport].maximum:
                    continue
                if required is not None and count != required.get(sport, 0):
                    continue
                uses = Counter(t.id for t in members)
                if any(uses[k] > value for k, value in limits.items()):
                    continue
                load = sum(loads[t.id] for t in members)
                sport_cap = target.discipline_caps.get(sport)
                if sport_cap is not None and load > Fraction(sport_cap.value) * scale:
                    continue
                lo = sum((times[t.id][0] for t in members), Fraction(0))
                hi = sum((times[t.id][1] for t in members), Fraction(0))
                if 5 * hi > lo + hi:
                    continue
                options.append((added, load, count))
        groups.append(options)
    best_prefix: tuple[int, int] | None = None
    best_n, best_d, best_total = 0, 1, 0
    best_ids: tuple[str, ...] = ()
    winner: tuple[V6Template, ...] | None = None
    visited = budget_valid = schedule_checks = 0
    for combo in product(*groups):
        visited += 1
        total = sum(option[1] for option in combo)
        if total > budget or len(retained) + sum(len(v[0]) for v in combo) > 24:
            continue
        budget_valid += 1
        leading = (
            -sum(v[2] > 0 for v in combo),
            -sum(
                min(v[2], frequency[s].requested) if s in frequency else 0
                for s, v in zip(sports, combo)
            ),
        )
        # All complete products are visited. This is only direct lexicographic
        # comparison with a feasible winner, never a bound on a partial state.
        if best_prefix is not None and leading > best_prefix:
            continue
        numerator = (
            sum(
                abs(
                    10 * v[1]
                    - total
                    * {Discipline.BIKE: 5, Discipline.RUN: 3, Discipline.SWIM: 2}[s]
                )
                for s, v in zip(sports, combo)
            )
            if total and goals == frozenset(Discipline)
            else 0
        )
        denominator = 10 * total if total else 1
        rows = retained + sum((v[0] for v in combo), ())
        identities = tuple(sorted(str(t.id) for t in rows))
        if best_prefix == leading:
            comparison = numerator * best_d - best_n * denominator
            if comparison > 0 or (
                comparison == 0
                and (
                    total < best_total or total == best_total and identities >= best_ids
                )
            ):
                continue
        schedule_checks += 1
        if not date_feasible(
            rows,
            controls=controls,
            week_start=week_start,
            timezone_name=timezone_name,
            dates=dates,
            prefix_ids=prefix_ids,
            prefix_count=len(prefix),
            fixed=fixed or {},
        ):
            continue
        best_prefix = leading
        best_n, best_d, best_total, best_ids = numerator, denominator, total, identities
        winner = rows
    return dict(
        outcome="complete" if winner is not None else "infeasible",
        products_visited=visited,
        budget_valid_products=budget_valid,
        independent_schedule_checks=schedule_checks,
        template_ids=list(best_ids),
        ranking=[
            *(best_prefix or (0, 0)),
            str(Fraction(best_n, best_d)),
            str(Fraction(-best_total, scale)),
            list(best_ids),
        ],
    )


def main() -> None:
    import argparse
    import json
    from pathlib import Path
    from time import perf_counter

    from app.modules.planning.domain import PlanningTargetBasis
    from benchmarks.v6_exact_search import CASES, inputs

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for label, *_ in CASES:
        values = inputs(label)
        controls = values["controls"]
        target = controls.authorized_target or PlanningTarget(
            TrainingPhase.BASE,
            PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            values["onboarding_baseline"].total,
        )
        began = perf_counter()
        result = exhaustive(
            catalog=values["catalog"],
            target=target,
            controls=controls,
            goals=values["goal_disciplines"],
            capabilities=values["zone_capabilities"],
            week_start=values["week_start"],
            timezone_name=values["timezone_name"],
            dates=values["available_dates"],
        )
        result.update(case=label, seconds=perf_counter() - began)
        records.append(result)
        args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        print(label, result["outcome"], result["products_visited"], flush=True)


if __name__ == "__main__":
    main()
