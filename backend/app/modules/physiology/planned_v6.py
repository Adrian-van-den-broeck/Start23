"""Owner-accepted prospective IF² method; historical dispatch is independent."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction

from .models import Discipline

METHOD = "joren-v6-planned-if2-1"
PARAMETERS = "joren-v6-approved-if-reference-1"
APPROVAL = "joren-v6-official-tss-acceptance-1"
IF_VALUES = tuple(map(Decimal, (".55", ".75", ".88", ".98", "1.15")))
REFERENCE_MINUTES = tuple(map(Decimal, ("2.17", "2.00", "1.83", "1.67", "1.50")))
FACTORS = {
    Discipline.RUN: Decimal("1.15"),
    Discipline.BIKE: Decimal("1.00"),
    Discipline.SWIM: Decimal(".90"),
}


@dataclass(frozen=True, slots=True, repr=False)
class OfficialPlannedLoad:
    value: Decimal
    numerator: int
    denominator: int
    method: str = field(default=METHOD, init=False)
    parameters: str = field(default=PARAMETERS, init=False)
    approval: str = field(default=APPROVAL, init=False)
    numeric_policy: str = field(
        default="rational-to-decimal50-half-even-once-1", init=False
    )


def calculate_v6(
    sport: Discipline, zone_quantities: tuple[Decimal, ...]
) -> OfficialPlannedLoad:
    """RUN/BIKE inputs are seconds, SWIM inputs meters; wall rest is absent.

    One conversion of the final rational, never a rounded segment or subtotal.
    The source adapter restricts use to the approved new immutable revisions.
    """
    if len(zone_quantities) != 5 or any(
        not isinstance(q, Decimal) or not q.is_finite() or q < 0
        for q in zone_quantities
    ):
        raise ValueError("invalid_v6_zone_quantities")
    total = Fraction(0)
    for i, quantity in enumerate(zone_quantities):
        minutes = (
            Fraction(quantity) * Fraction(REFERENCE_MINUTES[i]) / 100
            if sport is Discipline.SWIM
            else Fraction(quantity) / 60
        )
        total += minutes * Fraction(IF_VALUES[i]) ** 2
    total *= Fraction(100, 60) * Fraction(FACTORS[sport])
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        value = Decimal(total.numerator) / Decimal(total.denominator)
    return OfficialPlannedLoad(value, total.numerator, total.denominator)


def sum_official(values: tuple[Decimal, ...]) -> Decimal:
    """Exact sum of stored final decimal operands, independent of ambient context.

    Thresholds must never round a slightly excessive week down to its ceiling.
    Individual official operands remain the accepted 50-digit context results.
    """
    if any(not v.is_finite() for v in values):
        raise ValueError("invalid_official_value")
    exponent = min((int(v.as_tuple().exponent) for v in values), default=0)
    scaled = 0
    for v in values:
        part = v.as_tuple()
        coefficient = int("".join(map(str, part.digits))) * (-1 if part.sign else 1)
        scaled += coefficient * 10 ** (int(part.exponent) - exponent)
    return Decimal((int(scaled < 0), tuple(map(int, str(abs(scaled)))), exponent))
