"""Phase 6 deterministic target, deck, schedule, and warning tests."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.modules.physiology.anti_stack import ScheduledWorkout
from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    Fraction,
    IntensityBucket,
    InternalLoad,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    PlanningConstraintError,
    PlanningTarget,
    PlanningTargetBasis,
    SelectedWorkout,
    ZoneCapability,
    _bounded_selection,
    _injury_adjusted_target,
    _schedule_is_feasible,
    build_weekly_plan,
    eligible_workouts,
    remaining_workout_deck,
    resolve_target,
    schedule_workouts,
    select_workouts,
    validate_manual_schedule,
)
from app.modules.workouts.catalog import (
    REVIEWED_CATALOG,
    TrainingPhase,
    ZoneRequirement,
    active_catalog,
    snapshot_template,
)

_WEEK_START = date(2026, 8, 3)


def _capabilities() -> dict[Discipline, ZoneCapability]:
    return {
        Discipline.SWIM: ZoneCapability(frozenset({ZoneRequirement.PACE})),
        Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
        Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
    }


def _availability() -> tuple[date, ...]:
    return tuple(date(2026, 8, day) for day in (3, 5, 7))


def test_rpe_guidance_removes_numeric_zones_without_fake_zone_profile() -> None:
    deck = eligible_workouts(
        catalog=active_catalog(),
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            Discipline.RUN: ZoneCapability(
                requirements=frozenset(),
                protocol_ids=frozenset(
                    {
                        "start23_week1_run_calibration_v1",
                        "start23_run_threshold_30min_v1",
                    }
                ),
                rpe_guided=True,
            )
        },
    )

    regular = next(
        template for template in deck if not template.explicit_scheduling_only
    )
    # Protocol-only content no longer receives invented RPE-derived load.
    assert not any(template.explicit_scheduling_only for template in deck)
    assert all(segment.zone_target is None for segment in regular.segments)
    assert all(segment.rpe_target is not None for segment in regular.segments)


@pytest.mark.parametrize(
    ("goal_disciplines", "capabilities"),
    [
        (
            frozenset({Discipline.RUN}),
            {Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))},
        ),
        (
            frozenset({Discipline.BIKE}),
            {Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.POWER}))},
        ),
        (
            frozenset({Discipline.BIKE, Discipline.RUN}),
            {
                Discipline.BIKE: ZoneCapability(
                    frozenset({ZoneRequirement.HEART_RATE})
                ),
                Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
            },
        ),
        (
            frozenset(Discipline),
            {
                Discipline.SWIM: ZoneCapability(frozenset({ZoneRequirement.PACE})),
                Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.POWER})),
                Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
            },
        ),
    ],
)
def test_confirmed_known_values_cover_supported_build_goal_compositions(
    goal_disciplines: frozenset[Discipline],
    capabilities: dict[Discipline, ZoneCapability],
) -> None:
    values = dict(
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(days=7),
                load=InternalLoad(Decimal("100")),
                phase=TrainingPhase.BASE,
            ),
        ),
        goal_disciplines=goal_disciplines,
        confirmed_injuries=frozenset(),
        zone_capabilities=capabilities,
        available_dates=(_WEEK_START,),
    )
    if goal_disciplines == frozenset({Discipline.BIKE}):
        draft = build_weekly_plan(**values)
        assert draft.target.phase is TrainingPhase.BUILD
        assert {workout.discipline for workout in draft.workouts} == set(
            goal_disciplines
        )
    else:
        # The small built-in catalog has no Z3/Z4 load inside the newly
        # approved 70%-90% private high-budget window for this target.
        with pytest.raises(PlanningConstraintError) as error:
            build_weekly_plan(**values)
        assert error.value.code == "catalog_capacity_unsatisfied"


def test_confirmed_run_hr_uses_existing_reviewed_rpe_projection_in_build() -> None:
    deck = eligible_workouts(
        catalog=active_catalog(),
        phase=TrainingPhase.BUILD,
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))
        },
    )

    assert deck
    assert all(segment.zone_target is None for segment in deck[0].segments)
    assert all(segment.rpe_target is not None for segment in deck[0].segments)


@pytest.mark.parametrize(
    ("discipline", "requirement"),
    [
        (Discipline.RUN, ZoneRequirement.HEART_RATE),
        (Discipline.RUN, ZoneRequirement.PACE),
        (Discipline.BIKE, ZoneRequirement.HEART_RATE),
        (Discipline.BIKE, ZoneRequirement.POWER),
        (Discipline.SWIM, ZoneRequirement.PACE),
    ],
)
def test_each_supported_confirmed_metric_has_build_catalog_coverage(
    discipline: Discipline,
    requirement: ZoneRequirement,
) -> None:
    deck = eligible_workouts(
        catalog=active_catalog(),
        phase=TrainingPhase.BUILD,
        goal_disciplines=frozenset({discipline}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            discipline: ZoneCapability(frozenset({requirement})),
        },
    )

    assert {template.discipline for template in deck} == {discipline}


def test_genuine_taper_catalog_gap_has_an_actionable_error() -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        build_weekly_plan(
            week_start=date(2026, 11, 30),
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 7),
            catalog=active_catalog(),
            prior_loads=(
                PlanLoadSample(
                    week_start=date(2026, 11, 23),
                    load=InternalLoad(Decimal("100")),
                    phase=TrainingPhase.BUILD,
                ),
            ),
            goal_disciplines=frozenset({Discipline.BIKE}),
            confirmed_injuries=frozenset(),
            zone_capabilities={
                Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.POWER}))
            },
            available_dates=(date(2026, 11, 30),),
        )

    assert captured.value.code == "taper_catalog_coverage_unavailable"
    assert "bike" in str(captured.value)


def test_exact_test_date_is_owned_by_fixed_schedule_constraint() -> None:
    swim = next(
        template
        for template in active_catalog()
        if template.id.hex == "56000000000000000000000000000008"
    )
    scheduled = schedule_workouts(
        selected=(
            # The selection snapshot keeps the private load while the result exposes
            # only its exact local date.
            SelectedWorkout(
                discipline=swim.discipline,
                snapshot=snapshot_template(swim),
            ),
        ),
        week_start=date(2026, 8, 24),
        timezone_name="Europe/Amsterdam",
        available_dates=(date(2026, 8, 27),),
        fixed_template_dates={swim.id: date(2026, 8, 27)},
    )

    assert scheduled[0].scheduled_date == date(2026, 8, 27)


def test_field_test_without_zone_duration_cannot_enter_load_target_selection() -> None:
    swim_test = next(
        template
        for template in active_catalog()
        if template.id.hex == "56000000000000000000000000000008"
    )

    with pytest.raises(
        PlanningConstraintError,
        match="One or more selected workout templates are not eligible",
    ):
        build_weekly_plan(
            week_start=date(2026, 8, 24),
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(),
            prior_loads=(),
            goal_disciplines=frozenset({Discipline.SWIM}),
            confirmed_injuries=frozenset(),
            zone_capabilities={
                Discipline.SWIM: ZoneCapability(
                    requirements=frozenset(),
                    protocol_ids=frozenset({"start23_swim_css_400_200_v1"}),
                    rpe_guided=True,
                )
            },
            available_dates=(date(2026, 8, 27),),
            selected_template_ids=(swim_test.id,),
        )


def test_initial_plan_uses_catalog_baseline_and_explicit_availability() -> None:
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=_availability(),
    )

    assert draft.target.phase is TrainingPhase.BASE
    assert draft.target.basis is PlanningTargetBasis.INITIAL_CATALOG_BASELINE
    assert {workout.discipline for workout in draft.workouts} == set(Discipline)
    assert {workout.scheduled_date for workout in draft.workouts} <= set(
        _availability()
    )
    assert draft.low_intensity_percent == Decimal(100)
    assert draft.high_intensity_percent == Decimal(0)
    assert "intensity_distribution_outside_target" not in {
        warning.code for warning in draft.warnings
    }
    assert "value" not in repr(draft.planned_load)


@pytest.mark.parametrize(
    "week_start",
    [
        date(2026, 8, 3),  # Ordinary race-anchored build position.
        date(2026, 8, 17),  # Nominal race-anchored recovery position.
    ],
)
def test_first_plan_uses_onboarding_baseline_without_recovery_history(
    week_start: date,
) -> None:
    baseline = starting_baseline(
        {
            Discipline.SWIM: Decimal(60),
            Discipline.BIKE: Decimal(60),
            Discipline.RUN: Decimal(60),
        }
    )

    target = resolve_target(
        week_start=week_start,
        race_date=date(2026, 12, 6),
        prior_loads=(),
        initial_catalog_load=baseline.total,
    )
    assert target.phase is TrainingPhase.BASE
    assert target.basis is PlanningTargetBasis.INITIAL_CATALOG_BASELINE
    assert target.target.value == baseline.total.value == Decimal("171.6")
    # Approved bounded repeats can now cover a first-week target.
    draft = build_weekly_plan(
        week_start=week_start,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=(week_start, week_start + timedelta(days=2)),
        onboarding_baseline=baseline,
    )
    assert draft.target.target == baseline.total
    assert len(draft.workouts) > len(Discipline)


@pytest.mark.parametrize("hours", ["0", "1", "3", "6", "15"])
@pytest.mark.parametrize("week_start", [_WEEK_START, date(2026, 8, 17)])
def test_run_first_week_history_reaches_target_and_catalog_capacity(
    hours: str, week_start: date
) -> None:
    """The old one-card fallback masked a large approved first-week target."""
    baseline = starting_baseline({Discipline.RUN: Decimal(hours) * Decimal(60)})
    assert baseline.total.value == (
        Decimal("45.0")
        if hours == "0"
        else (Decimal(hours) * Decimal("64.6875")).quantize(Decimal("0.1"))
    )
    values = dict(
        week_start=week_start,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(),
        prior_loads=(),
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))
        },
        available_dates=(week_start, week_start + timedelta(days=2)),
        onboarding_baseline=baseline,
    )
    if hours == "15":
        # Repeating the tiny built-in deck still has a finite 24-card bound.
        # The reviewed source catalog matrix covers this volume separately.
        with pytest.raises(PlanningConstraintError) as error:
            build_weekly_plan(**values)
        assert error.value.code == "catalog_capacity_unsatisfied"
        return
    draft = build_weekly_plan(**values)
    assert draft.target.phase is TrainingPhase.BASE
    assert draft.target.target == baseline.total
    assert 1 <= len(draft.workouts) <= 24
    assert abs(draft.target.target.value - draft.planned_load.value) < Decimal("36.3")


def test_run_history_can_increase_count_when_reviewed_automatic_deck_exists() -> None:
    regular = next(
        template
        for template in active_catalog()
        if template.discipline is Discipline.RUN
        and TrainingPhase.BASE in template.training_phases
        and not template.athlete_selection_only
    )
    catalog = active_catalog(
        tuple(active_catalog())
        + tuple(
            replace(
                regular,
                id=uuid4(),
                template_key=uuid4(),
                name=f"Reviewed run alternative {index}",
            )
            for index in range(4)
        )
    )
    counts = []
    for hours in ("0", "1", "3"):
        draft = build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 6),
            catalog=catalog,
            prior_loads=(),
            goal_disciplines=frozenset({Discipline.RUN}),
            confirmed_injuries=frozenset(),
            zone_capabilities={
                Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))
            },
            available_dates=_availability(),
            onboarding_baseline=starting_baseline(
                {Discipline.RUN: Decimal(hours) * Decimal(60)}
            ),
        )
        counts.append(len(draft.workouts))
    assert counts[0] < counts[1] < counts[2]


def test_reviewed_source_option_is_eligible_for_normal_selection() -> None:
    regular_bike = next(
        template
        for template in active_catalog(REVIEWED_CATALOG)
        if template.discipline is Discipline.BIKE
        and TrainingPhase.BASE in template.training_phases
    )
    source_option = replace(
        regular_bike,
        id=uuid4(),
        template_key=uuid4(),
        name="BIK-001 · Herstel",
        athlete_selection_only=True,
    )
    catalog = active_catalog(REVIEWED_CATALOG + (source_option,))
    automatic = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=catalog,
        prior_loads=(),
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=(_WEEK_START,),
    )
    explicit = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=catalog,
        prior_loads=(),
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=(_WEEK_START,),
        selected_template_ids=(source_option.id,),
    )

    assert source_option.id in {
        template.id
        for template in eligible_workouts(
            catalog=catalog,
            phase=TrainingPhase.BASE,
            goal_disciplines=frozenset({Discipline.BIKE}),
            confirmed_injuries=frozenset(),
            zone_capabilities=_capabilities(),
        )
    }
    assert automatic.workouts
    assert explicit.workouts[0].snapshot.template_id == source_option.id


def test_distance_only_swim_source_load_cannot_enter_phase_13_target_fit() -> None:
    regular_swim = next(
        template
        for template in active_catalog(REVIEWED_CATALOG)
        if template.discipline is Discipline.SWIM
        and not template.explicit_scheduling_only
    )
    distance_swim = replace(
        regular_swim,
        id=uuid4(),
        template_key=uuid4(),
        name="SWI-007 · Duur",
        duration_minutes=None,
        segments=tuple(
            replace(segment, duration_minutes=None) for segment in regular_swim.segments
        ),
        athlete_selection_only=True,
        source_catalog="start23-v0.1",
        source_workout_id="SWI-007",
    )

    current = active_catalog(REVIEWED_CATALOG + (distance_swim,))
    stored = next(template for template in current if template.id == distance_swim.id)
    assert stored.duration_minutes is None
    assert stored.distance_meters == distance_swim.distance_meters
    assert distance_swim.internal_planned_load is not None
    assert stored.internal_planned_load is None
    deck = eligible_workouts(
        catalog=current,
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.SWIM}),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
    )
    assert distance_swim.id not in {template.id for template in deck}
    with pytest.raises(PlanningConstraintError) as error:
        select_workouts(
            deck=deck,
            required_disciplines=frozenset({Discipline.SWIM}),
            target=distance_swim.internal_planned_load,
            selected_template_ids=(distance_swim.id,),
        )
    assert error.value.code == "template_not_eligible"


def test_established_recovery_history_keeps_existing_recovery_target() -> None:
    prior = tuple(
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(weeks=4 - index),
            load=InternalLoad(Decimal(10 + index)),
            realized_load=InternalLoad(Decimal(10 + index)),
            phase=TrainingPhase.BUILD,
        )
        for index in range(4)
    )

    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 11, 22),
        prior_loads=prior,
        initial_catalog_load=InternalLoad(Decimal(5)),
    )

    assert target.phase is TrainingPhase.RECOVERY
    assert target.basis is PlanningTargetBasis.RECOVERY_FACTOR
    assert target.target.value == Decimal("7.8")


def test_race_date_anchors_cycle_independently_of_prior_plan_count() -> None:
    race_date = date(2026, 12, 6)
    samples = tuple(
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(weeks=index + 1),
            load=InternalLoad(Decimal("10")),
            phase=TrainingPhase.BUILD,
        )
        for index in range(4)
    )

    shorter_history = resolve_target(
        week_start=_WEEK_START,
        race_date=race_date,
        prior_loads=samples[:2],
        initial_catalog_load=InternalLoad(Decimal("5")),
    )
    longer_history = resolve_target(
        week_start=_WEEK_START,
        race_date=race_date,
        prior_loads=samples,
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert shorter_history.phase is TrainingPhase.BUILD
    assert longer_history.phase is TrainingPhase.BUILD


def test_regular_build_uses_canonical_realized_progression() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("10")),
                realized_load=InternalLoad(Decimal("8")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.basis is PlanningTargetBasis.REALIZED_PROGRESSION
    assert target.target.value == Decimal("11.0")


def test_heavy_undershoot_uses_available_realized_baseline() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("10")),
                realized_load=InternalLoad(Decimal("7")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.basis is PlanningTargetBasis.REALIZED_BASELINE
    assert target.target.value == Decimal("7")


def test_realized_overshoot_applies_debt_before_progression() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("10")),
                realized_load=InternalLoad(Decimal("12")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.basis is PlanningTargetBasis.PHYSIOLOGICAL_DEBT
    assert target.target.value == Decimal("9.0")


def test_non_positive_debt_creates_a_pending_manual_review_recovery_target() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("100")),
                realized_load=InternalLoad(Decimal("500")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.phase is TrainingPhase.RECOVERY
    assert target.basis is PlanningTargetBasis.MANUAL_REVIEW_RECOVERY
    assert target.target.value == Decimal("60.0")
    assert target.manual_review_required is True


def test_repeated_unsafe_debt_requires_qualified_escalation() -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        resolve_target(
            week_start=_WEEK_START,
            race_date=date(2026, 12, 6),
            prior_loads=(
                PlanLoadSample(
                    week_start=_WEEK_START - timedelta(weeks=1),
                    load=InternalLoad(Decimal("100")),
                    realized_load=InternalLoad(Decimal("500")),
                    phase=TrainingPhase.BUILD,
                    target_basis=PlanningTargetBasis.MANUAL_REVIEW_RECOVERY,
                ),
            ),
            initial_catalog_load=InternalLoad(Decimal("5")),
        )

    assert captured.value.code == "physiological_debt_escalation_required"


def test_reliable_realized_intensity_reduces_first_eligible_week_target() -> None:
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("100")),
                realized_load=InternalLoad(Decimal("80")),
                phase=TrainingPhase.BUILD,
                planned_high_minutes=DurationMinutes(Decimal("20")),
                planned_total_minutes=DurationMinutes(Decimal("100")),
                realized_high_minutes=DurationMinutes(Decimal("30")),
                realized_classified_minutes=DurationMinutes(Decimal("60")),
                realized_total_minutes=DurationMinutes(Decimal("100")),
            ),
        ),
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            **_capabilities(),
            Discipline.BIKE: ZoneCapability(
                frozenset({ZoneRequirement.HEART_RATE, ZoneRequirement.POWER})
            ),
        },
        available_dates=_availability(),
    )

    assert draft.target.desired_high_fraction.value == Decimal("0.05")
    assert "realized_intensity_debt_applied" in {
        warning.code for warning in draft.warnings
    }


def test_missing_realized_week_retains_the_safe_planned_hold() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("10")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.basis is PlanningTargetBasis.PRIOR_PLANNED_HOLD
    assert target.target.value == Decimal("10")


def test_missed_week_progresses_from_explicit_zero_without_inventing_load() -> None:
    realized = ("8", "12", "4", "0")
    prior = tuple(
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(weeks=4 - index),
            load=InternalLoad(Decimal("10")),
            realized_load=InternalLoad(Decimal(value)),
            phase=TrainingPhase.BUILD,
            completed_activity_count=0 if index == 3 else 1,
        )
        for index, value in enumerate(realized)
    )

    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=prior,
        initial_catalog_load=InternalLoad(Decimal("5")),
    )

    assert target.basis is PlanningTargetBasis.REALIZED_PROGRESSION
    assert target.target.value == Decimal("0")


def test_missed_week_does_not_require_four_week_history() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal(10)),
                realized_load=InternalLoad(Decimal(0)),
                phase=TrainingPhase.BUILD,
                completed_activity_count=0,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal(5)),
    )
    assert target.target.value == 0
    assert target.basis is PlanningTargetBasis.REALIZED_PROGRESSION


def test_explicit_maintenance_holds_prior_plan_without_progression() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 7, 26),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(weeks=1),
                load=InternalLoad(Decimal("10")),
                realized_load=InternalLoad(Decimal("10")),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal("5")),
        maintenance_active=True,
    )

    assert target.phase is TrainingPhase.BUILD
    assert target.basis is PlanningTargetBasis.MAINTENANCE_HOLD
    assert target.target.value == Decimal("10")


def test_exact_monday_race_taper_retains_reviewed_reduction() -> None:
    target = resolve_target(
        week_start=date(2026, 8, 10),
        race_date=date(2026, 8, 17),
        prior_loads=(
            PlanLoadSample(
                week_start=date(2026, 8, 3),
                load=InternalLoad(Decimal(10)),
                phase=TrainingPhase.BUILD,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal(5)),
    )
    assert target.phase is TrainingPhase.TAPER
    assert target.target.value == Decimal("3.50")


@pytest.mark.parametrize("weekday", range(1, 7))
def test_partial_week_taper_requires_approved_curve(weekday: int) -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        resolve_target(
            week_start=date(2026, 8, 10),
            race_date=date(2026, 8, 17) + timedelta(days=weekday),
            prior_loads=(),
            initial_catalog_load=InternalLoad(Decimal(5)),
        )
    assert captured.value.code == "partial_week_taper_rule_required"


def test_confirmed_injury_excludes_discipline_before_selection() -> None:
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset({Discipline.RUN}),
        zone_capabilities=_capabilities(),
        available_dates=_availability(),
        onboarding_baseline=starting_baseline(
            {sport: Decimal(60) for sport in Discipline}
        ),
    )

    assert {workout.discipline for workout in draft.workouts} == {
        Discipline.SWIM,
        Discipline.BIKE,
    }
    assert "injured_disciplines_excluded" in {
        warning.code for warning in draft.warnings
    }


def test_all_goal_disciplines_blocked_returns_pending_rest_only_draft() -> None:
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(Discipline),
        zone_capabilities=_capabilities(),
        available_dates=(),
    )

    assert draft.target.basis is PlanningTargetBasis.INJURY_REST_ONLY
    assert draft.planned_load.value == 0
    assert draft.workouts == ()
    assert [warning.code for warning in draft.warnings] == [
        "all_disciplines_blocked_rest_only"
    ]


def test_low_only_restriction_excludes_high_intensity_templates() -> None:
    deck = eligible_workouts(
        catalog=active_catalog(REVIEWED_CATALOG),
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        low_only_disciplines=frozenset({Discipline.BIKE}),
        zone_capabilities={
            Discipline.BIKE: ZoneCapability(
                frozenset({ZoneRequirement.HEART_RATE, ZoneRequirement.POWER})
            )
        },
    )

    assert all(workout.intensity_bucket is IntensityBucket.LOW for workout in deck)
    assert deck


def test_remaining_deck_is_selection_aware_and_rejects_stale_cards() -> None:
    deck = tuple(
        template
        for template in active_catalog(REVIEWED_CATALOG)
        if template.discipline is Discipline.BIKE
    )
    selected = deck[0]
    assert selected.internal_planned_load is not None
    remaining = remaining_workout_deck(
        deck=deck,
        target=InternalLoad(selected.internal_planned_load.value + Decimal("100")),
        selected_template_ids=(selected.id,),
    )

    assert selected.id not in {item.id for item in remaining}
    with pytest.raises(PlanningConstraintError) as captured:
        remaining_workout_deck(
            deck=deck,
            target=InternalLoad(Decimal("100")),
            selected_template_ids=(uuid4(),),
        )
    assert captured.value.code == "template_not_eligible"


def test_generated_schedule_can_consolidate_all_workouts_on_one_available_day() -> None:
    only_available_day = date(2026, 8, 3)

    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=(only_available_day,),
    )

    assert len(draft.workouts) == 3
    assert {workout.scheduled_date for workout in draft.workouts} == {
        only_available_day
    }
    assert "workouts_consolidated_on_available_dates" in {
        warning.code for warning in draft.warnings
    }


def test_live_run_first_week_uses_best_available_day() -> None:
    """Regression: the Android default Mon/Wed/Sat flow must reach the deck."""

    available_dates = (date(2026, 8, 3), date(2026, 8, 5), date(2026, 8, 8))
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={
            Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))
        },
        available_dates=available_dates,
        onboarding_baseline=starting_baseline({Discipline.RUN: Decimal("36")}),
    )

    assert len(draft.workouts) == 1
    assert draft.workouts[0].scheduled_date == date(2026, 8, 5)


def test_schedule_enforces_feasible_rest_limit() -> None:
    low_bike = next(
        template
        for template in active_catalog(REVIEWED_CATALOG)
        if template.discipline is Discipline.BIKE
        and template.intensity_bucket is IntensityBucket.LOW
        and not template.explicit_scheduling_only
        and not template.athlete_selection_only
    )
    low_bikes = tuple(
        SelectedWorkout(
            discipline=template.discipline,
            snapshot=snapshot_template(template),
        )
        for template in (
            low_bike,
            replace(low_bike, id=uuid4(), template_key=uuid4()),
        )
    )

    proposed = schedule_workouts(
        selected=low_bikes,
        available_dates=(date(2026, 8, 3), date(2026, 8, 6)),
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
    )

    assert {workout.scheduled_date for workout in proposed} == {
        date(2026, 8, 3),
        date(2026, 8, 6),
    }


def test_generated_schedule_balances_three_workouts_over_two_available_days() -> None:
    available_dates = (date(2026, 8, 3), date(2026, 8, 5))

    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=available_dates,
    )

    workout_counts = {
        scheduled_date: sum(
            workout.scheduled_date == scheduled_date for workout in draft.workouts
        )
        for scheduled_date in available_dates
    }
    assert sorted(workout_counts.values()) == [1, 2]


def test_manual_schedule_can_place_multiple_workouts_on_the_same_date() -> None:
    available_dates = (date(2026, 8, 3), date(2026, 8, 5))
    automatic = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=available_dates,
    )
    selected_ids = tuple(workout.snapshot.template_id for workout in automatic.workouts)

    consolidated = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="UTC",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(REVIEWED_CATALOG),
        prior_loads=(),
        goal_disciplines=frozenset(Discipline),
        confirmed_injuries=frozenset(),
        zone_capabilities=_capabilities(),
        available_dates=available_dates,
        selected_template_ids=selected_ids,
        fixed_template_dates={
            template_id: available_dates[0] for template_id in selected_ids
        },
    )

    assert {workout.scheduled_date for workout in consolidated.workouts} == {
        available_dates[0]
    }


def test_consolidation_keeps_same_discipline_high_intensity_spacing() -> None:
    high_run = next(
        template
        for template in active_catalog()
        if template.discipline is Discipline.RUN
        and template.intensity_bucket is IntensityBucket.HIGH
    )
    high_runs = (
        high_run,
        replace(high_run, id=uuid4(), template_key=uuid4()),
    )
    selected = tuple(
        SelectedWorkout(
            discipline=template.discipline,
            snapshot=snapshot_template(template),
        )
        for template in high_runs[:2]
    )

    with pytest.raises(PlanningConstraintError) as captured:
        schedule_workouts(
            selected=selected,
            available_dates=(date(2026, 8, 3),),
            week_start=_WEEK_START,
            timezone_name="UTC",
        )

    assert captured.value.code == "rest_or_anti_stack_unsatisfied"


@pytest.mark.parametrize("discipline", [Discipline.BIKE, Discipline.SWIM])
def test_auto_placement_uses_exact_48_hour_boundary_for_high_repeats(
    discipline: Discipline,
) -> None:
    template = next(
        item
        for item in active_catalog()
        if item.discipline is discipline
        and item.intensity_bucket is IntensityBucket.HIGH
        and not item.explicit_scheduling_only
    )
    first_id, second_id = uuid4(), uuid4()
    selected = (
        SelectedWorkout(discipline, snapshot_template(template), first_id),
        SelectedWorkout(discipline, snapshot_template(template), second_id),
    )
    scheduled = schedule_workouts(
        selected=selected,
        available_dates=(_WEEK_START, _WEEK_START + timedelta(days=2)),
        week_start=_WEEK_START,
        timezone_name="UTC",
        fixed_occurrence_dates={
            first_id: _WEEK_START,
            second_id: _WEEK_START + timedelta(days=2),
        },
    )
    assert {item.scheduled_date for item in scheduled} == {
        _WEEK_START,
        _WEEK_START + timedelta(days=2),
    }
    with pytest.raises(PlanningConstraintError) as error:
        schedule_workouts(
            selected=selected,
            available_dates=(_WEEK_START, _WEEK_START + timedelta(days=1)),
            week_start=_WEEK_START,
            timezone_name="UTC",
            fixed_occurrence_dates={
                first_id: _WEEK_START,
                second_id: _WEEK_START + timedelta(days=1),
            },
        )
    assert error.value.code == "rest_or_anti_stack_unsatisfied"


def test_build_selection_uses_safe_alternative_when_best_load_fit_stacks() -> None:
    catalog = active_catalog()
    low = next(
        item
        for item in catalog
        if item.discipline is Discipline.RUN
        and item.intensity_bucket is IntensityBucket.LOW
    )
    high = next(
        item
        for item in catalog
        if item.discipline is Discipline.RUN
        and item.intensity_bucket is IntensityBucket.HIGH
    )
    deck = (
        replace(
            high,
            id=UUID(int=1),
            template_key=UUID(int=1),
            internal_planned_load=InternalLoad(Decimal(8)),
        ),
        replace(
            high,
            id=UUID(int=2),
            template_key=UUID(int=2),
            internal_planned_load=InternalLoad(Decimal(16)),
        ),
        replace(
            low,
            id=UUID(int=3),
            template_key=UUID(int=3),
            internal_planned_load=InternalLoad(Decimal(84)),
        ),
        replace(
            low,
            id=UUID(int=4),
            template_key=UUID(int=4),
            internal_planned_load=InternalLoad(Decimal(42)),
        ),
    )
    common = dict(
        deck=deck,
        prefix=(),
        required_disciplines=frozenset({Discipline.RUN}),
        target=InternalLoad(Decimal(100)),
        phase=TrainingPhase.BUILD,
        build_week=1,
        desired_high_fraction=Fraction(Decimal("0.2")),
        required_count=3,
        required_composition={Discipline.RUN: 3},
    )
    unplaced = _bounded_selection(**common)
    assert unplaced is not None
    assert [item.id for item in unplaced] == [UUID(int=1), UUID(int=1), UUID(int=3)]
    placed = _bounded_selection(
        **common,
        feasible=lambda selection: _schedule_is_feasible(
            selection=selection,
            week_start=_WEEK_START,
            available_dates=(_WEEK_START, _WEEK_START + timedelta(days=2)),
            timezone_name="UTC",
        ),
    )
    assert placed is not None
    assert [item.id for item in placed] == [UUID(int=2), UUID(int=4), UUID(int=4)]
    assert (
        _bounded_selection(
            **{**common, "deck": (deck[0], deck[2])},
            feasible=lambda selection: _schedule_is_feasible(
                selection=selection,
                week_start=_WEEK_START,
                available_dates=(_WEEK_START,),
                timezone_name="UTC",
            ),
        )
        is None
    )


def test_manual_anti_stack_violation_rejects_at_71_hours_but_not_72() -> None:
    start = datetime(2026, 8, 3, 7, tzinfo=timezone.utc)

    with pytest.raises(PlanningConstraintError) as error:
        validate_manual_schedule(
            workouts=(
                ScheduledWorkout(
                    "first",
                    frozenset({Discipline.RUN}),
                    IntensityBucket.HIGH,
                    start,
                ),
                ScheduledWorkout(
                    "moved",
                    frozenset({Discipline.RUN}),
                    IntensityBucket.HIGH,
                    start + timedelta(hours=71),
                ),
            ),
            moved_workout_id="moved",
        )
    exact = validate_manual_schedule(
        workouts=(
            ScheduledWorkout(
                "first",
                frozenset({Discipline.RUN}),
                IntensityBucket.HIGH,
                start,
            ),
            ScheduledWorkout(
                "moved",
                frozenset({Discipline.RUN}),
                IntensityBucket.HIGH,
                start + timedelta(hours=72),
            ),
        ),
        moved_workout_id="moved",
    )

    assert error.value.code == "anti_stack_violation"
    assert exact == ()


def test_fatigue_uses_lower_realized_times_ten_percent() -> None:
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=(
            PlanLoadSample(
                week_start=_WEEK_START - timedelta(days=7),
                load=InternalLoad(Decimal(100)),
                realized_load=InternalLoad(Decimal(30)),
                phase=TrainingPhase.BUILD,
                reduced_realized_progression=True,
            ),
        ),
        initial_catalog_load=InternalLoad(Decimal(5)),
    )
    assert target.target.value == Decimal(33)


def test_sick_week_is_excluded_without_deleting_history() -> None:
    prior = (
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(days=14),
            load=InternalLoad(Decimal(100)),
            realized_load=InternalLoad(Decimal(100)),
            phase=TrainingPhase.BUILD,
        ),
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(days=7),
            load=InternalLoad(Decimal(5)),
            realized_load=InternalLoad(Decimal(1)),
            phase=TrainingPhase.BUILD,
            sick_week=True,
        ),
    )
    target = resolve_target(
        week_start=_WEEK_START,
        race_date=date(2026, 12, 6),
        prior_loads=prior,
        initial_catalog_load=InternalLoad(Decimal(5)),
    )
    assert target.target.value == Decimal(110)
    assert len(prior) == 2 and prior[1].sick_week


@pytest.mark.parametrize(
    ("minutes", "injuries", "expected_code"),
    [
        (
            {Discipline.RUN: Decimal(60)},
            frozenset(),
            "zero_history_discipline_baseline_unavailable",
        ),
        (
            {},
            frozenset({Discipline.SWIM}),
            "restricted_zero_base_allocation_unavailable",
        ),
    ],
)
def test_onboarding_never_invents_discipline_minimum_or_injury_allocation(
    minutes: dict[Discipline, Decimal],
    injuries: frozenset[Discipline],
    expected_code: str,
) -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="UTC",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(),
            prior_loads=(),
            goal_disciplines=frozenset(Discipline),
            confirmed_injuries=injuries,
            zone_capabilities=_capabilities(),
            available_dates=_availability(),
            onboarding_baseline=starting_baseline(
                {sport: minutes.get(sport, Decimal(0)) for sport in Discipline}
            ),
        )
    assert captured.value.code == expected_code


def test_injury_baseline_does_not_transfer_into_running() -> None:
    drafts = [
        build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="UTC",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(),
            prior_loads=(),
            goal_disciplines=frozenset(Discipline),
            confirmed_injuries=frozenset({Discipline.SWIM, Discipline.BIKE}),
            zone_capabilities=_capabilities(),
            available_dates=(date(2026, 8, 9),),
            onboarding_baseline=starting_baseline(
                {
                    Discipline.SWIM: other_minutes,
                    Discipline.BIKE: other_minutes,
                    Discipline.RUN: Decimal(60),
                }
            ),
        )
        for other_minutes in (Decimal(0), Decimal(600))
    ]
    assert all(
        abs(draft.target.target.value - Decimal("64.7")) < Decimal("0.1")
        for draft in drafts
    )
    assert all(workout.discipline is Discipline.RUN for workout in drafts[1].workouts)


def test_injury_target_uses_private_sport_caps_and_keeps_transfer_low_only() -> None:
    prior = PlanLoadSample(
        week_start=_WEEK_START - timedelta(days=7),
        load=InternalLoad(Decimal("480")),
        phase=TrainingPhase.BUILD,
        discipline_loads={
            Discipline.RUN: InternalLoad(Decimal("300")),
            Discipline.BIKE: InternalLoad(Decimal("120")),
            Discipline.SWIM: InternalLoad(Decimal("60")),
        },
    )
    adjusted, disciplines, replacements = _injury_adjusted_target(
        target=PlanningTarget(
            phase=TrainingPhase.BUILD,
            basis=PlanningTargetBasis.PRIOR_PLANNED_HOLD,
            target=InternalLoad(Decimal("480")),
        ),
        prior_loads=(prior,),
        onboarding_baseline=None,
        blocked=frozenset({Discipline.RUN}),
        goal_disciplines=frozenset(Discipline),
        eligible_recipients=frozenset({Discipline.BIKE, Discipline.SWIM}),
        cross_training_opt_ins=frozenset(),
        desired_high_fraction=Fraction(Decimal("0.20")),
    )
    assert adjusted.target.value == Decimal("198")
    assert adjusted.discipline_caps[Discipline.BIKE].value == Decimal("132")
    assert adjusted.discipline_caps[Discipline.SWIM].value == Decimal("66")
    assert adjusted.desired_high_fraction.value <= Decimal("0.20")
    assert disciplines == replacements == frozenset({Discipline.BIKE, Discipline.SWIM})
