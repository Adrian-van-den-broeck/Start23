"""Independent arithmetic/source oracles and real-planner policy conflict probes."""

import json
import socket
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, Inexact, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from app.jobs.joren_c2_dry_run import main, private_json
from app.modules.physiology.models import Discipline
from app.modules.physiology.planned_source import (
    SWIM_FIXED_HISTORICAL,
    SWIM_IF2,
    TIMED_IF2,
    SourceMethodError,
    calculate_source,
    require_operational_source,
)
from app.modules.workouts import joren_c2_verification as c2
from app.modules.workouts import joren_draft as c1
from app.modules.workouts.catalog import (
    CURRENT_CATALOG,
    active_catalog,
    snapshot_template,
)
from benchmarks.joren_c2 import evidence as policy_evidence
from benchmarks.joren_c2 import synthetic_deck
from benchmarks.planning import full_catalog

D = Decimal
EXACT = tuple(
    map(
        D,
        (
            "16.875",
            "25.3125",
            "33.75",
            "42.1875",
            "50.625",
            "59.0625",
            "67.5",
            "75.9375",
            "84.375",
            "31.421",
            "52.717",
            "58.145",
            "58.145",
            "61.6775",
            "39.88125",
            "54.759375",
            "69.6375",
            "39.88125",
            "54.759375",
            "69.6375",
        ),
    )
)
ROUNDED_PACE = tuple(
    map(
        D,
        (
            "16.875",
            "25.3125",
            "33.75",
            "42.1875",
            "50.625",
            "59.0625",
            "67.5",
            "75.9375",
            "84.375",
            "31.38228",
            "52.63956",
            "58.24104",
            "58.24104",
            "61.5807",
            "39.88125",
            "54.759375",
            "69.6375",
            "39.88125",
            "54.759375",
            "69.6375",
        ),
    )
)
SOURCE = (
    "16.9",
    "25.3",
    "33.8",
    "42.2",
    "50.6",
    "59.1",
    "67.5",
    "75.90000000000001",
    "84.40000000000001",
    "31.4",
    "52.6",
    "58.2",
    "58.2",
    "61.6",
    "39.9",
    "54.8",
    "69.59999999999999",
    "39.9",
    "54.8",
    "69.59999999999999",
)


@pytest.fixture(scope="module")
def rows() -> tuple[c2.SwimRow, ...]:
    return c2.swim_rows(c2.read_revision())


@pytest.mark.parametrize("index", range(20))
def test_all_twenty_source_bytes_and_calculations(
    rows: tuple[c2.SwimRow, ...], index: int
) -> None:
    row = rows[index]
    with ZipFile(c1.DEFAULT_SOURCES / c2.SWIM_IF2_SOURCE.filename) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    original = {c.attrib["r"]: c for c in sheet.findall("x:sheetData/x:row/x:c", c1.NS)}
    for cell in row.cells:
        xml = original[cell.coordinate]
        assert cell.xml == ET.tostring(xml, encoding="unicode")
        assert cell.formula is cell.cached_value is None
        assert cell.value == (
            xml.findtext("x:v", namespaces=c1.NS)
            if cell.cell_type == "n"
            else "".join(xml.itertext())
        )
    assert row.source_stored_p == SOURCE[index]
    assert row.planned_duration_seconds is row.operational_p is None
    assert row.activation_status == "INACTIVE"
    for paces, expected in (
        (c2.PDF_REFERENCE_SECONDS, EXACT[index]),
        (c2.RECONSTRUCTED_ROUNDED_SECONDS, ROUNDED_PACE[index]),
    ):
        calculated = calculate_source(
            method=SWIM_IF2,
            quantities=row.source_zones,
            if_values=c2.RECONSTRUCTED_IF,
            reference_seconds_per_100m=paces,
            sport_factor=D(".90"),
            stationary_rest_seconds=row.stationary_rest_seconds,
        )
        assert calculated.decimal_value == expected
        assert D(calculated.numerator) / calculated.denominator == expected
        assert calculated.operational_value is None
    assert ROUNDED_PACE[index].quantize(D(".1")) == D(row.source_display_p)
    assert row.structure_status == ("CONSISTENT" if index < 14 else "SOURCE-CONFLICTED")


@pytest.mark.parametrize("index", range(14, 20))
def test_six_conflicts_never_pass_strict_verification(
    rows: tuple[c2.SwimRow, ...], index: int
) -> None:
    row = rows[index]
    assert row.source_zones[1:3] == (D(600), D(0))
    assert row.ordered_zones[1:3] == (D(300), D(300))
    assert row.events[0].raw_token == "300m Z3 "
    for anchors in (c2.CONFIRMED_IF, c2.RECONSTRUCTED_IF):
        with pytest.raises(SourceMethodError, match="^source_prescription_conflict$"):
            c2.verify_swim_row(
                row, if_values=anchors, reference_seconds=c2.PDF_REFERENCE_SECONDS
            )


@pytest.mark.parametrize("index", (9, 10, 13))
def test_missing_z3_is_not_inferred(rows: tuple[c2.SwimRow, ...], index: int) -> None:
    assert c2.CONFIRMED_IF[2] is None
    with pytest.raises(SourceMethodError, match="^missing_if_anchor$"):
        c2.verify_swim_row(
            rows[index],
            if_values=c2.CONFIRMED_IF,
            reference_seconds=c2.PDF_REFERENCE_SECONDS,
        )


def test_exact_cell_diff_and_workbook_metadata() -> None:
    old = c1.read_document(
        (c1.DEFAULT_SOURCES / c1.SOURCES[2].filename).read_bytes(), c1.SOURCES[2]
    )
    new = c2.read_revision()
    assert len(old.cells) == len(new.cells) == 317
    assert old.extent == new.extent == "A1:O24"
    assert (old.worksheet, new.worksheet) == (
        "Zwemtrainingen Catalogus",
        "Zwemtrainingen",
    )
    changes = {n.coordinate for o, n in zip(old.cells, new.cells) if o.value != n.value}
    assert changes == {
        "A2",
        *(f"M{r}" for r in range(5, 25)),
        *(f"C{r}" for r in (14, 15, 16, 17, 19, 20, 21, 22, 23, 24)),
        *(f"{c}{r}" for c in "IJ" for r in range(19, 25)),
    }
    assert not any(c.formula for c in new.cells)
    for a, b in zip(old.cells, new.cells):
        if a.coordinate.startswith("N"):
            assert a.value == b.value
            assert a.cell_type == b.cell_type
            assert a.formula == b.formula
            assert a.number_format == b.number_format


def test_source_hash_mismatch_rejected_before_xml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = (c1.DEFAULT_SOURCES / c2.SWIM_IF2_SOURCE.filename).read_bytes()
    assert sha256(data).hexdigest() == c2.SWIM_IF2_SOURCE.sha256

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("XML processing before hash validation")

    monkeypatch.setattr(ET, "fromstring", forbidden)
    with pytest.raises(c1.SourceError, match="^source_revision_mismatch$"):
        c1.read_document(data + b"changed", c2.SWIM_IF2_SOURCE)
    with pytest.raises(c1.SourceError, match="^source_revision_mismatch$"):
        c1.read_document(data, c1.SOURCES[2])


@pytest.mark.parametrize("index", range(41))
def test_all_timed_rows_and_half_minute_sprints(index: int) -> None:
    record = c1.build_manifest().records[index]
    calculated = c2.verify_timed_row(record)
    assert calculated.decimal_value.quantize(D(".1")) == D(
        record.load.original_displayed_value
    )
    if record.original_workout_id == "TR-BIKE-020":
        assert calculated.decimal_value == D("84.4875")
        assert (
            sum(
                e.seconds
                for e in record.events
                if isinstance(e, c1.TimedZone) and e.zone == 5
            )
            == 180
        )
    if record.original_workout_id == "TR-BIKE-021":
        assert (calculated.numerator, calculated.denominator) == (1441, 15)
    assert record.load.approved_operational_tss is None


def test_stationary_rest_and_versioned_block_guidance(
    rows: tuple[c2.SwimRow, ...],
) -> None:
    row = rows[9]
    assert row.stationary_rest_seconds == 150
    assert row.original_session_focus == "5, 6"
    assert row.guidance[0].rpe_min == 3 and row.guidance[0].rpe_max == 4
    for event, guidance in zip(row.events, row.guidance):
        if isinstance(event, c1.WallRest):
            assert guidance.zone is guidance.rpe_min is guidance.rpe_max is None
    a = c2.verify_swim_row(
        row, if_values=c2.RECONSTRUCTED_IF, reference_seconds=c2.PDF_REFERENCE_SECONDS
    )
    b = c2.verify_swim_row(
        replace(row, stationary_rest_seconds=D(9999)),
        if_values=c2.RECONSTRUCTED_IF,
        reference_seconds=c2.PDF_REFERENCE_SECONDS,
    )
    assert a == b
    hard = next(
        r for r in c1.build_manifest().records if r.original_workout_id == "TR-BIKE-020"
    )
    assert hard.original_expected_rpe == "9, 10"
    assert {g.rpe_min for g in c2.block_guidance(hard.events, Discipline.BIKE)} == {
        1,
        3,
        9,
    }


def test_exact_fraction_and_caller_context_are_independent() -> None:
    params: dict[str, Any] = dict(
        method=TIMED_IF2,
        quantities=(D(0), D(0), D(0), D(6000), D(0)),
        if_values=c2.CONFIRMED_IF,
        sport_factor=D("1.00"),
    )
    # 100 min Z4 * .98^2 *100/60 = 2401/15, no intermediate rounding.
    reference = calculate_source(**params)
    assert (reference.numerator, reference.denominator) == (2401, 15)
    with localcontext() as context:
        context.prec = 3
        context.traps[Inexact] = True
        assert calculate_source(**params) == reference
    with pytest.raises(FrozenInstanceError):
        setattr(reference, "operational_value", D(1))


def test_historical_fixed_source_is_separate_and_cannot_double_factor() -> None:
    params: dict[str, Any] = dict(
        method=SWIM_FIXED_HISTORICAL,
        quantities=tuple(map(D, (0, 600, 1000, 0, 0))),
        if_values=(None,) * 5,
        sport_factor=D(1),
        fixed_per_100m=tuple(map(D, (".98", "1.44", "1.98", "2.4", "2.7"))),
    )
    old = calculate_source(**params)
    assert old.decimal_value == D("28.44")
    with pytest.raises(SourceMethodError, match="incompatible_source_parameters"):
        calculate_source(**{**params, "sport_factor": D(".9")})
    for method in (TIMED_IF2, SWIM_IF2, SWIM_FIXED_HISTORICAL):
        with pytest.raises(SourceMethodError, match="^source_method_not_approved$"):
            require_operational_source(method)
    with pytest.raises(SourceMethodError, match="^unsupported_source_method$"):
        require_operational_source("guessed")


@pytest.mark.parametrize("value", (D("NaN"), D("Infinity"), D(-1)))
def test_invalid_parameters_reject(value: Decimal) -> None:
    with pytest.raises(SourceMethodError, match="invalid_source_parameter"):
        calculate_source(
            method=TIMED_IF2,
            quantities=(value, D(0), D(0), D(0), D(0)),
            if_values=c2.CONFIRMED_IF,
            sport_factor=D(1),
        )


def test_dry_run_determinism_no_activation_history_mutation_or_private_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    before = {p: p.read_bytes() for p in c1.DEFAULT_SOURCES.iterdir()}
    historical = tuple(snapshot_template(t) for t in full_catalog())
    current = active_catalog(CURRENT_CATALOG)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("network in offline source verification")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    output = tmp_path / "private.json"
    assert main(["--dry-run", "--private-output", str(output)]) == 0
    summary = capsys.readouterr().out
    assert main(["--dry-run", "--private-output", str(output)]) == 0
    assert capsys.readouterr().out == summary
    assert (
        output.read_bytes()
        == (
            c1.ROOT
            / "docs/catalog/implementation/joren_c2_swim_if2_verification_v1.json"
        ).read_bytes()
    )
    assert summary == json.dumps(json.loads(summary), sort_keys=True) + "\n"
    assert not any(
        s in summary for s in ("16.9", "69.6", "source_stored_p", "decimal_value")
    )
    assert (
        main(
            [
                "--dry-run",
                "--private-output",
                str(c1.DEFAULT_SOURCES / c2.SWIM_IF2_SOURCE.filename),
            ]
        )
        == 1
    )
    assert "artifact_revision_conflict" in capsys.readouterr().out
    assert {p: p.read_bytes() for p in before} == before
    assert active_catalog(CURRENT_CATALOG) == current
    assert tuple(snapshot_template(t) for t in full_catalog()) == historical
    assert private_json(c2.private_evidence()) == output.read_text(encoding="utf-8")


def test_real_planner_45_64_5_constraints_and_consecutive_weeks() -> None:
    actual = policy_evidence()
    path = c1.ROOT / "docs/catalog/implementation/joren_c2_policy_probes_v1.json"
    assert actual == json.loads(path.read_text(encoding="utf-8"))
    cases = actual["scenarios"]
    assert cases["baseline_45_automatic"]["code"] == "catalog_capacity_unsatisfied"
    assert cases["baseline_45_explicit_three"]["code"] == "swipe_selection_invalid"
    starter = cases["exception_64_5"]
    assert (starter["count"], starter["planned_p"]) == (3, "64.5")
    assert starter["sport_loads"] == {"bike": "30.2", "run": "17.4", "swim": "16.9"}
    assert starter["unknown_swim_duration"] is True
    assert (
        cases["injured_run_zero"]["code"]
        == "restricted_zero_base_allocation_unavailable"
    )
    assert cases["all_injured"]["count"] == 0
    assert cases["exception_no_dates"]["outcome"] == "REJECTED"
    assert cases["missing_swim_capability"]["outcome"] == "REJECTED"
    assert cases["unconfirmed_swim_capability"]["outcome"] == "REJECTED"
    assert cases["exception_one_date"]["count"] == 3
    assert cases["long_bike_only_45"]["known_minutes"] == "420"
    assert cases["recovery"]["resolved_target"] == "38.700"
    assert cases["taper"]["resolved_target"] == "22.575"
    weeks = actual["following_weeks"]
    assert weeks["measured"]["resolved_target"] == "70.950"
    assert weeks["missing"]["resolved_basis"] == "prior_planned_hold"
    assert weeks["skipped"]["resolved_target"] == "47.6"
    assert weeks["third_after_incomplete_second"]["target"] == "64.5"
    assert all(
        t.source_workout_id not in {f"TR-SWIM-{i:03d}" for i in range(15, 21)}
        for t in synthetic_deck()
    )


def test_hard_distribution_and_budget_have_no_three_workout_solution() -> None:
    total = D("30.2") + D("17.4") + D("16.9")
    assert total == D("64.5") > 45
    targets = {"bike": D(45) * D(".5"), "run": D(45) * D(".3"), "swim": D(45) * D(".2")}
    assert targets == {"bike": D("22.5"), "run": D("13.5"), "swim": D(9)}
    for sport, minimum in (
        ("bike", D("30.2")),
        ("run", D("17.4")),
        ("swim", D("16.9")),
    ):
        assert minimum > targets[sport]
    assert D("16.9") > total * D(".2")


def test_draft_registry_preserves_all_c1_identities_and_never_activates() -> None:
    from uuid import UUID, uuid5

    path = (
        c1.ROOT / "docs/catalog/implementation/joren_c2_draft_revision_registry_v1.json"
    )
    registry = json.loads(path.read_text(encoding="utf-8"))
    old_bytes = (
        c1.ROOT / "docs/catalog/implementation/joren_c1_manifest_v1.json"
    ).read_bytes()
    assert (
        sha256(old_bytes).hexdigest()
        == "3c149c9096dd568156eab0246f7f6c679fc6ac98416b073a798c7bde3b68bc85"
    )
    old = {r["original_workout_id"]: r for r in json.loads(old_bytes)["records"]}
    assert len(registry["rows"]) == len(old) == 61
    candidate_ids = set()
    for row in registry["rows"]:
        historical = old[row["source_id"]]
        assert row["c1_template_id"] == historical["provisional_id"]
        assert row["provisional_key"] == historical["provisional_key"]
        assert row["activation_status"] == "INACTIVE"
        assert row["accepted_predecessor_mapping"] is row["operational_p"] is None
        if row["source_id"].startswith("TR-SWIM-"):
            assert row["candidate_template_version"] == 2
            assert row["candidate_template_id"] != row["c1_template_id"]
            assert row["candidate_template_id"] == str(
                uuid5(
                    UUID(row["provisional_key"]),
                    f"source-sha256:{c2.SWIM_IF2_SOURCE.sha256}|template-version:2",
                )
            )
        else:
            assert row["candidate_template_id"] == row["c1_template_id"]
        candidate_ids.add(row["candidate_template_id"])
    assert len(candidate_ids) == 61
    assert sum(r["status"] == "SOURCE-CONFLICTED" for r in registry["rows"]) == 6


def test_strict_experiment_and_unrecognized_source_dispatch(
    rows: tuple[c2.SwimRow, ...],
) -> None:
    for index, row in enumerate(rows[:14]):
        if index in (9, 10, 13):
            continue
        result = c2.verify_swim_row(
            row, if_values=c2.CONFIRMED_IF, reference_seconds=c2.PDF_REFERENCE_SECONDS
        )
        assert result.decimal_value == EXACT[index]
        assert result.operational_value is None
    with pytest.raises(SourceMethodError, match="^unsupported_source_revision$"):
        c2.verify_timed_row(
            replace(c1.build_manifest().records[0], source_sha256="0" * 64)
        )
    with pytest.raises(SourceMethodError, match="^missing_reference_pace$"):
        calculate_source(
            method=SWIM_IF2,
            quantities=(D(0), D(100), D(0), D(0), D(0)),
            if_values=c2.CONFIRMED_IF,
            sport_factor=D(".90"),
        )
