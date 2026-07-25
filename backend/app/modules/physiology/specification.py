"""Fail-closed approval boundary for physiological rule specifications."""

from dataclasses import dataclass
from enum import Enum

from app.modules.physiology.models import RuleId, RulesetVersion


class SpecificationStatus(str, Enum):
    """Lifecycle state of a physiological specification."""

    DRAFT = "draft"
    APPROVED = "approved"


class PhysiologySpecificationNotApproved(RuntimeError):
    """Raised when code attempts to use an unapproved physiological rule."""


@dataclass(frozen=True, slots=True)
class PhysiologySpecification:
    """Versioned allow-list for rules approved for deterministic evaluation."""

    version: RulesetVersion
    status: SpecificationStatus
    approved_rules: frozenset[RuleId]

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
