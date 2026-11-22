"""The separator repair restores exactly the text the catalog generator produced."""

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS = _ROOT / "supabase" / "migrations"
_IMPORT = _MIGRATIONS / "20260903074359_add_source_catalog_training_options.sql"
_REPAIR = _MIGRATIONS / "20261122120000_repair_source_catalog_separator.sql"
_GENERATOR = _ROOT / "backend" / "scripts" / "generate_source_catalog_payload.py"
_REPLACEMENT = "�"
_MIDDLE_DOT = "·"


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("catalog_generator", _GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stored_payload() -> list[dict[str, object]]:
    sql = _IMPORT.read_text(encoding="utf-8")
    match = re.search(r"\$catalog\$(.*?)\$catalog\$", sql, flags=re.DOTALL)
    assert match is not None
    payload = json.loads(match.group(1))
    assert isinstance(payload, list)
    return payload


def test_import_stored_replacement_characters_where_the_generator_wrote_dots() -> None:
    generated = _generator().generate_payload()
    stored = _stored_payload()

    assert _REPLACEMENT in json.dumps(stored, ensure_ascii=False)
    repaired = json.loads(
        json.dumps(stored, ensure_ascii=False).replace(_REPLACEMENT, _MIDDLE_DOT)
    )
    # Only the separator differs: ids, measures, loads and segments are identical.
    assert repaired == generated


def test_generator_refuses_to_emit_replacement_characters() -> None:
    rendered = _generator().render_payload()

    assert _REPLACEMENT not in rendered
    assert f"BIK-012 {_MIDDLE_DOT} Techniek" in rendered


def test_repair_is_text_only_and_restores_every_guard() -> None:
    sql = _REPAIR.read_text(encoding="utf-8")

    assert _REPLACEMENT not in sql
    for trigger in (
        "workout_templates_are_immutable",
        "workout_segments_are_immutable",
    ):
        assert sql.count(f"disable trigger {trigger}") == 1
        assert sql.count(f"enable trigger {trigger}") == 1
        assert sql.index(f"disable trigger {trigger}") < sql.index(
            f"enable trigger {trigger}"
        )
    assert "set_config('start23.critical_write', '', true)" in sql
    statements = re.findall(r"^update public\.(\w+)", sql, flags=re.MULTILINE)
    assert statements == ["workout_templates", "workout_segments", "planned_workouts"]
    for column in ("duration_minutes", "distance_meters", "planned_tss", "version"):
        assert f"{column} =" not in sql
    assert "replace(" in sql and "chr(65533), chr(183)" in sql
