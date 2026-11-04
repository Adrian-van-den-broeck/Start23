"""Private read-only source revision verification; never an active catalog adapter."""

from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_source import (
    SWIM_IF2,
    TIMED_IF2,
    SourceCalculation,
    SourceMethodError,
    calculate_source,
)
from app.modules.physiology.rpe_zones import SESSION_MAPPING_V2, rpe_zone
from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    SOURCES,
    DraftWorkout,
    Event,
    SourceCell,
    SourceDocument,
    SourceError,
    SourceSpec,
    SwimDistance,
    WallRest,
    build_manifest,
    parse_events,
    read_document,
)

SWIM_IF2_SOURCE = SourceSpec(
    "joren-swim-if2-intake-1",
    "swim",
    "Zwemtrainingen_IF2.xlsx",
    "7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb",
    7405,
    20,
    "Zwemtrainingen",
    "Zwemmen",
)
# A confirms these previously reconstructed populated coefficients. No Z3 added.
CONFIRMED_IF = (Decimal(".55"), Decimal(".75"), None, Decimal(".98"), Decimal("1.15"))
# Historical PDF reference, not yet confirmed as the revised source's inputs.
PDF_REFERENCE_SECONDS = tuple(map(Decimal, ("130", "120", "110", "100", "90")))
# Explicit RECONSTRUCTED verification inputs only. These are not approved anchors.
RECONSTRUCTED_IF = (*CONFIRMED_IF[:2], Decimal(".88"), *CONFIRMED_IF[3:])
RECONSTRUCTED_ROUNDED_SECONDS = tuple(
    map(Decimal, ("130.2", "120", "109.8", "100.2", "90"))
)


@dataclass(frozen=True, slots=True)
class BlockGuidance:
    sequence: int
    zone: int | None
    rpe_min: int | None
    rpe_max: int | None
    version: str


def block_guidance(
    events: tuple[Event, ...], sport: Discipline
) -> tuple[BlockGuidance, ...]:
    result = []
    for event in events:
        if isinstance(event, WallRest):
            result.append(
                BlockGuidance(event.sequence, None, None, None, SESSION_MAPPING_V2)
            )
        else:
            guidance = rpe_zone(
                sport, TrainingZone(event.zone), version=SESSION_MAPPING_V2
            )
            result.append(
                BlockGuidance(
                    event.sequence,
                    event.zone,
                    guidance.rpe_min,
                    guidance.rpe_max,
                    SESSION_MAPPING_V2,
                )
            )
    return tuple(result)


@dataclass(frozen=True, slots=True, repr=False)
class SwimRow:
    source_id: str
    row: int
    cells: tuple[SourceCell, ...]
    events: tuple[Event, ...]
    source_zones: tuple[Decimal, ...]
    ordered_zones: tuple[Decimal, ...]
    source_stored_p: str
    source_display_p: str
    stationary_rest_seconds: Decimal
    structure_status: str
    guidance: tuple[BlockGuidance, ...]
    original_session_focus: str
    source_sha256: str = field(default=SWIM_IF2_SOURCE.sha256, init=False)
    planned_duration_seconds: None = field(default=None, init=False)
    operational_p: None = field(default=None, init=False)
    activation_status: str = field(default="INACTIVE", init=False)


def read_revision(source_dir: Path = DEFAULT_SOURCES) -> SourceDocument:
    # read_document verifies the complete archive hash/length BEFORE XML processing.
    return read_document(
        (source_dir / SWIM_IF2_SOURCE.filename).read_bytes(), SWIM_IF2_SOURCE
    )


def swim_rows(document: SourceDocument) -> tuple[SwimRow, ...]:
    if document.spec != SWIM_IF2_SOURCE:
        raise SourceError("unsupported_source_revision")
    result = []
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        for row in range(5, 25):
            lookup = {c.coordinate: c for c in document.cells}
            cells = tuple(lookup[f"{col}{row}"] for col in "ABCDEFGHIJKLMNO")
            if any(c.formula is not None for c in cells):
                raise SourceError("unapproved_formula_revision")
            values = tuple(c.value or "" for c in cells)
            if values[0] != f"TR-SWIM-{row - 4:03d}":
                raise SourceError("source_identity_coverage_mismatch")
            events = parse_events(values[13], "swim", f"N{row}")
            zones = tuple(Decimal(v) for v in values[7:12])
            ordered = tuple(
                sum(
                    (
                        e.meters
                        for e in events
                        if isinstance(e, SwimDistance) and e.zone == z
                    ),
                    Decimal(0),
                )
                for z in range(1, 6)
            )
            consistent = zones == ordered and sum(zones) == Decimal(values[5])
            result.append(
                SwimRow(
                    values[0],
                    row,
                    cells,
                    events,
                    zones,
                    ordered,
                    values[12],
                    format(Decimal(values[12]).quantize(Decimal(".1")), ".1f"),
                    sum(
                        (e.seconds for e in events if isinstance(e, WallRest)),
                        Decimal(0),
                    ),
                    "CONSISTENT" if consistent else "SOURCE-CONFLICTED",
                    block_guidance(events, Discipline.SWIM),
                    values[3],
                )
            )
    return tuple(result)


def verify_swim_row(
    row: SwimRow,
    *,
    if_values: tuple[Decimal | None, ...],
    reference_seconds: tuple[Decimal | None, ...],
) -> SourceCalculation:
    """Strict experimental path: inconsistent prescriptions reject before arithmetic."""
    if row.source_sha256 != SWIM_IF2_SOURCE.sha256:
        raise SourceMethodError("unsupported_source_revision")
    if row.structure_status != "CONSISTENT" or row.source_zones != row.ordered_zones:
        raise SourceMethodError("source_prescription_conflict")
    return calculate_source(
        method=SWIM_IF2,
        quantities=row.source_zones,
        if_values=if_values,
        reference_seconds_per_100m=reference_seconds,
        sport_factor=Decimal(".90"),
        stationary_rest_seconds=row.stationary_rest_seconds,
    )


def verify_timed_row(record: DraftWorkout) -> SourceCalculation:
    if record.sport not in ("run", "bike"):
        raise SourceMethodError("unsupported_source_revision")
    source = next(s for s in SOURCES if s.sport == record.sport)
    if record.source_sha256 != source.sha256:
        raise SourceMethodError("unsupported_source_revision")
    return calculate_source(
        method=TIMED_IF2,
        quantities=tuple(
            sum(
                (
                    e.seconds
                    for e in record.events
                    if not isinstance(e, (SwimDistance, WallRest)) and e.zone == z
                ),
                Decimal(0),
            )
            for z in range(1, 6)
        ),
        if_values=CONFIRMED_IF,
        sport_factor=Decimal(record.original_cells[6].value or "NaN"),
    )


def private_evidence(source_dir: Path = DEFAULT_SOURCES) -> dict[str, object]:
    """Every source cell and both diagnostic interpretations; no approval inference.

    Candidate arithmetic for conflicted rows is explicitly analytical only, and
    does not pass verify_swim_row. It cannot produce operational load.
    """
    old = read_document((source_dir / SOURCES[2].filename).read_bytes(), SOURCES[2])
    new = read_revision(source_dir)
    old_cells = {c.coordinate: c for c in old.cells}
    diffs = [
        {
            "coordinate": c.coordinate,
            "old": asdict(old_cells[c.coordinate]),
            "new": asdict(c),
        }
        for c in new.cells
        if c != old_cells[c.coordinate]
    ]
    records = []
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        for row in swim_rows(new):
            calculations = {}
            for label, zones, anchors, paces in (
                (
                    "confirmed_if_pdf_reference",
                    row.source_zones,
                    CONFIRMED_IF,
                    PDF_REFERENCE_SECONDS,
                ),
                (
                    "RECONSTRUCTED_exact_seconds_aggregate",
                    row.source_zones,
                    RECONSTRUCTED_IF,
                    PDF_REFERENCE_SECONDS,
                ),
                (
                    "RECONSTRUCTED_rounded_minutes_aggregate",
                    row.source_zones,
                    RECONSTRUCTED_IF,
                    RECONSTRUCTED_ROUNDED_SECONDS,
                ),
                (
                    "RECONSTRUCTED_rounded_minutes_ordered",
                    row.ordered_zones,
                    RECONSTRUCTED_IF,
                    RECONSTRUCTED_ROUNDED_SECONDS,
                ),
            ):
                try:
                    calculation = calculate_source(
                        method=SWIM_IF2,
                        quantities=zones,
                        if_values=anchors,
                        reference_seconds_per_100m=paces,
                        sport_factor=Decimal(".90"),
                        stationary_rest_seconds=row.stationary_rest_seconds,
                    )
                    calculations[label] = {
                        **asdict(calculation),
                        "source_minus_calculated": str(
                            Decimal(row.source_stored_p) - calculation.decimal_value
                        ),
                        "display": str(
                            calculation.decimal_value.quantize(Decimal(".1"))
                        ),
                    }
                except SourceMethodError as exc:
                    calculations[label] = {"error": str(exc)}
            records.append({**asdict(row), "diagnostics_only": calculations})
    timed_records = []
    baseline = build_manifest(source_dir)
    if baseline.errors:
        raise SourceError("historical_source_validation_failed")
    for record in baseline.records:
        if record.sport == "swim":
            continue
        timed_records.append(
            {
                "source_id": record.original_workout_id,
                "source_sha256": record.source_sha256,
                "source_stored_p": record.load.source_numeric_lexeme,
                "source_display_p": record.load.original_displayed_value,
                "original_session_focus": record.original_expected_rpe,
                "guidance": tuple(
                    asdict(g)
                    for g in block_guidance(record.events, Discipline(record.sport))
                ),
                "calculation": asdict(verify_timed_row(record)),
                "activation_status": "INACTIVE",
                "operational_p": None,
            }
        )
    return {
        "schema": "joren-c2-source-verification-1",
        "old_document": asdict(old),
        "new_document": asdict(new),
        "cell_diffs": diffs,
        "records": records,
        "timed_records": timed_records,
        "activation_status": "INACTIVE",
        "operational_method": None,
        "candidate_status": "RECONSTRUCTED; NOT APPROVED",
        "reference_seconds": PDF_REFERENCE_SECONDS,
        "reconstructed_seconds": RECONSTRUCTED_ROUNDED_SECONDS,
        "confirmed_if": CONFIRMED_IF,
        "reconstructed_if": RECONSTRUCTED_IF,
    }
