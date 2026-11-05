"""Independent offline fixtures; no approval or operational safety is inferred."""

import ast
import json
from dataclasses import asdict, replace
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

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
    calculate_source,
    require_operational_source,
)
from app.modules.workouts.joren_c2_verification import CONFIRMED_IF as HISTORICAL_IF
from app.modules.workouts.joren_draft import (
    ROOT,
    DraftWorkout,
    SwimDistance,
    TimedZone,
    WallRest,
    parse_events,
)
from app.modules.workouts.joren_v6 import V6Manifest, build_v6_manifest
from benchmarks.v6_partial_approval import (
    CONFIRMED_IF,
    DECISION_VERSION,
    REFERENCE_MINUTES,
    REFERENCE_SECONDS,
    SELECTION_PRIORITIES,
    EstimatedSwimSession,
    EstimatedSwimWeek,
    estimate_swim,
    evaluate_swim_week,
)
from benchmarks.v6_partial_approval_evidence import evidence

START = date(2026, 11, 2)
FIXTURES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures/v6_partial_approval.json").read_text()
)


@pytest.fixture(scope="module")
def manifest() -> V6Manifest:
    return build_v6_manifest()


def synthetic(manifest: V6Manifest, text: str) -> DraftWorkout:
    base = next(r for r in manifest.records if r.original_workout_id == "TR-SWIM-021")
    events = parse_events(text, "swim", "N_SYNTHETIC")
    meters = tuple(
        sum(
            (e.meters for e in events if isinstance(e, SwimDistance) and e.zone == z),
            Decimal(0),
        )
        for z in range(1, 6)
    )
    return replace(
        base,
        original_workout_id="SYNTHETIC_OFFLINE_ONLY",
        original_execution_structure=text,
        events=events,
        original_zone_distribution=meters,
        original_measure=sum(meters, Decimal(0)),
        planned_distance_meters=sum(meters, Decimal(0)),
        stationary_rest_seconds=sum(
            (e.seconds for e in events if isinstance(e, WallRest)), Decimal(0)
        ),
    )


def week(record: DraftWorkout, delta: Fraction = Fraction(1, 200)) -> EstimatedSwimWeek:
    return evaluate_swim_week(
        START,
        (EstimatedSwimSession("synthetic-occurrence", START, record),),
        sensitivity_half_width=delta,
    )


@pytest.mark.parametrize("identifier", tuple(FIXTURES["if2_candidates"]))
def test_confirmed_parameters_against_independent_if2_fixtures(
    manifest: V6Manifest, identifier: str
) -> None:
    r = next(r for r in manifest.records if r.original_workout_id == identifier)
    quantities = (
        r.original_zone_distribution
        if r.sport == "swim"
        else tuple(
            sum(
                (
                    e.seconds
                    for e in r.events
                    if isinstance(e, TimedZone) and e.zone == z
                ),
                Decimal(0),
            )
            for z in range(1, 6)
        )
    )
    candidate = calculate_source(
        method=SWIM_IF2 if r.sport == "swim" else TIMED_IF2,
        quantities=quantities,
        if_values=CONFIRMED_IF,
        sport_factor=Decimal(r.original_cells[6].value or "NaN"),
        reference_seconds_per_100m=REFERENCE_SECONDS if r.sport == "swim" else None,
        stationary_rest_seconds=r.stationary_rest_seconds,
    )
    assert Fraction(candidate.numerator, candidate.denominator) == Fraction(
        FIXTURES["if2_candidates"][identifier]
    )
    assert candidate.operational_value is None
    assert r.load.approved_operational_tss is None
    with pytest.raises(SourceMethodError, match="source_method_not_approved"):
        require_operational_source(candidate.method)


def test_parameters_are_new_version_with_unchanged_historical_anchors() -> None:
    assert DECISION_VERSION == "joren-v6-partial-approval-1"
    assert CONFIRMED_IF[2] == Decimal(".88")
    assert HISTORICAL_IF[2] is None
    for z in (0, 1, 3, 4):
        assert CONFIRMED_IF[z] == HISTORICAL_IF[z]
    assert REFERENCE_MINUTES == tuple(
        map(Decimal, ("2.17", "2.00", "1.83", "1.67", "1.50"))
    )
    assert tuple(Fraction(v) * 60 for v in REFERENCE_MINUTES) == REFERENCE_SECONDS
    assert len(SELECTION_PRIORITIES) == 7


def test_private_evidence_retains_source_and_estimate_authority() -> None:
    result = evidence()
    assert len(result["if2_candidates"]) == 77
    assert result["source_method_status"] == "UNAPPROVED"
    for identifier, row in result["single_workout_swim_week_diagnostics"].items():
        expected = FIXTURES["swims"][identifier]
        assert row["source_execution_cell"]["value"] == expected["prescription"]
        assert row["estimated_low_minutes"] == expected["low_minutes"]
        assert row["estimated_high_minutes"] == expected["high_minutes"]
        assert row["original_prescribed_duration_seconds"] is None
        assert all(v is None for v in row["individual_prescribed_segment_durations"])
        assert row["authoritative_duration_compliance"] == "UNVERIFIED"
        assert row["operational_safety_gate_approved"] is False


@pytest.mark.parametrize("identifier", tuple(FIXTURES["swims"]))
def test_all_22_swims_against_independent_ordered_fixtures(
    manifest: V6Manifest, identifier: str
) -> None:
    r = next(r for r in manifest.records if r.original_workout_id == identifier)
    before = asdict(r)
    expected = FIXTURES["swims"][identifier]
    estimate = estimate_swim(r)
    result = week(r)
    assert estimate.original is r
    assert estimate.status == "ESTIMATED_FROM_APPROVED_REFERENCE_PACE"
    assert [str(s.estimated_active_minutes) for s in estimate.segments] == expected[
        "ordered_active_minutes"
    ]
    assert all(s.original is e for s, e in zip(estimate.segments, r.events))
    assert estimate.low_minutes == Fraction(expected["low_minutes"])
    assert estimate.high_minutes == Fraction(expected["high_minutes"])
    assert result.status == expected["status"]
    assert not result.boundary_sensitive  # Explicit +/- .005 scenario only.
    assert result.authoritative_duration_compliance == "UNVERIFIED"
    assert not result.operational_safety_gate_approved
    assert r.planned_duration_seconds is None
    assert r.original_execution_structure == expected["prescription"]
    assert r.planned_distance_meters == Decimal(expected["meters"])
    assert asdict(r) == before  # Including raw cells, missing times and suitability.
    authoritative = evaluate_training_week(
        START,
        (
            PlannedSession(
                Discipline.SWIM,
                START,
                tuple(
                    PlannedSegment(e.seconds, stationary_rest=True)
                    if isinstance(e, WallRest)
                    else PlannedSegment(None, TrainingZone(e.zone))
                    for e in r.events
                    if isinstance(e, SwimDistance | WallRest)
                ),
            ),
        ),
    )
    assert next(s for s in authoritative if s.sport == Discipline.SWIM).status == (
        "UNVERIFIED"
    )


@pytest.mark.parametrize(
    "text,low,high,status,sensitive",
    (
        ("500m Z2", "10", "0", "ESTIMATED_COMPLIANT", False),
        (
            "100m Z1|100m Z2|100m Z3|100m Z4|100m Z5",
            "4.17",
            "5",
            "ESTIMATED_EXCEEDED",
            False,
        ),
        ("300m Z2|100m Z5", "6", "1.5", "ESTIMATED_COMPLIANT", True),
        ("366m Z2|100m Z3", "7.32", "1.83", "ESTIMATED_COMPLIANT", True),
        ("334m Z2|100m Z4", "6.68", "1.67", "ESTIMATED_COMPLIANT", True),
        ("299m Z2|100m Z5", "5.98", "1.5", "ESTIMATED_EXCEEDED", True),
        ("301m Z2|100m Z5", "6.02", "1.5", "ESTIMATED_COMPLIANT", True),
        ("100m Z3", "0", "1.83", "ESTIMATED_EXCEEDED", False),
        ("300m Z2|999999s Rust|100m Z5", "6", "1.5", "ESTIMATED_COMPLIANT", True),
    ),
)
def test_synthetic_independent_boundaries_and_wall_rest(
    manifest: V6Manifest, text: str, low: str, high: str, status: str, sensitive: bool
) -> None:
    result = week(synthetic(manifest, text))
    assert result.low_minutes == Fraction(low)
    assert result.high_minutes == Fraction(high)
    assert result.high_ratio == Fraction(high) / (Fraction(low) + Fraction(high))
    assert result.status == status
    assert result.boundary_sensitive is sensitive


def test_week_aggregates_occurrences_and_is_not_a_per_workout_gate(
    manifest: V6Manifest,
) -> None:
    low = synthetic(manifest, "150m Z2")
    high = synthetic(manifest, "100m Z5")
    result = evaluate_swim_week(
        START,
        (
            EstimatedSwimSession("low1", START, low),
            EstimatedSwimSession("high", START + timedelta(days=2), high),
            EstimatedSwimSession("low2", START + timedelta(days=6), low),
        ),
        sensitivity_half_width=Fraction(0),
    )
    assert week(high).status == "ESTIMATED_EXCEEDED"
    assert result.high_ratio == Fraction(1, 5)
    assert result.status == "ESTIMATED_COMPLIANT"
    assert (
        result.sensitivity_ratio_min == result.sensitivity_ratio_max == Fraction(1, 5)
    )
    assert not result.boundary_sensitive
    empty = evaluate_swim_week(START, (), sensitivity_half_width=Fraction(0))
    assert empty.status == "NOT_APPLICABLE" and empty.high_ratio is None


def test_sport_isolation_and_authoritative_times_remain_separate(
    manifest: V6Manifest,
) -> None:
    r = synthetic(manifest, "300m Z2|100m Z5")
    assert week(r).status == "ESTIMATED_COMPLIANT"
    authoritative = evaluate_training_week(
        START,
        (
            PlannedSession(
                Discipline.SWIM, START, (PlannedSegment(None, TrainingZone(2)),)
            ),
            PlannedSession(
                Discipline.BIKE,
                START,
                (PlannedSegment(Decimal(3600), TrainingZone(5)),),
            ),
            PlannedSession(
                Discipline.RUN, START, (PlannedSegment(Decimal(600), TrainingZone(2)),)
            ),
        ),
    )
    assert {s.sport: s.status for s in authoritative} == {
        Discipline.SWIM: "UNVERIFIED",
        Discipline.BIKE: "REJECTED",
        Discipline.RUN: "ACCEPTED",
    }


def test_exact_arithmetic_under_hostile_decimal_context(manifest: V6Manifest) -> None:
    r = synthetic(manifest, "366m Z2|100m Z3|20s Rust")
    expected = week(r)
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.rounding = ROUND_DOWN
        ctx.traps[Inexact] = True
        assert week(r) == expected


@pytest.mark.parametrize("zone", range(1, 6))
def test_each_reference_pace_independently(manifest: V6Manifest, zone: int) -> None:
    estimate = estimate_swim(synthetic(manifest, f"100m Z{zone}"))
    assert estimate.low_minutes + estimate.high_minutes == Fraction(
        (217, 200, 183, 167, 150)[zone - 1], 100
    )


def test_invalid_prescriptions_fail_closed(manifest: V6Manifest) -> None:
    r = synthetic(manifest, "100m Z2")
    event = r.events[0]
    assert isinstance(event, SwimDistance)
    bad = (
        replace(r, sport="run"),
        replace(r, planned_duration_seconds=Decimal(120)),
        replace(r, events=()),
        replace(r, events=(replace(event, sequence=2),)),
        replace(r, events=(replace(event, zone=6),)),
        replace(r, events=(replace(event, meters=Decimal("NaN")),)),
        replace(r, events=(replace(event, meters=Decimal("1.5")),)),
        replace(r, planned_distance_meters=Decimal(101)),
        replace(r, events=(TimedZone(1, "1s Z2", "N", 0, 5, Decimal(1), 2),)),
    )
    for invalid in bad:
        with pytest.raises(ValueError):
            estimate_swim(invalid)
    s = EstimatedSwimSession("id", START, r)
    with pytest.raises(ValueError, match="monday"):
        evaluate_swim_week(
            START + timedelta(days=1), (), sensitivity_half_width=Fraction(0)
        )
    with pytest.raises(ValueError, match="outside"):
        evaluate_swim_week(
            START,
            (replace(s, local_date=START + timedelta(days=7)),),
            sensitivity_half_width=Fraction(0),
        )
    with pytest.raises(ValueError, match="identity"):
        evaluate_swim_week(START, (s, s), sensitivity_half_width=Fraction(0))
    for delta in (Fraction(-1), Fraction(3, 2)):
        with pytest.raises(ValueError, match="sensitivity"):
            week(r, delta)


def test_offline_only_no_active_import_or_infrastructure_dependency() -> None:
    target = ROOT / "backend/benchmarks/v6_partial_approval.py"
    tree = ast.parse(target.read_text())
    imports = [n for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)]
    allowed = {
        "dataclasses",
        "datetime",
        "decimal",
        "fractions",
        "typing",
        "app.modules.workouts.joren_draft",
    }
    for node in imports:
        modules = (
            [node.module]
            if isinstance(node, ast.ImportFrom)
            else [n.name for n in node.names]
        )
        assert all(m in allowed for m in modules)
    for path in (ROOT / "backend/app").rglob("*.py"):
        assert "v6_partial_approval" not in path.read_text(encoding="utf-8")
