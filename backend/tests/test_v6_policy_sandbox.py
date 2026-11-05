"""Prospective policy evidence is independent of legacy validity and approval."""

import ast
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from pathlib import Path

import pytest

from app.modules.physiology.models import Discipline, TrainingZone
from app.modules.physiology.planned_intensity_policy import (
    PlannedSegment,
    PlannedSession,
)
from app.modules.planning.domain import PlanningConstraintError, build_weekly_plan
from benchmarks.joren_c2 import START
from benchmarks.joren_v6 import projection, scenario, source_records
from benchmarks.prospective_planning_policy import (
    SOURCE_METHOD,
    TRIATHLON,
    Candidate,
    Evaluation,
    LegacyEvidence,
    RestrictionEvidence,
    Status,
    SuitabilityDimension,
    SuitabilityEvidence,
    enumerate_one_per_sport,
    evaluate,
    exact_sum,
    rank_experiment,
)
from benchmarks.v6_policy_sandbox import candidates, independent_fits

D = Decimal
NOT_SELECTED = LegacyEvidence("NOT_RUN", "OFFLINE_UNSELECTED", "test-witness")


@pytest.fixture(scope="module")
def rows() -> tuple[Candidate, ...]:
    return candidates(source_records())


def assess(selected: tuple[Candidate, ...], budget: str = "45") -> Evaluation:
    return evaluate(
        week_start=START,
        selected=selected,
        authorized_budget=D(budget),
        required_sports=TRIATHLON,
        goal="TRIATHLON",
        legacy=NOT_SELECTED,
    )


def statuses(result: Evaluation) -> set[Status]:
    return {f.status for f in result.findings}


def choose(rows: tuple[Candidate, ...], *ids: str) -> tuple[Candidate, ...]:
    return tuple(
        next(c for c in rows if c.source_id == identifier) for identifier in ids
    )


@pytest.mark.parametrize(
    ("case", "ids", "total", "remaining", "budget_status", "origin"),
    (
        (
            "tri_zero",
            ("TR-BIKE-022", "TR-RUN-027", "TR-SWIM-021"),
            "45.1",
            "-0.1",
            Status.PROSPECTIVE_BUDGET_EXCEEDED,
            "AUTOMATIC_PLANNER",
        ),
        (
            "candidate",
            ("TR-BIKE-023", "TR-RUN-024", "TR-SWIM-021"),
            "43.1",
            "1.9",
            Status.PROSPECTIVE_BUDGET_WITHIN,
            "EXPLICIT_MANUAL",
        ),
    ),
)
def test_actual_planner_and_prospective_budget_are_separate(
    rows: tuple[Candidate, ...],
    case: str,
    ids: tuple[str, ...],
    total: str,
    remaining: str,
    budget_status: Status,
    origin: str,
) -> None:
    plan = build_weekly_plan(**scenario(case, projection(source_records())))
    assert tuple(sorted(w.snapshot.name for w in plan.workouts)) == ids
    assert plan.target.target.value == 45
    result = evaluate(
        week_start=START,
        selected=choose(rows, *ids),
        authorized_budget=plan.target.target.value,
        required_sports=TRIATHLON,
        goal="TRIATHLON",
        legacy=LegacyEvidence(
            "RETURNED_PENDING",
            "AUTOMATIC_PLANNER" if case == "tri_zero" else "EXPLICIT_MANUAL",
            case,
        ),
    )
    assert result.legacy.origin == origin
    assert result.private_total == D(total) == plan.planned_load.value
    assert result.private_budget_remaining == D(remaining)
    assert {
        Status.LEGACY_VALID,
        budget_status,
        Status.SPORT_COVERAGE_SATISFIED,
        Status.SPORT_ALLOCATION_DEVIATION,
        Status.ATHLETE_SUITABILITY_UNAPPROVED,
        Status.SOURCE_METHOD_UNAPPROVED,
        Status.INTENSITY_TIME_UNVERIFIED,
    } <= statuses(result)
    assert result.suitable_coverage == "UNRESOLVED"
    assert result.source_method == SOURCE_METHOD
    assert (
        next(i for i in result.intensity if i.sport == Discipline.SWIM).high_ratio
        is None
    )


@pytest.mark.parametrize("easy_only", (True, False))
def test_actual_77_deck_complete_independent_feasibility(
    rows: tuple[Candidate, ...],
    easy_only: bool,
) -> None:
    subset = tuple(c for c in rows if not easy_only or c.all_easy)
    deck = projection(source_records())
    result = enumerate_one_per_sport(
        subset,
        required_sports=TRIATHLON,
        budget=D(45),
        legacy_minimum=D("5.8"),
        maximum_combinations=20000,
        evidence_mode="ARITHMETIC_ONLY",
        deterministic_ids=tuple((t.name, str(t.id)) for t in deck),
    )
    assert result.status == "COMPLETE"
    assert result.combinations_examined == result.candidate_space
    assert {c.source_ids for c in result.within_budget} == independent_fits(
        source_records(),
        D(45),
        easy_only=easy_only,
    )
    if easy_only:
        assert len(result.within_budget) == 33
    if not easy_only:
        assert result.candidate_space == 27 * 28 * 22
    fit = tuple(c for c in result.within_budget if c.legacy_fit)
    allocation = rank_experiment(fit, "ALLOCATION_FIRST")[0]
    utilization = rank_experiment(fit, "UTILIZATION_FIRST")[0]
    assert allocation.source_ids != utilization.source_ids
    assert allocation.share_error < utilization.share_error
    assert allocation.private_total < utilization.private_total <= 45
    assert rank_experiment(tuple(reversed(fit)), "ALLOCATION_FIRST")[0] == allocation
    witness = next(c for c in result.within_budget if c.private_total == D("43.1"))
    assert witness.legacy_fit
    smallest = min(result.within_budget, key=lambda c: c.private_total)
    assert smallest.private_total == D("29.3") and not smallest.legacy_fit


def test_bounded_search_never_returns_a_truncated_winner(
    rows: tuple[Candidate, ...],
) -> None:
    result = enumerate_one_per_sport(
        rows,
        required_sports=TRIATHLON,
        budget=D(45),
        legacy_minimum=D("5.8"),
        maximum_combinations=100,
        evidence_mode="ARITHMETIC_ONLY",
        deterministic_ids=tuple((c.source_id, c.source_id) for c in rows),
    )
    assert result.status == "BOUND_EXCEEDED"
    assert result.combinations_examined == 0 and not result.within_budget


@pytest.mark.parametrize(
    "run_id,total", (("TR-RUN-023", "40.2"), ("TR-RUN-026", "44.8"))
)
def test_alternative_rank_winners_can_be_explicitly_submitted(
    run_id: str,
    total: str,
) -> None:
    deck = projection(source_records())
    values = scenario("candidate", deck)
    requested = {"TR-BIKE-023", run_id, "TR-SWIM-021"}
    values["selected_template_ids"] = tuple(t.id for t in deck if t.name in requested)
    plan = build_weekly_plan(**values)
    assert {w.snapshot.name for w in plan.workouts} == requested
    assert plan.planned_load.value == D(total)


@pytest.mark.parametrize("budget", ("25.86", "15.085", "0"))
def test_low_targets_have_no_one_per_sport_solution(
    rows: tuple[Candidate, ...],
    budget: str,
) -> None:
    assert not independent_fits(source_records(), D(budget), easy_only=False)
    result = enumerate_one_per_sport(
        rows,
        required_sports=TRIATHLON,
        budget=D(budget),
        legacy_minimum=D("5.8"),
        maximum_combinations=20000,
        evidence_mode="ARITHMETIC_ONLY",
        deterministic_ids=tuple((c.source_id, c.source_id) for c in rows),
    )
    assert result.status == "COMPLETE" and not result.within_budget


def test_share_denominators_include_underfill_and_zero(
    rows: tuple[Candidate, ...],
) -> None:
    result = assess(choose(rows, "TR-BIKE-023", "TR-RUN-024", "TR-SWIM-021"))
    by_sport = {a.sport: a for a in result.allocation}
    bike = by_sport[Discipline.BIKE]
    assert bike.share == Fraction(202, 431)
    assert bike.share_deviation == Fraction(202, 431) - Fraction(1, 2)
    assert bike.budget_target == Fraction(45, 2)
    assert bike.budget_deviation == Fraction(-23, 10)
    assert sum((a.share_deviation or 0 for a in result.allocation), Fraction(0)) == 0
    assert sum(a.budget_deviation for a in result.allocation) == Fraction(-19, 10)
    empty = assess(())
    assert Status.SPORT_ALLOCATION_UNDEFINED in statuses(empty)
    assert all(a.share is None for a in empty.allocation)
    assert empty.suitable_coverage == "MISSING"


@pytest.mark.parametrize(
    "identifier,ratio,status",
    (
        ("TR-BIKE-020", Fraction(180, 5580), "ACCEPTED"),
        ("TR-BIKE-021", Fraction(240, 6240), "ACCEPTED"),
        ("TR-RUN-017", Fraction(1, 2), "REJECTED"),
        ("TR-BIKE-023", Fraction(0), "ACCEPTED"),
        ("TR-SWIM-021", None, "UNVERIFIED"),
    ),
)
def test_actual_ordered_interval_evidence(
    rows: tuple[Candidate, ...],
    identifier: str,
    ratio: Fraction | None,
    status: str,
) -> None:
    candidate = choose(rows, identifier)[0]
    result = assess((candidate,), "600")
    compliance = next(i for i in result.intensity if i.sport == candidate.sport)
    assert compliance.high_ratio == ratio and compliance.status == status
    assert compliance.policy_version == "joren-planned-active-time-maximum-1"


@pytest.mark.parametrize(
    "high,expected", ((0, "ACCEPTED"), (20, "ACCEPTED"), (21, "REJECTED"))
)
def test_synthetic_exact_time_boundary_and_swim_rest(
    rows: tuple[Candidate, ...],
    high: int,
    expected: str,
) -> None:
    swim = choose(rows, "TR-SWIM-021")[0]
    synthetic = replace(
        swim,
        source_id="SYNTHETIC-TIME-EVIDENCE",
        session=PlannedSession(
            Discipline.SWIM,
            START,
            (
                PlannedSegment(D(100 - high), TrainingZone(2)),
                PlannedSegment(D(900), stationary_rest=True),
                PlannedSegment(D(high), TrainingZone(3)),
            ),
        ),
    )
    compliance = next(
        i for i in assess((synthetic,)).intensity if i.sport == Discipline.SWIM
    )
    assert compliance.status == expected and compliance.high_ratio == Fraction(
        high, 100
    )


def test_time_is_separate_per_sport_and_week(rows: tuple[Candidate, ...]) -> None:
    run, bike = choose(rows, "TR-RUN-017", "TR-BIKE-013")
    # Seven hours of easy cycling cannot dilute a run's 50% high time.
    result = assess((run, bike), "1000")
    assert (
        next(i for i in result.intensity if i.sport == Discipline.RUN).status
        == "REJECTED"
    )
    with pytest.raises(ValueError, match="outside_training_week"):
        assess(
            (
                replace(
                    run,
                    session=replace(run.session, local_date=START + timedelta(days=7)),
                ),
            )
        )


def supported_synthetic(candidate: Candidate) -> Candidate:
    """Test-only invented identities/evidence, never eligibility for a real row."""
    return replace(
        candidate,
        source_id="SYNTHETIC-" + candidate.sport.value,
        suitability=tuple(
            SuitabilityEvidence(
                d,
                "SUPPORTED",
                "synthetic-athlete/template/week/phase/occurrences",
                "synthetic-rule-1",
                "test-only-not-scientific-approval",
            )
            for d in SuitabilityDimension
        ),
        restrictions=RestrictionEvidence(
            "ALLOWED", ("synthetic-fixture",), "test-only"
        ),
    )


def test_missing_suitability_is_not_infeasibility_or_sensor_readiness(
    rows: tuple[Candidate, ...],
) -> None:
    bike = choose(rows, "TR-BIKE-013")[0]
    assert bike.session.segments is not None
    assert sum(s.seconds or 0 for s in bike.session.segments) == 7 * 3600
    sensor_only = replace(
        bike,
        suitability=(
            SuitabilityEvidence(
                SuitabilityDimension.CONFIRMED_CAPABILITIES,
                "SUPPORTED",
                "synthetic-sensor-only",
                "test-rule",
                "test-only",
            ),
        ),
    )
    assert sensor_only.suitability_state == "UNRESOLVED"
    assert Status.ATHLETE_SUITABILITY_UNAPPROVED in statuses(
        assess((sensor_only,), "1000")
    )
    result = enumerate_one_per_sport(
        rows,
        required_sports=TRIATHLON,
        budget=D(45),
        legacy_minimum=D("5.8"),
        maximum_combinations=20000,
        evidence_mode="SUPPORTED_SUITABILITY",
        deterministic_ids=tuple((c.source_id, c.source_id) for c in rows),
    )
    assert result.status == "COMPLETE" and result.candidate_space == 0
    assert result.suitability_evidence_state == "UNRESOLVED"
    assert (
        not result.within_budget
    )  # No supported evidence, not proof of physical inability.


def test_synthetic_suitable_coverage_respects_injury_and_no_redistribution(
    rows: tuple[Candidate, ...],
) -> None:
    synthetic = tuple(
        supported_synthetic(c)
        for c in choose(
            rows,
            "TR-BIKE-023",
            "TR-RUN-024",
            "TR-SWIM-021",
        )
    )
    assert assess(synthetic).suitable_coverage == "SUPPORTED"
    restricted = tuple(
        replace(
            c,
            restrictions=RestrictionEvidence(
                "BLOCKED",
                ("synthetic_confirmed_run_injury",),
                "test-only",
            ),
        )
        if c.sport == Discipline.RUN
        else c
        for c in synthetic
    )
    result = enumerate_one_per_sport(
        restricted,
        required_sports=TRIATHLON,
        budget=D(45),
        legacy_minimum=D("5.8"),
        maximum_combinations=20,
        evidence_mode="SUPPORTED_SUITABILITY",
        deterministic_ids=tuple((c.source_id, c.source_id) for c in restricted),
    )
    assert not result.within_budget
    diagnostic = assess(restricted)
    assert Status.RESTRICTIONS_BLOCKED in statuses(diagnostic)
    assert diagnostic.private_total == D("43.1")
    assert diagnostic.suitable_coverage == "MISSING"


@pytest.mark.parametrize(
    "case,code",
    (
        ("injury_run", "restricted_zero_base_allocation_unavailable"),
        ("missing_swim_capability", "catalog_coverage_unsatisfied"),
        ("candidate_no_dates", "availability_required"),
        ("beginner_recovery", "swipe_selection_invalid"),
        ("beginner_taper", "swipe_selection_invalid"),
    ),
)
def test_actual_restrictions_and_reduced_targets_stay_fail_closed(
    case: str, code: str
) -> None:
    with pytest.raises(PlanningConstraintError) as caught:
        build_weekly_plan(**scenario(case, projection(source_records())))
    assert caught.value.code == code


@pytest.mark.parametrize("sport", tuple(Discipline))
def test_single_sport_has_no_triathlon_objective(
    rows: tuple[Candidate, ...], sport: Discipline
) -> None:
    candidate = next(c for c in rows if c.sport == sport)
    result = evaluate(
        week_start=START,
        selected=(candidate,),
        authorized_budget=D(1000),
        required_sports=frozenset({sport}),
        goal="OTHER",
        legacy=NOT_SELECTED,
    )
    assert not result.allocation
    assert Status.SPORT_ALLOCATION_NOT_APPLICABLE in statuses(result)


def test_decimal_context_cannot_change_budget_or_fraction_diagnostics(
    rows: tuple[Candidate, ...],
) -> None:
    selected = choose(rows, "TR-BIKE-022", "TR-RUN-027", "TR-SWIM-021")
    expected = assess(selected)
    with localcontext() as context:
        context.prec = 1
        context.traps[Inexact] = True
        context.clear_flags()
        assert assess(selected) == expected
        assert exact_sum((D("123456789.123"), D("-123456789"), D("0.001"))) == D(".124")
        assert not any(context.flags.values())
    assert "45.1" not in repr(expected)
    assert "21.6" not in repr(selected[1])


@pytest.mark.parametrize("budget", ("NaN", "Infinity", "-1"))
def test_invalid_budget_is_rejected(rows: tuple[Candidate, ...], budget: str) -> None:
    with pytest.raises(ValueError, match="invalid_authorized_budget"):
        assess(rows[:1], budget)


def test_no_active_import_or_io_dependency() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    module = app_root.parent / "benchmarks/prospective_planning_policy.py"
    tree = ast.parse(module.read_text())
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imports <= {
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "fractions",
        "itertools",
        "math",
        "typing",
        "app.modules.physiology.models",
        "app.modules.physiology.planned_intensity_policy",
    }
    for path in app_root.rglob("*.py"):
        if path == module:
            continue
        assert "prospective_planning_policy" not in path.read_text(encoding="utf-8")
