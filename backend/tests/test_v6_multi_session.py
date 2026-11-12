"""Test-only frequency authorizations; real immutable approved source workloads."""

from collections import Counter
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations_with_replacement, product
from random import Random
from uuid import UUID, uuid4

import pytest
from test_v6_automatic_selection import DATES, START, plan, target

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.physiology.planned_v6 import sum_official
from app.modules.planning.domain import PlanningConstraintError
from app.modules.planning.v6_frequency import SessionFrequency
from app.modules.planning.v6_selection import (
    V6Controls,
    active_times,
    week_valid,
)
from app.modules.planning.v6_service import (
    controls_json,
    effective_controls,
    frozen_controls,
)
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.joren_v6_official import V6Template, official_catalog


@pytest.fixture(scope="module")
def catalog() -> tuple[V6Template, ...]:
    return official_catalog()


def controls(
    budget: str = "100", run: int = 2, bike: int = 2, swim: int = 1
) -> V6Controls:
    return V6Controls(
        athlete_scope=UUID(int=1),
        week_scope=START,
        authorized_target=target(TrainingPhase.BASE, budget),
        session_frequency=tuple(
            SessionFrequency(
                s, n, "TEST_ONLY requested frequency; not product policy", n
            )
            for s, n in (
                (Discipline.RUN, run),
                (Discipline.BIKE, bike),
                (Discipline.SWIM, swim),
            )
        ),
    )


@pytest.mark.parametrize(
    "run,bike,swim", ((2, 2, 1), (2, 1, 1), (2, 0, 0), (0, 2, 0), (0, 0, 2))
)
def test_actual_authorized_sessions(
    catalog: tuple[V6Template, ...], run: int, bike: int, swim: int
) -> None:
    c = controls(run=run, bike=bike, swim=swim)
    goals = frozenset(r.sport for r in c.session_frequency if r.requested)
    p = plan(catalog, controls=c, goal_disciplines=goals)
    assert Counter(t.discipline for t in p.templates) == {
        s: n
        for s, n in (
            (Discipline.RUN, run),
            (Discipline.BIKE, bike),
            (Discipline.SWIM, swim),
        )
        if n
    }
    assert len({w.occurrence_id for w in p.workouts}) == run + bike + swim
    assert p.planned_load.value <= c.authorized_target.target.value  # type: ignore[union-attr]
    assert week_valid(p.templates, p.target, c)
    assert all(w.scheduled_date in DATES for w in p.workouts)
    assert p.selection_version == "joren-v6-multi-session-selection-1"
    assert p.workouts == plan(catalog, controls=c, goal_disciplines=goals).workouts


def test_maximum_is_not_target_and_legacy_is_unchanged(
    catalog: tuple[V6Template, ...],
) -> None:
    old = plan(catalog, "100")
    c = replace(
        controls(),
        session_frequency=tuple(
            replace(r, maximum=5, target=None) for r in controls().session_frequency
        ),
    )
    new = plan(catalog, controls=c)
    assert new.templates == old.templates
    assert len(new.workouts) == 3
    assert all(n == 1 for n in Counter(t.discipline for t in new.templates).values())


@pytest.mark.parametrize("budget", ("0", "10", "25", "45"))
def test_partial_target_and_zero_outcome(
    catalog: tuple[V6Template, ...], budget: str
) -> None:
    c = controls(budget)
    p = plan(catalog, controls=c)
    assert len(p.workouts) < 5
    assert p.planned_load.value <= Decimal(budget)
    assert any(
        w.code == ("partial_week" if p.workouts else "no_feasible_workouts_rest")
        for w in p.warnings
    )
    if budget == "0":
        assert p.workouts == ()


def test_retained_occurrences_consume_count_budget_repeat_and_keep_dates(
    catalog: tuple[V6Template, ...],
) -> None:
    easy = next(t for t in catalog if t.source_workout_id == "TR-RUN-003")
    c = controls(run=2, bike=0, swim=0)
    identities = (uuid4(), uuid4())
    p = plan(
        catalog,
        controls=c,
        prefix=(easy.id, easy.id),
        prefix_occurrence_ids=identities,
        fixed_occurrence_dates={identities[0]: DATES[0], identities[1]: DATES[-1]},
    )
    assert len(p.workouts) == 2
    assert {w.occurrence_id: w.scheduled_date for w in p.workouts} == {
        identities[0]: DATES[0],
        identities[1]: DATES[-1],
    }
    # One template is a repeated logical occurrence, never duplicate physical rows.
    assert [t.id for t in p.templates] == [easy.id, easy.id]
    extended = plan(
        (easy,),
        controls=c,
        goal_disciplines=frozenset({Discipline.RUN}),
        prefix=(easy.id,),
        prefix_occurrence_ids=identities[:1],
        fixed_occurrence_dates={identities[0]: DATES[0]},
    )
    assert len(extended.workouts) == 2
    assert (
        next(
            w for w in extended.workouts if w.occurrence_id == identities[0]
        ).scheduled_date
        == DATES[0]
    )
    assert len({w.occurrence_id for w in extended.workouts}) == 2
    for invalid in (
        replace(c, maximum_uses=((easy.id, 1),)),
        controls(run=1, bike=0, swim=0),
        controls("1", run=2, bike=0, swim=0),
    ):
        with pytest.raises(PlanningConstraintError):
            plan(catalog, controls=invalid, prefix=(easy.id, easy.id))


def test_repetition_restricted_and_distinct_instances(
    catalog: tuple[V6Template, ...],
) -> None:
    easy = next(t for t in catalog if t.source_workout_id == "TR-RUN-003")
    c = controls(run=2, bike=0, swim=0)
    p = plan((easy,), controls=replace(c, maximum_uses=((easy.id, 2),)))
    assert len(p.workouts) == 2 and len({w.occurrence_id for w in p.workouts}) == 2
    p = plan((easy,), controls=replace(c, maximum_uses=((easy.id, 1),)))
    assert len(p.workouts) == 1
    with pytest.raises(PlanningConstraintError):
        plan(
            (easy,),
            controls=replace(c, maximum_uses=((easy.id, 1),)),
            selected_template_ids=(easy.id, easy.id),
        )


def test_exact_official_decimal_boundary_across_occurrences(
    catalog: tuple[V6Template, ...],
) -> None:
    easy = next(t for t in catalog if t.source_workout_id == "TR-RUN-003")
    exact = sum_official((easy.official.value, easy.official.value))
    for precision in (6, 28, 70):
        with localcontext() as ctx:
            ctx.prec = precision
            p = plan((easy,), controls=controls(str(exact), run=2, bike=0, swim=0))
            assert len(p.workouts) == 2 and p.planned_load.value == exact
    smaller = Fraction(exact) - Fraction(1, 10**60)
    with localcontext() as ctx:
        ctx.prec = 100
        budget = Decimal(smaller.numerator) / Decimal(smaller.denominator)
    p = plan((easy,), controls=controls(str(budget), run=2, bike=0, swim=0))
    assert len(p.workouts) == 1


@pytest.mark.parametrize("sport", tuple(Discipline))
def test_limited_dates_allow_low_same_day(
    catalog: tuple[V6Template, ...], sport: Discipline
) -> None:
    c = controls(
        run=int(sport is Discipline.RUN) * 2,
        bike=int(sport is Discipline.BIKE) * 2,
        swim=int(sport is Discipline.SWIM) * 2,
    )
    p = plan(catalog, controls=c, available_dates=(DATES[0],))
    assert len(p.workouts) == 2
    assert {w.scheduled_date for w in p.workouts} == {DATES[0]}


def test_recovery_spacing_and_high_aggregation(catalog: tuple[V6Template, ...]) -> None:
    high = next(t for t in catalog if t.source_workout_id == "TR-RUN-017")
    easy = next(t for t in catalog if t.source_workout_id == "TR-RUN-003")
    ids = (high.id, high.id, easy.id, easy.id, easy.id, easy.id, easy.id, easy.id)
    c = controls("500", run=8, bike=0, swim=0)
    assert week_valid(tuple([high, high] + [easy] * 6), c.authorized_target, c)  # type: ignore[arg-type]
    p = plan(catalog, controls=c, selected_template_ids=ids)
    days = [w.scheduled_date for w in p.workouts if w.snapshot.template_id == high.id]
    assert (days[1] - days[0]).days >= 3
    with pytest.raises(PlanningConstraintError):
        plan(
            catalog,
            controls=c,
            selected_template_ids=ids,
            available_dates=(DATES[0], DATES[1]),
        )


def test_twenty_percent_equality_and_excess() -> None:
    # Exact rational active seconds; test-only prescribed swim times are scoped.
    # Use real source events and solve LOW duration to exercise the exact boundary.
    high = next(t for t in official_catalog() if t.source_workout_id == "TR-RUN-017")
    low = next(t for t in official_catalog() if t.source_workout_id == "TR-RUN-003")
    lo, hi, _ = active_times(high, V6Controls())
    elo, _, _ = active_times(low, V6Controls())
    needed = (hi * 4 - lo) / elo
    rows = (high,) * needed.denominator + (low,) * needed.numerator
    assert sum(active_times(t, V6Controls())[1] for t in rows) * 5 == sum(
        sum(active_times(t, V6Controls())[:2]) for t in rows
    )
    t = target(TrainingPhase.BASE, "100000")
    assert week_valid(rows, t, V6Controls())
    assert not week_valid(rows + (high,), t, V6Controls())


def test_injury_capability_and_sport_caps(catalog: tuple[V6Template, ...]) -> None:
    c = controls()
    p = plan(catalog, controls=c, confirmed_injuries=frozenset({Discipline.RUN}))
    assert not any(t.discipline is Discipline.RUN for t in p.templates)
    p = plan(catalog, controls=c, zone_capabilities={})
    assert not p.workouts
    assert c.authorized_target is not None
    p = plan(
        catalog,
        controls=replace(
            c,
            authorized_target=replace(
                c.authorized_target,
                discipline_caps={Discipline.RUN: InternalLoad(Decimal(0))},
            ),
        ),
    )
    assert not any(t.discipline is Discipline.RUN for t in p.templates)


def test_search_exhaustion_and_duplicate_catalog_fail_closed(
    catalog: tuple[V6Template, ...],
) -> None:
    with pytest.raises(PlanningConstraintError) as error:
        plan(catalog, controls=replace(controls(), maximum_search_nodes=1))
    assert error.value.code == "v6_search_incomplete"
    with pytest.raises(ValueError, match="ambiguous"):
        plan(catalog + (catalog[0],), controls=controls())


def test_authorization_scope_restart_and_no_expansion() -> None:
    import json

    c = controls()
    restored = frozen_controls(json.loads(controls_json(c)))
    assert restored.session_frequency == c.session_frequency
    assert restored.athlete_scope == c.athlete_scope and restored.week_scope == START
    increased = replace(
        c,
        session_frequency=tuple(
            replace(r, maximum=4, target=4) for r in c.session_frequency
        ),
    )
    assert (
        effective_controls(json.loads(controls_json(c)), increased).session_frequency
        == c.session_frequency
    )
    limited = replace(
        c,
        session_frequency=(
            SessionFrequency(
                Discipline.RUN,
                0,
                "TEST_ONLY newly tightened ceiling",
                0,
            ),
        ),
    )
    old = effective_controls(json.loads(controls_json(V6Controls())), limited)
    assert old.session_frequency[0].maximum == 0
    assert old.session_frequency[0].requested == 0
    with pytest.raises(ValueError, match="scope"):
        replace(c, athlete_scope=None)
    with pytest.raises(ValueError):
        SessionFrequency(Discipline.RUN, 2, "TEST_ONLY", 3)
    with pytest.raises(ValueError):
        SessionFrequency(Discipline.RUN, 2, "TEST_ONLY", 2, "mandatory_minimum")


@pytest.mark.parametrize("seed", range(30))
def test_independent_small_exhaustive_oracle(
    catalog: tuple[V6Template, ...], seed: int
) -> None:
    # Independent enumeration including permutations-with-replacement, whole-week
    # totals, counts, source segments, repeat restrictions and actual scheduling.
    # No production ranking, eligibility, HIGH predicate or enumerator is called.
    from app.modules.workouts.joren_draft import TimedZone, WallRest

    rng = Random(seed)
    by_sport = [
        [
            t
            for t in catalog
            if t.discipline is s
            and TrainingPhase.BASE in t.source_revision.phases
            and t.source_workout_id != "TR-BIKE-013"
        ]
        for s in Discipline
    ]
    small = tuple(t for values in by_sport for t in rng.sample(values, 2))
    c = replace(
        controls(str(rng.randint(35, 120))),
        maximum_uses=tuple((t.id, rng.randint(1, 2)) for t in small),
    )
    groups = []
    limits = dict(c.maximum_uses)
    for s in Discipline:
        options = tuple(t for t in small if t.discipline is s)
        maximum = next(r.target for r in c.session_frequency if r.sport is s)
        groups.append(
            [
                combo
                for n in range((maximum or 0) + 1)
                for combo in combinations_with_replacement(options, n)
            ]
        )
    contenders = []
    for group in product(*groups):
        rows = sum(group, ())
        if any(Counter(t.id for t in rows)[k] > n for k, n in limits.items()):
            continue
        total = sum((Fraction(t.official.value) for t in rows), Fraction(0))
        if total > Fraction(c.authorized_target.target.value):  # type: ignore[union-attr]
            continue
        valid = True
        for sport in Discipline:
            low = high = Fraction(0)
            for t in rows:
                if t.discipline is not sport:
                    continue
                for event in t.source_revision.predecessor.events:
                    if isinstance(event, WallRest):
                        continue
                    seconds = (
                        Fraction(event.seconds)
                        if isinstance(event, TimedZone)
                        else Fraction(event.meters)
                        * tuple(
                            map(Fraction, ("130.2", "120", "109.8", "100.2", "90"))
                        )[event.zone - 1]
                        / 100
                    )
                    if event.zone <= 2:
                        low += seconds
                    else:
                        high += seconds
            if high * 5 > low + high:
                valid = False
        if not valid:
            continue
        shares = {
            s: sum(
                (Fraction(t.official.value) for t in rows if t.discipline is s),
                Fraction(0),
            )
            for s in Discipline
        }
        distance = (
            sum(
                (
                    abs(shares[s] / total - ratio)
                    for s, ratio in (
                        (Discipline.RUN, Fraction(3, 10)),
                        (Discipline.BIKE, Fraction(1, 2)),
                        (Discipline.SWIM, Fraction(1, 5)),
                    )
                ),
                Fraction(0),
            )
            if total
            else Fraction(0)
        )
        score = (
            -len({t.discipline for t in rows}),
            -sum(
                min(sum(t.discipline is r.sport for t in rows), r.requested)
                for r in c.session_frequency
            ),
            distance,
            -total,
            tuple(sorted(str(t.id) for t in rows)),
        )
        contenders.append((score, rows))
    expected = min(contenders, key=lambda x: x[0])[1]
    actual = plan(small, controls=c)
    assert Counter(t.id for t in actual.templates) == Counter(t.id for t in expected)
