"""Fail-closed BR-009 tests and BR-010 redistribution fixtures."""

from decimal import Decimal

import pytest

from app.modules.physiology.injury import redistribute_injury_load
from app.modules.physiology.models import (
    Discipline,
    InternalLoad,
    RuleId,
    RulesetVersion,
)
from app.modules.physiology.specification import (
    PhysiologySpecification,
    PhysiologySpecificationNotApproved,
    SpecificationStatus,
)
from app.modules.physiology.zones import (
    ClinicalRange,
    ZoneBoundary,
    ZoneClinicalLimitsMissingError,
    ZoneMetric,
    ZoneMetricKind,
    validate_metric_with_limits,
    validate_zone_boundaries,
)


def _load(value: str) -> InternalLoad:
    return InternalLoad(Decimal(value))


def _approved_zone_specification() -> PhysiologySpecification:
    return PhysiologySpecification(
        version=RulesetVersion("test-zone-ruleset"),
        status=SpecificationStatus.APPROVED,
        approved_rules=frozenset({RuleId.DISCIPLINE_ZONES}),
    )


def _five_boundaries() -> tuple[ZoneBoundary, ...]:
    return tuple(
        ZoneBoundary(
            zone=zone,
            lower=Decimal((zone - 1) * 100),
            upper=Decimal(zone * 100),
        )
        for zone in range(1, 6)
    )


def test_zone_metric_requires_its_canonical_discipline() -> None:
    with pytest.raises(ValueError, match="does not belong"):
        ZoneMetric(
            discipline=Discipline.RUN,
            kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=Decimal("250"),
        )


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-1"), Decimal("NaN")])
def test_zone_metric_requires_positive_finite_value(value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        ZoneMetric(
            discipline=Discipline.BIKE,
            kind=ZoneMetricKind.BIKE_FTP_WATTS,
            value=value,
        )


def test_production_ruleset_cannot_activate_unapproved_zone_policy() -> None:
    metric = ZoneMetric(
        discipline=Discipline.BIKE,
        kind=ZoneMetricKind.BIKE_FTP_WATTS,
        value=Decimal("250"),
    )

    with pytest.raises(PhysiologySpecificationNotApproved):
        validate_metric_with_limits(metric, {})


def test_approved_zone_validation_still_fails_if_clinical_limits_are_missing() -> None:
    metric = ZoneMetric(
        discipline=Discipline.BIKE,
        kind=ZoneMetricKind.BIKE_FTP_WATTS,
        value=Decimal("250"),
    )

    with pytest.raises(ZoneClinicalLimitsMissingError, match="No approved"):
        validate_metric_with_limits(
            metric,
            {},
            specification=_approved_zone_specification(),
        )


def test_zone_clinical_limits_are_inclusive() -> None:
    specification = _approved_zone_specification()
    limits = {
        ZoneMetricKind.BIKE_FTP_WATTS: ClinicalRange(
            minimum=Decimal("100"),
            maximum=Decimal("500"),
        )
    }
    for value in (Decimal("100"), Decimal("500")):
        validate_metric_with_limits(
            ZoneMetric(
                discipline=Discipline.BIKE,
                kind=ZoneMetricKind.BIKE_FTP_WATTS,
                value=value,
            ),
            limits,
            specification=specification,
        )

    with pytest.raises(ValueError, match="outside"):
        validate_metric_with_limits(
            ZoneMetric(
                discipline=Discipline.BIKE,
                kind=ZoneMetricKind.BIKE_FTP_WATTS,
                value=Decimal("500.01"),
            ),
            limits,
            specification=specification,
        )


def test_zone_boundaries_require_all_five_ordered_zones() -> None:
    with pytest.raises(ValueError, match="Zones 1 through 5"):
        validate_zone_boundaries(
            _five_boundaries()[:-1],
            allow_adjacent_equality=True,
            specification=_approved_zone_specification(),
        )


def test_zone_boundary_adjacency_uses_explicit_policy() -> None:
    boundaries = _five_boundaries()
    specification = _approved_zone_specification()

    validate_zone_boundaries(
        boundaries,
        allow_adjacent_equality=True,
        specification=specification,
    )
    with pytest.raises(ValueError, match="equality is not approved"):
        validate_zone_boundaries(
            boundaries,
            allow_adjacent_equality=False,
            specification=specification,
        )


def test_zone_boundaries_reject_overlap() -> None:
    boundaries = list(_five_boundaries())
    boundaries[1] = ZoneBoundary(
        zone=2,
        lower=Decimal("99"),
        upper=Decimal("200"),
    )

    with pytest.raises(ValueError, match="cannot overlap"):
        validate_zone_boundaries(
            tuple(boundaries),
            allow_adjacent_equality=True,
            specification=_approved_zone_specification(),
        )


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
