"""BR-010 injury redistribution fixtures."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.modules.physiology.injury import (
    MVP_AUTOMATIC_INJURY_REDISTRIBUTION,
    AllowedIntensity,
    DisciplineRestriction,
    apply_mvp_injury_policy,
    redistribute_confirmed_injury_load,
    redistribute_injury_load,
)
from app.modules.physiology.models import Discipline, InternalLoad


def _load(value: str) -> InternalLoad:
    return InternalLoad(Decimal(value))


def test_unconfirmed_injury_has_no_planning_effect() -> None:
    result = redistribute_injury_load(
        planned_loads={
            Discipline.SWIM: _load("100"),
            Discipline.BIKE: _load("200"),
            Discipline.RUN: _load("300"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
        confirmed=False,
    )

    assert result.evaluated is False
    assert result.allocations == ()
    assert result.removed_load.value == Decimal(0)


def test_single_injury_redistributes_80_percent_by_existing_proportions() -> None:
    result = redistribute_injury_load(
        planned_loads={
            Discipline.SWIM: _load("100"),
            Discipline.BIKE: _load("200"),
            Discipline.RUN: _load("300"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
        confirmed=True,
    )

    assert result.removed_load.value == Decimal("300")
    assert result.redistributed_load.value == Decimal("240.00")
    assert {
        allocation.discipline: allocation.load.value
        for allocation in result.allocations
    } == {
        Discipline.BIKE: Decimal("160.00"),
        Discipline.SWIM: Decimal("80.00"),
    }


def test_two_blocked_disciplines_allocate_to_the_remaining_discipline() -> None:
    result = redistribute_injury_load(
        planned_loads={
            Discipline.SWIM: _load("100"),
            Discipline.BIKE: _load("200"),
            Discipline.RUN: _load("300"),
        },
        blocked_disciplines=frozenset({Discipline.BIKE, Discipline.RUN}),
        confirmed=True,
    )

    assert len(result.allocations) == 1
    assert result.allocations[0].discipline is Discipline.SWIM
    assert result.allocations[0].load.value == Decimal("400.00")


def test_all_blocked_disciplines_produce_rest_without_redistribution() -> None:
    result = redistribute_injury_load(
        planned_loads={
            Discipline.SWIM: _load("100"),
            Discipline.BIKE: _load("200"),
            Discipline.RUN: _load("300"),
        },
        blocked_disciplines=frozenset(Discipline),
        confirmed=True,
    )

    assert result.rest_only is True
    assert result.redistributed_load.value == Decimal(0)
    assert result.allocations == ()


def test_zero_existing_shares_for_multiple_disciplines_require_review() -> None:
    result = redistribute_injury_load(
        planned_loads={
            Discipline.SWIM: _load("0"),
            Discipline.BIKE: _load("0"),
            Discipline.RUN: _load("100"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
        confirmed=True,
    )

    assert result.requires_review is True
    assert result.allocations == ()


def test_mvp_removes_blocked_load_without_automatic_redistribution() -> None:
    result = apply_mvp_injury_policy(
        planned_loads={
            Discipline.SWIM: _load("100"),
            Discipline.BIKE: _load("200"),
            Discipline.RUN: _load("300"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
        confirmed=True,
    )

    assert MVP_AUTOMATIC_INJURY_REDISTRIBUTION is False
    assert result.removed_load.value == Decimal("300")
    assert result.redistributed_load.value == Decimal(0)
    assert result.allocations == ()


def test_self_reported_limited_restriction_rechecks_without_auto_clear() -> None:
    started = datetime(2026, 8, 11, 8, tzinfo=timezone.utc)
    restriction = DisciplineRestriction.self_reported_limited(
        discipline=Discipline.RUN,
        start_at=started,
    )

    assert restriction.allowed_intensity is AllowedIntensity.LOW_ONLY
    assert restriction.requires_recheck(as_of=started + timedelta(days=6)) is False
    assert restriction.requires_recheck(as_of=started + timedelta(days=7)) is True
    assert restriction.end_at is None


def test_new_ruleset_distributes_only_to_safe_low_impact_capacity() -> None:
    result = redistribute_confirmed_injury_load(
        pre_injury_targets={
            Discipline.RUN: _load("300"),
            Discipline.BIKE: _load("120"),
            Discipline.SWIM: _load("60"),
        },
        recipient_safe_caps={
            Discipline.BIKE: _load("180"),
            Discipline.SWIM: _load("90"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
    )
    assert result.removed_load.value == Decimal("300")
    assert result.redistributed_load.value == Decimal("90")
    assert {
        allocation.discipline: allocation.load.value
        for allocation in result.allocations
    } == {Discipline.BIKE: Decimal("60"), Discipline.SWIM: Decimal("30")}


def test_new_ruleset_uses_remaining_recipient_when_other_saturates() -> None:
    result = redistribute_confirmed_injury_load(
        pre_injury_targets={
            Discipline.RUN: _load("100"),
            Discipline.BIKE: _load("120"),
            Discipline.SWIM: _load("60"),
        },
        recipient_safe_caps={
            Discipline.BIKE: _load("130"),
            Discipline.SWIM: _load("100"),
        },
        blocked_disciplines=frozenset({Discipline.RUN}),
    )
    assert result.redistributed_load.value == Decimal("50")
    assert {
        allocation.discipline: allocation.load.value
        for allocation in result.allocations
    } == {Discipline.BIKE: Decimal("10"), Discipline.SWIM: Decimal("40")}


def test_new_ruleset_never_auto_adds_zero_basis_even_after_opt_in() -> None:
    values = {Discipline.RUN: _load("100"), Discipline.BIKE: _load("0")}
    caps = {Discipline.BIKE: _load("0")}
    for opt_ins in (frozenset(), frozenset({Discipline.BIKE})):
        result = redistribute_confirmed_injury_load(
            pre_injury_targets=values,
            recipient_safe_caps=caps,
            blocked_disciplines=frozenset({Discipline.RUN}),
            cross_training_opt_ins=opt_ins,
        )
        assert result.allocations == ()
        assert result.redistributed_load.value == 0
        assert result.rest_only
    assert result.cross_training_consent_required is False


def test_new_ruleset_never_transfers_into_running() -> None:
    result = redistribute_confirmed_injury_load(
        pre_injury_targets={
            Discipline.BIKE: _load("100"),
            Discipline.RUN: _load("120"),
        },
        recipient_safe_caps={Discipline.RUN: _load("200")},
        blocked_disciplines=frozenset({Discipline.BIKE}),
    )
    assert result.allocations == ()
    assert result.redistributed_load.value == 0
