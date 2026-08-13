"""Tests for the locked Phase 0 rule precedence."""

from datetime import date
from uuid import UUID

import pytest

from app.modules.physiology.models import (
    ConstraintStage,
    EvaluationState,
    RuleEvaluation,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.precedence import (
    build_decision_run,
    first_conflict,
    order_evaluations,
)
from app.modules.physiology.specification import (
    PHASE_3_DRAFT_SPECIFICATION,
    PHASE_3_RULESET_V1,
    PHASE_3_RULESET_V2,
    PHASE_3_RULESET_V3,
    PhysiologyProductionReviewRequired,
    PhysiologySpecification,
    PhysiologySpecificationNotApproved,
    SpecificationStatus,
)


def _evaluation(
    rule_id: RuleId,
    stage: ConstraintStage,
    *,
    state: EvaluationState = EvaluationState.SATISFIED,
) -> RuleEvaluation:
    return RuleEvaluation(
        rule_id=rule_id,
        stage=stage,
        state=state,
        code=f"{rule_id.name.lower()}_{state.value}",
    )


def test_locked_precedence_orders_higher_constraints_first() -> None:
    """Lower-priority rules cannot run ahead of injury, taper, or recovery."""
    evaluations = (
        _evaluation(RuleId.PROGRESSIVE_LOAD, ConstraintStage.PROGRESSIVE_LOAD),
        _evaluation(
            RuleId.INJURY_REDISTRIBUTION,
            ConstraintStage.IDENTITY_OWNERSHIP_VALIDITY_INJURY,
        ),
        _evaluation(RuleId.RECOVERY_CYCLE, ConstraintStage.RECOVERY_WEEK),
        _evaluation(RuleId.TAPER, ConstraintStage.RACE_TAPER),
        _evaluation(RuleId.SOFT_BOUNDARIES, ConstraintStage.PHYSIOLOGICAL_DEBT),
        _evaluation(RuleId.ANTI_STACK, ConstraintStage.INTENSITY_AND_PLACEMENT),
    )

    assert [item.rule_id for item in order_evaluations(evaluations)] == [
        RuleId.INJURY_REDISTRIBUTION,
        RuleId.TAPER,
        RuleId.RECOVERY_CYCLE,
        RuleId.SOFT_BOUNDARIES,
        RuleId.PROGRESSIVE_LOAD,
        RuleId.ANTI_STACK,
    ]


def test_first_conflict_uses_locked_precedence() -> None:
    """The highest-priority conflict is reported regardless of input order."""
    taper_conflict = _evaluation(
        RuleId.TAPER,
        ConstraintStage.RACE_TAPER,
        state=EvaluationState.CONFLICT,
    )
    load_conflict = _evaluation(
        RuleId.PROGRESSIVE_LOAD,
        ConstraintStage.PROGRESSIVE_LOAD,
        state=EvaluationState.CONFLICT,
    )

    assert first_conflict((load_conflict, taper_conflict)) == taper_conflict


def test_draft_specification_fails_closed() -> None:
    """No physiological rule can activate from the unapproved draft."""
    with pytest.raises(PhysiologySpecificationNotApproved):
        build_decision_run(
            run_id=UUID("10000000-0000-0000-0000-000000000001"),
            specification=PHASE_3_DRAFT_SPECIFICATION,
            evaluations=(
                _evaluation(
                    RuleId.PROGRESSIVE_LOAD,
                    ConstraintStage.PROGRESSIVE_LOAD,
                ),
            ),
        )


def test_decision_run_records_approved_ruleset_version() -> None:
    """Approved synthetic evaluations retain an auditable ruleset version."""
    specification = PhysiologySpecification(
        version=RulesetVersion("test-ruleset-1"),
        status=SpecificationStatus.APPROVED,
        approved_rules=frozenset({RuleId.TAPER, RuleId.RECOVERY_CYCLE}),
    )

    result = build_decision_run(
        run_id=UUID("10000000-0000-0000-0000-000000000001"),
        specification=specification,
        evaluations=(
            _evaluation(RuleId.RECOVERY_CYCLE, ConstraintStage.RECOVERY_WEEK),
            _evaluation(RuleId.TAPER, ConstraintStage.RACE_TAPER),
        ),
    )

    assert result.ruleset_version == RulesetVersion("test-ruleset-1")
    assert [item.rule_id for item in result.evaluations] == [
        RuleId.TAPER,
        RuleId.RECOVERY_CYCLE,
    ]


def test_ruleset_three_fails_closed_for_production_until_board_approval() -> None:
    with pytest.raises(PhysiologyProductionReviewRequired):
        PHASE_3_RULESET_V3.require_production_review(as_of=date(2026, 8, 11))


def test_phase_3_ruleset_v1_remains_immutable_and_excludes_zones() -> None:
    assert PHASE_3_RULESET_V1.approved_rules == frozenset(
        {
            RuleId.SOFT_BOUNDARIES,
            RuleId.TIME_INTENSITY,
            RuleId.PROGRESSIVE_LOAD,
            RuleId.ANTI_STACK,
            RuleId.RECOVERY_CYCLE,
            RuleId.TAPER,
            RuleId.INJURY_REDISTRIBUTION,
        }
    )
    assert RuleId.DISCIPLINE_ZONES not in PHASE_3_RULESET_V1.approved_rules


def test_phase_3_ruleset_v2_adds_approved_zone_policy() -> None:
    assert PHASE_3_RULESET_V2.version == RulesetVersion("phase-3-ruleset-2")
    assert PHASE_3_RULESET_V2.approved_rules == (
        PHASE_3_RULESET_V1.approved_rules | {RuleId.DISCIPLINE_ZONES}
    )
