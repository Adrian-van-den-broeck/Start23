"""Phase 6 deterministic target, deck, schedule, and warning tests."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.physiology.anti_stack import ScheduledWorkout
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    IntensityBucket,
    InternalLoad,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    PlanningConstraintError,
    PlanningTargetBasis,
    SelectedWorkout,
    ZoneCapability,
    build_weekly_plan,
    eligible_workouts,
    remaining_workout_deck,
    resolve_target,
    schedule_workouts,
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
    field_test = next(
        template for template in deck if template.explicit_scheduling_only
    )
    assert all(segment.zone_target is None for segment in regular.segments)
    assert all(segment.rpe_target is not None for segment in regular.segments)
    assert all(segment.protocol_target is not None for segment in field_test.segments)


def test_exact_test_date_is_owned_by_fixed_schedule_constraint() -> None:
    run = next(
        template
        for template in active_catalog()
        if template.id.hex == "55000000000000000000000000000009"
    )
    scheduled = schedule_workouts(
        selected=(
            # The selection snapshot keeps the private load while the result exposes
            # only its exact local date.
            SelectedWorkout(
                discipline=run.discipline,
                snapshot=snapshot_template(run),
            ),
        ),
        week_start=date(2026, 8, 24),
        timezone_name="Europe/Amsterdam",
        available_dates=(date(2026, 8, 27),),
        fixed_template_dates={run.id: date(2026, 8, 27)},
    )

    assert scheduled[0].scheduled_date == date(2026, 8, 27)


def test_explicit_field_test_cannot_be_selected_without_an_exact_date() -> None:
    run_test = next(
        template
        for template in active_catalog()
        if template.id.hex == "55000000000000000000000000000009"
    )

    with pytest.raises(
        PlanningConstraintError,
        match="Every explicitly scheduled field test requires an exact date",
    ):
        build_weekly_plan(
            week_start=date(2026, 8, 24),
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(),
            prior_loads=(),
            goal_disciplines=frozenset({Discipline.RUN}),
            confirmed_injuries=frozenset(),
            zone_capabilities={
                Discipline.RUN: ZoneCapability(
                    requirements=frozenset(),
                    protocol_ids=frozenset({"start23_run_threshold_30min_v1"}),
                    rpe_guided=True,
                )
            },
            available_dates=(date(2026, 8, 27),),
            selected_template_ids=(run_test.id,),
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
    assert "value" not in repr(draft.planned_load)


def test_every_fifth_week_uses_recovery_target() -> None:
    prior = tuple(
        PlanLoadSample(
            week_start=_WEEK_START - timedelta(weeks=4 - index),
            load=InternalLoad(Decimal(10 + index)),
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
                load=InternalLoad(Decimal("7")),
                realized_load=InternalLoad(Decimal("5.6")),
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


def test_inactive_completed_week_uses_four_calendar_week_restart_average() -> None:
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

    assert target.basis is PlanningTargetBasis.INACTIVE_RESTART
    assert target.target.value == Decimal("6")


def test_inactive_restart_fails_closed_without_four_complete_weeks() -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        resolve_target(
            week_start=_WEEK_START,
            race_date=date(2026, 12, 6),
            prior_loads=(
                PlanLoadSample(
                    week_start=_WEEK_START - timedelta(weeks=1),
                    load=InternalLoad(Decimal("10")),
                    realized_load=InternalLoad(Decimal("0")),
                    phase=TrainingPhase.BUILD,
                    completed_activity_count=0,
                ),
            ),
            initial_catalog_load=InternalLoad(Decimal("5")),
        )

    assert captured.value.code == "inactive_restart_baseline_unavailable"


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


@pytest.mark.parametrize(
    ("weeks_before", "expected"),
    [(2, Decimal("6.0")), (1, Decimal("3.50"))],
)
def test_a_race_taper_context_has_precedence(
    weeks_before: int,
    expected: Decimal,
) -> None:
    race_week = date(2026, 8, 17)
    requested_week = race_week - timedelta(weeks=weeks_before)
    prior = (
        PlanLoadSample(
            week_start=requested_week - timedelta(weeks=1),
            load=InternalLoad(Decimal(10)),
            phase=TrainingPhase.BUILD,
        ),
    )

    target = resolve_target(
        week_start=requested_week,
        race_date=race_week + timedelta(days=6),
        prior_loads=prior,
        initial_catalog_load=InternalLoad(Decimal(5)),
    )

    assert target.phase is TrainingPhase.TAPER
    assert target.basis is PlanningTargetBasis.TAPER_FACTOR
    assert target.target.value == expected


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


def test_generated_schedule_fails_when_availability_cannot_fit_deck() -> None:
    with pytest.raises(PlanningConstraintError) as captured:
        build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="UTC",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(REVIEWED_CATALOG),
            prior_loads=(),
            goal_disciplines=frozenset(Discipline),
            confirmed_injuries=frozenset(),
            zone_capabilities=_capabilities(),
            available_dates=(date(2026, 8, 3),),
        )

    assert captured.value.code == "availability_unsatisfied"


def test_generated_schedule_rejects_four_consecutive_rest_days() -> None:
    early_week_availability = tuple(date(2026, 8, day) for day in (3, 4, 5))

    with pytest.raises(PlanningConstraintError) as captured:
        build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="UTC",
            race_date=date(2026, 12, 6),
            catalog=active_catalog(REVIEWED_CATALOG),
            prior_loads=(),
            goal_disciplines=frozenset(Discipline),
            confirmed_injuries=frozenset(),
            zone_capabilities=_capabilities(),
            available_dates=early_week_availability,
        )

    assert captured.value.code == "rest_or_anti_stack_unsatisfied"


def test_manual_anti_stack_violation_warns_at_71_hours_but_not_72() -> None:
    start = datetime(2026, 8, 3, 7, tzinfo=timezone.utc)

    warning = validate_manual_schedule(
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

    assert [item.code for item in warning] == ["anti_stack_violation"]
    assert exact == ()
