"""Fail-closed approval boundary for physiological rule specifications."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.modules.physiology.models import RuleId, RulesetVersion


class SpecificationStatus(str, Enum):
    """Lifecycle state of a physiological specification."""

    DRAFT = "draft"
    APPROVED = "approved"


class PhysiologySpecificationNotApproved(RuntimeError):
    """Raised when code attempts to use an unapproved physiological rule."""


class PhysiologyProductionReviewRequired(RuntimeError):
    """Raised when a ruleset lacks the required qualified production review."""


@dataclass(frozen=True, slots=True)
class PhysiologyProductionReview:
    """Named, dated approval from the accountable qualified reviewer."""

    accountable_reviewer: str
    qualification: str
    responsible_owner: str
    approved_on: date
    review_due_on: date

    def __post_init__(self) -> None:
        if not self.accountable_reviewer.strip() or not self.qualification.strip():
            raise ValueError("A named qualified accountable reviewer is required.")
        if not self.responsible_owner.strip():
            raise ValueError("A responsible ruleset owner is required.")
        if self.review_due_on <= self.approved_on:
            raise ValueError("The physiology review date must follow approval.")


@dataclass(frozen=True, slots=True)
class PhysiologySpecification:
    """Versioned allow-list for rules approved for deterministic evaluation."""

    version: RulesetVersion
    status: SpecificationStatus
    approved_rules: frozenset[RuleId]
    evidence_references: tuple[str, ...] = ()
    applicability: str = ""
    contraindications: tuple[str, ...] = ()
    test_references: tuple[str, ...] = ()
    production_review: PhysiologyProductionReview | None = None

    def require_approved(self, rule_ids: frozenset[RuleId]) -> None:
        """Reject evaluation unless the specification explicitly approves every rule."""
        missing_rules = rule_ids - self.approved_rules
        if self.status is not SpecificationStatus.APPROVED or missing_rules:
            missing = ", ".join(sorted(rule.value for rule in missing_rules))
            suffix = f" Missing rules: {missing}." if missing else ""
            raise PhysiologySpecificationNotApproved(
                f"Physiology specification {self.version.value!r} is not approved."
                f"{suffix}"
            )

    def require_production_review(self, *, as_of: date) -> None:
        """Fail closed until the review board records a current named approval."""
        review = self.production_review
        if (
            review is None
            or not self.evidence_references
            or not self.applicability.strip()
            or not self.test_references
            or as_of > review.review_due_on
        ):
            raise PhysiologyProductionReviewRequired(
                f"Physiology specification {self.version.value!r} is not ready "
                "for production."
            )


PHASE_3_DRAFT_SPECIFICATION = PhysiologySpecification(
    version=RulesetVersion("phase-3-draft-2026-07-24"),
    status=SpecificationStatus.DRAFT,
    approved_rules=frozenset(),
)

PHASE_3_RULESET_V1 = PhysiologySpecification(
    version=RulesetVersion("phase-3-ruleset-1"),
    status=SpecificationStatus.APPROVED,
    approved_rules=frozenset(
        {
            RuleId.SOFT_BOUNDARIES,
            RuleId.TIME_INTENSITY,
            RuleId.PROGRESSIVE_LOAD,
            RuleId.ANTI_STACK,
            RuleId.RECOVERY_CYCLE,
            RuleId.TAPER,
            RuleId.INJURY_REDISTRIBUTION,
        }
    ),
)

PHASE_3_RULESET_V2 = PhysiologySpecification(
    version=RulesetVersion("phase-3-ruleset-2"),
    status=SpecificationStatus.APPROVED,
    approved_rules=PHASE_3_RULESET_V1.approved_rules
    | frozenset({RuleId.DISCIPLINE_ZONES}),
)

PHASE_3_RULESET_V3 = PhysiologySpecification(
    version=RulesetVersion("phase-3-ruleset-3"),
    status=SpecificationStatus.APPROVED,
    approved_rules=PHASE_3_RULESET_V2.approved_rules,
    evidence_references=(
        "docs/requirements/physiology-formula-specification.md",
        "docs/requirements/phase-0-7-decision-register.md",
    ),
    applicability="Local MVP development for race-oriented adult triathletes.",
    contraindications=(
        "No diagnosis or medical clearance.",
        "No automatic injury-load redistribution.",
    ),
    test_references=(
        "backend/tests/physiology",
        "backend/tests/test_planning_domain.py",
    ),
    # A named qualified reviewer must be appointed before production activation.
    production_review=None,
)
