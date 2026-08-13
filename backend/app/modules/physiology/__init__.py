"""Framework-independent deterministic physiology contracts."""

from app.modules.physiology.models import (
    ConstraintStage,
    DecisionRun,
    Discipline,
    DurationMinutes,
    EvaluationState,
    Fraction,
    IntensityBucket,
    InternalLoad,
    RuleEvaluation,
    RuleId,
    RulesetVersion,
    TrainingZone,
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
    PhysiologyProductionReview,
    PhysiologyProductionReviewRequired,
    PhysiologySpecification,
    PhysiologySpecificationNotApproved,
    SpecificationStatus,
)

__all__ = [
    "PHASE_3_DRAFT_SPECIFICATION",
    "PHASE_3_RULESET_V1",
    "PHASE_3_RULESET_V2",
    "PHASE_3_RULESET_V3",
    "ConstraintStage",
    "DecisionRun",
    "Discipline",
    "DurationMinutes",
    "EvaluationState",
    "Fraction",
    "IntensityBucket",
    "InternalLoad",
    "PhysiologySpecification",
    "PhysiologySpecificationNotApproved",
    "PhysiologyProductionReview",
    "PhysiologyProductionReviewRequired",
    "RuleEvaluation",
    "RuleId",
    "RulesetVersion",
    "SpecificationStatus",
    "TrainingZone",
    "build_decision_run",
    "first_conflict",
    "order_evaluations",
]
