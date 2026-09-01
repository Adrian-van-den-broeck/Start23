"""Pure state transitions for a server-authoritative swipe-week draft."""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.modules.physiology.models import Discipline

from .domain import PlanningConstraintError


class SwipeDecisionKind(str, Enum):
    """One athlete decision recorded against the exact current card."""

    ACCEPT = "accept"
    PASS = "pass"


@dataclass(frozen=True, slots=True)
class SwipeDecision:
    """Immutable, TSS-free decision history entry."""

    action: SwipeDecisionKind
    template_id: UUID


@dataclass(frozen=True, slots=True)
class SwipeSelectionState:
    """Derived accepted/passed state; history remains the source of truth."""

    history: tuple[SwipeDecision, ...] = ()

    @property
    def accepted_template_ids(self) -> tuple[UUID, ...]:
        return tuple(
            decision.template_id
            for decision in self.history
            if decision.action is SwipeDecisionKind.ACCEPT
        )

    @property
    def passed_template_ids(self) -> frozenset[UUID]:
        return frozenset(
            decision.template_id
            for decision in self.history
            if decision.action is SwipeDecisionKind.PASS
        )


def apply_swipe_decision(
    state: SwipeSelectionState,
    *,
    action: SwipeDecisionKind,
    current_template_id: UUID,
    expected_template_id: UUID,
    target_workout_count: int,
) -> SwipeSelectionState:
    """Apply one decision only to the exact server-selected current card."""

    if current_template_id != expected_template_id:
        raise PlanningConstraintError(
            "swipe_candidate_stale",
            "The visible workout card changed. Refresh the swipe draft.",
        )
    accepted = state.accepted_template_ids
    passed = state.passed_template_ids
    if current_template_id in accepted or current_template_id in passed:
        raise PlanningConstraintError(
            "swipe_candidate_decided",
            "This workout card was already decided in the current draft.",
        )
    if action is SwipeDecisionKind.ACCEPT and len(accepted) >= target_workout_count:
        raise PlanningConstraintError(
            "swipe_target_complete",
            "The fixed workout target is already complete.",
        )
    return SwipeSelectionState(
        history=state.history
        + (SwipeDecision(action=action, template_id=current_template_id),)
    )


def undo_last_swipe(state: SwipeSelectionState) -> SwipeSelectionState:
    """Remove exactly the last accept/pass decision."""

    if not state.history:
        raise PlanningConstraintError(
            "swipe_undo_empty",
            "There is no swipe decision to undo.",
        )
    return SwipeSelectionState(history=state.history[:-1])


def reset_passed_cards(state: SwipeSelectionState) -> SwipeSelectionState:
    """Make passed cards eligible again without changing accepted cards."""

    return SwipeSelectionState(
        history=tuple(
            decision
            for decision in state.history
            if decision.action is SwipeDecisionKind.ACCEPT
        )
    )


def discipline_composition(
    disciplines: tuple[Discipline, ...],
) -> dict[Discipline, int]:
    """Return a stable three-discipline count map."""

    return {
        discipline: sum(item is discipline for item in disciplines)
        for discipline in Discipline
    }


def composition_can_extend(
    *,
    accepted_disciplines: tuple[Discipline, ...],
    candidate_discipline: Discipline,
    target_composition: dict[Discipline, int],
) -> bool:
    """Reject a candidate that would exceed the fixed discipline composition."""

    current = discipline_composition(accepted_disciplines)
    return current[candidate_discipline] < target_composition[candidate_discipline]


def composition_is_complete(
    *,
    accepted_disciplines: tuple[Discipline, ...],
    target_composition: dict[Discipline, int],
) -> bool:
    """Count alone is insufficient: exact deterministic composition must match."""

    return discipline_composition(accepted_disciplines) == target_composition
