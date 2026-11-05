"""Private phase custody and disabled C3-C5 contract tests using real revisions."""

import ast
import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from app.jobs.joren_catalog_dry_run import offline_reserved_ids, write_immutable
from app.jobs.joren_v6_phase_intake import artifact, main
from app.modules.physiology.models import Discipline
from app.modules.planning.v6_phase_review import (
    DIMENSIONS,
    review_week,
)
from app.modules.workouts.catalog import TrainingPhase
from app.modules.workouts.joren_draft import SourceError, SwimDistance, WallRest
from app.modules.workouts.joren_v6 import PRECISION_VERSION, calculation_evidence
from app.modules.workouts.joren_v6_phase import (
    EXPORT_LEXEME_CHANGES,
    PHASE_SOURCES,
    PHASES,
    SOURCE_DIR,
    PhaseCatalog,
    build_phase_catalog,
    normalize_phases,
    read_phase_document,
    validate_phase_document,
)
from app.modules.workouts.planned_swim_estimate import estimate_swim
from benchmarks.v6_partial_approval import estimate_swim as historical_estimator
from benchmarks.v6_phase_integration import (
    WITNESSES,
    conditional_evidence,
    evidence,
    make_scope,
    phase_projection,
)

D = Decimal
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalog() -> PhaseCatalog:
    return build_phase_catalog(reserved=offline_reserved_ids())


@pytest.mark.parametrize("index", range(77))
def test_all_77_immutable_lineages(catalog: PhaseCatalog, index: int) -> None:
    row = catalog.templates[index]
    old = row.predecessor
    assert row.logical_key == old.provisional_key
    assert row.revision_id != old.provisional_id
    assert row.version == old.provisional_template_version + 1
    assert row.source_row == old.source_row
    assert row.activation_status == "INACTIVE"
    assert row.official_planned_load is None and row.official_method is None
    assert len(row.source_cells) == 15
    for before, after in zip(old.original_cells, row.source_cells):
        assert before.coordinate == after.coordinate
        assert after.xml and before.xml
        if (old.sport, before.coordinate) in EXPORT_LEXEME_CHANGES:
            assert (
                before.numeric_lexeme,
                after.numeric_lexeme,
            ) == EXPORT_LEXEME_CHANGES[old.sport, before.coordinate]
        elif before.cell_type == "n":
            assert D(before.value or "NaN") == D(after.value or "NaN")
        else:
            assert before.value == after.value
    assert row.source_cells[13].value == old.original_execution_structure
    assert row.source_cells[3].value == old.original_expected_rpe
    assert row.source_cells[14].value == old.original_training_focus
    assert row.phases == normalize_phases(row.phase_cell.value)
    assert old.events  # Never reconstruct or sort interval/rest events by zone.


def test_source_bytes_and_no_duplicate_keys(catalog: PhaseCatalog) -> None:
    assert len({r.logical_key for r in catalog.templates}) == 77
    assert len({r.revision_id for r in catalog.templates}) == 77
    for spec in PHASE_SOURCES:
        blob = (SOURCE_DIR / spec.filename).read_bytes()
        assert len(blob) == spec.byte_count and sha256(blob).hexdigest() == spec.sha256
        assert read_phase_document(blob, spec).spec == spec
        with pytest.raises(SourceError, match="source_revision_mismatch"):
            read_phase_document(blob + b"x", spec)
        with pytest.raises(SourceError, match="conflicting_source_revision"):
            read_phase_document(blob, replace(spec, document_id="changed"))
    with pytest.raises(SourceError, match="catalog_revision_collision"):
        build_phase_catalog(reserved=frozenset({catalog.templates[0].revision_id}))


@pytest.mark.parametrize(
    "text", (None, "", " ", "base", "Base,Unknown", "Base,", "Base,Base")
)
def test_invalid_phase_rejected(text: str | None) -> None:
    with pytest.raises(SourceError):
        normalize_phases(text)


def test_phase_normalization_order_and_noteworthy_labels(catalog: PhaseCatalog) -> None:
    assert normalize_phases(" Taper, Base , Recovery,Build ") == PHASES
    lookup = {r.predecessor.original_workout_id: r for r in catalog.templates}
    assert TrainingPhase.TAPER in lookup["TR-BIKE-013"].phases
    for i in (17, 18):
        assert lookup[f"TR-RUN-{i:03d}"].phases == (TrainingPhase.BASE,)
    for i in range(21, 25):
        assert lookup[f"TR-RUN-{i:03d}"].phases == (
            TrainingPhase.RECOVERY,
            TrainingPhase.TAPER,
        )


@pytest.mark.parametrize(
    "kind",
    (
        "duplicate_id",
        "missing_phase",
        "unknown_phase",
        "missing_row",
        "extra_row",
        "changed_interval",
        "changed_numeric",
        "header",
        "duplicate_coordinate",
    ),
)
def test_document_fail_closed(catalog: PhaseCatalog, kind: str) -> None:
    doc = catalog.documents[0]
    cells = list(doc.cells)
    positions = {c.coordinate: i for i, c in enumerate(cells)}
    if kind == "missing_row":
        cells = [c for c in cells if c.coordinate != "N5"]
    elif kind == "extra_row":
        cells.append(replace(cells[positions["A5"]], coordinate="A99"))
    elif kind == "duplicate_coordinate":
        cells.append(cells[positions["A5"]])
    else:
        coord, value = {
            "duplicate_id": ("A6", "TR-RUN-001"),
            "missing_phase": ("P5", None),
            "unknown_phase": ("P5", "Race"),
            "changed_interval": ("N5", "1min Z5"),
            "changed_numeric": ("M5", "17.5"),
            "header": ("P4", "Trainingsfase"),
        }[kind]
        cells[positions[coord]] = replace(cells[positions[coord]], value=value)
    with pytest.raises(SourceError):
        validate_phase_document(
            replace(doc, cells=tuple(cells)),
            tuple(
                t.predecessor for t in catalog.templates if t.predecessor.sport == "run"
            ),
        )


def test_phase_projection_uses_real_metadata_only(catalog: PhaseCatalog) -> None:
    for row, template in zip(catalog.templates, phase_projection(catalog)):
        assert row.phases == template.training_phases
        assert row.revision_id == template.id
        assert row.logical_key == template.template_key
        assert row.version == template.version
        if row.predecessor.sport == "swim":
            assert template.duration_minutes is None
            assert row.predecessor.planned_duration_seconds is None
            assert sum(isinstance(e, WallRest) for e in row.predecessor.events) >= 0


@pytest.mark.parametrize("label", WITNESSES)
def test_phase_eligibility_of_witnesses(catalog: PhaseCatalog, label: str) -> None:
    ids = WITNESSES[label]
    for phase in TrainingPhase:
        scope = make_scope(catalog, ids, phase=phase)
        result = review_week(scope)
        expected_total = Fraction(label.split("_")[0])
        assert result.private_total == expected_total
        allowed = all(phase in o.template.phases for o in scope.proposed)
        assert ("source_phase_not_allowed" not in result.constraint_failures) == allowed
        assert (
            not result.operational_approval and result.selected_recommendation is None
        )
        assert set(result.unresolved_safeguards) == DIMENSIONS
    base = review_week(make_scope(catalog, ids))
    assert (
        "source_phase_not_allowed" not in base.constraint_failures
    ) == label.startswith(("44.8", "45.1"))


@pytest.mark.parametrize(
    "budget,within",
    (
        ("45", False),
        ("45.1", True),
        ("45.10000000000000000000001", True),
        ("45.09999999999999999999999", False),
    ),
)
def test_exact_budget_ceiling(catalog: PhaseCatalog, budget: str, within: bool) -> None:
    scope = make_scope(catalog, WITNESSES["45.1_legacy_overshoot"], budget=budget)
    with localcontext() as ctx:
        ctx.prec = 3
        result = review_week(scope)
    assert result.budget_within == within
    assert ("authorized_weekly_budget_exceeded" in result.constraint_failures) != within


def test_retained_occurrences_consume_remaining_capacity(catalog: PhaseCatalog) -> None:
    scope = make_scope(catalog, WITNESSES["44.8_utilization"])
    scope = replace(scope, retained=scope.proposed[:1], proposed=scope.proposed[1:])
    result = review_week(scope)
    assert result.private_remaining_before_additions == Fraction("24.8")
    assert result.private_remaining == Fraction(".2")
    assert result.private_total == Fraction("44.8")


@pytest.mark.parametrize("dimension", sorted(DIMENSIONS))
def test_safeguards_never_inferred_from_load(
    catalog: PhaseCatalog, dimension: str
) -> None:
    scope = make_scope(
        catalog, ("TR-BIKE-013",), phase=TrainingPhase.TAPER, budget="500"
    )
    ev = conditional_evidence(scope)
    missing = review_week(scope, tuple(e for e in ev if e.dimension != dimension))
    assert dimension in missing.unresolved_safeguards
    blocked = review_week(
        scope,
        tuple(
            replace(e, state="BLOCKED") if e.dimension == dimension else e for e in ev
        ),
    )
    assert dimension + "_blocked" in blocked.constraint_failures
    assert not blocked.operational_approval
    assert missing.budget_within  # A fitting seven-hour ride is not proof of readiness.


@pytest.mark.parametrize(
    "change",
    (
        "athlete",
        "revision",
        "week",
        "phase",
        "budget",
        "dates",
        "occurrence",
        "prescription",
    ),
)
def test_evidence_stale_and_account_safe(catalog: PhaseCatalog, change: str) -> None:
    scope = make_scope(catalog, ("TR-SWIM-021",))
    ev = conditional_evidence(scope)
    cases: dict[str, dict[str, Any]] = {
        "athlete": {"athlete_id": uuid4()},
        "revision": {"expected_revision": uuid4()},
        "week": {
            "week_start": scope.week_start - timedelta(days=7),
            "available_dates": frozenset(),
            "proposed": (),
        },
        "phase": {"phase": TrainingPhase.BUILD},
        "budget": {"authorized_budget": D(46)},
        "dates": {"available_dates": frozenset()},
        "occurrence": {
            "proposed": (replace(scope.proposed[0], occurrence_id=uuid4()),)
        },
        "prescription": {
            "proposed": (
                replace(
                    scope.proposed[0],
                    prescribed_seconds=tuple(
                        D(100) for _ in scope.proposed[0].template.predecessor.events
                    ),
                    prescribed_time_reference="TEST_ONLY:prescription",
                ),
            )
        },
    }
    with pytest.raises(ValueError, match="stale_or_cross_scope"):
        review_week(replace(scope, **cases[change]), ev)


@pytest.mark.parametrize(
    "ids,phase,budget,coverage",
    (
        (WITNESSES["44.8_utilization"], TrainingPhase.BUILD, "45", "THREE"),
        (("TR-BIKE-022", "TR-RUN-021"), TrainingPhase.RECOVERY, "25.86", "TWO"),
        (("TR-RUN-021",), TrainingPhase.TAPER, "15.085", "ONE"),
        ((), TrainingPhase.BASE, "0", "ZERO"),
    ),
)
def test_partial_week_contracts(
    catalog: PhaseCatalog,
    ids: tuple[str, ...],
    phase: TrainingPhase,
    budget: str,
    coverage: str,
) -> None:
    scope = make_scope(catalog, ids, phase=phase, budget=budget)
    result = review_week(scope, conditional_evidence(scope))
    assert result.coverage == coverage
    assert not result.constraint_failures and not result.unresolved_safeguards
    assert result.budget_within and not result.operational_approval
    assert result.selected_recommendation is None
    for item in result.authoritative_intensity:
        assert item.known_high_seconds == 0  # BUILD permits all easy.


def test_availability_goals_repeat_and_distinct_occurrences(
    catalog: PhaseCatalog,
) -> None:
    scope = make_scope(
        catalog, ("TR-BIKE-023", "TR-BIKE-023"), goals=frozenset({Discipline.BIKE})
    )
    result = review_week(
        scope, maximum_uses=((scope.proposed[0].template.revision_id, 1),)
    )
    assert "repeat_limit_exceeded" in result.constraint_failures
    assert result.coverage == "ONE"
    assert (
        "date_unavailable"
        in review_week(replace(scope, available_dates=frozenset())).constraint_failures
    )
    assert (
        "sport_outside_goal"
        in review_week(
            replace(scope, goal_sports=frozenset({Discipline.RUN}))
        ).constraint_failures
    )
    with pytest.raises(ValueError, match="duplicate_occurrence"):
        replace(scope, proposed=(scope.proposed[0], scope.proposed[0]))
    with pytest.raises(ValueError, match="invalid_repeat"):
        review_week(scope, maximum_uses=((uuid4(), -1),))
    with pytest.raises(ValueError, match="duplicate_safeguard"):
        review_week(scope, conditional_evidence(scope) * 2)


@pytest.mark.parametrize("high,status", (("20", "ACCEPTED"), ("20.0001", "REJECTED")))
def test_authoritative_swim_maximum_distinct_from_estimate(
    catalog: PhaseCatalog, high: str, status: str
) -> None:
    scope = make_scope(
        catalog, ("TR-SWIM-010",), phase=TrainingPhase.BUILD, budget="100"
    )
    row = scope.proposed[0]
    events = row.template.predecessor.events
    lows = sum(isinstance(e, SwimDistance) and e.zone <= 2 for e in events)
    highs = sum(isinstance(e, SwimDistance) and e.zone > 2 for e in events)
    seconds = tuple(
        D(1)
        if isinstance(e, WallRest)
        else D(80) / lows
        if e.zone <= 2
        else D(high) / highs
        for e in events
    )
    prescribed = replace(
        row,
        prescribed_seconds=seconds,
        prescribed_time_reference="TEST_ONLY:independent-prescription",
    )
    result = review_week(replace(scope, proposed=(prescribed,)))
    swim = next(c for c in result.authoritative_intensity if c.sport == Discipline.SWIM)
    assert swim.status == status
    assert row.template.predecessor.planned_duration_seconds is None
    assert result.estimated_swim_high_ratio is not None
    estimated = review_week(scope)
    assert (
        next(
            c for c in estimated.authoritative_intensity if c.sport == Discipline.SWIM
        ).status
        == "UNVERIFIED"
    )
    assert "operational_acceptance_of_estimated_swim_time" in estimated.activation_gates
    assert (
        "operational_acceptance_of_estimated_swim_time" not in result.activation_gates
    )


@pytest.mark.parametrize(
    "identifier,display",
    (
        ("TR-SWIM-011", "52.6"),
        ("TR-SWIM-012", "58.2"),
        ("TR-SWIM-013", "58.2"),
        ("TR-SWIM-014", "61.6"),
        ("TR-RUN-009", "86.2"),
        ("TR-BIKE-001", "30.2"),
        ("TR-BIKE-010", "281.2"),
        ("TR-BIKE-004", "84.4"),
    ),
)
def test_precision_evidence_not_official_authority(
    catalog: PhaseCatalog, identifier: str, display: str
) -> None:
    row = next(
        t for t in catalog.templates if t.predecessor.original_workout_id == identifier
    )
    calc = calculation_evidence(row.predecessor)[PRECISION_VERSION]
    assert calc["display"] == display and calc["display_matches"]
    assert row.official_method is None and row.official_planned_load is None


def test_estimator_reuse_and_wall_rest(catalog: PhaseCatalog) -> None:
    assert estimate_swim is historical_estimator
    for row in catalog.templates:
        if row.predecessor.sport != "swim":
            continue
        estimate = estimate_swim(row.predecessor)
        assert estimate.original is row.predecessor
        assert estimate.status == "ESTIMATED_FROM_APPROVED_REFERENCE_PACE"
        assert estimate.authoritative_duration_compliance == "UNVERIFIED"
        assert not estimate.operational_safety_gate_approved
        assert all(
            s.estimated_active_minutes == 0
            for s in estimate.segments
            if isinstance(s.original, WallRest)
        )


def test_artifact_reproduction_and_idempotence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "private.json"
    text = artifact()
    write_immutable(output, text)
    write_immutable(output, text)
    assert main(["--dry-run", "--private-output", str(output)]) == 0
    assert output.read_bytes() == text.encode()
    assert "Validated 77 inactive" in capsys.readouterr().out
    with pytest.raises(SourceError, match="artifact_revision_conflict"):
        write_immutable(output, text + " ")
    stored = ROOT / "docs/catalog/implementation/phase-tss/catalog.json"
    assert stored.read_bytes() == text.encode()


def test_arithmetic_and_simulation_reproduce() -> None:
    data = evidence()
    arithmetic = data["source_only_arithmetic"]
    assert arithmetic["base"]["count"] == arithmetic["build"]["count"] == 10
    assert arithmetic["recovery"]["count"] == arithmetic["taper"]["count"] == 0
    stored = ROOT / "docs/catalog/implementation/phase-tss/simulation.json"
    assert json.loads(stored.read_text()) == json.loads(json.dumps(data))


def test_disabled_dependency_boundary() -> None:
    app = ROOT / "backend/app"
    new_modules = {
        "app.modules.planning.v6_phase_review",
        "app.modules.workouts.joren_v6_phase",
    }
    for path in app.rglob("*.py"):
        if path.name in {
            "v6_phase_review.py",
            "joren_v6_phase.py",
            "joren_v6_phase_intake.py",
        }:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        assert not any(
            isinstance(n, ast.ImportFrom) and n.module in new_modules
            for n in ast.walk(tree)
        ), str(path)
    assert "experience" not in DIMENSIONS and "beginner" not in DIMENSIONS
    assert (
        "official_planned_tss_authority_binding"
        in review_week(make_scope(build_phase_catalog(), ())).activation_gates
    )
