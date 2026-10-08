# ruff: noqa: E402
# The pinned backend path must be installed before importing the local oracle.
"""Offline source manifest and syntactic decision inventory; no database access."""

import ast
import dataclasses
import enum
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/joren-training-review"
sys.path.insert(0, str(ROOT / "backend"))
from app.modules.workouts.catalog import CURRENT_CATALOG, active_catalog
from app.modules.workouts.repository import parse_planning_catalog


def json_value(value):
    if dataclasses.is_dataclass(value):
        return {
            f.name: json_value(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, dict):
        return {str(json_value(k)): json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_value(v) for v in value]
    return value


sql = (
    ROOT / "supabase/migrations/20260903074359_add_source_catalog_training_options.sql"
).read_text(encoding="utf8")
raw = json.loads(
    re.search(r"\$catalog\$(.*?)\$catalog\$::jsonb", sql, re.DOTALL).group(1)
)
successor_sql = (
    ROOT / "supabase/migrations/20260929210000_joren_planning_ruleset_v2.sql"
).read_text(encoding="utf8")
rows = []
for s in raw:
    row = {
        **s,
        "fallback_compatibility": "compatible",
        "explicit_scheduling_only": False,
        "athlete_selection_only": False,
        "source_catalog": "start23-v0.1",
        "version": 2,
        "training_phases": ["build"]
        if any(x.get("zone_number", 0) > 2 for x in s["segments"])
        else ["base", "build", "recovery", "taper"],
        "zone_requirements": [],
        "segments": [{**x, "is_swim_technique": False} for x in s["segments"]],
    }
    # v2 generates new random UUIDs. Retained v1 IDs are explicitly local fixture IDs.
    # They do not establish deployed identity or tie-breaker parity.
    rows.append(row)
imported = parse_planning_catalog(tuple(rows))
catalog = active_catalog((*CURRENT_CATALOG, *imported))
(OUT / "fixtures/catalog.json").write_text(
    json.dumps(json_value(catalog), ensure_ascii=False, indent=2), encoding="utf8"
)
(OUT / "fixtures/catalog_encoding_gaps.json").write_text(
    json.dumps(
        [
            {"id": str(x.id), "name": x.name, "description": x.description}
            for x in catalog
            if any("\ufffd" in v for v in (x.name, x.description))
        ],
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf8",
)
(OUT / "fixtures/source_catalog_original.json").write_text(
    json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf8"
)
modules = [
    "physiology",
    "planning",
    "calibration",
    "activities",
    "checkins",
    "onboarding",
    "workouts",
    "integrations",
]
paths = []
for m in modules:
    paths.extend(sorted((ROOT / "backend/app/modules" / m).glob("*.py")))
paths.extend(sorted((ROOT / "supabase/migrations").glob("*.sql")))
paths.extend(sorted((ROOT / "backend/tests").rglob("*.py")))
paths.extend(sorted((ROOT / "supabase/tests").glob("*.sql")))
paths.extend(sorted((ROOT / "mobile").rglob("AGENTS.md")))
manifest = []
functions = []
decisions = []
constants = []
for p in paths:
    text = p.read_text(encoding="utf-8-sig")
    rel = p.relative_to(ROOT).as_posix()
    manifest.append(
        {
            "path": rel,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "lines": len(text.splitlines()),
        }
    )
    if p.suffix != ".py" or "/app/modules/" not in rel:
        continue
    tree = ast.parse(text)
    owners = {}

    def walk(n, parent="", owners=owners):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parent = parent + "." + n.name if parent else n.name
        owners[id(n)] = parent
        for child in ast.iter_child_nodes(n):
            walk(child, parent)

    walk(tree)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "id": f"FN-{len(functions) + 1:04d}",
                    "path": rel,
                    "function": owners[id(n)],
                    "start": n.lineno,
                    "end": n.end_lineno,
                    "description": ast.get_docstring(n)
                    or "Geen functiedocumentatie in bron.",
                    "inputs": ast.unparse(n.args),
                    "return_type": ast.unparse(n.returns) if n.returns else None,
                    "classification": (
                        "CURRENT IMPLEMENTATION; reachability review required"
                    ),
                    "failure": [
                        ast.unparse(x.exc)
                        for x in ast.walk(n)
                        if isinstance(x, ast.Raise) and x.exc
                    ],
                    "formula_assignments": [
                        {"line": x.lineno, "expression": ast.unparse(x)}
                        for x in ast.walk(n)
                        if isinstance(x, (ast.Assign, ast.AnnAssign, ast.Return))
                        and any(isinstance(t, ast.BinOp) for t in ast.walk(x))
                    ],
                    "excel": "NOT IMPLEMENTED unless covered by explicit rule map",
                    "manual_review": "OPEN",
                }
            )
        if isinstance(n, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            decisions.append(
                {
                    "id": f"DEC-{len(decisions) + 1:04d}",
                    "path": rel,
                    "function": owners[id(n)],
                    "line": n.lineno,
                    "kind": type(n).__name__,
                    "condition": ast.unparse(n.test),
                    "true_outcome": "source branch",
                    "false_outcome": "source alternative",
                    "coverage": "NOT VERIFIED",
                }
            )
        if isinstance(n, ast.comprehension):
            for cond in n.ifs:
                decisions.append(
                    {
                        "id": f"DEC-{len(decisions) + 1:04d}",
                        "path": rel,
                        "function": owners.get(id(cond), ""),
                        "line": cond.lineno,
                        "kind": "comprehension_filter",
                        "condition": ast.unparse(cond),
                        "coverage": "NOT VERIFIED",
                    }
                )
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(x, ast.Name) and x.id.upper() == x.id for x in targets):
                constants.append(
                    {"path": rel, "line": n.lineno, "expression": ast.unparse(n)}
                )
for name, value in [
    ("source_manifest", manifest),
    ("function_inventory", functions),
    ("decision_inventory", decisions),
    ("constant_inventory", constants),
]:
    (OUT / "fixtures" / f"{name}.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf8"
    )
print(
    json.dumps(
        {
            "source_files": len(manifest),
            "function_records": len(functions),
            "syntactic_decisions": len(decisions),
            "catalog": len(catalog),
            "source_rows": len(raw),
            "catalog_identity_gate": "successor SQL transformation requires review",
        }
    )
)
