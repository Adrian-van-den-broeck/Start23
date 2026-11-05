"""Independent source arithmetic, exhaustive optimum and actual V6 plan checks."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from itertools import product
from pathlib import Path
from uuid import uuid4

import pytest

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.physiology.planned_v6 import calculate_v6, sum_official
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
    week_valid,
)
from app.modules.workouts.catalog import TrainingPhase, ZoneRequirement
from app.modules.workouts.joren_draft import SwimDistance, TimedZone, WallRest
from app.modules.workouts.joren_v6_official import V6Template, official_catalog

D = Decimal
START = date(2026, 10, 26)
DATES = tuple(START + timedelta(days=i) for i in range(7))


@pytest.fixture(scope="module")
def catalog() -> tuple[V6Template, ...]:
    return official_catalog()


def target(phase: TrainingPhase, budget: str) -> PlanningTarget:
    return PlanningTarget(
        phase,
        PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
        InternalLoad(D(budget)),
        build_week=4 if phase is TrainingPhase.BUILD else None,
    )


def plan(
    catalog: tuple[V6Template, ...],
    budget: str = "45",
    phase: TrainingPhase = TrainingPhase.BASE,
    **kwargs: object,
) -> V6Plan:
    values = dict(
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
        available_dates=DATES,
        controls=V6Controls(authorized_target=target(phase, budget)),
    )
    values.update(kwargs)
    return build_v6_plan(**values)  # type: ignore[arg-type]


def independent_load(t: V6Template) -> tuple[Fraction, Decimal]:
    # Independent formula from immutable original segments, no production helper.
    anchors = tuple(map(Fraction, (".55", ".75", ".88", ".98", "1.15")))
    paces = tuple(map(Fraction, ("2.17", "2", "1.83", "1.67", "1.50")))
    factor = {"run": Fraction("1.15"), "bike": Fraction(1), "swim": Fraction(".9")}[
        t.discipline.value
    ]
    total = Fraction(0)
    for e in t.source_revision.predecessor.events:
        if isinstance(e, WallRest):
            continue
        minutes = (
            Fraction(e.meters) * paces[e.zone - 1] / 100
            if isinstance(e, SwimDistance)
            else Fraction(e.seconds) / 60
        )
        total += minutes * anchors[e.zone - 1] ** 2
    total *= Fraction(5, 3) * factor
    with localcontext(Context(prec=50)):
        return total, D(total.numerator) / D(total.denominator)


@pytest.mark.parametrize("index", range(77))
def test_independent_77_official_values(
    catalog: tuple[V6Template, ...], index: int
) -> None:
    row = catalog[index]
    rational, value = independent_load(row)
    assert row.official.value == value
    assert Fraction(row.official.numerator, row.official.denominator) == rational
    assert row.official.method == "joren-v6-planned-if2-1"
    assert row.internal_planned_load and row.internal_planned_load.value == value
    assert row.id == row.source_revision.revision_id
    assert row.activation_status == "INACTIVE"
    assert (
        row.source_revision.official_method is None
    )  # historical preparation unchanged
    with localcontext(Context(prec=50)):
        assert value.quantize(D(".1")) == D(
            row.source_revision.predecessor.load.original_displayed_value
        )


@pytest.mark.parametrize(
    "phase,budget",
    (
        (TrainingPhase.BASE, "45"),
        (TrainingPhase.BUILD, "45"),
        (TrainingPhase.RECOVERY, "25.86"),
        (TrainingPhase.TAPER, "15.085"),
        (TrainingPhase.BASE, "10"),
        (TrainingPhase.BASE, "0"),
    ),
)
def test_independent_exhaustive_optimum(
    catalog: tuple[V6Template, ...], phase: TrainingPhase, budget: str
) -> None:
    result = plan(catalog, budget, phase)
    candidates = []
    for sport in (Discipline.BIKE, Discipline.RUN, Discipline.SWIM):
        allowed = []
        for t in catalog:
            if (
                t.discipline is not sport
                or phase not in t.source_revision.phases
                or t.source_workout_id == "TR-BIKE-013"
            ):
                continue
            low = high = Fraction(0)
            for e in t.source_revision.predecessor.events:
                if isinstance(e, WallRest):
                    continue
                sec = (
                    Fraction(e.seconds)
                    if isinstance(e, TimedZone)
                    else Fraction(e.meters)
                    * tuple(map(Fraction, ("130.2", "120", "109.8", "100.2", "90")))[
                        e.zone - 1
                    ]
                    / 100
                )
                if e.zone <= 2:
                    low += sec
                else:
                    high += sec
            if high * 5 <= low + high:
                allowed.append(t)
        candidates.append([None, *allowed])
    expected = []
    for combo in product(*candidates):
        rows = tuple(t for t in combo if t is not None)
        values = [Fraction(independent_load(t)[1]) for t in rows]
        total = sum(values, Fraction(0))
        if total > Fraction(budget):
            continue
        shares = {
            s: sum((v for t, v in zip(rows, values) if t.discipline is s), Fraction(0))
            for s in Discipline
        }
        distance = (
            sum(
                (
                    abs(shares[s] / total - r)
                    for s, r in (
                        (Discipline.BIKE, Fraction(1, 2)),
                        (Discipline.RUN, Fraction(3, 10)),
                        (Discipline.SWIM, Fraction(1, 5)),
                    )
                ),
                Fraction(0),
            )
            if total
            else Fraction(0)
        )
        expected.append(
            (
                (-len(rows), distance, -total, tuple(sorted(str(t.id) for t in rows))),
                rows,
            )
        )
    expected_rows = min(expected, key=lambda v: v[0])[1]
    assert {t.id for t in result.templates} == {t.id for t in expected_rows}
    assert result.planned_load.value == sum_official(
        tuple(t.official.value for t in expected_rows)
    )
    assert result.planned_load.value <= D(budget)
    assert result.optimality == "EXHAUSTIVE_GLOBAL_OPTIMUM"
    assert len(result.workouts) == len(expected_rows)
    assert all(w.scheduled_date in DATES for w in result.workouts)


def test_real_selected_examples_and_soft_allocation(
    catalog: tuple[V6Template, ...],
) -> None:
    p = plan(catalog)
    assert [t.source_workout_id for t in p.templates] == [
        "TR-BIKE-023",
        "TR-RUN-025",
        "TR-SWIM-021",
    ]
    assert p.planned_load.value < D(40)
    assert {
        t.discipline for t in plan(catalog, "25.86", TrainingPhase.RECOVERY).templates
    } == {Discipline.RUN, Discipline.BIKE}
    assert {
        t.discipline for t in plan(catalog, "15.085", TrainingPhase.TAPER).templates
    } == {Discipline.RUN, Discipline.SWIM}
    assert not plan(catalog, "1").workouts
    assert len(plan(catalog, "10").workouts) == 1
    assert p.high_intensity_percent == 0


def test_precision_boundary_and_historical_overshoot(
    catalog: tuple[V6Template, ...],
) -> None:
    ids = tuple(
        t.id
        for name in ("TR-BIKE-022", "TR-RUN-027", "TR-SWIM-021")
        for t in catalog
        if t.source_workout_id == name
    )
    with pytest.raises(PlanningConstraintError):
        plan(catalog, selected_template_ids=ids)
    p = plan(catalog, "45.125", selected_template_ids=ids)
    assert p.planned_load.value == D("45.125")
    with pytest.raises(PlanningConstraintError):
        plan(
            catalog,
            "45.124999999999999999999999999999999999999999999999",
            selected_template_ids=ids,
        )
    with localcontext() as ctx:
        ctx.prec = 3
        rows = official_catalog()
        assert [t.official.value for t in rows] == [t.official.value for t in catalog]
        assert plan(rows).planned_load.value == plan(catalog).planned_load.value


def test_partial_injury_capability_goals_and_dates(
    catalog: tuple[V6Template, ...],
) -> None:
    p = plan(catalog, confirmed_injuries=frozenset({Discipline.RUN}))
    assert p.workouts and all(w.discipline is not Discipline.RUN for w in p.workouts)
    caps = {
        s: ZoneCapability(frozenset(ZoneRequirement))
        for s in (Discipline.RUN, Discipline.BIKE)
    }
    assert {
        w.discipline for w in plan(catalog, zone_capabilities=caps).workouts
    } == set(caps)
    for sport in Discipline:
        p = plan(catalog, goal_disciplines=frozenset({sport}))
        assert len(p.workouts) == 1 and p.workouts[0].discipline is sport
    assert (
        len(plan(catalog, available_dates=(START,)).workouts) == 3
    )  # existing consolidated-day contract
    assert not plan(catalog, available_dates=()).workouts


def test_long_duration_targeted_exclusion(catalog: tuple[V6Template, ...]) -> None:
    long = next(t for t in catalog if t.source_workout_id == "TR-BIKE-013")
    p = plan(catalog, "500", TrainingPhase.TAPER)
    assert (long.id, "individual_420_minute_duration_evidence_missing") in p.exclusions
    assert p.workouts
    with pytest.raises(PlanningConstraintError):
        plan(catalog, "500", TrainingPhase.TAPER, selected_template_ids=(long.id,))
    with pytest.raises(ValueError, match="athlete_week_scope"):
        V6Controls(duration_evidence=((long.id, "test"),))


def test_swim_estimate_and_authoritative_twenty_percent(
    catalog: tuple[V6Template, ...],
) -> None:
    swim = next(t for t in catalog if t.source_workout_id == "TR-SWIM-010")
    events = swim.source_revision.predecessor.events
    lows = sum(not isinstance(e, WallRest) and e.zone <= 2 for e in events)
    highs = sum(not isinstance(e, WallRest) and e.zone > 2 for e in events)
    seconds = tuple(
        D(1) if isinstance(e, WallRest) else D(highs * 4) if e.zone <= 2 else D(lows)
        for e in events
    )
    controls = V6Controls(
        athlete_scope=uuid4(),
        week_scope=START,
        authorized_target=target(TrainingPhase.BUILD, "100"),
        prescribed_swim_seconds=(
            (swim.id, seconds, "TEST_ONLY:independent-prescription"),
        ),
    )
    p = plan(catalog, controls=controls, selected_template_ids=(swim.id,))
    assert p.estimated_sports == frozenset()
    assert active_times(swim, controls)[1] * 5 == sum(active_times(swim, controls)[:2])
    changed = list(seconds)
    changed[
        next(
            i
            for i, e in enumerate(events)
            if not isinstance(e, WallRest) and e.zone > 2
        )
    ] += 1
    with pytest.raises(PlanningConstraintError):
        plan(
            catalog,
            controls=replace(
                controls,
                prescribed_swim_seconds=((swim.id, tuple(changed), "TEST_ONLY"),),
            ),
            selected_template_ids=(swim.id,),
        )
    p = plan(catalog)
    assert p.estimated_sports == {Discipline.SWIM}
    assert (
        next(t for t in p.templates if t.discipline is Discipline.SWIM).duration_minutes
        is None
    )
    assert Discipline.SWIM not in {
        w.discipline
        for w in plan(
            catalog,
            controls=V6Controls(
                estimate_swim_for_preview=False,
                authorized_target=target(TrainingPhase.BASE, "45"),
            ),
        ).workouts
    }


def test_repeats_complete_week_and_search_bound(
    catalog: tuple[V6Template, ...],
) -> None:
    lookup = {t.source_workout_id: t for t in catalog}
    high = lookup["TR-RUN-017"]
    easy = lookup["TR-RUN-003"]
    ids = (high.id, easy.id, easy.id, easy.id)
    p = plan(catalog, "200", selected_template_ids=ids)
    assert len(p.workouts) == 4 and len({w.occurrence_id for w in p.workouts}) == 4
    assert week_valid(p.templates, p.target, V6Controls())
    with pytest.raises(PlanningConstraintError):
        plan(
            catalog,
            "200",
            selected_template_ids=ids,
            controls=V6Controls(
                authorized_target=target(TrainingPhase.BASE, "200"),
                maximum_uses=((easy.id, 2),),
            ),
        )
    with pytest.raises(PlanningConstraintError, match="bounded selection"):
        plan(
            catalog,
            controls=V6Controls(
                authorized_target=target(TrainingPhase.BASE, "45"),
                maximum_combinations=1,
            ),
        )


def test_v6_realized_compatibility_remains_fail_closed() -> None:
    from test_realized_context import planned_context, selection

    from app.modules.activities.realized_context import ApprovedWorkoutBasis
    from app.modules.physiology.joren import zone_load

    basis = ApprovedWorkoutBasis.parse(
        planned_context(
            planned_method="joren-v6-planned-if2-1",
            planned_version="joren-v6-planned-if2-1",
        )
    )
    result = selection(basis=basis)
    assert (
        result.value is None and result.reason == "unsupported_planned_method_version"
    )
    observed = zone_load(
        discipline=Discipline.BIKE,
        total_minutes=D(60),
        minutes_by_zone=(D(0), D(60), D(0), D(0), D(0)),
    )
    assert selection(basis=basis, measurement=observed).reason == "observation_selected"
    assert observed.load is not None and observed.load.value == D(48)


def test_existing_history_future_week_uses_authorized_progression(
    catalog: tuple[V6Template, ...],
) -> None:
    from app.modules.physiology.joren import starting_baseline
    from app.modules.planning.domain import PlanLoadSample, resolve_target

    baseline = starting_baseline({s: D(0) for s in Discipline})
    sample = PlanLoadSample(
        START - timedelta(weeks=1),
        InternalLoad(D(45)),
        TrainingPhase.BASE,
        realized_load=InternalLoad(D(42)),
        has_prior_approved_plan=True,
    )
    expected = resolve_target(
        week_start=START,
        race_date=START + timedelta(weeks=12),
        prior_loads=(sample,),
        initial_catalog_load=baseline.total,
        prior_approved_plan_exists=True,
    )
    p = plan(
        catalog,
        prior_loads=(sample,),
        onboarding_baseline=baseline,
        controls=V6Controls(),
    )
    assert p.target.target == expected.target and p.target.basis == expected.basis
    assert p.planned_load.value <= expected.target.value
    assert p.workouts


def test_no_new_production_registration_or_historical_rewrite() -> None:
    root = Path(__file__).resolve().parents[1]
    assert "v6_service" not in (root / "app/main.py").read_text(encoding="utf-8")
    assert "V6PlanningService" not in (
        root / "app/modules/planning/router.py"
    ).read_text(encoding="utf-8")
    assert calculate_v6(Discipline.BIKE, (D(3600), D(0), D(0), D(0), D(0))).value == D(
        "30.25"
    )
