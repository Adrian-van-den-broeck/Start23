"""Pure Phase 10.1 swipe-state boundary tests."""

from uuid import uuid4

from app.modules.planning.swipe import (
    SwipeDecisionKind,
    SwipeSelectionState,
    apply_swipe_decision,
    reset_passed_cards,
    undo_last_swipe,
)


def test_ten_passes_then_three_accepts_keep_the_fixed_target() -> None:
    cards = tuple(uuid4() for _ in range(13))
    state = SwipeSelectionState()

    for card in cards[:10]:
        state = apply_swipe_decision(
            state,
            action=SwipeDecisionKind.PASS,
            current_template_id=card,
            expected_template_id=card,
            target_workout_count=3,
        )
    for card in cards[10:]:
        state = apply_swipe_decision(
            state,
            action=SwipeDecisionKind.ACCEPT,
            current_template_id=card,
            expected_template_id=card,
            target_workout_count=3,
        )

    assert state.accepted_template_ids == cards[10:]
    assert state.passed_template_ids == cards[:10]
    assert len(state.accepted_template_ids) == 3


def test_undo_and_reset_passed_are_exact_and_do_not_drop_accepts() -> None:
    first, second, third = uuid4(), uuid4(), uuid4()
    state = SwipeSelectionState()
    for action, card in (
        (SwipeDecisionKind.PASS, first),
        (SwipeDecisionKind.ACCEPT, second),
        (SwipeDecisionKind.PASS, third),
    ):
        state = apply_swipe_decision(
            state,
            action=action,
            current_template_id=card,
            expected_template_id=card,
            target_workout_count=3,
        )

    undone = undo_last_swipe(state)
    assert undone.passed_template_ids == (first,)
    reset = reset_passed_cards(undone)
    assert reset.passed_template_ids == ()
    assert reset.accepted_template_ids == (second,)


def test_same_template_has_distinct_accepted_and_passed_occurrences() -> None:
    template, first, second, third = uuid4(), uuid4(), uuid4(), uuid4()
    state = SwipeSelectionState()
    for action, occurrence in (
        (SwipeDecisionKind.ACCEPT, first),
        (SwipeDecisionKind.PASS, second),
        (SwipeDecisionKind.ACCEPT, third),
    ):
        state = apply_swipe_decision(
            state,
            action=action,
            current_template_id=template,
            expected_template_id=template,
            current_occurrence_id=occurrence,
            expected_occurrence_id=occurrence,
            target_workout_count=2,
        )
    assert state.accepted_template_ids == (template, template)
    assert state.accepted_occurrence_ids == (first, third)
    assert state.passed_occurrence_ids == (second,)
    assert undo_last_swipe(state).accepted_occurrence_ids == (first,)
