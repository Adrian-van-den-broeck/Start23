"""Parity checks for time- or distance-driven START23 catalog alternatives."""

import csv
import json
import re
from decimal import Decimal
from pathlib import Path

from app.modules.physiology.models import Discipline, InternalLoad
from app.modules.planning.domain import eligible_workouts, select_workouts
from app.modules.planning.repository import JsonObject
from app.modules.planning.service import PlanningService
from app.modules.workouts.catalog import TrainingPhase, WorkoutTemplate
from app.modules.workouts.repository import parse_planning_catalog

_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = _ROOT / "docs" / "trainings" / "Trainingen START23.v01.xlsx - Sheet1.csv"
_MIGRATION = (
    _ROOT
    / "supabase"
    / "migrations"
    / "20260903074359_add_source_catalog_training_options.sql"
)


def _migration_catalog() -> list[dict[str, object]]:
    sql = _MIGRATION.read_text(encoding="utf-8")
    match = re.search(
        r"jsonb_to_recordset\(\$catalog\$(.*?)\$catalog\$::jsonb\)",
        sql,
        flags=re.DOTALL,
    )
    assert match is not None
    payload = json.loads(match.group(1))
    assert isinstance(payload, list)
    return payload


def _runtime_template(source_workout_id: str) -> WorkoutTemplate:
    imported = next(
        row
        for row in _migration_catalog()
        if row["source_workout_id"] == source_workout_id
    )
    segments = imported["segments"]
    assert isinstance(segments, list)
    rpc_row = {
        **imported,
        "fallback_compatibility": "compatible",
        "explicit_scheduling_only": False,
        "athlete_selection_only": True,
        "source_catalog": "start23-v0.1",
        "training_phases": ["base", "build", "recovery"],
        "zone_requirements": [],
        "segments": [{**segment, "is_swim_technique": False} for segment in segments],
    }
    return parse_planning_catalog((rpc_row,))[0]


def test_import_contains_every_source_row_without_guessing_swim_duration() -> None:
    with _SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {row["ID"] for row in rows}
    imported = _migration_catalog()

    assert len(imported) == 154
    assert {str(row["source_workout_id"]) for row in imported} == expected
    swim = [row for row in imported if row["discipline"] == "swim"]
    assert len(swim) == 54
    assert all(row["duration_minutes"] is None for row in swim)
    assert all(int(str(row["distance_meters"])) > 0 for row in swim)


def test_import_preserves_declared_bucket_private_load_and_segment_measure() -> None:
    with _SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        source = {row["ID"]: row for row in csv.DictReader(handle)}

    for imported in _migration_catalog():
        source_row = source[str(imported["source_workout_id"])]
        expected_bucket = "low" if source_row["Emmer (80/20)"] == "80%" else "high"
        segments = imported["segments"]
        assert isinstance(segments, list)
        assert imported["intensity_bucket"] == expected_bucket
        assert str(imported["planned_tss"]) == source_row["TSS"]
        if imported["discipline"] == "swim":
            assert all(segment["duration_minutes"] is None for segment in segments)
            assert sum(
                int(str(segment["distance_meters"])) for segment in segments
            ) == int(str(imported["distance_meters"]))
        else:
            assert sum(
                int(str(segment["duration_minutes"])) for segment in segments
            ) == int(str(imported["duration_minutes"]))


def test_distance_only_swim_payload_parses_as_runtime_catalog_template() -> None:
    template = _runtime_template("SWI-007")

    assert template.duration_minutes is None
    assert template.distance_meters == 2500
    assert template.athlete_selection_only is True
    assert template.source_catalog == "start23-v0.1"


def test_calibration_week_can_choose_source_workout_without_calibration_test() -> None:
    source_workout = _runtime_template("BIK-001")
    snapshot: JsonObject = {
        "profile": {"timezone": "Europe/Amsterdam"},
        "goal": {
            "target_date": "2026-12-06",
            "race_discipline_profile": ["bike"],
        },
        "zones": [],
        "discipline_setups": [
            {
                "discipline": "bike",
                "setup_route": "calibration_week",
                "setup_status": "calibration_pending",
                "protocol_id": "start23_week1_bike_calibration_v1",
            }
        ],
    }
    _, _, _, capabilities = PlanningService._context_values(snapshot)
    deck = eligible_workouts(
        catalog=(source_workout,),
        phase=TrainingPhase.BASE,
        goal_disciplines=frozenset({Discipline.BIKE}),
        confirmed_injuries=frozenset(),
        zone_capabilities=capabilities,
    )

    selected = select_workouts(
        deck=deck,
        required_disciplines=frozenset({Discipline.BIKE}),
        target=InternalLoad(Decimal("999")),
        selected_template_ids=(source_workout.id,),
    )

    assert len(deck) == 1
    assert selected[0].snapshot.template_id == source_workout.id
    assert all(
        segment.protocol_target is None for segment in selected[0].snapshot.segments
    )
