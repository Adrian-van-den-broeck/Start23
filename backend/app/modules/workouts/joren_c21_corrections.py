"""Lossless approved six-cell overlay; originals and C1/C2 evidence stay intact."""

from dataclasses import asdict, replace
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path

from app.modules.physiology.models import Discipline
from app.modules.physiology.planned_source import SourceMethodError
from app.modules.workouts.joren_c2_verification import (
    CONFIRMED_IF,
    PDF_REFERENCE_SECONDS,
    RECONSTRUCTED_IF,
    RECONSTRUCTED_ROUNDED_SECONDS,
    SWIM_IF2_SOURCE,
    block_guidance,
    read_revision,
    swim_rows,
    verify_swim_row,
)
from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    SourceError,
    SwimDistance,
    parse_events,
)

REVISION = "joren-swim-if2-approved-prescription-overlay-1"
APPROVAL = "C2.1-SWIM-1"


def correction_evidence(source_dir: Path = DEFAULT_SOURCES) -> dict[str, object]:
    """Rebuild the entire candidate from pinned bytes plus six exact replacements.

    The manifest is the derived source revision, never a modified XLSX. Original
    cells/XML and events remain under `original`; derived fields are separate.
    No template IDs, operational values or active catalog entries are created.
    """
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        return _correction_evidence(source_dir)


def _correction_evidence(source_dir: Path) -> dict[str, object]:
    document = read_revision(source_dir)
    records = []
    for original in swim_rows(document):
        text = original.cells[13].value or ""
        corrected = original.row in range(19, 25)
        if corrected:
            if not text.startswith("300m Z3 |") or text.count("300m Z3") != 1:
                raise SourceError("correction_precondition_failed")
            prescription = text.replace("300m Z3", "300m Z2", 1)
        else:
            prescription = text
        events = parse_events(prescription, "swim", f"N{original.row}")
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
        if ordered != original.source_zones or sum(ordered) != Decimal(
            original.cells[5].value or "NaN"
        ):
            raise SourceError("corrected_prescription_conflict")
        # Internal verification view only; never serialize this as an original.
        candidate = replace(
            original,
            events=events,
            ordered_zones=ordered,
            structure_status="CONSISTENT",
            guidance=block_guidance(events, Discipline.SWIM),
        )
        calculations = {}
        for label, anchors, paces in (
            ("confirmed_if_pdf_reference", CONFIRMED_IF, PDF_REFERENCE_SECONDS),
            ("RECONSTRUCTED_exact_seconds", RECONSTRUCTED_IF, PDF_REFERENCE_SECONDS),
            (
                "RECONSTRUCTED_rounded_minutes",
                RECONSTRUCTED_IF,
                RECONSTRUCTED_ROUNDED_SECONDS,
            ),
        ):
            try:
                calculation = verify_swim_row(
                    candidate, if_values=anchors, reference_seconds=paces
                )
                calculations[label] = {
                    **asdict(calculation),
                    "source_display_matches": calculation.decimal_value.quantize(
                        Decimal(".1")
                    )
                    == Decimal(original.source_display_p),
                }
            except SourceMethodError as exc:
                calculations[label] = {"error": str(exc)}
        records.append(
            {
                "source_id": original.source_id,
                "original": asdict(original),
                "correction": {
                    "approval": APPROVAL,
                    "coordinate": f"N{original.row}",
                    "before": text,
                    "after": prescription,
                }
                if corrected
                else None,
                "derived_prescription": prescription,
                "derived_events": tuple(asdict(e) for e in events),
                "derived_ordered_zones": ordered,
                "derived_guidance": tuple(asdict(g) for g in candidate.guidance),
                "structure_status": "CONSISTENT",
                "calculations_unapproved_method": calculations,
                "planned_active_seconds": None,
                "time_compliance": "UNVERIFIED",
                "operational_p": None,
                "activation_status": "INACTIVE",
            }
        )
    return {
        "schema": REVISION,
        "parent_source": asdict(SWIM_IF2_SOURCE),
        "original_document": asdict(document),
        "approval": {
            "id": APPROVAL,
            "authority": "Joren; explicitly relayed by owner in WOMBO C2.1 task",
            "intake_date": "2026-11-04",
            "original_approval_date": None,
            "reference": (
                "docs/catalog/implementation/JOREN_C2_UPDATED_DECISIONS.md#c21-approval"
            ),
            "scope": "TR-SWIM-015 through TR-SWIM-020: ordered 300m Z3 becomes 300m Z2",
        },
        "records": records,
        "structure_status": "CONSISTENT",
        "operational_method": None,
        "activation_status": "INACTIVE",
    }
