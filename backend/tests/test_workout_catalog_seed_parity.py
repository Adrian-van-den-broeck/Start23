"""Prevent the reviewed Python and durable SQL workout seeds from drifting."""

import ast
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.modules.workouts.catalog import PHASE_6_CATALOG_ADDITIONS, REVIEWED_CATALOG

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260727170000_phase_5_workout_catalog.sql"
)
_PHASE_6_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260729140000_phase_6_weekly_planning.sql"
)


def _insert_rows(
    table: str,
    migration: Path = _MIGRATION,
) -> list[tuple[Any, ...]]:
    sql = migration.read_text(encoding="utf-8")
    match = re.search(
        rf"insert into {re.escape(table)}\s*\([^;]+?\)\s*values\s*(.*?);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match is not None, f"Missing reviewed seed insert for {table}."
    values = re.sub(r"\bnull\b", "None", match.group(1), flags=re.IGNORECASE)
    values = re.sub(r"\btrue\b", "True", values, flags=re.IGNORECASE)
    values = re.sub(r"\bfalse\b", "False", values, flags=re.IGNORECASE)
    parsed = ast.literal_eval(f"[{values}]")
    return [tuple(row) for row in parsed]


def _load_rows(migration: Path = _MIGRATION) -> set[tuple[str, Decimal]]:
    sql = migration.read_text(encoding="utf-8")
    match = re.search(
        r"insert into private\.workout_template_loads\s*"
        r"\([^;]+?\)\s*values\s*(.*?);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match is not None
    return {
        (template_id, Decimal(planned_tss))
        for template_id, planned_tss in re.findall(
            r"\('([^']+)',\s*([0-9]+(?:\.[0-9]+)?)\s*,",
            match.group(1),
        )
    }


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def test_python_catalog_matches_every_durable_sql_seed_field() -> None:
    template_rows = _insert_rows("public.workout_templates")
    expected_templates = [
        (
            str(template.id),
            str(template.template_key),
            template.version,
            template.discipline.value,
            template.name,
            template.description,
            template.duration_minutes,
            template.distance_meters,
            template.intensity_bucket.value,
            template.expected_rpe_min,
            template.expected_rpe_max,
            template.fallback_compatibility.value,
        )
        for template in REVIEWED_CATALOG
    ]
    actual_templates = [(*row[:6], _decimal(row[6]), *row[7:]) for row in template_rows]
    assert actual_templates == expected_templates

    expected_segments = [
        (
            str(template.id),
            segment.sequence,
            segment.name,
            segment.instructions,
            segment.duration_minutes,
            segment.distance_meters,
            segment.zone.value,
            segment.expected_rpe,
            segment.is_swim_technique,
        )
        for template in REVIEWED_CATALOG
        for segment in template.segments
    ]
    actual_segments = [
        (*row[:4], _decimal(row[4]), *row[5:])
        for row in _insert_rows("public.workout_segments")
    ]
    assert actual_segments == expected_segments

    expected_phases = {
        (str(template.id), phase.value)
        for template in REVIEWED_CATALOG
        for phase in template.training_phases
    }
    assert set(_insert_rows("public.workout_template_phase_tags")) == expected_phases

    expected_requirements = {
        (str(template.id), requirement.value)
        for template in REVIEWED_CATALOG
        for requirement in template.zone_requirements
    }
    assert (
        set(_insert_rows("public.workout_template_zone_requirements"))
        == expected_requirements
    )

    expected_loads = {
        (str(template.id), template.internal_planned_load.value)
        for template in REVIEWED_CATALOG
    }
    actual_loads = _load_rows()
    assert actual_loads == expected_loads


def test_phase_6_catalog_addition_matches_its_durable_seed() -> None:
    template = PHASE_6_CATALOG_ADDITIONS[0]
    template_rows = _insert_rows(
        "public.workout_templates",
        _PHASE_6_MIGRATION,
    )
    assert [(*row[:6], _decimal(row[6]), *row[7:]) for row in template_rows] == [
        (
            str(template.id),
            str(template.template_key),
            template.version,
            template.discipline.value,
            template.name,
            template.description,
            template.duration_minutes,
            template.distance_meters,
            template.intensity_bucket.value,
            template.expected_rpe_min,
            template.expected_rpe_max,
            template.fallback_compatibility.value,
        )
    ]
    assert [
        (*row[:4], _decimal(row[4]), *row[5:])
        for row in _insert_rows(
            "public.workout_segments",
            _PHASE_6_MIGRATION,
        )
    ] == [
        (
            str(template.id),
            segment.sequence,
            segment.name,
            segment.instructions,
            segment.duration_minutes,
            segment.distance_meters,
            segment.zone.value,
            segment.expected_rpe,
            segment.is_swim_technique,
        )
        for segment in template.segments
    ]
    assert set(
        _insert_rows(
            "public.workout_template_phase_tags",
            _PHASE_6_MIGRATION,
        )
    ) == {(str(template.id), phase.value) for phase in template.training_phases}
    assert set(
        _insert_rows(
            "public.workout_template_zone_requirements",
            _PHASE_6_MIGRATION,
        )
    ) == {
        (str(template.id), requirement.value)
        for requirement in template.zone_requirements
    }
    assert {
        (str(row[0]), _decimal(row[1]))
        for row in _insert_rows(
            "private.workout_template_loads",
            _PHASE_6_MIGRATION,
        )
    } == {(str(template.id), template.internal_planned_load.value)}
