"""Independent finite-set and policy boundary checks; no real suitability grants."""

import ast
import json
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Literal

import pytest

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
)
from benchmarks.joren_c2 import START
from benchmarks.joren_v6 import source_records
from benchmarks.prospective_planning_policy import (
    Candidate,
    RestrictionEvidence,
    SuitabilityDimension,
)
from benchmarks.v6_final_policy import (
    POLICY_VERSION,
    Feasibility,
    PolicyInput,
    enumerate_weeks,
    intensity_evidence,
)
from benchmarks.v6_final_policy_evidence import ASSUMED, evidence, fixture_support
from benchmarks.v6_partial_approval import estimate_swim
from benchmarks.v6_policy_sandbox import candidates

D = Decimal
DATES = frozenset(START + timedelta(days=i) for i in range(7))


def timed(sport: Discipline, low: str, high: str) -> PolicyInput:
    return fixture_support(
        PolicyInput(
            Candidate(
                f"TEST_ONLY:{sport.value}",
                sport,
                D("1"),
                PlannedSession(
                    sport,
                    START,
                    (
                        PlannedSegment(D(low), TrainingZone.ZONE_2),
                        PlannedSegment(D(high), TrainingZone.ZONE_3),
                    ),
                ),
                D(high) == 0,
            )
        )
    )


def assess(rows: tuple[PolicyInput, ...], budget: str = "45") -> Feasibility:
    return enumerate_weeks(
        rows,
        week_start=START,
        authorized_budget=D(budget),
        available_dates=DATES,
        safeguards=ASSUMED,
        maximum_combinations=20000,
    )


@pytest.mark.parametrize("build_week", (1, 2, 3, 4))
def test_all_easy_BUILD_has_no_high_minimum_but_requires_suitability(
    build_week: int,
) -> None:
    rows = tuple(timed(s, "600", "0") for s in Discipline)
    # Phase/week evidence is explicit fixture context, never inferred from easy.
    context = replace(ASSUMED, reference=f"TEST_ONLY:BUILD:{build_week}:safeguards")
    result = enumerate_weeks(
        rows,
        week_start=START,
        authorized_budget=D(3),
        available_dates=DATES,
        safeguards=context,
        maximum_combinations=7,
    )
    assert result.status == "FULL_WEEK_WITNESSES"
    assert all(
        i.high_ratio == 0 for w in result.supported_witnesses for i in w.intensity
    )
    unknown = tuple(
        replace(r, candidate=replace(r.candidate, suitability=())) for r in rows
    )
    assert assess(unknown).status == "UNRESOLVED_FAIL_CLOSED"
    assert result.policy_version == POLICY_VERSION
    assert not result.operational_approval and not result.source_method_approved


@pytest.mark.parametrize(
    ("low", "high", "status", "ratio"),
    (
        ("240", "60", "COMPLIANT", Fraction(1, 5)),
        ("239", "60", "EXCEEDED", Fraction(60, 299)),
        ("600", "0", "COMPLIANT", Fraction(0)),
    ),
)
def test_active_time_boundary(
    low: str, high: str, status: str, ratio: Fraction
) -> None:
    result = intensity_evidence(timed(Discipline.RUN, low, high), START)
    assert (result.status, result.high_ratio) == (status, ratio)


def test_mixed_intervals_count_low_recoveries_and_isolate_sports() -> None:
    row = timed(Discipline.BIKE, "0", "0")
    segments = tuple(
        segment
        for _ in range(3)
        for segment in (
            PlannedSegment(D(60), TrainingZone.ZONE_5),
            PlannedSegment(D(240), TrainingZone.ZONE_1),
        )
    )
    row = replace(
        row,
        candidate=replace(
            row.candidate, session=replace(row.candidate.session, segments=segments)
        ),
    )
    assert intensity_evidence(row, START).high_ratio == Fraction(1, 5)
    run = timed(Discipline.RUN, "1", "100")
    result = assess((row, run))
    assert result.excluded_ids == (run.candidate.source_id,)
    assert all(
        run.candidate.source_id not in w.source_ids for w in result.supported_witnesses
    )


def test_partial_permission_is_separate_from_ranking_and_full_coverage() -> None:
    rows = tuple(timed(s, "600", "0") for s in Discipline)
    assert assess(rows, "3").status == "FULL_WEEK_WITNESSES"
    partial = assess(rows, "2")
    assert partial.status == "PARTIAL_WEEK_WITNESSES"
    assert sum(len(w.sports) == 2 for w in partial.supported_witnesses) == 3
    assert partial.ranking == "UNRESOLVED_NO_DEFAULT"
    assert assess(rows, "1").status == "PARTIAL_WEEK_WITNESSES"
    assert assess(rows, "0").status == "NO_PLAN_REST_FAIL_CLOSED"
    assert assess(()).status == "NO_PLAN_REST_FAIL_CLOSED"
    assert assess(tuple(reversed(rows)), "2") == partial
    # An unknown third sport cannot establish impossibility of safe full cover.
    unknown = replace(rows[0], candidate=replace(rows[0].candidate, suitability=()))
    assert assess((unknown, *rows[1:]), "3").status == "UNRESOLVED_FAIL_CLOSED"


def test_BUILD_zero_high_with_a_compliant_Z5_alternative_available() -> None:
    easy = tuple(timed(s, "600", "0") for s in Discipline)
    mixed = timed(Discipline.BIKE, "600", "100")
    mixed = replace(
        mixed,
        candidate=replace(
            mixed.candidate,
            source_id="TEST_ONLY:alternative_Z5",
            session=replace(
                mixed.candidate.session,
                segments=(
                    PlannedSegment(D(600), TrainingZone.ZONE_2),
                    PlannedSegment(D(100), TrainingZone.ZONE_5),
                ),
            ),
        ),
    )
    result = assess((*easy, mixed), "3")
    full = tuple(w for w in result.supported_witnesses if len(w.sports) == 3)
    assert len(full) == 2
    assert any(all(i.high_ratio == 0 for i in w.intensity) for w in full)
    assert any(mixed.candidate.source_id in w.source_ids for w in full)


@pytest.mark.parametrize("dimension", tuple(SuitabilityDimension))
def test_no_high_minimum_does_not_approve_other_suitability_gaps(
    dimension: SuitabilityDimension,
) -> None:
    row = timed(Discipline.RUN, "600", "0")
    row = replace(
        row,
        candidate=replace(
            row.candidate,
            suitability=tuple(
                e for e in row.candidate.suitability if e.dimension != dimension
            ),
        ),
    )
    assert assess((row,)).status == "UNRESOLVED_FAIL_CLOSED"


def test_swimming_rest_and_uncertain_active_time_remain_separate() -> None:
    row = timed(Discipline.SWIM, "240", "60")
    row = replace(
        row,
        candidate=replace(
            row.candidate,
            session=replace(
                row.candidate.session,
                segments=(
                    *(row.candidate.session.segments or ()),
                    PlannedSegment(D(999999), stationary_rest=True),
                ),
            ),
        ),
    )
    assert intensity_evidence(row, START).high_ratio == Fraction(1, 5)
    uncertain = replace(
        row,
        candidate=replace(
            row.candidate,
            session=replace(
                row.candidate.session,
                segments=(PlannedSegment(None, TrainingZone.ZONE_2),),
            ),
        ),
    )
    assert intensity_evidence(uncertain, START).status == "UNVERIFIED"
    assert assess((uncertain,)).status == "UNRESOLVED_FAIL_CLOSED"


def test_availability_and_unverified_plan_safeguards_fail_closed() -> None:
    rows = (timed(Discipline.RUN, "60", "0"),)
    cases: tuple[
        tuple[frozenset[date], Literal["ALLOWED", "UNVERIFIED", "BLOCKED"], str], ...
    ] = (
        (frozenset(), "ALLOWED", "NO_PLAN_REST_FAIL_CLOSED"),
        (DATES, "UNVERIFIED", "UNRESOLVED_FAIL_CLOSED"),
        (DATES, "BLOCKED", "NO_PLAN_REST_FAIL_CLOSED"),
    )
    for dates, state, expected in cases:
        guards = RestrictionEvidence(state, ("test_safeguards",), "TEST_ONLY")
        result = enumerate_weeks(
            rows,
            week_start=START,
            authorized_budget=D(45),
            available_dates=dates,
            safeguards=guards,
            maximum_combinations=1,
        )
        assert result.status == expected
        assert not result.supported_witnesses


@pytest.mark.parametrize("budget", ("45", "25.86", "15.085"))
def test_77_catalog_finite_sets_match_independent_rational_oracle(budget: str) -> None:
    records = source_records()
    rows = tuple(PolicyInput(c) for c in candidates(records))
    result = assess(rows, budget)
    oracle = {
        tuple(sorted(r.original_workout_id for r in combo))
        for size in (1, 2, 3)
        for combo in combinations(records, size)
        if len({r.sport for r in combo}) == size
        and sum((Fraction(r.load.original_displayed_value) for r in combo), Fraction())
        <= Fraction(budget)
    }
    actual = {tuple(sorted(w.source_ids)) for w in result.arithmetic_witnesses}
    assert actual == oracle
    assert result.candidate_space == result.examined == 18675
    assert not result.supported_witnesses
    assert result.status == "UNRESOLVED_FAIL_CLOSED"
    assert sum(len(w.sports) == 3 for w in result.arithmetic_witnesses) == (
        33 if budget == "45" else 0
    )
    with localcontext() as ctx:
        ctx.prec = 1
        ctx.traps[Inexact] = True
        assert assess(rows, budget) == result


def test_swim_estimate_never_fills_authoritative_or_performed_time() -> None:
    records = source_records()
    record = next(r for r in records if r.original_workout_id == "TR-SWIM-021")
    row = next(
        c for c in candidates(records) if c.source_id == record.original_workout_id
    )
    missing = fixture_support(PolicyInput(row))
    assert assess((missing,)).status == "UNRESOLVED_FAIL_CLOSED"
    estimated = replace(missing, swim_estimate=estimate_swim(record))
    result = intensity_evidence(estimated, START)
    assert result.high_ratio == 0 and result.status == "COMPLIANT"
    assert result.provenance.startswith("ESTIMATED_FROM_APPROVED_REFERENCE_PACE:")
    assert result.authoritative_duration_compliance == "UNVERIFIED"
    assert record.planned_duration_seconds is None
    assert assess((estimated,)).status == "PARTIAL_WEEK_WITNESSES"
    assert not assess((estimated,)).operational_approval


def test_bound_and_invalid_scope_are_not_infeasibility() -> None:
    row = timed(Discipline.RUN, "60", "0")
    with pytest.raises(ValueError, match="ambiguous_candidate"):
        assess((row, row))
    with pytest.raises(ValueError, match="invalid_explicit"):
        assess((row,), "-1")
    result = enumerate_weeks(
        tuple(timed(s, "60", "0") for s in Discipline),
        week_start=START,
        authorized_budget=D(45),
        available_dates=DATES,
        safeguards=ASSUMED,
        maximum_combinations=6,
    )
    assert result.status == "BOUND_EXCEEDED" and result.examined == 0
    assert not result.supported_witnesses and not result.arithmetic_witnesses


def test_application_never_imports_new_offline_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    for path in (root / "app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        assert all(
            not (node.module or "").startswith("benchmarks")
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        assert all(
            not alias.name.startswith("benchmarks")
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )


def test_simulations_and_committed_evidence_reproduce() -> None:
    generated = evidence()
    root = Path(__file__).resolve().parents[2]
    stored = json.loads(
        (root / "docs/catalog/implementation/final-policy/evidence.json").read_text()
    )
    assert generated == stored
    assert generated["catalog_rows"] == 77
    cases = generated["cases"]
    for key in (
        "recovery_25.86_two_sport_conditional_fixture",
        "taper_15.085_partial_conditional_fixture",
        "partial_missing_swim_capability",
        "partial_run_injury",
        "safe_one_sport_conditional_fixture",
    ):
        assert cases[key]["result"]["status"] == "PARTIAL_WEEK_WITNESSES"
    assert (
        cases["no_suitable_workout"]["result"]["status"] == "NO_PLAN_REST_FAIL_CLOSED"
    )
    assert cases["missing_swim_time"]["result"]["status"] == "UNRESOLVED_FAIL_CLOSED"
