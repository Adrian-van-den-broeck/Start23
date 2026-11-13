"""Approved frequency resolver. No load/history-to-capability inference."""

import json
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.modules.physiology.models import Discipline

from .domain import PlanningConstraintError
from .v6_frequency import MAX_OCCURRENCES, SessionFrequency

POLICY = "joren-v6-real-athlete-frequency-policy-1"
EVIDENCE_REFERENCES = (
    "history_source_reference",
    "history_completeness_reference",
    "current_context_reference",
    "capability_reference",
    "phase_reference",
    "rationale_reference",
    "review_record_reference",
)


def resolve_frequency(
    context: Mapping[str, Any],
    *,
    athlete_id: UUID,
    week_start: date,
    timezone_name: str,
    now: datetime,
) -> tuple[SessionFrequency, ...]:
    """Resolve trusted persisted facts; preserve the original P in the envelope.

    Invalid lifecycle/evidence cannot expand the legacy envelope. A malformed
    read is an error, not absence. TEST_ONLY belongs to the separate local seam.
    """
    if (
        context["policy_version"] != POLICY
        or UUID(context["athlete_id"]) != athlete_id
        or date.fromisoformat(context["week_start"]) != week_start
        or context["timezone"] != timezone_name
        or now.tzinfo is None
    ):
        raise ValueError("invalid_frequency_scope")
    preference = context["preference"]
    values = preference["preferences"]
    reconfirm = preference["reconfirmation_required"]
    decisions = {Discipline(d["sport"]): d for d in context["decisions"]}
    if len(decisions) != len(context["decisions"]):
        raise ValueError("duplicate_frequency_decision")
    result = []
    for sport in Discipline:
        requested = values[sport.value]
        if requested is not None and (
            type(requested) is not int or not 0 <= requested <= MAX_OCCURRENCES
        ):
            raise ValueError("invalid_frequency_preference")
        retained = context["retained_counts"].get(sport.value, 0)
        if type(retained) is not int or not 0 <= retained <= MAX_OCCURRENCES:
            raise ValueError("invalid_retained_frequency")
        decision = decisions.get(sport)
        valid = False
        if decision is not None:
            # A TEST_ONLY label is not silently converted into absent authority.
            if "TEST_ONLY" in json.dumps(decision).upper():
                raise ValueError("test_only_frequency_authority")
            evidence = decision["evidence"]
            valid = (
                decision["status"] == "authorized"
                and decision["reviewer_authorized"] is True
                and decision["policy_version"] == POLICY
                and decision["athlete_id"] == str(athlete_id)
                and decision["week_start"] == week_start.isoformat()
                and decision["timezone"] == timezone_name
                and decision["evidence_context"] == context["basis"]
                and bool(decision["reviewer_reference"].strip())
                and bool(decision["operator_reference"].strip())
                and sport.value not in reconfirm
                and datetime.fromisoformat(
                    decision["expires_at"].replace("Z", "+00:00")
                )
                > now
                and datetime.fromisoformat(
                    decision["reviewed_at"].replace("Z", "+00:00")
                )
                <= datetime.fromisoformat(decision["decided_at"].replace("Z", "+00:00"))
                <= now
                and all(str(evidence.get(k, "")).strip() for k in EVIDENCE_REFERENCES)
                and bool(evidence.get("period_from"))
                and bool(evidence.get("period_to"))
                and date.fromisoformat(evidence["period_from"])
                <= date.fromisoformat(evidence["period_to"])
            )
        if valid:
            assert decision is not None
            maximum = decision["maximum"]
            if retained > maximum:
                raise PlanningConstraintError(
                    "v6_frequency_retained_conflict",
                    "Existing sessions require review under the current "
                    "weekly conditions.",
                )
            reference = f"{POLICY}:{decision['id']}:{decision['revision']}"
            target = min(requested, maximum) if requested is not None else None
        else:
            # This is a generation envelope, never a retroactive cap of one.
            maximum = max(1, retained)
            target = min(requested, 1) if requested is not None else None
            if requested == 0 or context["unmatched_activities"]:
                maximum = retained
                target = 0
            reference = f"{POLICY}:default:{preference['revision']}"
        if context["unmatched_activities"]:
            # No new occurrence can hide unmatched evidence from the whole week.
            maximum = min(maximum, retained)
            target = min(target or 0, maximum)
        if valid or requested is not None or context["unmatched_activities"]:
            result.append(SessionFrequency(sport, maximum, reference, target))
    return tuple(result)
