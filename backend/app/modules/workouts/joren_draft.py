"""Private, offline C1 source custody and lossless normalization. No active templates.

Only the pinned intake is supported. New bytes require a separately reviewed source
revision, never a caller-supplied replacement hash. No method is operational here.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from app.modules.physiology.joren import VERSION, zone_load
from app.modules.physiology.models import Discipline

STATUS = "DRAFT — SOURCE VALIDATED, METHODOLOGY NOT APPROVED"
MANIFEST_VERSION = "joren-optie1-c1-draft-1"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
Sport = Literal["run", "bike", "swim"]
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SOURCES = ROOT / "docs/catalog/sources"
PROPOSAL_FILE = "JOREN_THREE_SPORT_FINAL_RECONCILIATION.md"
PROPOSAL_SHA = "7ab267fedf1c2e7ff4e1ee043e5a0896047235ed15d6cc0592314cf50c4a59e0"


class SourceError(ValueError):
    """Safe fixed error code only; never interpolate source/private cell values."""


@dataclass(frozen=True, slots=True)
class SourceSpec:
    document_id: str
    sport: Sport
    filename: str
    sha256: str
    byte_count: int
    row_count: int
    sheet_name: str
    sport_label: str


SOURCES = (
    SourceSpec(
        "joren-optie1-run",
        "run",
        "Looptrainingen_Definitief_Optie1.xlsx",
        "dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3",
        7198,
        20,
        "Looptrainingen Catalogus",
        "Lopen",
    ),
    SourceSpec(
        "joren-optie1-bike",
        "bike",
        "Fietstrainingen_Definitief_Optie1.xlsx",
        "5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df",
        7376,
        21,
        "Fietstrainingen Catalogus",
        "Fietsen",
    ),
    SourceSpec(
        "joren-optie1-swim",
        "swim",
        "Zwemtrainingen_Definitief_Optie1.xlsx",
        "bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674",
        7333,
        20,
        "Zwemtrainingen Catalogus",
        "Zwemmen",
    ),
)
SPEC_PDF = (
    "Specificatie Zwem TSS.pdf",
    "ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a",
    149021,
)


@dataclass(frozen=True, slots=True, repr=False)
class SourceCell:
    coordinate: str
    cell_type: str
    value: str | None
    numeric_lexeme: str | None
    formula: str | None
    cached_value: str | None
    style_index: int
    number_format: str
    xml: str


@dataclass(frozen=True, slots=True, repr=False)
class SourceDocument:
    spec: SourceSpec
    worksheet: str
    worksheet_state: str
    extent: str
    cells: tuple[SourceCell, ...]
    revision_status: str = field(
        default="PINNED ORIGINAL; REVISION UNAPPROVED", init=False
    )
    acceptance_state: str = field(
        default="NOT ACCEPTED FOR OPERATIONAL SELECTION", init=False
    )
    accepted_owner: None = field(default=None, init=False)
    acceptance_decision_reference: None = field(default=None, init=False)


@dataclass(frozen=True, slots=True)
class TimedZone:
    sequence: int
    raw_token: str
    source_cell: str
    start: int
    end: int
    seconds: Decimal
    zone: int
    kind: Literal["timed_zone"] = field(default="timed_zone", init=False)


@dataclass(frozen=True, slots=True)
class SwimDistance:
    sequence: int
    raw_token: str
    source_cell: str
    start: int
    end: int
    meters: Decimal
    zone: int
    duration_seconds: None = field(default=None, init=False)
    kind: Literal["swim_distance"] = field(default="swim_distance", init=False)


@dataclass(frozen=True, slots=True)
class WallRest:
    sequence: int
    raw_token: str
    source_cell: str
    start: int
    end: int
    seconds: Decimal
    distance_meters: None = field(default=None, init=False)
    zone: None = field(default=None, init=False)
    rpe: None = field(default=None, init=False)
    kind: Literal["stationary_wall_rest"] = field(
        default="stationary_wall_rest", init=False
    )


Event = TimedZone | SwimDistance | WallRest


@dataclass(frozen=True, slots=True)
class DraftField:
    proposal: str | None
    state: Literal["DRAFT"] = field(default="DRAFT", init=False)


@dataclass(frozen=True, slots=True)
class SelectionDraft:
    source_report: str
    report_sha256: str
    line: int
    original_columns: tuple[str, ...]
    bucket_and_phases: DraftField
    athlete_capability: DraftField
    selection: DraftField
    block_rpe: DraftField
    beginner_eligibility: DraftField
    repeat_eligibility: DraftField
    source_method_compatibility: DraftField
    swim_distance_planning_compatibility: DraftField


@dataclass(frozen=True, slots=True, repr=False)
class DraftLoad:
    original_source_tss: Decimal
    original_displayed_value: str
    source_numeric_lexeme: str
    source_significant_digits: int
    source_decimal_exponent: int
    source_number_format: str
    mathematical_reference: Decimal | None
    reference_method: str
    reference_version: str
    proposed_calculation_method: str
    approved_operational_tss: None = field(default=None, init=False)
    operational_status: Literal["UNAVAILABLE"] = field(
        default="UNAVAILABLE", init=False
    )
    approval_status: Literal["PENDING"] = field(default="PENDING", init=False)
    original_method_rounding_policy: None = field(default=None, init=False)
    display_rendering_policy: str = field(
        default=(
            "Stored numeric cell rendered with #,##0.0; Decimal HALF_EVEN; no locale"
        ),
        init=False,
    )


@dataclass(frozen=True, slots=True, repr=False)
class DraftWorkout:
    document_id: str
    sport: Sport
    source_sha256: str
    worksheet: str
    source_row: int
    original_workout_id: str
    provisional_key: UUID
    provisional_id: UUID
    original_cells: tuple[SourceCell, ...]
    original_training_name: str
    original_training_focus: str
    original_expected_rpe: str
    original_expected_zone: int
    original_zone_distribution: tuple[Decimal, ...]
    distribution_unit: Literal["minutes", "meters"]
    original_measure: Decimal
    original_execution_structure: str
    events: tuple[Event, ...]
    planned_duration_seconds: Decimal | None
    planned_distance_meters: Decimal | None
    stationary_rest_seconds: Decimal
    load: DraftLoad
    selection: SelectionDraft
    provisional_template_version: int = field(default=1, init=False)
    catalog_release: None = field(default=None, init=False)
    operational_method_version: None = field(default=None, init=False)
    activation_status: Literal["INACTIVE"] = field(default="INACTIVE", init=False)
    acceptance_state: Literal["PENDING"] = field(default="PENDING", init=False)


@dataclass(frozen=True, slots=True)
class RowIssue:
    document_id: str
    row: int
    code: str


@dataclass(frozen=True, slots=True, repr=False)
class DraftManifest:
    documents: tuple[SourceDocument, ...]
    records: tuple[DraftWorkout, ...]
    errors: tuple[RowIssue, ...]
    swim_specification: tuple[str, str, int] = field(default=SPEC_PDF, init=False)
    manifest_version: str = field(default=MANIFEST_VERSION, init=False)
    status: str = field(default=STATUS, init=False)
    catalog_release: None = field(default=None, init=False)
    method_version: None = field(default=None, init=False)
    activation_status: Literal["INACTIVE"] = field(default="INACTIVE", init=False)
    reference_numeric_policy: str = field(
        default="Decimal precision 50; HALF_EVEN; no intermediate quantization",
        init=False,
    )
    approval_gaps: tuple[str, ...] = field(
        default=(
            "A: planned method/precision",
            "B: release/replacement policy",
            "C: selection/athlete scope",
            "D: block guidance",
            "E: swim distance/rest/time scope",
            "F: activation/release",
        ),
        init=False,
    )


def _read_verified(path: Path, digest: str, byte_count: int | None = None) -> bytes:
    try:
        content = path.read_bytes()
    except OSError:
        raise SourceError("source_unreadable") from None
    if sha256(content).hexdigest() != digest or (
        byte_count is not None and len(content) != byte_count
    ):
        raise SourceError("source_revision_mismatch")
    return content


def _number(value: str | None, *, positive: bool = False) -> Decimal:
    try:
        result = Decimal(value) if value is not None else Decimal("NaN")
    except InvalidOperation:
        raise SourceError("invalid_numeric_cell") from None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise SourceError("invalid_numeric_cell")
    return result


def read_document(content: bytes, spec: SourceSpec) -> SourceDocument:
    """Verify bytes again before XML; never save or calculate a workbook."""
    if sha256(content).hexdigest() != spec.sha256 or len(content) != spec.byte_count:
        raise SourceError("source_revision_mismatch")
    try:
        with ZipFile(BytesIO(content)) as archive:
            book = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = book.findall("x:sheets/x:sheet", NS)
            if len(sheets) != 1 or sheets[0].get("name") != spec.sheet_name:
                raise SourceError("unsupported_worksheet_schema")
            styles = ET.fromstring(archive.read("xl/styles.xml"))
            formats = {0: "General", 1: "0", 2: "0.00", 3: "#,##0"}
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
                cell_type = cell.get("t", "n")
                if cell_type not in ("n", "inlineStr"):
                    raise SourceError("unsupported_cell_type")
                raw = cell.findtext("x:v", namespaces=NS)
                value = "".join(cell.itertext()) if cell_type == "inlineStr" else raw
                style = int(cell.get("s", "0"))
                number_format = formats[int(xfs[style].get("numFmtId", "0"))]
                formula = cell.find("x:f", NS)
                cells.append(
                    SourceCell(
                        cell.attrib["r"],
                        cell_type,
                        value,
                        raw if cell_type == "n" else None,
                        ET.tostring(formula, encoding="unicode")
                        if formula is not None
                        else None,
                        raw if formula is not None else None,
                        style,
                        number_format,
                        ET.tostring(cell, encoding="unicode"),
                    )
                )
            extent = sheet.find("x:dimension", NS)
            if extent is None:
                raise SourceError("missing_sheet_extent")
            return SourceDocument(
                spec,
                spec.sheet_name,
                sheets[0].get("state", "visible"),
                extent.attrib["ref"],
                tuple(cells),
            )
    except (BadZipFile, KeyError, IndexError, ET.ParseError, ValueError) as exc:
        if isinstance(exc, SourceError):
            raise
        raise SourceError("unsupported_workbook_schema") from None


def parse_events(text: str, sport: Sport, source_cell: str) -> tuple[Event, ...]:
    """One token -> one event; spans retain whitespace and repeated blocks exactly."""
    if sport not in ("run", "bike", "swim"):
        raise SourceError("unsupported_sport")
    events: list[Event] = []
    start = 0
    for sequence, raw in enumerate(text.split("|"), 1):
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)(m|s) (Z[1-5]|Rust)\s*", raw)
        if match is None:
            raise SourceError("unsupported_execution_token")
        amount = _number(match[1], positive=True)
        unit, target = match[2], match[3]
        common = (sequence, raw, source_cell, start, start + len(raw))
        if target == "Rust":
            if sport != "swim" or unit != "s":
                raise SourceError("invalid_stationary_rest")
            events.append(WallRest(*common, amount))
        elif sport == "swim":
            if unit != "m" or amount != amount.to_integral_value():
                raise SourceError("invalid_swim_distance")
            events.append(SwimDistance(*common, amount, int(target[1])))
        else:
            events.append(
                TimedZone(*common, amount * (60 if unit == "m" else 1), int(target[1]))
            )
        start += len(raw) + 1
    return tuple(events)


def provisional_identity(
    sport: Sport, source_id: str, source_sha: str
) -> tuple[UUID, UUID]:
    if (
        sport not in ("run", "bike", "swim")
        or not re.fullmatch(rf"TR-{sport.upper()}-\d{{3}}", source_id)
        or not re.fullmatch(r"[0-9a-f]{64}", source_sha)
    ):
        raise SourceError("invalid_source_identity")
    key = uuid5(NAMESPACE_URL, f"wombo:joren:optie1:{sport}:{source_id}")
    return key, uuid5(key, f"source-sha256:{source_sha}|template-version:1")


def _proposals(content: bytes) -> dict[str, SelectionDraft]:
    proposals = {}
    for line, text in enumerate(content.decode("utf-8").splitlines(), 1):
        columns = tuple(part.strip() for part in text.split("|")[1:-1])
        if len(columns) != 6 or not re.fullmatch(
            r"TR-(RUN|BIKE|SWIM)-\d{3}", columns[0]
        ):
            continue
        identifier = columns[0]
        if identifier in proposals:
            raise SourceError("duplicate_proposal_identity")
        proposals[identifier] = SelectionDraft(
            PROPOSAL_FILE,
            PROPOSAL_SHA,
            line,
            columns,
            DraftField(columns[2]),
            DraftField(columns[3]),
            DraftField(columns[5]),
            DraftField(columns[4]),
            DraftField(
                "HELD FROM AUTOMATIC BEGINNER USE; scope pending"
                if identifier == "TR-BIKE-013"
                else None
            ),
            DraftField("distinct occurrence IDs; existing automatic bound 24"),
            DraftField(None),
            DraftField(None),
        )
    if len(proposals) != 61:
        raise SourceError("incomplete_selection_proposal")
    return proposals


def _headers(sport: Sport) -> tuple[str, ...]:
    measure = {
        "run": "Totale Duur",
        "bike": "Totale Duur\n(min)",
        "swim": "Totale Afstand",
    }[sport]
    suffix = {"run": "", "bike": "\n(min)", "swim": " (m)"}[sport]
    return (
        "Workout_ID",
        "Sport",
        "Titel Training",
        "Expected RPE",
        "Expected Zone",
        measure,
        "Sport Multiplier",
        *(f"Z{i}{suffix}" for i in range(1, 6)),
        "Expected TSS (Berekend)",
        "Interval Structuur (Volgorde voor Software)",
        "Trainingsfocus",
    )


def normalize_row(
    document: SourceDocument,
    row: int,
    cells: tuple[SourceCell, ...],
    proposal: SelectionDraft,
) -> DraftWorkout:
    """Validate all structural aggregates, independently of method approval."""
    spec = document.spec
    if tuple(c.coordinate for c in cells) != tuple(
        f"{c}{row}" for c in "ABCDEFGHIJKLMNO"
    ):
        raise SourceError("missing_or_reordered_cells")
    if any(c.formula is not None for c in cells):
        raise SourceError("unapproved_formula_revision")
    values = tuple(c.value or "" for c in cells)
    identifier = values[0]
    key, identity = provisional_identity(spec.sport, identifier, spec.sha256)
    if values[1] != spec.sport_label or proposal.original_columns[0] != identifier:
        raise SourceError("source_identity_mismatch")
    if (
        not values[2]
        or not values[14]
        or not re.fullmatch(r"[1-9], (?:[2-9]|10)", values[3])
    ):
        raise SourceError("invalid_source_metadata")
    if values[3] != proposal.original_columns[1]:
        raise SourceError("source_focus_proposal_mismatch")
    for index in (4, 5, 6, 7, 8, 9, 10, 11, 12):
        if cells[index].cell_type != "n":
            raise SourceError("invalid_numeric_cell_type")
    zone = _number(values[4], positive=True)
    if zone not in tuple(Decimal(i) for i in range(1, 6)):
        raise SourceError("invalid_expected_zone")
    measure = _number(values[5], positive=True)
    _number(values[6], positive=True)  # Preserve, never multiply a reference again.
    distribution = tuple(_number(v) for v in values[7:12])
    events = parse_events(values[13], spec.sport, f"N{row}")
    by_zone = [Decimal(0)] * 5
    rest = Decimal(0)
    for event in events:
        if isinstance(event, WallRest):
            rest += event.seconds
        else:
            by_zone[event.zone - 1] += (
                event.meters if isinstance(event, SwimDistance) else event.seconds / 60
            )
    if tuple(by_zone) != distribution or sum(distribution) != measure:
        raise SourceError("execution_aggregate_mismatch")
    raw_load = _number(values[12], positive=True)
    fmt = cells[12].number_format
    if fmt != "#,##0.0":
        raise SourceError("unsupported_display_format")
    # This is formatting of an existing numeric cell, not a chosen load method.
    displayed = format(
        raw_load.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN), ",.1f"
    )
    reference: Decimal | None
    if spec.sport == "swim":
        reference = sum(
            (
                d * c / 100
                for d, c in zip(
                    distribution, map(Decimal, (".98", "1.44", "1.98", "2.40", "2.70"))
                )
            ),
            Decimal(0),
        )
        reference_method = "published_distance_matrix_REFERENCE_ONLY"
        reference_version = SPEC_PDF[1]
        proposed = "published fixed-distance matrix; A/E approval pending"
    else:
        calculated = zone_load(
            discipline=Discipline(spec.sport),
            total_minutes=measure,
            minutes_by_zone=distribution,
            planned=True,
        )
        reference = calculated.load.value if calculated.load is not None else None
        reference_method = calculated.calculation_method + "_REFERENCE_ONLY"
        reference_version = VERSION.value
        proposed = (
            "IF² reconstruction OR retained source OR zone minutes; A decision pending"
        )
    load = DraftLoad(
        raw_load,
        displayed,
        values[12],
        len(raw_load.as_tuple().digits),
        int(str(raw_load.as_tuple().exponent)),
        fmt,
        reference,
        reference_method,
        reference_version,
        proposed,
    )
    return DraftWorkout(
        spec.document_id,
        spec.sport,
        spec.sha256,
        document.worksheet,
        row,
        identifier,
        key,
        identity,
        cells,
        values[2],
        values[14],
        values[3],
        int(zone),
        distribution,
        "meters" if spec.sport == "swim" else "minutes",
        measure,
        values[13],
        events,
        None if spec.sport == "swim" else measure * 60,
        measure if spec.sport == "swim" else None,
        rest,
        load,
        proposal,
    )


def validate_identities(
    records: tuple[DraftWorkout, ...], reserved: frozenset[UUID] = frozenset()
) -> None:
    source_ids: set[tuple[str, str]] = set()
    uuids = set(reserved)
    for record in records:
        source_key = (record.sport, record.original_workout_id)
        if source_key in source_ids:
            raise SourceError("duplicate_source_identity_or_revision")
        source_ids.add(source_key)
        for identity in (record.provisional_key, record.provisional_id):
            if identity in uuids:
                raise SourceError("provisional_uuid_collision")
            uuids.add(identity)


def build_manifest(
    source_dir: Path = DEFAULT_SOURCES, *, reserved: frozenset[UUID] = frozenset()
) -> DraftManifest:
    """Verify every original before processing any workbook; quarantine invalid rows."""
    inputs = tuple(
        _read_verified(source_dir / s.filename, s.sha256, s.byte_count) for s in SOURCES
    )
    _read_verified(source_dir / SPEC_PDF[0], SPEC_PDF[1], SPEC_PDF[2])
    proposals = _proposals(
        _read_verified(source_dir.parent / PROPOSAL_FILE, PROPOSAL_SHA)
    )
    documents = tuple(
        read_document(content, spec) for content, spec in zip(inputs, SOURCES)
    )
    records = []
    issues = []
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_HALF_EVEN
        for document in documents:
            headers = tuple(
                c.value for c in document.cells if re.fullmatch(r"[A-O]4", c.coordinate)
            )
            if headers != _headers(document.spec.sport):
                raise SourceError("unsupported_source_headers")
            expected_rows = set(range(5, document.spec.row_count + 5))
            actual_rows = {
                int(re.sub(r"[A-Z]+", "", c.coordinate))
                for c in document.cells
                if int(re.sub(r"[A-Z]+", "", c.coordinate)) >= 5
            }
            if (
                actual_rows != expected_rows
                or document.extent != f"A1:O{document.spec.row_count + 4}"
            ):
                raise SourceError("source_row_coverage_mismatch")
            for row in sorted(expected_rows):
                cells = tuple(
                    c
                    for c in document.cells
                    if re.fullmatch(rf"[A-Z]+{row}", c.coordinate)
                )
                try:
                    proposal = proposals.get(cells[0].value or "") if cells else None
                    if proposal is None:
                        raise SourceError("missing_selection_proposal")
                    records.append(normalize_row(document, row, cells, proposal))
                except SourceError as exc:
                    issues.append(RowIssue(document.spec.document_id, row, str(exc)))
    result = tuple(records)
    validate_identities(result, reserved)
    if not issues and {r.original_workout_id for r in result} != set(proposals):
        raise SourceError("source_identity_coverage_mismatch")
    return DraftManifest(documents, result, tuple(issues))


def manifest_json(manifest: DraftManifest) -> str:
    """Explicit private developer artifact; never use as an athlete/API serializer."""

    def encode(value: object) -> str:
        if isinstance(value, Decimal | UUID):
            return str(value)
        raise TypeError("unsupported_manifest_value")

    return (
        json.dumps(
            asdict(manifest),
            default=encode,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
