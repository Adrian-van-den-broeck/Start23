"""Run history matrix against the reviewed, occurrence-capable source catalog."""

import json
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    TrainingZone,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    WeeklyPlanDraft,
    ZoneCapability,
    build_weekly_plan,
    eligible_workouts,
)
from app.modules.planning.service import PlanningService
from app.modules.planning.swipe import (
    SwipeDecisionKind,
    SwipeSelectionState,
    apply_swipe_decision,
)
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
    active_catalog,
)
from app.modules.workouts.repository import parse_planning_catalog

_WEEK_START = date(2026, 8, 3)
_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260903074359_add_source_catalog_training_options.sql"
)


def _durable_run_catalog() -> tuple[WorkoutTemplate, ...]:
    """Project immutable source version 2 as installed by the forward migration."""
    sql = _MIGRATION.read_text(encoding="utf-8")
    match = re.search(r"\$catalog\$(.*?)\$catalog\$::jsonb", sql, re.DOTALL)
    assert match is not None
    source_rows = json.loads(match.group(1))
    assert isinstance(source_rows, list)
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        if source["discipline"] != "run":
            continue
        rows.append(
            {
                **source,
                "fallback_compatibility": "compatible",
                "explicit_scheduling_only": False,
                "athlete_selection_only": False,
                "version": 2,
                "source_catalog": "start23-v0.1",
                "training_phases": (
                    ["build"]
                    if any(
                        segment.get("zone_number", 0) > 2
                        for segment in source["segments"]
                    )
                    else ["base", "build", "recovery", "taper"]
                ),
                "zone_requirements": [],
                "segments": [
                    {**segment, "is_swim_technique": False}
                    for segment in source["segments"]
                ],
            }
        )
    return active_catalog((*CURRENT_CATALOG, *parse_planning_catalog(tuple(rows))))


def _run_capability(mode: str) -> ZoneCapability:
    if mode == "calibration_pending":
        return ZoneCapability(
            frozenset(),
            protocol_ids=frozenset({"start23_week1_run_calibration_v1"}),
            rpe_guided=True,
        )
    return ZoneCapability(frozenset({ZoneRequirement.HEART_RATE}))


@pytest.mark.parametrize(
    "mode", ["approved_calibration", "known_values", "calibration_pending"]
)
def test_reviewed_source_run_catalog_enters_normal_deck(mode: str) -> None:
    catalog = _durable_run_catalog()
    source = tuple(template for template in catalog if template.source_catalog)
    deck = eligible_workouts(
        catalog=catalog,
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={Discipline.RUN: _run_capability(mode)},
    )
    automatic = tuple(
        template for template in deck if not template.explicit_scheduling_only
    )

    assert len(source) == 50
    assert all(not template.athlete_selection_only for template in source)
    assert len(deck) > 1
    assert len(automatic) == len(deck)
    assert all(
        segment.zone_target is None or segment.zone_target <= 2
        for template in deck
        for segment in template.segments
    )
    if mode == "calibration_pending":
        assert all(
            segment.zone_target is None
            for template in deck
            for segment in template.segments
        )


def test_descriptive_source_event_labels_do_not_restrict_run_deck() -> None:
    deck = eligible_workouts(
        catalog=_durable_run_catalog(),
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={Discipline.RUN: _run_capability("known_values")},
    )
    descriptions = " ".join(template.description for template in deck)
    assert all(label in descriptions for label in ("Fitheid", "Halve", "Volledige"))


@pytest.mark.parametrize(
    ("hours", "private_target"),
    [
        ("0", "45.0"),
        ("1", "64.7"),
        ("3", "194.1"),
        ("6", "388.1"),
        ("15", "970.3"),
    ],
)
@pytest.mark.parametrize(
    "mode", ["approved_calibration", "known_values", "calibration_pending"]
)
def test_marathon_history_matrix_uses_reviewed_catalog_and_bounded_repeats(
    hours: str, private_target: str, mode: str
) -> None:
    baseline = starting_baseline({Discipline.RUN: Decimal(hours) * Decimal(60)})
    assert baseline.total.value == Decimal(private_target)
    catalog = _durable_run_catalog()
    deck = eligible_workouts(
        catalog=catalog,
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={Discipline.RUN: _run_capability(mode)},
    )
    assert any(template.source_catalog for template in deck)

    kwargs = dict(
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=catalog,
        prior_loads=(),
        goal_disciplines=frozenset({Discipline.RUN}),
        confirmed_injuries=frozenset(),
        zone_capabilities={Discipline.RUN: _run_capability(mode)},
        available_dates=tuple(
            _WEEK_START + timedelta(days=offset) for offset in (0, 2, 5)
        ),
        onboarding_baseline=baseline,
    )
    draft = build_weekly_plan(**kwargs)
    assert draft.target.target == baseline.total
    assert 1 <= len(draft.workouts) <= 24
    assert abs(baseline.total.value - draft.planned_load.value) < min(
        template.internal_planned_load.value
        for template in deck
        if template.internal_planned_load is not None
        and not template.explicit_scheduling_only
    )
    if Decimal(hours) >= 6:
        assert len(draft.workouts) > len(
            {workout.snapshot.template_id for workout in draft.workouts}
        )


@pytest.mark.parametrize(("hours", "expected_count"), [("3", 2), ("6", 9), ("15", 11)])
def test_complete_run_swipes_place_distinct_occurrences_and_submit_payload(
    hours: str, expected_count: int
) -> None:
    baseline = starting_baseline({Discipline.RUN: Decimal(hours) * Decimal(60)})
    catalog = _durable_run_catalog()
    available = tuple(_WEEK_START + timedelta(days=offset) for offset in range(7))

    def build_selected(
        template_ids: tuple[UUID, ...] | None = None,
        occurrence_ids: tuple[UUID, ...] | None = None,
    ) -> WeeklyPlanDraft:
        return build_weekly_plan(
            week_start=_WEEK_START,
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 6),
            catalog=catalog,
            prior_loads=(),
            goal_disciplines=frozenset({Discipline.RUN}),
            confirmed_injuries=frozenset(),
            zone_capabilities={Discipline.RUN: _run_capability("known_values")},
            available_dates=available,
            onboarding_baseline=baseline,
            selected_template_ids=template_ids,
            selected_occurrence_ids=occurrence_ids,
        )

    automatic = build_selected()
    assert len(automatic.workouts) == expected_count

    selection = SwipeSelectionState()
    for workout in automatic.workouts:
        occurrence_id = uuid4()
        selection = apply_swipe_decision(
            selection,
            action=SwipeDecisionKind.ACCEPT,
            current_template_id=workout.snapshot.template_id,
            expected_template_id=workout.snapshot.template_id,
            current_occurrence_id=occurrence_id,
            expected_occurrence_id=occurrence_id,
            target_workout_count=expected_count,
        )
    assert len(selection.accepted_template_ids) == expected_count
    assert len(set(selection.accepted_occurrence_ids)) == expected_count

    placed = build_selected(
        selection.accepted_template_ids, selection.accepted_occurrence_ids
    )
    assert len(placed.workouts) == expected_count
    assert {workout.occurrence_id for workout in placed.workouts} == set(
        selection.accepted_occurrence_ids
    )
    assert {workout.scheduled_date for workout in placed.workouts} <= set(available)
    if expected_count > len(available):
        assert (
            len({workout.scheduled_date for workout in placed.workouts})
            < expected_count
        )
    payload = PlanningService._proposal_payload(
        request_id=uuid4(),
        input_fingerprint="a" * 32,
        generation_fingerprint="b" * 64,
        plan_id=None,
        expected_base_revision=0,
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        available_dates=available,
        availability_source="athlete_selected",
        injuries=frozenset(),
        low_only_disciplines=frozenset(),
        goal_disciplines=frozenset({Discipline.RUN}),
        draft=placed,
        workout_source="generated",
    )
    rows = payload["workouts"]
    assert isinstance(rows, list)
    assert len(rows) == expected_count
    assert {row["occurrence_id"] for row in rows} == {
        str(occurrence_id) for occurrence_id in selection.accepted_occurrence_ids
    }
    if hours != "3":
        assert len({row["template_id"] for row in rows}) < len(rows)


@pytest.mark.parametrize(
    "minutes",
    [
        {Discipline.BIKE: Decimal(180)},
        {Discipline.BIKE: Decimal(180), Discipline.RUN: Decimal(120)},
        {
            Discipline.SWIM: Decimal(60),
            Discipline.BIKE: Decimal(180),
            Discipline.RUN: Decimal(120),
        },
    ],
)
def test_other_ordinary_goal_compositions_use_bounded_repeats(
    minutes: dict[Discipline, Decimal],
) -> None:
    capabilities = {
        Discipline.SWIM: ZoneCapability(frozenset({ZoneRequirement.PACE})),
        Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.POWER})),
        Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
    }
    draft = build_weekly_plan(
        week_start=_WEEK_START,
        timezone_name="Europe/Amsterdam",
        race_date=date(2026, 12, 6),
        catalog=active_catalog(),
        prior_loads=(),
        goal_disciplines=frozenset(minutes),
        confirmed_injuries=frozenset(),
        zone_capabilities=capabilities,
        available_dates=(_WEEK_START,),
        onboarding_baseline=starting_baseline(minutes),
    )
    assert {workout.discipline for workout in draft.workouts} == set(minutes)
    assert len(draft.workouts) <= 24
    assert abs(draft.target.target.value - draft.planned_load.value) < Decimal("36.3")


def test_race_anchored_build_block_progresses_and_releases_z5_in_week_four() -> None:
    catalog = _durable_run_catalog()
    starts = (
        date(2026, 7, 20),
        date(2026, 7, 27),
        date(2026, 8, 3),
        date(2026, 8, 10),
    )
    history = [
        PlanLoadSample(
            week_start=starts[0] - timedelta(days=7),
            load=InternalLoad(Decimal("300")),
            realized_load=InternalLoad(Decimal("300")),
            phase=TrainingPhase.BUILD,
        )
    ]
    targets: list[Decimal] = []
    for expected_build_week, week_start in enumerate(starts, start=1):
        draft = build_weekly_plan(
            week_start=week_start,
            timezone_name="Europe/Amsterdam",
            race_date=date(2026, 12, 6),
            catalog=catalog,
            prior_loads=tuple(history),
            goal_disciplines=frozenset({Discipline.RUN}),
            confirmed_injuries=frozenset(),
            zone_capabilities={Discipline.RUN: _run_capability("known_values")},
            available_dates=tuple(
                week_start + timedelta(days=offset) for offset in (0, 2, 5)
            ),
        )
        assert draft.target.phase is TrainingPhase.BUILD
        assert draft.target.build_week == expected_build_week
        target = draft.target.target.value
        targets.append(target)
        high_load = sum(
            (
                workout.snapshot.internal_planned_load.value
                for workout in draft.workouts
                if workout.snapshot.intensity_bucket is IntensityBucket.HIGH
            ),
            Decimal(0),
        )
        nominal_high = target * draft.target.desired_high_fraction.value
        assert high_load <= nominal_high
        has_z5 = any(
            segment.zone_target is TrainingZone.ZONE_5
            for workout in draft.workouts
            for segment in workout.snapshot.segments
        )
        if expected_build_week < 4:
            assert nominal_high * Decimal("0.70") <= high_load
            assert high_load <= nominal_high * Decimal("0.90")
            assert not has_z5
        else:
            assert has_z5
        history.append(
            PlanLoadSample(
                week_start=week_start,
                load=draft.target.target,
                realized_load=draft.target.target,
                phase=TrainingPhase.BUILD,
            )
        )
    assert targets == sorted(targets)
    assert len(set(targets)) == 4
