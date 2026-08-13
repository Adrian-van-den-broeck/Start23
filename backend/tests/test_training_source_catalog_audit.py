from pathlib import Path

from app.modules.workouts.source_catalog_audit import audit_source_catalog


def test_phase_8_source_catalog_is_audited_without_inventing_taper_rows() -> None:
    source = (
        Path(__file__).parents[2]
        / "docs"
        / "trainings"
        / "Trainingen START23.v01.xlsx - Sheet1.csv"
    )

    audit = audit_source_catalog(source)

    assert audit.row_count == 160
    assert audit.sport_counts == {"Fietsen": 50, "Lopen": 50, "Zwemmen": 60}
    assert audit.bucket_counts == {"80%": 73, "20%": 87}
    assert audit.issue_counts == {"duration": 60}
    assert audit.taper_marker_present is False
    assert audit.structurally_importable is False
