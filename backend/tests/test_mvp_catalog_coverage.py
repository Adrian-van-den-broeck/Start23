"""Private evidence for the remaining reviewed automatic-catalog gap."""

import json
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.modules.physiology.joren import starting_baseline
from app.modules.physiology.models import Discipline
from app.modules.planning.domain import (
    PlanningConstraintError,
    ZoneCapability,
    build_weekly_plan,
    eligible_workouts,
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
    """Recreate the existing source RPC rows without changing their review flag."""
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
                "athlete_selection_only": True,
                "source_catalog": "start23-v0.1",
                "training_phases": (
                    ["base", "build", "recovery"]
                    if source["intensity_bucket"] == "low"
                    else ["base", "build"]
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
def test_source_run_catalog_is_athlete_selected_in_each_zone_state(mode: str) -> None:
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
        template
        for template in deck
        if not template.athlete_selection_only and not template.explicit_scheduling_only
    )

    assert len(source) == 50
    assert all(template.athlete_selection_only for template in source)
    assert len(deck) == 51
    assert len(automatic) == 1
    assert automatic[0].name == "Easy aerobic run"
    if mode == "calibration_pending":
        assert all(
            segment.zone_target is None
            for template in deck
            for segment in template.segments
        )


@pytest.mark.parametrize(
    ("hours", "private_target", "private_gap", "count"),
    [
        ("0", "45.0", "8.70", 1),
        ("1", "64.7", "28.40", 1),
        ("3", "194.1", "157.80", None),
        ("6", "388.1", "351.80", None),
        ("15", "970.3", "934.00", None),
    ],
)
@pytest.mark.parametrize(
    "mode", ["approved_calibration", "known_values", "calibration_pending"]
)
def test_marathon_history_matrix_retains_explicit_catalog_gap(
    hours: str, private_target: str, private_gap: str, count: int | None, mode: str
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
    automatic = tuple(
        template
        for template in deck
        if not template.athlete_selection_only and not template.explicit_scheduling_only
    )
    capacity = sum(
        (
            template.internal_planned_load.value
            for template in automatic
            if template.internal_planned_load is not None
        ),
        Decimal(0),
    )
    assert baseline.total.value - capacity == Decimal(private_gap)

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
    if count is None:
        with pytest.raises(PlanningConstraintError) as error:
            build_weekly_plan(**kwargs)
        assert error.value.code == "catalog_capacity_unsatisfied"
        assert "tss" not in str(error.value).casefold()
    else:
        draft = build_weekly_plan(**kwargs)
        assert len(draft.workouts) == count
        assert draft.target.target == baseline.total
        assert baseline.total.value - draft.planned_load.value == Decimal(private_gap)


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
def test_other_ordinary_goal_compositions_fail_explicitly_when_deck_is_small(
    minutes: dict[Discipline, Decimal],
) -> None:
    capabilities = {
        Discipline.SWIM: ZoneCapability(frozenset({ZoneRequirement.PACE})),
        Discipline.BIKE: ZoneCapability(frozenset({ZoneRequirement.POWER})),
        Discipline.RUN: ZoneCapability(frozenset({ZoneRequirement.HEART_RATE})),
    }
    with pytest.raises(PlanningConstraintError) as error:
        build_weekly_plan(
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
    assert error.value.code == "catalog_capacity_unsatisfied"
