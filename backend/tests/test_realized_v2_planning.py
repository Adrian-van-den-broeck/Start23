"""D11 prospective completeness at planning service and domain boundaries."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest

from app.modules.physiology.models import DurationMinutes, InternalLoad
from app.modules.physiology.weekly_registration import (
    WorkoutRegistration,
    aggregate_week,
)
from app.modules.planning.domain import (
    PlanLoadSample,
    PlanningTargetBasis,
    _desired_high_fraction,
    resolve_target,
)
from app.modules.planning.service import PlanningDomainError, PlanningService


def evidence(*, skipped: bool) -> dict[str, Any]:
    return {
        "policy": "weekly-registration-2",
        "expected_known": True,
        "expected_occurrences": ["one", "two", "three"],
        "registrations": [
            {
                "activity_id": "a",
                "occurrence_id": "one",
                "status": "measured",
                "value": "60",
                "method": "observed_zone_minutes",
                "version": "phase-13-joren-ruleset-1",
                "eligible": True,
                "calculation_id": "a:1",
            },
            {
                "activity_id": "b",
                "occurrence_id": "two",
                "status": "estimated",
                "value": "50",
                "method": "duration_adjusted_session_rpe",
                "version": "joren-realized-tss-matrix-2",
                "eligible": True,
                "calculation_id": "b:2",
            },
            *(
                [
                    {
                        "activity_id": None,
                        "occurrence_id": "three",
                        "status": "skipped",
                        "value": None,
                        "method": "explicit_skipped",
                        "version": "weekly-registration-2",
                        "eligible": True,
                        "calculation_id": "s:1",
                    }
                ]
                if skipped
                else []
            ),
        ],
    }


def sample(*, skipped: bool, week: date = date(2026, 10, 19)) -> PlanLoadSample:
    return PlanningService._load_samples(
        (
            {
                "week_start": week.isoformat(),
                "phase": "build",
                "planned_tss": "100",
                "realized_tss": "110",
                "has_prior_approved_plan": True,
                "weekly_registration": evidence(skipped=skipped),
            },
        )
    )[0]


def target(
    samples: tuple[PlanLoadSample, ...],
    *,
    week: date = date(2026, 10, 26),
    race: date = date(2026, 12, 27),
) -> Any:
    return resolve_target(
        week_start=week,
        race_date=race,
        prior_loads=samples,
        initial_catalog_load=InternalLoad(Decimal(45)),
    )


def test_known_subtotal_is_never_passed_as_realized_week_to_progression() -> None:
    incomplete = sample(skipped=False)
    assert incomplete.weekly_registration is not None
    assert incomplete.weekly_registration.known_subtotal == 110
    assert incomplete.realized_load is None
    held = target((incomplete,))
    assert (
        held.target.value == 100
        and held.basis is PlanningTargetBasis.PRIOR_PLANNED_HOLD
    )
    complete = sample(skipped=True)
    assert complete.realized_load is not None and complete.realized_load.value == 110
    progressed = target((complete,))
    assert progressed.target.value == 110
    assert progressed.basis is PlanningTargetBasis.REALIZED_PROGRESSION


def test_incomplete_subtotal_does_not_enter_volume_debt_or_fatigue_progression() -> (
    None
):
    incomplete = replace(
        sample(skipped=False),
        realized_load=InternalLoad(Decimal(200)),
        reduced_realized_progression=True,
    )
    held = target((incomplete,))
    assert (
        held.basis is PlanningTargetBasis.PRIOR_PLANNED_HOLD
        and held.target.value == 100
    )


def test_recovery_taper_and_sickness_precede_registration_hold() -> None:
    incomplete = sample(skipped=False)
    recovery = target((incomplete,), race=date(2026, 12, 6))
    assert recovery.basis is PlanningTargetBasis.RECOVERY_FACTOR
    assert recovery.target.value == 60
    taper = target((incomplete,), race=date(2026, 11, 2))
    assert taper.basis is PlanningTargetBasis.TAPER_FACTOR
    assert taper.target.value == 35
    previous = replace(sample(skipped=True), week_start=date(2026, 10, 12))
    sick = replace(incomplete, sick_week=True)
    assert target((previous, sick)).target.value == 110


def test_incomplete_evidence_cannot_manufacture_intensity_debt() -> None:
    incomplete = replace(
        sample(skipped=False),
        planned_high_minutes=DurationMinutes(Decimal(20)),
        planned_total_minutes=DurationMinutes(Decimal(100)),
        realized_high_minutes=DurationMinutes(Decimal(80)),
        realized_classified_minutes=DurationMinutes(Decimal(100)),
        realized_total_minutes=DurationMinutes(Decimal(100)),
    )
    assert _desired_high_fraction(
        target=target((incomplete,)), prior_loads=(incomplete,)
    ).value == Decimal("0.20")


def test_three_consecutive_weeks_do_not_zero_fill_missing_registration() -> None:
    weeks = []
    for offset, complete in enumerate((True, False, True)):
        current = sample(
            skipped=complete, week=date(2026, 10, 12) + timedelta(weeks=offset)
        )
        weeks.append(current)
        result = target(tuple(weeks), week=current.week_start + timedelta(weeks=1))
        if complete:
            assert result.target.value == 110
        else:
            assert result.target.value == 100


def test_unknown_aggregate_policy_or_method_fails_closed() -> None:
    row = {
        "week_start": "2026-10-19",
        "phase": "build",
        "planned_tss": "100",
        "weekly_registration": {**evidence(skipped=True), "policy": "unknown"},
    }
    with pytest.raises(PlanningDomainError):
        PlanningService._load_samples((row,))
    with pytest.raises(ValueError):
        aggregate_week(
            expected_occurrences=("one",),
            expected_known=True,
            registrations=(
                WorkoutRegistration(
                    "a",
                    "one",
                    "estimated",
                    Decimal(20),
                    "power_tss",
                    "unreviewed",
                    True,
                ),
            ),
        )


def test_ineligible_old_subtotal_is_excluded_from_reference_baseline() -> None:
    older = replace(
        sample(skipped=False, week=date(2026, 10, 12)),
        realized_load=InternalLoad(Decimal(999)),
    )
    quality = aggregate_week(
        expected_occurrences=("one",),
        expected_known=True,
        registrations=(
            WorkoutRegistration(
                "a",
                "one",
                "estimated",
                Decimal(70),
                "duration_adjusted_session_rpe",
                "joren-realized-tss-matrix-2",
                True,
            ),
        ),
    )
    latest = replace(
        sample(skipped=True),
        realized_load=InternalLoad(Decimal(70)),
        weekly_registration=quality,
    )
    result = target((older, latest))
    assert result.basis is PlanningTargetBasis.REALIZED_BASELINE
    assert result.target.value == 70


def test_new_consumer_does_not_round_a_subthreshold_completion_up_to_80_percent() -> (
    None
):
    from decimal import localcontext

    raw = Decimal("79." + "9" * 40)
    quality = aggregate_week(
        expected_occurrences=("one",),
        expected_known=True,
        registrations=(
            WorkoutRegistration(
                "a",
                "one",
                "estimated",
                raw,
                "duration_adjusted_session_rpe",
                "joren-realized-tss-matrix-2",
                True,
            ),
        ),
    )
    latest = replace(
        sample(skipped=True),
        realized_load=InternalLoad(raw),
        weekly_registration=quality,
    )
    with localcontext() as context:
        context.prec = 8
        result = target((latest,))
    assert result.basis is PlanningTargetBasis.REALIZED_BASELINE
    assert result.target.value == raw


def single_estimated(value: Decimal) -> PlanLoadSample:
    quality = aggregate_week(
        expected_occurrences=("one",),
        expected_known=True,
        registrations=(
            WorkoutRegistration(
                "a",
                "one",
                "estimated",
                value,
                "duration_adjusted_session_rpe",
                "joren-realized-tss-matrix-2",
                True,
            ),
        ),
    )
    return replace(
        sample(skipped=True),
        realized_load=InternalLoad(value),
        weekly_registration=quality,
    )


def test_complete_estimated_week_retains_existing_lower_realized_fatigue_rule() -> None:
    latest = replace(single_estimated(Decimal(60)), reduced_realized_progression=True)
    result = target((latest,))
    assert result.basis is PlanningTargetBasis.REALIZED_PROGRESSION
    assert result.target.value == 66


def test_raw_estimated_week_above_110_percent_retains_strict_debt_boundary() -> None:
    raw = Decimal("110." + "0" * 39 + "1")
    result = target((single_estimated(raw),))
    assert result.basis is PlanningTargetBasis.PHYSIOLOGICAL_DEBT
    assert result.target.value < 100
    assert (
        target((single_estimated(Decimal(110)),)).basis
        is PlanningTargetBasis.REALIZED_PROGRESSION
    )


def test_confirmed_injury_restrictions_precede_even_incomplete_week_evidence() -> None:
    from app.modules.physiology.models import Discipline
    from app.modules.planning.domain import build_weekly_plan
    from benchmarks.planning import full_catalog, scenario

    inputs = scenario("run_history", full_catalog())
    inputs["prior_loads"] = (sample(skipped=False),)
    inputs["confirmed_injuries"] = frozenset({Discipline.RUN})
    result = build_weekly_plan(**inputs)
    assert result.target.basis is PlanningTargetBasis.INJURY_REST_ONLY
    assert result.workouts == () and result.target.target.value == 0


def test_private_evidence_repr_and_validation_do_not_echo_numeric_values() -> None:
    from pydantic import ValidationError

    from app.modules.planning.registration import (
        RegistrationEvidence,
        parse_weekly_registration,
    )

    data = evidence(skipped=True)
    data["registrations"][0]["value"] = "987.654321"
    parsed = RegistrationEvidence.model_validate(data["registrations"][0])
    assert "987.654321" not in repr(parsed)
    data["registrations"][0]["value"] = 987.654321
    with pytest.raises(ValidationError) as caught:
        parse_weekly_registration(data)
    assert "987.654321" not in str(caught.value)
