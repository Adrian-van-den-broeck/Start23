"""C1 uses original OOXML as an independent oracle, never active catalog input."""

import json
import shutil
import socket
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from uuid import UUID
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from app.jobs.joren_catalog_dry_run import main, offline_reserved_ids, write_immutable
from app.modules.workouts import joren_draft as draft
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    active_catalog,
    snapshot_template,
)
from benchmarks.planning import full_catalog

IDS = tuple(
    f"TR-{sport}-{i:03d}"
    for sport, count in (("RUN", 20), ("BIKE", 21), ("SWIM", 20))
    for i in range(1, count + 1)
)
GOLDEN = draft.ROOT / "docs/catalog/implementation/joren_c1_manifest_v1.json"


@pytest.fixture(scope="module")
def manifest() -> draft.DraftManifest:
    return draft.build_manifest(reserved=offline_reserved_ids())


def _original_cells(spec: draft.SourceSpec) -> dict[str, ET.Element]:
    with ZipFile(draft.DEFAULT_SOURCES / spec.filename) as archive:
        tree = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    return {c.attrib["r"]: c for c in tree.findall("x:sheetData/x:row/x:c", draft.NS)}


@pytest.mark.parametrize("identifier", IDS)
def test_every_original_value_and_ordered_event(
    manifest: draft.DraftManifest, identifier: str
) -> None:
    record = next(r for r in manifest.records if r.original_workout_id == identifier)
    document = next(d for d in manifest.documents if d.spec.sport == record.sport)
    originals = _original_cells(document.spec)
    assert len(record.original_cells) == 15
    for cell in record.original_cells:
        original = originals[cell.coordinate]
        assert cell.cell_type == original.attrib["t"]
        if cell.cell_type == "n":
            assert cell.numeric_lexeme == original.findtext("x:v", namespaces=draft.NS)
            assert Decimal(cell.numeric_lexeme or "NaN").is_finite()
        else:
            assert cell.value == "".join(original.itertext())
        assert cell.xml == ET.tostring(original, encoding="unicode")
        assert cell.formula is None and cell.cached_value is None
    raw = "".join(originals[f"N{record.source_row}"].itertext())
    tokens = raw.split("|")
    assert len(tokens) == len(record.events)
    assert "|".join(e.raw_token for e in record.events) == raw
    zone_totals = [Decimal(0)] * 5
    for position, (token, event) in enumerate(zip(tokens, record.events), 1):
        assert event.sequence == position
        assert event.raw_token == token == raw[event.start : event.end]
        assert event.source_cell == f"N{record.source_row}"
        amount, target = token.strip().split(" ")
        value, unit = Decimal(amount[:-1]), amount[-1]
        if target == "Rust":
            assert isinstance(event, draft.WallRest)
            assert event.seconds == value and unit == "s"
            assert event.zone is event.rpe is event.distance_meters is None
        elif record.sport == "swim":
            assert isinstance(event, draft.SwimDistance) and unit == "m"
            assert event.meters == value and event.duration_seconds is None
            assert event.zone == int(target[1:])
            zone_totals[event.zone - 1] += value
        else:
            assert isinstance(event, draft.TimedZone)
            assert event.seconds == value * (60 if unit == "m" else 1)
            assert event.zone == int(target[1:])
            zone_totals[event.zone - 1] += event.seconds / 60
    assert tuple(zone_totals) == record.original_zone_distribution
    assert sum(zone_totals) == record.original_measure
    assert record.original_expected_rpe == record.original_cells[3].value
    assert record.original_training_name == record.original_cells[2].value
    assert record.original_training_focus == record.original_cells[14].value
    if record.sport == "swim":
        assert record.planned_duration_seconds is None
        assert record.planned_distance_meters == sum(zone_totals)
        assert record.distribution_unit == "meters"
    else:
        assert record.planned_duration_seconds == sum(zone_totals) * 60
        assert record.planned_distance_meters is None
        assert record.distribution_unit == "minutes"


@pytest.mark.parametrize("identifier", IDS)
def test_every_private_load_reference_and_metadata_remains_draft(
    manifest: draft.DraftManifest, identifier: str
) -> None:
    record = next(r for r in manifest.records if r.original_workout_id == identifier)
    load = record.load
    assert load.original_source_tss == Decimal(record.original_cells[12].value or "NaN")
    assert load.source_numeric_lexeme == record.original_cells[12].numeric_lexeme
    assert load.source_significant_digits == len(
        load.original_source_tss.as_tuple().digits
    )
    assert load.source_decimal_exponent == load.original_source_tss.as_tuple().exponent
    # Review references are independently materialized; no IF² execution is required.
    report = (draft.DEFAULT_SOURCES.parent / draft.PROPOSAL_FILE).read_text(
        encoding="utf-8"
    )
    numeric = next(
        line for line in report.splitlines() if line.startswith(f"| {identifier} /")
    )
    columns = [value.strip() for value in numeric.split("|")[1:-1]]
    assert load.original_source_tss == Decimal(columns[2])
    expected_reference = columns[4] if record.sport == "swim" else columns[3]
    assert load.mathematical_reference == Decimal(expected_reference)
    assert load.approved_operational_tss is None
    assert (
        load.operational_status == "UNAVAILABLE" and load.approval_status == "PENDING"
    )
    assert record.catalog_release is record.operational_method_version is None
    assert (
        record.activation_status == "INACTIVE" and record.acceptance_state == "PENDING"
    )
    for selection_field in fields(record.selection):
        value = getattr(record.selection, selection_field.name)
        if isinstance(value, draft.DraftField):
            assert value.state == "DRAFT"
    assert record.selection.original_columns[0] == identifier
    assert (
        record.selection.beginner_eligibility.proposal is None
        or identifier == "TR-BIKE-013"
    )
    assert record.selection.source_method_compatibility.proposal is None
    assert record.selection.swim_distance_planning_compatibility.proposal is None


def test_complete_coverage_and_stable_provisional_identities(
    manifest: draft.DraftManifest,
) -> None:
    assert tuple(r.original_workout_id for r in manifest.records) == IDS
    assert not manifest.errors
    assert len({r.provisional_id for r in manifest.records}) == 61
    assert len({r.provisional_key for r in manifest.records}) == 61
    assert draft.provisional_identity("run", "TR-RUN-001", draft.SOURCES[0].sha256) == (
        UUID("d8520c07-aadb-5529-a0c7-6b78cf53ae15"),
        UUID("9d732bc4-85c9-52f9-a2ce-6caac4b841be"),
    )
    assert draft.provisional_identity(
        "bike", "TR-BIKE-001", draft.SOURCES[1].sha256
    ) == (
        UUID("b2cfa062-b8a8-51be-af35-41054fb4b2a7"),
        UUID("7b71861a-c2d0-5176-86e0-b338731d9824"),
    )
    assert draft.provisional_identity(
        "swim", "TR-SWIM-001", draft.SOURCES[2].sha256
    ) == (
        UUID("9c9e54eb-b2a7-5e02-8aba-d7999909565c"),
        UUID("d176d407-a925-53a1-a708-4535237304c7"),
    )
    draft.validate_identities(manifest.records, offline_reserved_ids())


def test_decimal_residue_and_thirty_second_sprints(
    manifest: draft.DraftManifest,
) -> None:
    records = {r.original_workout_id: r for r in manifest.records}
    for identifier, raw, displayed in (
        ("TR-RUN-017", "87.59999999999999", "87.6"),
        ("TR-BIKE-004", "84.40000000000001", "84.4"),
        ("TR-BIKE-021", "96.09999999999999", "96.1"),
    ):
        assert records[identifier].load.source_numeric_lexeme == raw
        assert records[identifier].load.original_displayed_value == displayed
    for identifier, count in (("TR-BIKE-020", 6), ("TR-BIKE-021", 8)):
        sprints = [
            e
            for e in records[identifier].events
            if isinstance(e, draft.TimedZone) and e.zone == 5
        ]
        assert len(sprints) == count
        assert all(e.seconds == Decimal(30) for e in sprints)
        assert sum(e.seconds for e in sprints) / 60 == Decimal(count) / 2
    swim = records["TR-SWIM-010"]
    assert swim.stationary_rest_seconds == 150
    assert swim.load.original_source_tss == Decimal("28.4")
    assert swim.load.mathematical_reference == Decimal("28.44")
    assert "HELD" in (
        records["TR-BIKE-013"].selection.beginner_eligibility.proposal or ""
    )


@pytest.mark.parametrize(
    "sport,text",
    [
        ("run", "30m Z1 garbage"),
        ("run", "0m Z1"),
        ("run", "-1m Z2"),
        ("run", "NaNm Z2"),
        ("bike", "30m Z6"),
        ("bike", "30 Z2"),
        ("bike", "30s Rust"),
        ("swim", "30s Z2"),
        ("swim", "30m Rust"),
        ("swim", "0s Rust"),
        ("swim", "0.5m Z2"),
        ("run", "1m Z1 || 1m Z1"),
        ("run", "1m Z1 |"),
        ("run", ""),
    ],
)
def test_malformed_tokens_fail_closed(sport: draft.Sport, text: str) -> None:
    with pytest.raises(draft.SourceError):
        draft.parse_events(text, sport, "N5")


@pytest.mark.parametrize(
    "index,value",
    [(5, "31"), (7, "29"), (12, "NaN"), (12, "Infinity"), (4, "2.5"), (6, "-1")],
)
def test_malformed_row_aggregates_and_numbers(
    manifest: draft.DraftManifest, index: int, value: str
) -> None:
    row = manifest.records[0]
    cells = list(row.original_cells)
    cells[index] = replace(cells[index], value=value, numeric_lexeme=value)
    with pytest.raises(draft.SourceError):
        draft.normalize_row(
            manifest.documents[0], row.source_row, tuple(cells), row.selection
        )


def test_missing_reordered_and_formula_cells_rejected(
    manifest: draft.DraftManifest,
) -> None:
    row = manifest.records[0]
    cells = row.original_cells
    for invalid in (
        cells[:-1],
        cells[::-1],
        (replace(cells[0], formula="unapproved"),) + cells[1:],
    ):
        with pytest.raises(draft.SourceError):
            draft.normalize_row(
                manifest.documents[0], row.source_row, invalid, row.selection
            )


def test_duplicate_sources_revisions_and_uuid_collisions(
    manifest: draft.DraftManifest,
) -> None:
    row = manifest.records[0]
    key, new_id = draft.provisional_identity(
        row.sport, row.original_workout_id, "0" * 64
    )
    assert key == row.provisional_key and new_id != row.provisional_id
    for duplicate in (row, replace(row, source_sha256="0" * 64, provisional_id=new_id)):
        with pytest.raises(
            draft.SourceError, match="duplicate_source_identity_or_revision"
        ):
            draft.validate_identities((row, duplicate))
    with pytest.raises(draft.SourceError, match="provisional_uuid_collision"):
        draft.validate_identities((row,), frozenset({row.provisional_key}))


@pytest.mark.parametrize(
    "filename", [s.filename for s in draft.SOURCES] + [draft.SPEC_PDF[0]]
)
def test_changed_original_rejected_before_any_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filename: str
) -> None:
    target = tmp_path / "sources"
    shutil.copytree(draft.DEFAULT_SOURCES, target)
    (target / filename).write_bytes((target / filename).read_bytes() + b"changed")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("XML processing began before all hashes were verified")

    monkeypatch.setattr(draft, "read_document", forbidden)
    with pytest.raises(draft.SourceError, match="source_revision_mismatch"):
        draft.build_manifest(target)


def test_idempotent_manifest_golden_and_decimal_context(
    manifest: draft.DraftManifest,
) -> None:
    expected = GOLDEN.read_text(encoding="utf-8")
    assert draft.manifest_json(manifest) == expected
    with localcontext() as context:
        context.prec = 3
        assert draft.manifest_json(draft.build_manifest()) == expected


def test_manifest_and_load_are_frozen_and_cannot_approve(
    manifest: draft.DraftManifest,
) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(manifest, "activation_status", "ACTIVE")
    with pytest.raises(ValueError, match="init=False"):
        replace(manifest.records[0].load, approved_operational_tss=None)
    assert manifest.method_version is manifest.catalog_release is None
    assert len(manifest.approval_gaps) == 6


def test_local_command_is_offline_private_and_preserves_bytes_and_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Source revisions now have custody subdirectories; verify every file.
    paths = [p for p in draft.DEFAULT_SOURCES.rglob("*") if p.is_file()]
    before = {p: p.read_bytes() for p in paths}
    historical = tuple(snapshot_template(t) for t in full_catalog())
    current = active_catalog(CURRENT_CATALOG)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("dry-run attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    output = tmp_path / "draft.json"
    assert (
        main(
            [
                "--dry-run",
                "--private-output",
                str(output),
                "--timings",
                str(tmp_path / "timings.json"),
            ]
        )
        == 0
    )
    first = capsys.readouterr().out
    assert main(["--dry-run", "--private-output", str(output)]) == 0
    assert capsys.readouterr().out == first
    assert json.loads(first)["sport_counts"] == {"run": 20, "bike": 21, "swim": 20}
    assert output.read_bytes() == GOLDEN.read_bytes()
    assert not any(
        word in first
        for word in ("original_source_tss", "87.599", "mathematical_reference")
    )
    assert active_catalog(CURRENT_CATALOG) == current
    assert tuple(snapshot_template(t) for t in full_catalog()) == historical
    assert {p: p.read_bytes() for p in paths} == before


def test_no_output_path_can_overwrite_original_or_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    original = draft.DEFAULT_SOURCES / draft.SOURCES[0].filename
    before = original.read_bytes()
    assert main(["--dry-run", "--timings", str(original)]) == 1
    assert "artifact_revision_conflict" in capsys.readouterr().out
    assert original.read_bytes() == before
    artifact = tmp_path / "existing"
    write_immutable(artifact, "first")
    write_immutable(artifact, "first")
    with pytest.raises(draft.SourceError, match="artifact_revision_conflict"):
        write_immutable(artifact, "changed")
    assert artifact.read_text() == "first"


def test_no_private_evidence_in_reprs_or_error_output(
    manifest: draft.DraftManifest, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    for value in (
        manifest,
        manifest.records[0],
        manifest.records[0].load,
        manifest.documents[0],
        manifest.records[0].original_cells[0],
    ):
        assert "original_source_tss" not in repr(value)
        assert "mathematical_reference" not in repr(value)
    assert main(["--dry-run", "--sources", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().out) == {
        "error_code": "source_unreadable",
        "status": "INVALID",
    }
    with pytest.raises(SystemExit):
        main([])  # There is no apply/activation mode.


def test_original_document_and_proposal_hashes(manifest: draft.DraftManifest) -> None:
    for document in manifest.documents:
        content = (draft.DEFAULT_SOURCES / document.spec.filename).read_bytes()
        assert len(content) == document.spec.byte_count
        assert sha256(content).hexdigest() == document.spec.sha256
        assert document.worksheet_state == "visible"
        assert document.acceptance_state == "NOT ACCEPTED FOR OPERATIONAL SELECTION"
        assert document.extent == f"A1:O{document.spec.row_count + 4}"
    assert (
        sha256((draft.DEFAULT_SOURCES / draft.SPEC_PDF[0]).read_bytes()).hexdigest()
        == draft.SPEC_PDF[1]
    )
    assert (
        sha256(
            (draft.DEFAULT_SOURCES.parent / draft.PROPOSAL_FILE).read_bytes()
        ).hexdigest()
        == draft.PROPOSAL_SHA
    )
