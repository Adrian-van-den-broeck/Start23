"""Exact A8 logical outputs and intermediates; deliberately no timing assertions."""

import json
from pathlib import Path

import pytest

from benchmarks.planning import SCENARIOS, calculate, digest, full_catalog, scenario

EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / "docs/audits/remediation/evidence/a9/backend-baseline.json"
)
BASELINE = json.loads(EVIDENCE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", SCENARIOS)
def test_a8_deterministic_parity(name: str) -> None:
    catalog = full_catalog()
    assert digest(catalog) == BASELINE["catalog_sha256"]
    inputs = scenario(name, catalog)
    expected = BASELINE["cases"][name]
    # Never silently accept a different input corpus as deterministic parity.
    assert digest(inputs) == expected["input_sha256"]
    assert calculate(inputs) == {
        key: value
        for key, value in expected.items()
        if key in {"outcome", "code", "output_sha256", "trace"}
    }
