"""V6 source custody, immutable lineage and actual-planner policy boundaries."""

import json
from collections import Counter
from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from uuid import uuid5

import pytest

from app.jobs.joren_catalog_dry_run import offline_reserved_ids, write_immutable
from app.jobs.joren_v6_dry_run import main
from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
    evaluate_training_week,
)
from app.modules.physiology.planned_source import (
    SWIM_IF2,
    TIMED_IF2,
    SourceMethodError,
    require_operational_source,
)
from app.modules.workouts.catalog import CURRENT_CATALOG
from app.modules.workouts.joren_c21_corrections import correction_evidence
from app.modules.workouts.joren_draft import (
    DEFAULT_SOURCES,
    ROOT,
    SourceError,
    SwimDistance,
    TimedZone,
    WallRest,
    normalize_row,
    read_document,
    validate_identities,
)
from app.modules.workouts.joren_v6 import (
    EXACT_SECONDS_VERSION,
    PRECISION_VERSION,
    V6_SOURCES,
    V6Manifest,
    build_v6_manifest,
    calculation_evidence,
    private_evidence,
    private_json,
    revision_differences,
)
from benchmarks.joren_c2 import START
from benchmarks.joren_v6 import (
    CANDIDATE,
    MINIMUM,
    combinations,
    continuation,
    inspect_plan,
    projection,
    scenario,
)

D = Decimal
ALL_IDS = tuple(
    f"TR-{sport}-{i:03d}"
    for sport, n in (("RUN", 28), ("BIKE", 27), ("SWIM", 22))
    for i in range(1, n + 1)
)


@pytest.fixture(scope="module")
def manifest() -> V6Manifest:
    return build_v6_manifest(reserved=offline_reserved_ids())


@pytest.mark.parametrize("identifier", ALL_IDS)
def test_every_source_row_is_lossless_and_reconciles(
    manifest: V6Manifest, identifier: str
) -> None:
    r = next(r for r in manifest.records if r.original_workout_id == identifier)
    doc = next(d for d in manifest.documents if d.spec.document_id == r.document_id)
    assert (
        tuple(
            c
            for c in doc.cells
            if c.coordinate in {f"{col}{r.source_row}" for col in "ABCDEFGHIJKLMNO"}
        )
        == r.original_cells
    )
    reparsed = normalize_row(doc, r.source_row, r.original_cells, r.selection)
    assert reparsed.events == r.events
    assert reparsed.original_zone_distribution == r.original_zone_distribution
    assert sum(r.original_zone_distribution) == r.original_measure
    assert r.original_cells[12].numeric_lexeme == r.load.source_numeric_lexeme
    assert all(
        e.raw_token == r.original_execution_structure[e.start : e.end] for e in r.events
    )
    assert r.load.approved_operational_tss is None
    assert r.operational_method_version is None and r.activation_status == "INACTIVE"
    assert r.selection.beginner_eligibility.state == "DRAFT"
    assert r.original_expected_zone == max(
        e.zone for e in r.events if not isinstance(e, WallRest)
    )
    assert r.original_expected_rpe == (
        f"{2 * r.original_expected_zone - 1}, {2 * r.original_expected_zone}"
    )
    calculation = calculation_evidence(r)[PRECISION_VERSION]
    assert calculation["display_matches"]
    assert calculation["operational_value"] is None
    if r.sport == "swim":
        assert r.planned_duration_seconds is None
        assert all(
            e.duration_seconds is None for e in r.events if isinstance(e, SwimDistance)
        )
    else:
        assert (
            sum(e.seconds for e in r.events if isinstance(e, TimedZone))
            == r.original_measure * 60
        )


def test_counts_and_exact_pin(manifest: V6Manifest) -> None:
    assert len(manifest.records) == 77
    assert Counter(
        (r.sport, sum(v > 0 for v in r.original_zone_distribution) == 1)
        for r in manifest.records
    ) == {
        ("run", True): 24,
        ("run", False): 4,
        ("bike", True): 19,
        ("bike", False): 8,
        ("swim", True): 11,
        ("swim", False): 11,
    }
    for spec in V6_SOURCES:
        original = ROOT.parent.parent / "docs/trainings" / spec.filename
        archived = DEFAULT_SOURCES / spec.filename
        assert sha256(archived.read_bytes()).hexdigest() == spec.sha256
        if original.exists():
            assert original.read_bytes() == archived.read_bytes()
        with pytest.raises(SourceError, match="source_revision_mismatch"):
            read_document(archived.read_bytes() + b"changed", spec)


def test_revision_diff_uses_immediate_swim_parent(manifest: V6Manifest) -> None:
    diffs = revision_differences(manifest)["rows"]
    assert len([r for r in diffs if r["kind"] == "NEW"]) == 16
    changed = {
        r["source_id"]: [c["coordinate"][0] for c in r["changed_values"]]
        for r in diffs
        if r["changed_values"]
    }
    expected = {f"TR-RUN-{i:03d}": ["C"] for i in range(4, 17)}
    expected["TR-RUN-017"] = ["C", "O"]
    expected.update({f"TR-BIKE-{i:03d}": ["C"] for i in (14, 15, 16, 17, 20, 21)})
    expected.update({f"TR-SWIM-{i:03d}": ["N"] for i in range(15, 21)})
    assert changed == expected
    assert sum(r["unchanged_prescription"] for r in diffs) == 55
    assert all(c["coordinate"][0] != "M" for r in diffs for c in r["changed_values"])
    assert manifest.previous_documents[2].spec.filename == "Zwemtrainingen_IF2.xlsx"


def test_versioned_identities_and_no_title_merge(manifest: V6Manifest) -> None:
    assert len({r.provisional_key for r in manifest.records}) == 77
    assert len({r.provisional_id for r in manifest.records}) == 77
    for r in manifest.records:
        new = r.predecessor_source_sha256 is None
        assert r.provisional_template_version == (
            1 if new else 3 if r.sport == "swim" else 2
        )
        assert r.provisional_id == uuid5(
            r.provisional_key,
            f"source-sha256:{r.source_sha256}|template-version:{r.provisional_template_version}",
        )
        assert r.provisional_id != r.predecessor_provisional_id
        assert r.accepted_predecessor_mapping is None
    with pytest.raises(SourceError, match="provisional_uuid_collision"):
        validate_identities(
            manifest.records, frozenset({manifest.records[0].provisional_id})
        )
    with pytest.raises(SourceError, match="duplicate_source_identity_or_revision"):
        validate_identities((manifest.records[0], manifest.records[0]))
    r = manifest.records[3]
    assert (
        replace(r, original_training_name="another title").provisional_id
        == r.provisional_id
    )


@pytest.mark.parametrize(
    "i,rest", ((15, 300), (16, 450), (17, 600), (18, 150), (19, 225), (20, 300))
)
def test_six_already_corrected_swims(manifest: V6Manifest, i: int, rest: int) -> None:
    r = next(r for r in manifest.records if r.original_workout_id == f"TR-SWIM-{i:03d}")
    evidence = json.loads(private_json(correction_evidence()))
    overlay = next(
        row for row in evidence["records"] if row["source_id"] == r.original_workout_id
    )
    assert r.original_execution_structure == overlay["derived_prescription"]
    assert r.original_zone_distribution[1:3] == (D(600), D(0))
    assert isinstance(r.events[0], SwimDistance)
    assert r.events[0].meters == 300 and r.events[0].zone == 2
    assert r.stationary_rest_seconds == rest
    assert all(
        e.zone is None and e.rpe is None for e in r.events if isinstance(e, WallRest)
    )
    assert calculation_evidence(r)[PRECISION_VERSION]["display_matches"]


def test_precision_reconstruction_is_not_approval(manifest: V6Manifest) -> None:
    differences = {}
    for r in manifest.records:
        c = calculation_evidence(r)
        if c[EXACT_SECONDS_VERSION]["display"] != c[PRECISION_VERSION]["display"]:
            differences[r.original_workout_id] = (
                c[EXACT_SECONDS_VERSION]["display"],
                c[PRECISION_VERSION]["display"],
            )
        strict = c["confirmed_if_exact_reference"]
        if r.original_workout_id in ("TR-SWIM-010", "TR-SWIM-011", "TR-SWIM-014"):
            assert strict == {"error": "missing_if_anchor"}
    assert differences == {
        "TR-SWIM-011": ("52.7", "52.6"),
        "TR-SWIM-012": ("58.1", "58.2"),
        "TR-SWIM-013": ("58.1", "58.2"),
        "TR-SWIM-014": ("61.7", "61.6"),
    }
    for method in (TIMED_IF2, SWIM_IF2):
        with pytest.raises(SourceMethodError, match="source_method_not_approved"):
            require_operational_source(method)
    r = next(r for r in manifest.records if r.original_workout_id == "TR-BIKE-001")
    assert calculation_evidence(r)[PRECISION_VERSION]["decimal_value"] == D("30.25")
    assert calculation_evidence(r)[PRECISION_VERSION]["display"] == "30.2"


def test_manifest_reproducibility_and_decimal_isolation(manifest: V6Manifest) -> None:
    artifact = ROOT / "docs/catalog/implementation/joren_v6_manifest_v1.json"
    expected = private_json(private_evidence(manifest))
    assert artifact.read_bytes() == expected.encode()
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        assert private_json(private_evidence(build_v6_manifest())) == expected


def test_cli_immutable_output_and_safe_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "v6.json"
    assert main(["--dry-run", "--private-output", str(path)]) == 0
    before = path.stat().st_mtime_ns
    assert main(["--dry-run", "--private-output", str(path)]) == 0
    assert path.stat().st_mtime_ns == before
    assert "43.1" not in capsys.readouterr().out
    with pytest.raises(SourceError, match="artifact_revision_conflict"):
        write_immutable(path, "different revision")


def test_beginner_candidate_and_minimum_actual_engine(manifest: V6Manifest) -> None:
    before = CURRENT_CATALOG
    deck = projection(manifest.records)
    minimum = sum(
        D(r.load.original_displayed_value)
        for r in manifest.records
        if r.original_workout_id in MINIMUM
    )
    assert minimum == D("29.3")
    assert (
        inspect_plan(scenario("minimum", deck), manifest.records)["code"]
        == "swipe_selection_invalid"
    )
    candidate = inspect_plan(scenario("candidate", deck), manifest.records)
    assert candidate["target"] == "45.0"
    assert candidate["selected_p"] == "43.1" and candidate["count"] == 3
    assert set(candidate["source_ids"]) == set(CANDIDATE)
    assert candidate["budget_ceiling"] == "WITHIN"
    assert candidate["active_time_compliance"]["run"]["high_ratio"] == "0"
    assert candidate["active_time_compliance"]["bike"]["high_ratio"] == "0"
    assert candidate["active_time_compliance"]["swim"]["status"] == "UNVERIFIED"
    assert candidate["known_minutes"] == "65"
    assert combinations(manifest.records)["one_each_all_easy_within_45_count"] > 1
    assert CURRENT_CATALOG == before


def test_capability_availability_injury_fail_closed(manifest: V6Manifest) -> None:
    deck = projection(manifest.records)
    for case in (
        "candidate_no_dates",
        "missing_swim_capability",
        "unconfirmed_swim_capability",
        "injury_run",
    ):
        result = inspect_plan(scenario(case, deck), manifest.records)
        assert result["outcome"] == "FAIL_CLOSED"
    one = inspect_plan(scenario("candidate_one_day", deck), manifest.records)
    assert "workouts_consolidated_on_available_dates" in one["warnings"]
    rest = inspect_plan(scenario("all_injured", deck), manifest.records)
    assert rest["count"] == 0


def test_all_easy_build_recovery_taper_and_repeat_identity(
    manifest: V6Manifest,
) -> None:
    deck = projection(manifest.records)
    easy = inspect_plan(scenario("all_easy_build", deck), manifest.records)
    assert easy["outcome"] == "PENDING_HYPOTHETICAL_PLAN"
    assert easy["active_time_compliance"]["bike"]["high_ratio"] == "0"
    assert easy["active_time_compliance"]["run"]["high_ratio"] == "0"
    for case in ("beginner_recovery", "beginner_taper"):
        assert (
            inspect_plan(scenario(case, deck), manifest.records)["outcome"]
            == "FAIL_CLOSED"
        )
    repeat = inspect_plan(scenario("repeat_explicit", deck), manifest.records)
    assert repeat["source_ids"] == ["TR-BIKE-023", "TR-BIKE-023"]
    assert repeat["occurrence_identity_status"] == "UNIQUE"
    assert repeat["selected_p"] == "40.4"


@pytest.mark.parametrize(
    "identifier,high,total",
    (
        ("TR-BIKE-020", 180, 5580),
        ("TR-BIKE-021", 240, 6240),
        ("TR-RUN-017", 1800, 3600),
    ),
)
def test_mixed_active_time_not_whole_workout(
    manifest: V6Manifest, identifier: str, high: int, total: int
) -> None:
    r = next(r for r in manifest.records if r.original_workout_id == identifier)
    assert all(isinstance(e, TimedZone) for e in r.events)
    segments = tuple(
        PlannedSegment(e.seconds, TrainingZone(e.zone))
        for e in r.events
        if isinstance(e, TimedZone)
    )
    compliance = next(
        c
        for c in evaluate_training_week(
            START, (PlannedSession(Discipline(r.sport), START, segments),)
        )
        if c.sport.value == r.sport
    )
    assert compliance.known_high_seconds == high
    assert compliance.high_ratio == Fraction(high, total)
    assert compliance.status == ("ACCEPTED" if high * 5 <= total else "REJECTED")


def test_consecutive_weeks_use_registration_not_source_prescription(
    manifest: V6Manifest,
) -> None:
    results = continuation(projection(manifest.records), manifest.records)
    assert results["measured"]["target"] == "47.410"
    assert results["unknown"]["target"] == "43.1"
    assert results["partial_observed"]["target"] == "43.1"
    assert results["skipped"]["target"] == "34"
    assert results["partial_observed"]["registration"]["known_subtotal"] == "37"
    assert not results["partial_observed"]["registration"]["progression_eligible"]
    assert results["third_after_incomplete_second"]["target"] == "43.1"
