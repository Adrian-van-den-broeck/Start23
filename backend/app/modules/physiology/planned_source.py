"""Pure, experimental source arithmetic. No operational method is authorized.

Callers supply every coefficient. Exact rational evidence precedes the isolated
Decimal review result; the numeric policy is engineering evidence, not approval
of the source's undocumented rounding stages. No athlete time is returned.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction

TIMED_IF2 = "joren-timed-if2-experimental-1"
SWIM_IF2 = "joren-swim-if2-experimental-1"
SWIM_FIXED_HISTORICAL = "joren-swim-fixed-pdf-historical-1"
NUMERIC_POLICY = (
    "exact rational; Decimal precision 50 HALF_EVEN; no intermediate rounding"
)


class SourceMethodError(ValueError):
    """Fixed, private-value-free failure code."""


@dataclass(frozen=True, slots=True, repr=False)
class SourceCalculation:
    method: str
    numerator: int
    denominator: int
    decimal_value: Decimal
    numeric_policy: str = field(default=NUMERIC_POLICY, init=False)
    operational_value: None = field(default=None, init=False)


def _valid(value: Decimal, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise SourceMethodError("invalid_source_parameter")
    if value < 0 or (positive and value == 0):
        raise SourceMethodError("invalid_source_parameter")


def calculate_source(
    *,
    method: str,
    quantities: tuple[Decimal, ...],
    if_values: tuple[Decimal | None, ...],
    sport_factor: Decimal,
    reference_seconds_per_100m: tuple[Decimal | None, ...] | None = None,
    fixed_per_100m: tuple[Decimal, ...] | None = None,
    stationary_rest_seconds: Decimal = Decimal(0),
) -> SourceCalculation:
    """Timed quantities are seconds, swim quantities meters; rests contribute zero.

    IF2 uses sum(minutes * IF**2) * 100/60 * sport_factor, with the factor
    exactly once. Historical fixed constants already contain the sport factor,
    so that dispatch requires an explicit unity factor. Unknown versions reject.
    """
    if method not in (TIMED_IF2, SWIM_IF2, SWIM_FIXED_HISTORICAL):
        raise SourceMethodError("unsupported_source_method")
    if len(quantities) != 5 or len(if_values) != 5:
        raise SourceMethodError("invalid_zone_parameter_count")
    _valid(sport_factor, positive=True)
    _valid(stationary_rest_seconds)
    if stationary_rest_seconds and method != SWIM_IF2:
        if method != SWIM_FIXED_HISTORICAL:
            raise SourceMethodError("invalid_stationary_rest")
    if method == SWIM_IF2:
        if reference_seconds_per_100m is None or len(reference_seconds_per_100m) != 5:
            raise SourceMethodError("missing_reference_pace")
        if fixed_per_100m is not None:
            raise SourceMethodError("incompatible_source_parameters")
    elif reference_seconds_per_100m is not None:
        raise SourceMethodError("incompatible_source_parameters")
    if method == SWIM_FIXED_HISTORICAL:
        if fixed_per_100m is None or len(fixed_per_100m) != 5:
            raise SourceMethodError("missing_fixed_constants")
        if sport_factor != 1 or any(v is not None for v in if_values):
            raise SourceMethodError("incompatible_source_parameters")
    elif fixed_per_100m is not None:
        raise SourceMethodError("incompatible_source_parameters")
    total = Fraction(0)
    for index, quantity in enumerate(quantities):
        _valid(quantity)
        anchor = if_values[index]
        if anchor is not None:
            _valid(anchor, positive=True)
        if method == SWIM_FIXED_HISTORICAL:
            assert fixed_per_100m is not None
            _valid(fixed_per_100m[index], positive=True)
            total += Fraction(quantity) * Fraction(fixed_per_100m[index]) / 100
            continue
        pace = (
            reference_seconds_per_100m[index]
            if reference_seconds_per_100m is not None
            else None
        )
        if pace is not None:
            _valid(pace, positive=True)
        if not quantity:
            continue
        if anchor is None:
            raise SourceMethodError("missing_if_anchor")
        seconds = Fraction(quantity)
        if method == SWIM_IF2:
            if pace is None:
                raise SourceMethodError("missing_reference_pace")
            seconds = seconds * Fraction(pace) / 100
        total += seconds * Fraction(anchor) ** 2 * Fraction(sport_factor) / 36
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        value = Decimal(total.numerator) / Decimal(total.denominator)
    return SourceCalculation(method, total.numerator, total.denominator, value)


def require_operational_source(method: str) -> Decimal:
    """No caller flag can convert a review calculation into approved plan load."""
    if method not in (TIMED_IF2, SWIM_IF2, SWIM_FIXED_HISTORICAL):
        raise SourceMethodError("unsupported_source_method")
    raise SourceMethodError("source_method_not_approved")
