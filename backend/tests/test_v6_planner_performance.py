"""Differential proof fixtures for monotone overshoot pruning, not new policies."""

import json
import random
from dataclasses import replace
from decimal import (
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    Decimal,
    localcontext,
)
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.modules.physiology.models import (
    Discipline,
    Fraction,
    IntensityBucket,
    InternalLoad,
)
from app.modules.planning import domain
from app.modules.workouts.catalog import TrainingPhase, WorkoutTemplate
from benchmarks.joren_v6 import projection, scenario, source_records
from benchmarks.planning import canonical
from benchmarks.v6_planner_performance import (
    Counters,
    SearchCounters,
    independent_checks,
    search_variant,
)

PERFORMANCE = (
    Path(__file__).resolve().parents[2] / "docs/catalog/implementation/performance"
)
BEFORE = json.loads((PERFORMANCE / "reference_cold_verified.json").read_text())
AFTER = json.loads((PERFORMANCE / "optimized_cold_verified.json").read_text())
REFERENCE_COMPLETIONS = tuple(
    k
    for k, v in BEFORE["cases"].items()
    if v["result"]["outcome"] != "DIAGNOSTIC_TIMEOUT"
)


@pytest.fixture(scope="module")
def deck() -> tuple[WorkoutTemplate, ...]:
    return projection(source_records())


def selected(variant: str, values: dict[str, Any]) -> tuple[str, ...] | None:
    with search_variant(variant):
        result = domain._bounded_selection(**values)
    return tuple(str(t.id) for t in result) if result is not None else None


@pytest.mark.parametrize("seed", range(72))
def test_exact_oracle_differential(
    seed: int, deck: tuple[WorkoutTemplate, ...]
) -> None:
    rng = random.Random(seed)
    bases = [
        next(t for t in deck if t.discipline == sport and t.intensity_bucket == bucket)
        for sport in Discipline
        for bucket in IntensityBucket
    ]
    templates = tuple(
        replace(
            t,
            id=UUID(int=i + 1),
            internal_planned_load=InternalLoad(Decimal(rng.randint(1, 35)) / 10),
        )
        for i, t in enumerate(rng.sample(bases, 4))
    )
    phase = (TrainingPhase.BASE, TrainingPhase.BUILD, TrainingPhase.RECOVERY)[seed % 3]
    prefix = templates[:1] if seed % 5 == 0 else ()
    values: dict[str, Any] = dict(
        deck=templates,
        prefix=prefix,
        required_disciplines=frozenset(t.discipline for t in templates),
        target=InternalLoad(Decimal(rng.randint(25, 120)) / 10),
        phase=phase,
        build_week=4 if seed % 4 == 0 else 1,
        desired_high_fraction=Fraction(Decimal(".2")),
        required_count=4 if seed % 4 == 1 else None,
        required_composition={s: 2 for s in Discipline} if seed % 7 == 0 else None,
        maximum_uses={t.id: 2 for t in templates} if seed % 5 == 0 else None,
        discipline_caps={s: InternalLoad(Decimal(6)) for s in Discipline}
        if seed % 6 == 0
        else None,
        feasible=(lambda selection: sum(t.id.int == 1 for t in selection) <= 1)
        if seed % 8 == 0
        else None,
    )
    assert selected("optimized", values) == selected("reference", values)
    assert selected(
        "optimized", {**values, "deck": tuple(reversed(templates))}
    ) == selected("reference", {**values, "deck": tuple(reversed(templates))})


@pytest.mark.parametrize("precision", (8, 28, 50))
@pytest.mark.parametrize("target", ("0", "1.9", "2.0", "2.1", "8.4"))
def test_strict_fit_boundary_and_ties(
    precision: int, target: str, deck: tuple[WorkoutTemplate, ...]
) -> None:
    base = next(t for t in deck if t.name == "TR-BIKE-023")
    templates = tuple(
        replace(
            base, id=UUID(int=i + 1), internal_planned_load=InternalLoad(Decimal(p))
        )
        for i, p in enumerate(("1.0", "2.0", "2.0", "0.1"))
    )
    values = dict(
        deck=templates,
        prefix=(),
        required_disciplines=frozenset({Discipline.BIKE}),
        target=InternalLoad(Decimal(target)),
        phase=TrainingPhase.BASE,
        build_week=None,
        desired_high_fraction=Fraction(Decimal(".2")),
    )
    with localcontext() as context:
        context.prec = precision
        assert selected("optimized", values) == selected("reference", values)


def test_zero_load_and_arbitrary_prefix_remain_fail_closed(
    deck: tuple[WorkoutTemplate, ...],
) -> None:
    t = replace(deck[0], internal_planned_load=InternalLoad(Decimal(0)))
    values = dict(
        deck=(t,),
        prefix=(t,),
        required_disciplines=frozenset({t.discipline}),
        target=InternalLoad(Decimal(0)),
        phase=TrainingPhase.BASE,
        build_week=None,
        desired_high_fraction=Fraction(Decimal(".2")),
    )
    assert selected("reference", values) is None
    assert selected("optimized", values) is None


def test_counters_are_transparent_and_prune_work(
    deck: tuple[WorkoutTemplate, ...],
) -> None:
    values: dict[str, Any] = dict(
        deck=deck,
        prefix=(),
        required_disciplines=frozenset(Discipline),
        target=InternalLoad(Decimal("29.3")),
        phase=TrainingPhase.BASE,
        build_week=None,
        desired_high_fraction=Fraction(Decimal(".2")),
        required_count=3,
    )
    counts = {}
    results = []
    for variant in ("reference", "optimized"):
        c = Counters(None)
        with search_variant(variant, c):
            result = domain._bounded_selection(**values)
        counts[variant] = c.counts["candidate_transitions"]
        results.append(tuple(t.id for t in result) if result else None)
    assert results[0] == results[1]
    assert counts["optimized"] < counts["reference"]


def test_full_plan_identity_and_instrumentation_parity(
    deck: tuple[WorkoutTemplate, ...],
) -> None:
    values = scenario("candidate", deck)
    results = []
    for variant, instrument in (
        ("reference", False),
        ("reference", True),
        ("optimized", False),
        ("optimized", True),
    ):
        c = Counters(None) if instrument else None
        with search_variant(variant, c):
            plan = domain.build_weekly_plan(**values)
        results.append(canonical(plan))
        checks = independent_checks(values, plan)
        assert checks["legacy_independent_constraints"] == "PASS"
        assert (
            checks["prospective_v6_diagnostics"]["per_sport_active_time"]["swim"][
                "status"
            ]
            == "UNVERIFIED"
        )
    assert all(result == results[0] for result in results)


def test_independent_checks_reject_unsafe_returned_data(
    deck: tuple[WorkoutTemplate, ...],
) -> None:
    values = scenario("candidate", deck)
    plan = domain.build_weekly_plan(**values)
    first = plan.workouts[0]
    changed = replace(
        plan,
        workouts=(
            replace(first, scheduled_date=values["week_start"].replace(year=2027)),
            *plan.workouts[1:],
        ),
    )
    assert "availability" in independent_checks(values, changed)["errors"]


def test_reference_fixture_is_an_explicit_offline_oracle() -> None:
    from hashlib import sha256

    from benchmarks.v6_planner_performance import REFERENCE, REFERENCE_SHA

    assert sha256(REFERENCE.read_bytes()).hexdigest() == REFERENCE_SHA
    assert "new_total > target.value" not in REFERENCE.read_text()
    assert SearchCounters is not None


@pytest.mark.parametrize(
    "rounding", (ROUND_HALF_EVEN, ROUND_DOWN, ROUND_FLOOR, ROUND_CEILING)
)
@pytest.mark.parametrize("target", ("3.987654321", "1.23456666", "2.97777777"))
def test_directed_rounding_uses_the_original_score_expression(
    rounding: str, target: str, deck: tuple[WorkoutTemplate, ...]
) -> None:
    template = next(t for t in deck if t.name == "TR-BIKE-023")
    templates = tuple(
        replace(
            template,
            id=UUID(int=i + 1),
            internal_planned_load=InternalLoad(Decimal(value)),
        )
        for i, value in enumerate(
            ("1.23456789", ".0100000009", "2.98765432", ".000000013")
        )
    )
    values: dict[str, Any] = dict(
        deck=templates,
        prefix=(),
        required_disciplines=frozenset({Discipline.BIKE}),
        target=InternalLoad(Decimal(target)),
        phase=TrainingPhase.BASE,
        build_week=None,
        required_count=4,
        desired_high_fraction=Fraction(Decimal(".2")),
    )
    with localcontext() as context:
        context.prec = 3
        context.rounding = rounding
        assert selected("optimized", values) == selected("reference", values)


def test_decimal_traps_keep_original_search(deck: tuple[WorkoutTemplate, ...]) -> None:
    from decimal import Inexact

    t = replace(deck[0], internal_planned_load=InternalLoad(Decimal("1.23456789")))
    values: dict[str, Any] = dict(
        deck=(t,),
        prefix=(),
        required_disciplines=frozenset({Discipline.BIKE}),
        target=InternalLoad(Decimal("2.987654321")),
        phase=TrainingPhase.BASE,
        build_week=None,
        required_count=3,
        desired_high_fraction=Fraction(Decimal(".2")),
    )
    outcomes = []
    for variant in ("reference", "optimized"):
        with localcontext() as context:
            context.prec = 3
            context.traps[Inexact] = True
            try:
                result = selected(variant, values)
            except Inexact:
                outcomes.append("same trapped arithmetic")
            else:
                outcomes.append(str(result))
    assert outcomes[0] == outcomes[1]


@pytest.fixture(scope="module")
def corpus_inputs() -> dict[str, dict[str, Any]]:
    from benchmarks.planning import full_catalog

    decks = {
        mode: projection(source_records(mode), historical=mode == "historical61")
        for mode in ("v6", "previous61", "historical61")
    }
    decks["current"] = full_catalog()
    return {
        key: scenario(key.split(":")[1], decks[key.split(":")[0]])
        for key in BEFORE["cases"]
    }


@pytest.mark.parametrize("key", REFERENCE_COMPLETIONS)
def test_full_completed_reference_corpus_is_exact(
    key: str, corpus_inputs: dict[str, dict[str, Any]]
) -> None:
    from benchmarks.planning import digest

    values = corpus_inputs[key]
    assert digest(values) == BEFORE["cases"][key]["ready"]["input_sha256"]
    try:
        plan = domain.build_weekly_plan(**values)
    except domain.PlanningConstraintError as exc:
        result = {"outcome": "FAIL_CLOSED", "code": exc.code, "message": str(exc)}
    else:
        result = {"outcome": "PENDING_HYPOTHETICAL_PLAN", "plan": canonical(plan)}
        assert (
            independent_checks(values, plan)["legacy_independent_constraints"] == "PASS"
        )
    assert result == BEFORE["cases"][key]["result"]


def test_complete_measurement_corpus_has_no_parity_or_independent_failures() -> None:
    assert set(BEFORE["cases"]) == set(AFTER["cases"])
    assert len(BEFORE["cases"]) == 40 and len(REFERENCE_COMPLETIONS) == 22
    for key, before in BEFORE["cases"].items():
        after = AFTER["cases"][key]
        assert before["ready"]["input_sha256"] == after["ready"]["input_sha256"]
        if before["result"]["outcome"] != "DIAGNOSTIC_TIMEOUT":
            assert before["output_sha256"] == after["output_sha256"]
        if after.get("independent_checks"):
            assert (
                after["independent_checks"]["legacy_independent_constraints"] == "PASS"
            )


def test_former_beginner_timeout_has_bounded_work_and_explicit_policy_gap(
    deck: tuple[WorkoutTemplate, ...],
) -> None:
    c = Counters(None)
    values = scenario("tri_zero", deck)
    with search_variant("optimized", c):
        plan = domain.build_weekly_plan(**values)
    assert c.counts["candidate_transitions"] < 100_000
    assert canonical(plan) == AFTER["cases"]["v6:tri_zero"]["result"]["plan"]
    checks = independent_checks(values, plan)
    assert checks["legacy_independent_constraints"] == "PASS"
    assert not checks["prospective_v6_diagnostics"]["within_target_budget"]
    assert (
        checks["prospective_v6_diagnostics"]["per_sport_active_time"]["swim"]["status"]
        == "UNVERIFIED"
    )
