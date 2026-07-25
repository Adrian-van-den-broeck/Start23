"""Architecture tests for the deterministic physiology module."""

import ast
from pathlib import Path

_FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "openai",
    "sqlalchemy",
    "supabase",
}


def test_physiology_module_has_no_framework_or_io_imports() -> None:
    """Physiology code remains pure Python without API, database, or LLM clients."""
    module_root = Path(__file__).parents[2] / "app" / "modules" / "physiology"

    imported_roots: set[str] = set()
    for path in module_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", maxsplit=1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])

    assert imported_roots.isdisjoint(_FORBIDDEN_IMPORT_ROOTS)
