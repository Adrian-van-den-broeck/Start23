"""Tests for pure physiology value objects."""

from decimal import Decimal

import pytest

from app.modules.physiology.models import (
    DurationMinutes,
    Fraction,
    InternalLoad,
    RulesetVersion,
)


@pytest.mark.parametrize(
    "value",
    [Decimal("-0.01"), Decimal("NaN"), Decimal("Infinity")],
)
def test_internal_load_rejects_invalid_values(value: Decimal) -> None:
    """Server-only load values are finite and non-negative."""
    with pytest.raises(ValueError, match="finite and non-negative"):
        InternalLoad(value)


def test_internal_load_value_is_hidden_from_repr() -> None:
    """Accidental object logging does not reveal the internal load value."""
    load = InternalLoad(Decimal("123.45"))

    assert "123.45" not in repr(load)


@pytest.mark.parametrize(
    "value",
    [Decimal("-0.01"), Decimal("NaN"), Decimal("Infinity")],
)
def test_duration_rejects_invalid_values(value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        DurationMinutes(value)


@pytest.mark.parametrize(
    "value",
    [Decimal("-0.01"), Decimal("1.01"), Decimal("NaN")],
)
def test_fraction_rejects_values_outside_zero_to_one(value: Decimal) -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        Fraction(value)


@pytest.mark.parametrize(
    "value",
    ["", "Phase-3", "contains spaces", "a" * 65],
)
def test_ruleset_version_rejects_unstable_identifiers(value: str) -> None:
    """Ruleset identifiers remain safe to persist and compare."""
    with pytest.raises(ValueError, match="stable lowercase identifier"):
        RulesetVersion(value)
