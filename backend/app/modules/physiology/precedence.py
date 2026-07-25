"""Locked orchestration order for deterministic rule evaluations."""

from collections.abc import Iterable
from uuid import UUID

from app.modules.physiology.models import (
    DecisionRun,
    EvaluationState,
    RuleEvaluation,
)
from app.modules.physiology.specification import PhysiologySpecification


def order_evaluations(
    evaluations: Iterable[RuleEvaluation],
) -> tuple[RuleEvaluation, ...]:
    """Return evaluations in locked precedence order, preserving ties."""
    return tuple(sorted(evaluations, key=lambda evaluation: evaluation.stage))


def first_conflict(
    evaluations: Iterable[RuleEvaluation],
) -> RuleEvaluation | None:
    """Return the highest-precedence unsatisfied constraint, when present."""
    return next(
        (
            evaluation
            for evaluation in order_evaluations(evaluations)
            if evaluation.state is EvaluationState.CONFLICT
        ),
        None,
    )


def build_decision_run(
    *,
    run_id: UUID,
    specification: PhysiologySpecification,
    evaluations: Iterable[RuleEvaluation],
) -> DecisionRun:
    """Build an auditable run only when every evaluated rule is approved."""
    ordered = order_evaluations(evaluations)
    specification.require_approved(
        frozenset(evaluation.rule_id for evaluation in ordered)
    )
    return DecisionRun(
        run_id=run_id,
        ruleset_version=specification.version,
        evaluations=ordered,
    )
