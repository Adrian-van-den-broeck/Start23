"""Independent exhaustive BUILD optima and frozen Phase 1 differential checks."""

import decimal
import json
import random
from dataclasses import replace
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction as Rational
from hashlib import sha256
from itertools import product
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.modules.physiology.models import (
    Discipline,
    Fraction,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.planning import domain
from app.modules.workouts.catalog import TrainingPhase, WorkoutTemplate
from benchmarks.joren_v6 import projection, scenario, source_records
from benchmarks.planning import canonical
from benchmarks.v6_planner_performance import (
    ACCEPTED,
    ACCEPTED_SHA,
    Counters,
    independent_checks,
    search_variant,
)


@pytest.fixture(scope="module")
def bases() -> tuple[WorkoutTemplate, ...]:
    deck = projection(source_records())
    return tuple(
        next(
            t
            for t in deck
            if t.discipline is sport and t.intensity_bucket is IntensityBucket.LOW
        )
        for sport in Discipline
    )


def small_values(seed: int, bases: tuple[WorkoutTemplate, ...]) -> dict[str, Any]:
    rng = random.Random(seed)
    deck = tuple(
        replace(
            rng.choice(bases),
            id=UUID(int=i + 1),
            internal_planned_load=InternalLoad(Decimal(rng.randint(0, 20)) / 10),
            intensity_bucket=rng.choice(tuple(IntensityBucket)),
            reviewed_zone_numbers=frozenset({TrainingZone.ZONE_5})
            if rng.randrange(5) == 0
            else frozenset(),
        )
        for i in range(3 + seed % 2)
    )
    count = 3 + seed % 3
    return dict(
        deck=tuple(reversed(deck)) if seed % 2 else deck,
        prefix=deck[:1] if seed % 7 == 0 else (),
        required_disciplines=frozenset(t.discipline for t in deck),
        target=InternalLoad(Decimal(rng.randint(0, 90)) / 10),
        phase=TrainingPhase.BUILD,
        build_week=4 if seed % 2 else 1,
        desired_high_fraction=Fraction(
            rng.choice((Decimal(".2"), Decimal(".5"), Decimal(1)))
        ),
        required_count=count,
        required_composition={s: 1 for s in Discipline} if seed % 11 == 0 else None,
        maximum_uses={t.id: rng.choice((0, 1, 2, 24)) for t in deck}
        if seed % 3 == 0
        else None,
        discipline_caps={s: InternalLoad(Decimal(3)) for s in Discipline}
        if seed % 13 == 0
        else None,
    )


def result(variant: str, values: dict[str, Any]) -> Any:
    with search_variant(variant):
        return canonical(domain._bounded_selection(**values))


def exhaustive(values: dict[str, Any]) -> Any:
    """Enumerate ordered occurrences, independently spelling out legacy rules.

    These fixtures use permutation-invariant feasibility and exact arithmetic.
    They therefore also test the unrestricted optimum, not just the DP merging.
    """
    deck = values["deck"]
    prefix = values["prefix"]
    count = values["required_count"]
    target = values["target"].value
    budget = target * values["desired_high_fraction"].value
    minimum = min(t.internal_planned_load.value for t in deck)
    high_available = any(
        t.intensity_bucket is IntensityBucket.HIGH
        and t.internal_planned_load.value <= budget
        for t in deck
    )

    def zone5(t: WorkoutTemplate) -> bool:
        return TrainingZone.ZONE_5 in t.reviewed_zone_numbers or any(
            s.zone_target is TrainingZone.ZONE_5 for s in t.segments
        )

    z5_available = values["build_week"] == 4 and any(
        t.intensity_bucket is IntensityBucket.HIGH
        and t.internal_planned_load.value <= budget
        and zone5(t)
        for t in deck
    )
    best = None
    best_score = None
    for suffix in product(deck, repeat=count - len(prefix)):
        selection = prefix + suffix
        uses = values["maximum_uses"]
        if uses is not None and any(
            sum(t.id == identity for t in selection) > limit
            for identity, limit in uses.items()
        ):
            continue
        if not values["required_disciplines"].issubset(t.discipline for t in selection):
            continue
        composition = values["required_composition"]
        if composition is not None and any(
            sum(t.discipline is sport for t in selection) != composition.get(sport, 0)
            for sport in Discipline
        ):
            continue
        caps = values["discipline_caps"]
        if caps and any(
            sum(
                (t.internal_planned_load.value for t in selection if t.discipline is s),
                Decimal(0),
            )
            > cap.value
            for s, cap in caps.items()
        ):
            continue
        total = sum((t.internal_planned_load.value for t in selection), Decimal(0))
        high = sum(
            (
                t.internal_planned_load.value
                for t in selection
                if t.intensity_bucket is IntensityBucket.HIGH
            ),
            Decimal(0),
        )
        if abs(target - total) >= minimum or high > budget:
            continue
        if not high_available:
            if high != 0:
                continue
        elif values["build_week"] != 4:
            if not budget * Decimal(".70") <= high <= budget * Decimal(".90"):
                continue
        elif high <= 0 or (z5_available and not any(zone5(t) for t in selection)):
            continue
        if values.get("feasible") is not None and not values["feasible"](selection):
            continue
        score = (
            abs(total - target),
            abs(high - budget),
            count,
            tuple(str(t.id) for t in selection),
        )
        if best_score is None or score < best_score:
            best, best_score = selection, score
    return canonical(best)


@pytest.mark.parametrize("seed", range(240))
def test_seeded_full_optimum(seed: int, bases: tuple[WorkoutTemplate, ...]) -> None:
    values = small_values(seed, bases)
    # With caps, use one load per sport so the historical key is sufficient for
    # the unrestricted oracle as well. Arbitrary caps get differential tests below.
    if values["discipline_caps"]:
        values["deck"] = tuple(
            replace(t, internal_planned_load=InternalLoad(Decimal(1)))
            for t in values["deck"]
        )
        values["prefix"] = ()
    expected = exhaustive(values)
    assert result("accepted", values) == expected
    assert result("optimized", values) == expected


@pytest.mark.parametrize("seed", range(240, 480))
def test_frozen_accepted_search(seed: int, bases: tuple[WorkoutTemplate, ...]) -> None:
    values = small_values(seed, bases)
    if seed % 4 == 0:
        # Arbitrary deterministic feasibility, including rejection of canonical
        # paths. Do not replace historical merging with a different optimum.
        values["feasible"] = lambda path: sum(t.id.int == 1 for t in path) == 1
    assert result("optimized", values) == result("accepted", values)
    values["deck"] = tuple(reversed(values["deck"]))
    assert result("optimized", values) == result("accepted", values)


def test_frozen_oracle_digest() -> None:
    assert sha256(ACCEPTED.read_bytes()).hexdigest() == ACCEPTED_SHA
    assert "_build_high_reachability" not in ACCEPTED.read_text()


def test_untracked_use_counts_do_not_split_historical_states(
    bases: tuple[WorkoutTemplate, ...],
) -> None:
    deck = tuple(
        replace(
            bases[0], id=UUID(int=i), internal_planned_load=InternalLoad(Decimal(1))
        )
        for i in (1, 2)
    )
    deck += (
        replace(
            bases[1], id=UUID(int=3), internal_planned_load=InternalLoad(Decimal(2))
        ),
    )
    values = {
        **small_values(1, bases),
        "deck": deck,
        "prefix": (),
        "target": InternalLoad(Decimal(3)),
        "required_count": 2,
        "required_disciplines": frozenset(t.discipline for t in deck),
        "maximum_uses": {t.id: 24 for t in deck},
        "feasible": lambda selection: any(t.id.int == 2 for t in selection),
    }
    assert result("accepted", values) is None
    assert result("optimized", values) is None


@pytest.mark.parametrize(
    "rounding",
    (
        decimal.ROUND_05UP,
        decimal.ROUND_CEILING,
        decimal.ROUND_DOWN,
        decimal.ROUND_FLOOR,
        decimal.ROUND_HALF_DOWN,
        decimal.ROUND_HALF_EVEN,
        decimal.ROUND_HALF_UP,
        decimal.ROUND_UP,
    ),
)
@pytest.mark.parametrize("precision", (1, 3, 8, 28, 50))
def test_decimal_contexts(
    rounding: str, precision: int, bases: tuple[WorkoutTemplate, ...]
) -> None:
    values = small_values(307, bases)
    values["deck"] = tuple(
        replace(t, internal_planned_load=InternalLoad(Decimal(v)))
        for t, v in zip(
            values["deck"],
            ("1.23456789", ".000000013", ".0100000009", "2.98765432"),
            strict=True,
        )
    )
    values["prefix"] = ()
    values["target"] = InternalLoad(Decimal("3.987654321"))
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = precision, rounding
        assert result("optimized", values) == result("accepted", values)


@pytest.mark.parametrize(
    "signal",
    (
        decimal.Clamped,
        decimal.Inexact,
        decimal.Rounded,
        decimal.Subnormal,
        decimal.Underflow,
    ),
)
def test_trap_fallback(
    signal: type[decimal.DecimalException], bases: tuple[WorkoutTemplate, ...]
) -> None:
    values = small_values(307, bases)
    values["deck"] = tuple(
        replace(t, internal_planned_load=InternalLoad(Decimal("1.23456789")))
        for t in values["deck"]
    )
    values["prefix"] = ()
    outcomes = []
    for variant in ("accepted", "optimized"):
        with localcontext() as ctx:
            ctx.prec = 3
            ctx.traps[signal] = True
            try:
                outcomes.append(result(variant, values))
            except decimal.DecimalException as error:
                outcomes.append(type(error).__name__)
    assert outcomes[0] == outcomes[1]


@pytest.mark.parametrize("exponent", (-8, -2, 1, 8))
def test_extreme_exponents_fall_back(
    exponent: int, bases: tuple[WorkoutTemplate, ...]
) -> None:
    values = small_values(309, bases)
    values["deck"] = tuple(
        replace(t, internal_planned_load=InternalLoad(Decimal(f"1e{exponent}")))
        for t in values["deck"]
    )
    values["prefix"] = ()
    with localcontext() as ctx:
        ctx.Emin, ctx.Emax = -4, 4
        ctx.traps[decimal.Overflow] = False
        assert result("optimized", values) == result("accepted", values)


@pytest.mark.parametrize("week", (1, 4))
@pytest.mark.parametrize(
    "high_load", ("0", "1.3999", "1.4", "1.8", "1.8001", "2", "2.0001")
)
def test_high_boundaries_and_z5(
    week: int, high_load: str, bases: tuple[WorkoutTemplate, ...]
) -> None:
    low = replace(
        bases[0], id=UUID(int=1), internal_planned_load=InternalLoad(Decimal(8))
    )
    high = replace(
        bases[1],
        id=UUID(int=2),
        internal_planned_load=InternalLoad(Decimal(high_load)),
        intensity_bucket=IntensityBucket.HIGH,
        reviewed_zone_numbers=frozenset({TrainingZone.ZONE_5}),
    )
    values = {
        **small_values(1, bases),
        "deck": (low, high),
        "prefix": (),
        "target": InternalLoad(Decimal(10)),
        "desired_high_fraction": Fraction(Decimal(".2")),
        "build_week": week,
        "required_count": 2,
        "required_disciplines": frozenset(t.discipline for t in (low, high)),
    }
    assert (
        result("optimized", values) == result("accepted", values) == exhaustive(values)
    )


def test_infeasible_high_count_and_missing_sport(
    bases: tuple[WorkoutTemplate, ...],
) -> None:
    values = small_values(333, bases)
    values["required_composition"] = {s: 4 for s in Discipline}
    values["required_disciplines"] = frozenset(Discipline)
    values["required_count"] = 3
    assert result("optimized", values) == result("accepted", values) is None


@pytest.mark.parametrize(
    "kind",
    (
        "equal_score",
        "repeat",
        "prefix",
        "limited_exhaustion",
        "missing_high",
        "missing_z5",
        "caps",
        "caps_infeasible",
        "unavailable",
        "high_count",
    ),
)
def test_explicit_exhaustive_cases(
    kind: str, bases: tuple[WorkoutTemplate, ...]
) -> None:
    low = replace(
        bases[0], id=UUID(int=1), internal_planned_load=InternalLoad(Decimal(2))
    )
    high = replace(
        bases[1],
        id=UUID(int=2),
        internal_planned_load=InternalLoad(Decimal(1)),
        intensity_bucket=IntensityBucket.HIGH,
        reviewed_zone_numbers=frozenset({TrainingZone.ZONE_5}),
    )
    alternate = replace(low, id=UUID(int=3))
    values = {
        **small_values(1, bases),
        "deck": (alternate, high, low),
        "prefix": (),
        "target": InternalLoad(Decimal(5)),
        "required_count": 3,
        "required_disciplines": frozenset({low.discipline, high.discipline}),
        "desired_high_fraction": Fraction(Decimal(".2")),
        "build_week": 4,
        "maximum_uses": {low.id: 24, alternate.id: 24, high.id: 24},
    }
    if kind == "prefix":
        values["prefix"] = (alternate,)
    if kind == "repeat":
        values["maximum_uses"][alternate.id] = 0
    if kind == "limited_exhaustion":
        values["maximum_uses"][low.id] = values["maximum_uses"][alternate.id] = 0
    if kind in ("missing_high", "missing_z5"):
        values["maximum_uses"][high.id] = 0
        if kind == "missing_z5":
            values["deck"] += (
                replace(high, id=UUID(int=4), reviewed_zone_numbers=frozenset()),
            )
    if kind.startswith("caps"):
        values["discipline_caps"] = {
            low.discipline: InternalLoad(
                Decimal(3 if kind.endswith("infeasible") else 4)
            ),
            high.discipline: InternalLoad(Decimal(1)),
        }
    if kind == "unavailable":
        values["feasible"] = lambda path: domain._schedule_is_feasible(
            selection=path,
            week_start=date(2026, 10, 26),
            available_dates=(),
            timezone_name="Europe/Amsterdam",
        )
    if kind == "high_count":
        values["feasible"] = lambda path: (
            sum(t.intensity_bucket is IntensityBucket.HIGH for t in path) >= 4
        )
    expected = exhaustive(values)
    assert result("accepted", values) == expected
    assert result("optimized", values) == expected
    if kind in ("equal_score", "repeat", "prefix", "caps"):
        assert expected is not None
    else:
        assert expected is None


def test_first_exact_layer_precedes_better_high_score_later(
    bases: tuple[WorkoutTemplate, ...],
) -> None:
    deck = tuple(
        replace(
            bases[sport],
            id=UUID(int=i + 1),
            internal_planned_load=InternalLoad(Decimal(load)),
            intensity_bucket=bucket,
        )
        for i, (sport, load, bucket) in enumerate(
            (
                (0, "6", IntensityBucket.LOW),
                (0, "5", IntensityBucket.LOW),
                (1, "4", IntensityBucket.HIGH),
                (1, "2.5", IntensityBucket.HIGH),
            )
        )
    )
    values = {
        **small_values(1, bases),
        "deck": deck,
        "prefix": (),
        "required_count": None,
        "target": InternalLoad(Decimal(10)),
        "desired_high_fraction": Fraction(Decimal(".5")),
        "build_week": 4,
        "required_disciplines": frozenset(t.discipline for t in deck),
    }
    expected = result("accepted", values)
    assert result("optimized", values) == expected
    assert [t["id"] for t in expected] == [str(deck[0].id), str(deck[2].id)]


def test_fallback_above_automatic_occurrence_bound(
    bases: tuple[WorkoutTemplate, ...],
) -> None:
    values = {
        **small_values(1, bases),
        "deck": bases[:2],
        "prefix": (),
        "required_count": 25,
        "target": InternalLoad(Decimal(1)),
        "required_disciplines": frozenset(t.discipline for t in bases[:2]),
    }
    # Force an immediate original bound rejection, avoiding a large fixture.
    values["maximum_uses"] = {t.id: 0 for t in values["deck"]}
    assert result("optimized", values) == result("accepted", values) is None


def test_accelerator_and_observers_are_transparent() -> None:
    deck = projection(source_records())
    values = scenario("build_1", deck)
    normal = domain.build_weekly_plan(**values)
    counts = Counters(None)
    with search_variant("optimized", counts):
        observed = domain.build_weekly_plan(**values)
    assert canonical(normal) == canonical(observed)
    assert (
        independent_checks(values, observed)["legacy_independent_constraints"] == "PASS"
    )
    assert 0 < counts.counts["exact_join_attempts"] <= 200000
    assert counts.counts["candidate_transitions"] == 0
    assert counts.snapshot()["peak_resident_bytes"] > 0


def test_isolated_prospective_beginner_policy_fixture() -> None:
    fixture = json.loads(
        (
            Path(__file__).parent / "fixtures/planner_performance/v6_budget_policy.json"
        ).read_text()
    )
    deck = projection(source_records())
    values = scenario("tri_zero", deck)
    automatic = domain.build_weekly_plan(**values)
    checks = independent_checks(values, automatic)
    assert automatic.planned_load.value == Decimal("45.1")
    assert automatic.target.target.value == Decimal("45.0")
    assert {w.snapshot.name for w in automatic.workouts} == {
        "TR-BIKE-022",
        "TR-RUN-027",
        "TR-SWIM-021",
    }
    assert checks["legacy_independent_constraints"] == "PASS"
    assert not checks["prospective_v6_diagnostics"]["within_target_budget"]
    assert checks["prospective_v6_diagnostics"]["beginner_one_each"]
    assert (
        checks["prospective_v6_diagnostics"]["per_sport_active_time"]["swim"]["status"]
        == "UNVERIFIED"
    )
    witness = domain.build_weekly_plan(**scenario("candidate", deck))
    assert witness.planned_load.value == Decimal("43.1")
    assert independent_checks(scenario("candidate", deck), witness)[
        "prospective_v6_diagnostics"
    ]["within_target_budget"]
    for name, plan in (("automatic", automatic), ("manual_witness", witness)):
        expected = fixture[name]
        assert plan.planned_load.value == Decimal(expected["total"])
        assert sorted(w.snapshot.name for w in plan.workouts) == sorted(
            expected["source_ids"]
        )
        assert expected["individual_athlete_suitability"] == "UNAPPROVED"
        assert not expected["approved_beginner_training_plan"]
        actual = independent_checks(values, plan)["prospective_v6_diagnostics"]
        assert actual["beginner_one_each"] == expected["one_session_per_sport"]
        assert {w.discipline for w in plan.workouts} == set(Discipline)
        for sport in Discipline:
            load = sum(
                (
                    w.snapshot.internal_planned_load.value
                    for w in plan.workouts
                    if w.discipline is sport and w.snapshot.internal_planned_load
                ),
                Decimal(0),
            )
            assert load == Decimal(expected["planned_sport_loads"][sport.value])
            assert Rational(load) / Rational(plan.planned_load.value) == Rational(
                expected["planned_sport_shares_exact"][sport.value]
            )
            active = actual["per_sport_active_time"][sport.value]
            if sport is Discipline.SWIM:
                assert active["status"] == "UNVERIFIED"
            else:
                assert active["status"] == "PASS"
                assert Rational(active["high_ratio"]) == 0
    assert (
        fixture["automatic"]["classification"]
        == "LEGACY_VALID / PROSPECTIVE_BUDGET_EXCEEDED"
    )
