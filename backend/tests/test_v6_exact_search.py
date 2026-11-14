"""Exact bounds and independent complete-week/scheduling differentials."""

from collections import Counter
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from itertools import product
from random import Random
from uuid import UUID

import pytest
from test_v6_automatic_selection import DATES, START, plan, target
from test_v6_multi_session import controls

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.planning.domain import PlanningConstraintError, ZoneCapability
from app.modules.planning.v6_frequency import SessionFrequency
from app.modules.planning.v6_search import (
    SearchWork,
    _bound,
    _Option,
    _Span,
    multi_options,
)
from app.modules.workouts.catalog import TrainingPhase, ZoneRequirement
from app.modules.workouts.joren_v6_official import V6Template, official_catalog
from benchmarks.v6_search_oracle import exhaustive, source_times


@pytest.fixture(scope="module")
def catalog() -> tuple[V6Template, ...]:
    return official_catalog()


@pytest.mark.parametrize("seed", range(60))
def test_every_box_bound_is_optimistic_and_every_leaf_exact(seed: int) -> None:
    rng = Random(seed)
    weights = (Fraction(1, 2), Fraction(3, 10), Fraction(1, 5))
    box = []
    for sport in range(3):
        count = rng.randrange(4)
        options = tuple(
            _Option(
                (), Fraction(load, 17), count, min(count, 2), (f"{sport}:{i}",) * count
            )
            for i, load in enumerate(sorted(rng.randrange(60) for _ in range(4)))
        )
        first = rng.randrange(4)
        stop = rng.randrange(first + 1, 5)
        box.append(_Span(options, first, stop))
    budget = Fraction(rng.randrange(180), 17)
    bound = _bound(tuple(box), budget, weights)
    scores = []
    for options in product(*(s.options[s.first : s.stop] for s in box)):
        total = sum((o.load for o in options), Fraction(0))
        if total > budget:
            continue
        score = (
            -sum(o.count > 0 for o in options),
            -sum(o.requested for o in options),
            sum(
                (abs(o.load / total - w) for o, w in zip(options, weights)), Fraction(0)
            )
            if total
            else Fraction(0),
            -total,
            tuple(sorted(k for o in options for k in o.identities)),
        )
        scores.append(score)
    if scores:
        assert bound is not None and bound <= min(scores)
        if all(s.stop - s.first == 1 for s in box):
            assert bound == scores[0]
    elif bound is None:
        assert sum((s.low for s in box), Fraction(0)) > budget


@pytest.mark.parametrize("seed", range(48))
def test_independent_restricted_week_oracle(
    catalog: tuple[V6Template, ...], seed: int
) -> None:
    rng = Random(seed)
    phase = tuple(TrainingPhase)[seed % len(tuple(TrainingPhase))]
    small = tuple(
        t
        for s in Discipline
        for t in rng.sample(
            [
                row
                for row in catalog
                if row.discipline is s
                and phase in row.source_revision.phases
                and row.source_workout_id != "TR-BIKE-013"
            ],
            2,
        )
    )
    c = replace(
        controls(),
        authorized_target=target(phase, str(rng.randint(30, 200))),
        session_frequency=tuple(
            SessionFrequency(s, n, "TEST_ONLY independent restricted oracle", n)
            for s in Discipline
            for n in (rng.randrange(3),)
        ),
        maximum_uses=tuple((t.id, rng.randrange(3)) for t in small),
    )
    assert c.authorized_target is not None
    c = replace(
        c,
        authorized_target=replace(
            c.authorized_target,
            build_week=1 if seed % 3 == 0 else c.authorized_target.build_week,
            discipline_caps={Discipline.RUN: InternalLoad(Decimal(50))}
            if seed % 5 == 0
            else {},
        ),
    )
    goals = frozenset(Discipline) if seed % 4 else frozenset({Discipline.RUN})
    capabilities = {s: ZoneCapability(frozenset(ZoneRequirement)) for s in Discipline}
    if seed % 7 == 0:
        capabilities.pop(Discipline.SWIM)
    injuries = frozenset({Discipline.BIKE}) if seed % 6 == 0 else frozenset()
    low_only = frozenset({Discipline.RUN}) if seed % 8 == 0 else frozenset()
    dates = DATES[:1] if seed % 3 == 0 else DATES[::2]
    assert c.authorized_target is not None
    expected = exhaustive(
        catalog=small,
        target=c.authorized_target,
        controls=c,
        goals=goals,
        capabilities=capabilities,
        injuries=injuries,
        low_only=low_only,
        dates=dates,
        week_start=START,
        timezone_name="Europe/Amsterdam",
    )
    actual = plan(
        small,
        controls=c,
        goal_disciplines=goals,
        zone_capabilities=capabilities,
        confirmed_injuries=injuries,
        low_only_disciplines=low_only,
        available_dates=dates,
    )
    assert sorted(str(t.id) for t in actual.templates) == expected["template_ids"]


def test_scheduling_failure_continues_to_next_exact_candidate(
    catalog: tuple[V6Template, ...],
) -> None:
    rows = tuple(
        t for t in catalog if t.source_workout_id in ("TR-RUN-017", "TR-RUN-003")
    )
    c = controls("500", run=8, bike=0, swim=0)
    assert c.authorized_target is not None
    dates = DATES[:2]
    expected = exhaustive(
        catalog=rows,
        target=c.authorized_target,
        controls=c,
        goals=frozenset({Discipline.RUN}),
        capabilities={Discipline.RUN: ZoneCapability(frozenset(ZoneRequirement))},
        week_start=START,
        timezone_name="Europe/Amsterdam",
        dates=dates,
    )
    actual = plan(
        rows,
        controls=c,
        goal_disciplines=frozenset({Discipline.RUN}),
        available_dates=dates,
    )
    assert sorted(str(t.id) for t in actual.templates) == expected["template_ids"]
    assert sum(t.source_workout_id == "TR-RUN-017" for t in actual.templates) == 1
    assert len(actual.templates) == 8


@pytest.mark.parametrize("fixed_day", (DATES[0], DATES[-1]))
def test_independent_retained_repeat_date_and_composition(
    catalog: tuple[V6Template, ...],
    fixed_day: object,
) -> None:
    from datetime import date

    assert isinstance(fixed_day, date)
    rows = tuple(
        t
        for t in catalog
        if t.source_workout_id
        in ("TR-RUN-003", "TR-RUN-025", "TR-BIKE-023", "TR-SWIM-021")
    )
    retained = next(t for t in rows if t.source_workout_id == "TR-RUN-025")
    c = replace(controls("200"), maximum_uses=((retained.id, 2),))
    ids = (UUID(int=101), UUID(int=102))
    prefix = (retained.id, retained.id)
    fixed = {ids[0]: fixed_day, ids[1]: DATES[3]}
    assert c.authorized_target is not None
    required = {Discipline.RUN: 2, Discipline.BIKE: 2, Discipline.SWIM: 1}
    expected = exhaustive(
        catalog=rows,
        target=c.authorized_target,
        controls=c,
        goals=frozenset(Discipline),
        capabilities={
            s: ZoneCapability(frozenset(ZoneRequirement)) for s in Discipline
        },
        week_start=START,
        timezone_name="Europe/Amsterdam",
        dates=DATES,
        prefix=prefix,
        prefix_ids=ids,
        fixed=fixed,
        required=required,
    )
    actual = plan(
        rows,
        controls=c,
        prefix=prefix,
        prefix_occurrence_ids=ids,
        fixed_occurrence_dates=fixed,
        required_composition=required,
    )
    assert sorted(str(t.id) for t in actual.templates) == expected["template_ids"]
    assert {
        w.occurrence_id: w.scheduled_date
        for w in actual.workouts
        if w.occurrence_id in ids
    } == fixed


def test_lazy_full_iteration_has_independent_rank_order_and_no_identity_merge(
    catalog: tuple[V6Template, ...],
) -> None:
    rows = tuple(
        t
        for t in catalog
        if t.source_workout_id
        in ("TR-RUN-003", "TR-RUN-025", "TR-BIKE-023", "TR-SWIM-021")
    )
    c = controls("200")
    assert c.authorized_target is not None
    options = list(
        multi_options(
            deck=tuple(sorted(rows, key=lambda t: str(t.id))),
            retained=(),
            goals=frozenset(Discipline),
            excluded=frozenset(),
            target=c.authorized_target,
            controls=c,
            work=SearchWork(200000),
            required_composition=None,
        )
    )
    scores = []
    for option in options:
        counts = Counter(t.discipline for t in option)
        shares = {
            s: sum(
                (Fraction(t.official.value) for t in option if t.discipline is s),
                Fraction(0),
            )
            for s in Discipline
        }
        total = sum(shares.values(), Fraction(0))
        scores.append(
            (
                -len(counts),
                -sum(min(counts[r.sport], r.requested) for r in c.session_frequency),
                sum(
                    (
                        abs(shares[s] / total - w)
                        for s, w in (
                            (Discipline.RUN, Fraction(3, 10)),
                            (Discipline.BIKE, Fraction(1, 2)),
                            (Discipline.SWIM, Fraction(1, 5)),
                        )
                    ),
                    Fraction(0),
                )
                if total
                else Fraction(0),
                -total,
                tuple(sorted(str(t.id) for t in option)),
            )
        )
        for s in Discipline:
            lo = sum(
                (source_times(t, c)[0] for t in option if t.discipline is s),
                Fraction(0),
            )
            hi = sum(
                (source_times(t, c)[1] for t in option if t.discipline is s),
                Fraction(0),
            )
            assert 5 * hi <= lo + hi
    assert scores == sorted(scores)
    assert len({score[-1] for score in scores}) == len(scores)
    assert any(len({t.id for t in option}) < len(option) for option in options)


def test_exhaustion_after_scheduling_failure_never_returns_a_truncated_week(
    catalog: tuple[V6Template, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.planning import v6_selection

    def cannot_place(**kwargs: object) -> object:
        raise PlanningConstraintError("rest_or_anti_stack_unsatisfied", "TEST_ONLY")

    monkeypatch.setattr(v6_selection, "schedule_workouts", cannot_place)
    with pytest.raises(PlanningConstraintError, match="bounded selection") as error:
        plan(catalog, controls=replace(controls("300"), maximum_search_nodes=1800))
    assert error.value.code == "v6_search_incomplete"
