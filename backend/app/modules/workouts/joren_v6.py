"""Pinned V6 offline intake. No runtime catalog, repository or activation imports.

The unchanged C1 OOXML reader and row parser own lossless normalization. V6 adds
explicit source revisions, provisional successor identities and review evidence.
"""

import json
from dataclasses import asdict, dataclass, fields
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from app.modules.physiology.models import Discipline
from app.modules.physiology.planned_source import (
    SWIM_IF2,
    TIMED_IF2,
    SourceMethodError,
    calculate_source,
)
from app.modules.workouts.joren_c2_verification import (
    CONFIRMED_IF,
    PDF_REFERENCE_SECONDS,
    RECONSTRUCTED_IF,
    RECONSTRUCTED_ROUNDED_SECONDS,
    SWIM_IF2_SOURCE,
    block_guidance,
    read_revision,
)
from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    DraftField,
    DraftWorkout,
    SelectionDraft,
    SourceCell,
    SourceDocument,
    SourceError,
    SourceSpec,
    TimedZone,
    _headers,
    _read_verified,
    build_manifest,
    normalize_row,
    read_document,
    validate_identities,
)

RELEASE = "joren-v6-draft-source-release-1"
PRECISION_VERSION = "joren-v6-if2-rounded-reference-minutes-candidate-1"
EXACT_SECONDS_VERSION = "joren-v6-if2-exact-reference-seconds-candidate-1"
V6_SOURCES = (
    SourceSpec(
        "joren-v6-run",
        "run",
        "Looptrainingen_Definitief_v6.xlsx",
        "f9efc53405ae80ea06b7c4f45c288d77e0572aabe0309ef17d29336562a5c46c",
        7731,
        28,
        "Looptrainingen",
        "Lopen",
    ),
    SourceSpec(
        "joren-v6-bike",
        "bike",
        "Fietstrainingen_Definitief_v6.xlsx",
        "e291a6e40b193d279e1371032242972f4f940454b544832e04087aec6fec4b95",
        7813,
        27,
        "Fietstrainingen",
        "Fietsen",
    ),
    SourceSpec(
        "joren-v6-swim",
        "swim",
        "Zwemtrainingen_Definitief_v6.xlsx",
        "acd05e0d02664a09320fc70a4519d518fb0103a34801823d04de1ac929c96348",
        7551,
        22,
        "Zwemtrainingen",
        "Zwemmen",
    ),
)
PROPOSAL_RULES = (
    "joren-v6-selection-proposal-1: Z1/Z2 only -> low, all phases; any Z3+ -> "
    "high, build; HR run/bike, pace swim; distinct repeated occurrences; "
    "athlete suitability unapproved; TR-BIKE-013 held from automatic beginner "
    "use; source display load only in labeled hypothetical planner probes"
)


@dataclass(frozen=True, slots=True, repr=False)
class V6Workout(DraftWorkout):
    provisional_template_version: int = 1
    source_release: str = RELEASE
    predecessor_source_sha256: str | None = None
    predecessor_source_row: int | None = None
    predecessor_provisional_id: UUID | None = None
    predecessor_template_version: int | None = None
    accepted_predecessor_mapping: None = None


@dataclass(frozen=True, slots=True, repr=False)
class V6Manifest:
    documents: tuple[SourceDocument, ...]
    records: tuple[V6Workout, ...]
    previous_documents: tuple[SourceDocument, ...]
    schema: str = RELEASE
    activation_status: str = "INACTIVE"
    operational_method: None = None
    status: str = "SOURCE STRUCTURES VALIDATED; POLICY/METHOD APPROVAL PENDING"


def _proposal(cells: tuple[SourceCell, ...]) -> SelectionDraft:
    identifier = cells[0].value or ""
    rpe = cells[3].value or ""
    high = any(Decimal(c.value or "0") > 0 for c in cells[9:12])
    return SelectionDraft(
        "backend/app/modules/workouts/joren_v6.py#PROPOSAL_RULES",
        sha256(PROPOSAL_RULES.encode()).hexdigest(),
        0,
        (identifier, rpe),
        DraftField("high / build" if high else "low / base,build,recovery,taper"),
        DraftField("PACE" if identifier.startswith("TR-SWIM") else "HEART_RATE"),
        DraftField("PROPOSAL ONLY; auto/swipe after method and athlete scope approval"),
        DraftField("joren-realized-tss-matrix-2; session focus retained separately"),
        DraftField(
            "HELD FROM AUTOMATIC BEGINNER USE; scope pending"
            if identifier == "TR-BIKE-013"
            else "UNAPPROVED; no universal beginner suitability inferred"
        ),
        DraftField("distinct occurrence IDs; existing automatic bound 24"),
        DraftField(None),
        DraftField(None),
    )


def _rows(document: SourceDocument) -> dict[str, tuple[SourceCell, ...]]:
    return {
        cells[0].value or "": cells
        for row in range(5, document.spec.row_count + 5)
        for cells in [
            tuple(
                c
                for c in document.cells
                if c.coordinate in {f"{column}{row}" for column in "ABCDEFGHIJKLMNO"}
            )
        ]
    }


def build_v6_manifest(
    source_dir: Path = DEFAULT_SOURCES, *, reserved: frozenset[UUID] = frozenset()
) -> V6Manifest:
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        return _build_v6_manifest(source_dir, reserved=reserved)


def _build_v6_manifest(source_dir: Path, *, reserved: frozenset[UUID]) -> V6Manifest:
    # All three complete archive hashes are verified before parsing any V6 XML.
    inputs = tuple(
        _read_verified(source_dir / s.filename, s.sha256, s.byte_count)
        for s in V6_SOURCES
    )
    baseline = build_manifest(source_dir)
    if baseline.errors:
        raise SourceError("historical_source_validation_failed")
    previous = (*baseline.documents[:2], read_revision(source_dir))
    documents = tuple(read_document(b, s) for b, s in zip(inputs, V6_SOURCES))
    old = {r.original_workout_id: r for r in baseline.records}
    records = []
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        for document, parent in zip(documents, previous):
            headers = list(_headers(document.spec.sport))
            if document.spec.sport == "bike":
                headers[5] = "Totale Duur"
                headers[7:12] = [f"Z{i} (min)" for i in range(1, 6)]
            if tuple(
                c.value
                for c in document.cells
                if c.coordinate in {f"{col}4" for col in "ABCDEFGHIJKLMNO"}
            ) != tuple(headers):
                raise SourceError("unsupported_source_headers")
            expected = {
                f"{col}{row}"
                for row in range(5, document.spec.row_count + 5)
                for col in "ABCDEFGHIJKLMNO"
            }
            actual = {
                c.coordinate
                for c in document.cells
                if int("".join(filter(str.isdigit, c.coordinate))) >= 5
            }
            if actual != expected or document.extent != (
                f"A1:O{document.spec.row_count + 4}"
            ):
                raise SourceError("source_row_coverage_mismatch")
            parents = _rows(parent)
            for index, (identifier, cells) in enumerate(_rows(document).items(), 1):
                if identifier != f"TR-{document.spec.sport.upper()}-{index:03d}":
                    raise SourceError("source_identity_coverage_mismatch")
                row = index + 4
                normalized = normalize_row(document, row, cells, _proposal(cells))
                existing = identifier in parents
                version = (3 if document.spec.sport == "swim" else 2) if existing else 1
                parent_version = 2 if document.spec.sport == "swim" else 1
                parent_id = (
                    uuid5(
                        normalized.provisional_key,
                        f"source-sha256:{parent.spec.sha256}|template-version:{parent_version}",
                    )
                    if existing
                    else None
                )
                values: dict[str, Any] = {
                    f.name: getattr(normalized, f.name)
                    for f in fields(normalized)
                    if f.init
                }
                values["provisional_id"] = uuid5(
                    normalized.provisional_key,
                    f"source-sha256:{document.spec.sha256}|template-version:{version}",
                )
                records.append(
                    V6Workout(
                        **values,
                        provisional_template_version=version,
                        predecessor_source_sha256=parent.spec.sha256
                        if existing
                        else None,
                        predecessor_source_row=old[identifier].source_row
                        if existing
                        else None,
                        predecessor_provisional_id=parent_id,
                        predecessor_template_version=parent_version
                        if existing
                        else None,
                    )
                )
    validate_identities(tuple(records), reserved)
    # Stable logical keys intentionally repeat; immutable revision UUIDs never do.
    historical_ids = {r.provisional_id for r in baseline.records}
    historical_ids.update(
        uuid5(
            r.provisional_key,
            f"source-sha256:{SWIM_IF2_SOURCE.sha256}|template-version:2",
        )
        for r in baseline.records
        if r.sport == "swim"
    )
    if any(r.provisional_id in historical_ids for r in records):
        raise SourceError("provisional_revision_collision")
    return V6Manifest(documents, tuple(records), previous)


def calculation_evidence(record: V6Workout) -> dict[str, Any]:
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        return _calculation_evidence(record)


def _calculation_evidence(record: V6Workout) -> dict[str, Any]:
    quantities = record.original_zone_distribution
    if record.sport != "swim":
        quantities = tuple(
            sum(
                (
                    e.seconds
                    for e in record.events
                    if isinstance(e, TimedZone) and e.zone == z
                ),
                Decimal(0),
            )
            for z in range(1, 6)
        )
    results: dict[str, Any] = {}
    for label, anchors, paces in (
        ("confirmed_if_exact_reference", CONFIRMED_IF, PDF_REFERENCE_SECONDS),
        (EXACT_SECONDS_VERSION, RECONSTRUCTED_IF, PDF_REFERENCE_SECONDS),
        (PRECISION_VERSION, RECONSTRUCTED_IF, RECONSTRUCTED_ROUNDED_SECONDS),
    ):
        try:
            calculation = calculate_source(
                method=SWIM_IF2 if record.sport == "swim" else TIMED_IF2,
                quantities=quantities,
                if_values=anchors,
                sport_factor=Decimal(record.original_cells[6].value or "NaN"),
                reference_seconds_per_100m=paces if record.sport == "swim" else None,
                stationary_rest_seconds=record.stationary_rest_seconds,
            )
            with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
                display = calculation.decimal_value.quantize(Decimal(".1"))
                difference = record.load.original_source_tss - calculation.decimal_value
            results[label] = {
                **asdict(calculation),
                "display": str(display),
                "display_matches": display
                == Decimal(record.load.original_displayed_value),
                "source_raw_minus_candidate": str(difference),
                "parameter_status": "RECONSTRUCTED; NOT APPROVED"
                if label != "confirmed_if_exact_reference"
                else "CONFIRMED IF; SWIM REFERENCE PRECISION UNAPPROVED",
            }
        except SourceMethodError as exc:
            results[label] = {"error": str(exc)}
    return results


def revision_differences(manifest: V6Manifest) -> dict[str, Any]:
    rows = []
    documents = []
    for new, old in zip(manifest.documents, manifest.previous_documents):
        old_rows = _rows(old)
        for identifier, cells in _rows(new).items():
            parent = old_rows.get(identifier)
            changes = []
            unchanged = []
            if parent:
                for before, after in zip(parent, cells):
                    if (before.value, before.cell_type) != (
                        after.value,
                        after.cell_type,
                    ):
                        changes.append(
                            {
                                "coordinate": after.coordinate,
                                "before": asdict(before),
                                "after": asdict(after),
                            }
                        )
                    else:
                        unchanged.append(after.coordinate)
            rows.append(
                {
                    "source_id": identifier,
                    "kind": "EXISTING" if parent else "NEW",
                    "parent_source_sha256": old.spec.sha256 if parent else None,
                    "v6_source_sha256": new.spec.sha256,
                    "changed_values": changes,
                    "unchanged_value_coordinates": unchanged,
                    "unchanged_prescription": bool(
                        parent and parent[13].value == cells[13].value
                    ),
                    "all_cell_record_changes": [
                        after.coordinate
                        for before, after in zip(parent or (), cells)
                        if before != after
                    ],
                }
            )
        old_cells = {c.coordinate: c for c in old.cells}
        documents.append(
            {
                "sport": new.spec.sport,
                "parent": asdict(old.spec),
                "v6": asdict(new.spec),
                "old_extent": old.extent,
                "new_extent": new.extent,
                "non_row_changes": [
                    {
                        "before": asdict(old_cells[c.coordinate])
                        if c.coordinate in old_cells
                        else None,
                        "after": asdict(c),
                    }
                    for c in new.cells
                    if int("".join(filter(str.isdigit, c.coordinate))) < 5
                    and c != old_cells.get(c.coordinate)
                ],
            }
        )
    return {"documents": documents, "rows": rows}


def private_evidence(manifest: V6Manifest) -> dict[str, Any]:
    return {
        **asdict(manifest),
        "source_differences": revision_differences(manifest),
        "calculations": {
            r.original_workout_id: calculation_evidence(r) for r in manifest.records
        },
        "block_guidance": {
            r.original_workout_id: tuple(
                asdict(g) for g in block_guidance(r.events, Discipline(r.sport))
            )
            for r in manifest.records
        },
        "precision_candidate": {
            "version": PRECISION_VERSION,
            "reference_minutes_per_100m": ("2.17", "2.00", "1.83", "1.67", "1.50"),
            "reference_seconds": RECONSTRUCTED_ROUNDED_SECONDS,
            "if_values": RECONSTRUCTED_IF,
            "approval": "UNAPPROVED RECONSTRUCTION",
        },
        "correction": {
            "authority": "C2.1-SWIM-1",
            "applied_to_v6": False,
            "v6_already_corrected": tuple(f"TR-SWIM-{i:03d}" for i in range(15, 21)),
            "overlay_revision": "joren-swim-if2-approved-prescription-overlay-1",
        },
        "policy_evidence": {
            "intake_date": "2026-11-05",
            "authority": "owner-relayed Joren, WOMBO V6 task",
            "original_approval_date": None,
            "triathlon_planned_load_target": {
                "bike": ".50",
                "run": ".30",
                "swim": ".20",
            },
            "intensity": "maximum 20% active time per sport/week; no high minimum",
            "beginner": "one suitable workout per sport; baseline unchanged at 45",
            "scope": "diagnostics only; no active planner policy changed",
        },
    }


def private_json(value: object) -> str:
    def encode(item: object) -> str:
        if isinstance(item, (Decimal, UUID)):
            return str(item)
        raise TypeError("unsupported_private_evidence_value")

    return (
        json.dumps(value, default=encode, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n"
    )
