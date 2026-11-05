"""Pinned, inactive C3 phase revision; never an active catalog repository.

Column P is phase metadata. Historical A:O values, lexemes, identities and draft
selection proposals remain separately attributable to their original revisions.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid5
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    NS,
    SourceCell,
    SourceDocument,
    SourceError,
    SourceSpec,
    _read_verified,
)
from app.modules.workouts.joren_v6 import V6Workout, build_v6_manifest

RELEASE = "joren-v6-phase-source-release-1"
ADAPTER = "joren-v6-shared-strings-phase-adapter-1"
SOURCE_DIR = DEFAULT_SOURCES / "joren-v6-phase-1"
PHASES = tuple(TrainingPhase)
PHASE_SOURCES = (
    SourceSpec(
        "joren-v6-phase-run-1",
        "run",
        "Looptrainingen_Definitief_v6 (1) (1).xlsx",
        "7380c88ef8bccb3cb35b0f6416d9debba8342b9802fc716f0a99dcfcb8626d88",
        11912,
        28,
        "Looptrainingen",
        "Lopen",
    ),
    SourceSpec(
        "joren-v6-phase-bike-1",
        "bike",
        "Fietstrainingen_Definitief_v6 (1) (1).xlsx",
        "6322d7f93b3e074c77c4efa28b2a95de3f04f0f5c6af226ce50e8c2ff716ddbc",
        12772,
        27,
        "Fietstrainingen",
        "Fietsen",
    ),
    SourceSpec(
        "joren-v6-phase-swim-1",
        "swim",
        "Zwemtrainingen_Definitief_v6 (2) (1).xlsx",
        "48a0f6448f003ef048f40e53fda74b5220f272ebd4300180c108777c6e0be3ba",
        12387,
        22,
        "Zwemtrainingen",
        "Zwemmen",
    ),
)
EXPECTED_COUNTS = {
    "run": (22, 22, 18, 18),
    "bike": (23, 27, 13, 19),
    "swim": (16, 22, 8, 8),
}
# Exact, hash-bound export changes. No epsilon, rounding or numerical authority
# follows from display-equivalent lexemes. Both original cells remain retained.
EXPORT_LEXEME_CHANGES = {
    ("run", "M21"): ("87.59999999999999", "87.6"),
    ("run", "M26"): ("8.699999999999999", "8.7"),
    ("bike", "M8"): ("84.40000000000001", "84.4"),
    ("bike", "M25"): ("96.09999999999999", "96.1"),
    ("swim", "M12"): ("75.90000000000001", "75.9"),
    ("swim", "M13"): ("84.40000000000001", "84.4"),
    ("swim", "M21"): ("69.59999999999999", "69.6"),
    ("swim", "M24"): ("69.59999999999999", "69.6"),
}


def normalize_phases(text: str | None) -> tuple[TrainingPhase, ...]:
    if text is None or not text.strip():
        raise SourceError("missing_phase_data")
    labels = tuple(s.strip() for s in text.split(","))
    mapping = {p.value.capitalize(): p for p in PHASES}
    if any(s not in mapping for s in labels):
        raise SourceError("unknown_phase_label")
    if len(set(labels)) != len(labels):
        raise SourceError("duplicate_phase_label")
    return tuple(p for p in PHASES if p in {mapping[s] for s in labels})


def read_phase_document(content: bytes, spec: SourceSpec) -> SourceDocument:
    """Strict version-specific OOXML reader; raw archives are never rewritten."""
    if spec not in PHASE_SOURCES:
        raise SourceError("conflicting_source_revision")
    # Reuse archive hash/length verification without accepting replacement specs.
    if sha256(content).hexdigest() != spec.sha256 or len(content) != spec.byte_count:
        raise SourceError("source_revision_mismatch")
    try:
        with ZipFile(BytesIO(content)) as archive:
            book = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = book.findall("x:sheets/x:sheet", NS)
            if len(sheets) != 1 or sheets[0].get("name") != spec.sheet_name:
                raise SourceError("unsupported_worksheet_schema")
            strings = tuple(
                "".join(t.text or "" for t in si.findall(".//x:t", NS))
                for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))
            )
            styles = ET.fromstring(archive.read("xl/styles.xml"))
            formats = {0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00"}
            formats.update(
                {
                    int(f.attrib["numFmtId"]): f.attrib["formatCode"]
                    for f in styles.findall("x:numFmts/x:numFmt", NS)
                }
            )
            xfs = styles.findall("x:cellXfs/x:xf", NS)
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            cells = []
            for cell in sheet.findall("x:sheetData/x:row/x:c", NS):
                kind = cell.get("t", "n")
                raw = cell.findtext("x:v", namespaces=NS)
                if cell.find("x:f", NS) is not None or kind not in ("n", "s"):
                    raise SourceError("unsupported_phase_cell")
                value = strings[int(raw)] if kind == "s" and raw is not None else raw
                style = int(cell.get("s", "0"))
                cells.append(
                    SourceCell(
                        cell.attrib["r"],
                        kind,
                        value,
                        raw if kind == "n" else None,
                        None,
                        None,
                        style,
                        formats[int(xfs[style].get("numFmtId", "0"))],
                        ET.tostring(cell, encoding="unicode"),
                    )
                )
            # This export has no dimension element. Coverage is derived and checked
            # against every expected coordinate, never guessed from row count.
            return SourceDocument(
                spec,
                spec.sheet_name,
                sheets[0].get("state", "visible"),
                f"A1:P{spec.row_count + 4}",
                tuple(cells),
            )
    except (BadZipFile, KeyError, IndexError, ET.ParseError, ValueError) as exc:
        if isinstance(exc, SourceError):
            raise
        raise SourceError("unsupported_phase_workbook_schema") from None


@dataclass(frozen=True, slots=True, repr=False)
class PhaseTemplate:
    logical_key: UUID
    revision_id: UUID
    version: int
    source_sha256: str
    source_row: int
    source_cells: tuple[SourceCell, ...]
    phase_cell: SourceCell
    phases: tuple[TrainingPhase, ...]
    predecessor: V6Workout
    # Contains full ordered timed/distance/rest events and original RPE/focus.
    # Historical provisional selection fields are evidence, never accepted fields.
    activation_status: Literal["INACTIVE"] = field(default="INACTIVE", init=False)
    official_planned_load: None = field(default=None, init=False)
    official_method: None = field(default=None, init=False)
    source_release: str = field(default=RELEASE, init=False)


@dataclass(frozen=True, slots=True, repr=False)
class PhaseCatalog:
    documents: tuple[SourceDocument, ...]
    templates: tuple[PhaseTemplate, ...]
    adapter_version: str = field(default=ADAPTER, init=False)
    release: str = field(default=RELEASE, init=False)
    activation_status: Literal["INACTIVE"] = field(default="INACTIVE", init=False)


def validate_phase_document(
    document: SourceDocument, parents: tuple[V6Workout, ...]
) -> tuple[PhaseTemplate, ...]:
    spec = document.spec
    if spec not in PHASE_SOURCES:
        raise SourceError("conflicting_source_revision")
    coordinates = [c.coordinate for c in document.cells]
    if len(set(coordinates)) != len(coordinates):
        raise SourceError("duplicate_source_coordinate")
    cells = {c.coordinate: c for c in document.cells}
    if cells.get("P4") is None or cells["P4"].value != "Trainingsfase ":
        raise SourceError("unsupported_phase_header")
    expected = {
        f"{col}{row}"
        for row in range(5, spec.row_count + 5)
        for col in "ABCDEFGHIJKLMNOP"
    }
    actual = {
        c.coordinate
        for c in document.cells
        if int("".join(filter(str.isdigit, c.coordinate))) >= 5
        and (c.value is not None or c.coordinate in expected)
    }
    if expected != actual or len(parents) != spec.row_count:
        raise SourceError("source_row_coverage_mismatch")
    identifiers = [cells[f"A{row}"].value for row in range(5, spec.row_count + 5)]
    if len(set(identifiers)) != len(identifiers):
        raise SourceError("duplicate_workout_id")
    result = []
    for index, parent in enumerate(parents, 5):
        row = tuple(cells[f"{col}{index}"] for col in "ABCDEFGHIJKLMNO")
        if row[0].value != parent.original_workout_id or parent.sport != spec.sport:
            raise SourceError("source_identity_coverage_mismatch")
        for before, after in zip(parent.original_cells, row):
            equal = (
                Decimal(before.value or "NaN") == Decimal(after.value or "NaN")
                if before.cell_type == "n" and after.cell_type == "n"
                else before.value == after.value
            )
            documented_export = EXPORT_LEXEME_CHANGES.get(
                (spec.sport, after.coordinate)
            )
            if not equal and documented_export != (before.value, after.value):
                raise SourceError("historical_source_value_changed")
        phase = cells[f"P{index}"]
        version = parent.provisional_template_version + 1
        result.append(
            PhaseTemplate(
                parent.provisional_key,
                uuid5(
                    parent.provisional_key,
                    f"source-sha256:{spec.sha256}|template-version:{version}",
                ),
                version,
                spec.sha256,
                index,
                row,
                phase,
                normalize_phases(phase.value),
                parent,
            )
        )
    counts = tuple(sum(p in r.phases for r in result) for p in PHASES)
    if counts != EXPECTED_COUNTS[spec.sport]:
        raise SourceError("phase_membership_count_mismatch")
    return tuple(result)


def build_phase_catalog(
    source_dir: Path = SOURCE_DIR,
    *,
    historical_dir: Path = DEFAULT_SOURCES,
    reserved: frozenset[UUID] = frozenset(),
) -> PhaseCatalog:
    blobs = tuple(
        _read_verified(source_dir / s.filename, s.sha256, s.byte_count)
        for s in PHASE_SOURCES
    )
    historical = build_v6_manifest(historical_dir)
    documents = tuple(read_phase_document(b, s) for b, s in zip(blobs, PHASE_SOURCES))
    templates = tuple(
        r
        for doc in documents
        for r in validate_phase_document(
            doc, tuple(p for p in historical.records if p.sport == doc.spec.sport)
        )
    )
    keys = [r.logical_key for r in templates]
    ids = [r.revision_id for r in templates]
    previous = {r.provisional_id for r in historical.records}
    if len(set(keys)) != 77 or len(set(ids)) != 77 or set(ids) & (reserved | previous):
        raise SourceError("catalog_revision_collision")
    return PhaseCatalog(documents, templates)
