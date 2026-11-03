"""Actual immutable catalog coverage, with independently expected source IDs."""

from benchmarks.realized_v2 import catalog_coverage


def test_per_sport_structural_coverage_and_exact_eligible_source_ids() -> None:
    coverage = catalog_coverage()
    assert [
        (coverage[sport]["total"], coverage[sport]["structurally_eligible"])
        for sport in ("swim", "bike", "run")
    ] == [(56, 0), (54, 5), (52, 5)]
    assert coverage["bike"]["eligible_source_or_template_ids"] == [
        "BIK-001",
        "BIK-002",
        "BIK-003",
        "BIK-004",
        "BIK-005",
    ]
    assert coverage["run"]["eligible_source_or_template_ids"] == [
        "RUN-001",
        "RUN-002",
        "RUN-003",
        "RUN-004",
        "RUN-005",
    ]
    assert coverage["swim"]["source_total"] == 54
