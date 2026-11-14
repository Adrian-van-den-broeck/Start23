"""Exact lazy ranked search for explicitly requested sessions.

Only nonnegative load/cap/repetition excesses are pruned during construction.
HIGH is checked after a sport is complete: a LOW continuation can dilute it.
Disjoint load-sorted product boxes have optimistic lexicographic bounds. A leaf
is yielded only when no unexplored box can beat its exact rank. Scheduling stays
with the caller; an unschedulable leaf never certifies a feasible optimum.
"""

from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from fractions import Fraction
from heapq import heappop, heappush
from itertools import count, product
from typing import TYPE_CHECKING
from uuid import UUID

from app.modules.physiology.models import Discipline
from app.modules.workouts.joren_v6_official import V6Template

from .domain import PlanningConstraintError, PlanningTarget
from .v6_frequency import MAX_OCCURRENCES

if TYPE_CHECKING:
    from .v6_selection import V6Controls


@dataclass(slots=True)
class SearchWork:
    maximum: int
    nodes: int = 0

    def step(self) -> None:
        self.nodes += 1
        if self.nodes > self.maximum:
            raise PlanningConstraintError(
                "v6_search_incomplete",
                "The bounded selection search did not complete; no optimum is claimed.",
            )


Rank = tuple[int, int, Fraction, Fraction, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class _Option:
    added: tuple[V6Template, ...]
    load: Fraction  # Complete sport, including the fixed retained prefix.
    count: int
    requested: int
    identities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Span:
    options: tuple[_Option, ...]  # One exact complete-sport count stratum.
    first: int
    stop: int

    @property
    def low(self) -> Fraction:
        return self.options[self.first].load

    @property
    def high(self) -> Fraction:
        return self.options[self.stop - 1].load


def _bound(
    box: tuple[_Span, ...], budget: Fraction, weights: tuple[Fraction, ...]
) -> Rank | None:
    """Lower rank bound. See JOREN_V6_SEARCH_OPTIMALITY_PROOF.md.

    Every box has fixed coverage/request components. Share intervals relax all
    correlations, hence their summed distance is optimistic. Nonleaf UUID () is
    below every real tuple; no identity-based dominance is assumed.
    """
    low = sum((span.low for span in box), Fraction(0))
    if low > budget:
        return None
    high = sum((span.high for span in box), Fraction(0))
    leaf = all(span.stop - span.first == 1 for span in box)
    distance = Fraction(0)
    if weights and low:
        for span, weight in zip(box, weights):
            # x/(x+others) increases in x and decreases in others. The budget
            # further bounds the denominator, without asserting reachability.
            minimum = span.low / min(budget, span.low + high - span.high)
            maximum = span.high / (span.high + low - span.low)
            distance += max(minimum - weight, weight - maximum, Fraction(0))
    options = tuple(span.options[span.first] for span in box)
    return (
        -sum(option.count > 0 for option in options),
        -sum(option.requested for option in options),
        distance,
        -min(high, budget),
        tuple(sorted(k for option in options for k in option.identities))
        if leaf
        else (),
    )


def multi_options(
    *,
    deck: tuple[V6Template, ...],
    retained: tuple[V6Template, ...],
    goals: frozenset[Discipline],
    excluded: frozenset[UUID],
    target: PlanningTarget,
    controls: "V6Controls",
    work: SearchWork,
    required_composition: Mapping[Discipline, int] | None,
) -> Iterator[tuple[V6Template, ...]]:
    from .v6_selection import TARGET, active_times

    frequencies = {r.sport: r for r in controls.session_frequency}
    counts = Counter(t.discipline for t in retained)
    # Missing authorization retains the old one-per-sport generation envelope.
    desired = {
        s: max(counts[s], frequencies[s].requested if s in frequencies else 1)
        for s in goals
    }
    if sum(desired.values()) > MAX_OCCURRENCES:
        raise PlanningConstraintError(
            "v6_search_incomplete",
            "The authorized search exceeds the occurrence bound.",
        )
    if any(counts[r.sport] > r.maximum for r in controls.session_frequency):
        return
    budget = Fraction(target.target.value)
    loads = {t.id: Fraction(t.official.value) for t in deck}
    times = {t.id: active_times(t, controls) for t in deck}
    uses = Counter(t.id for t in retained)
    limits = dict(controls.maximum_uses)
    if any(uses[k] > n for k, n in controls.maximum_uses):
        return
    retained_load = sum((loads[t.id] for t in retained), Fraction(0))
    if retained_load > budget:
        return
    identities = {t.id: str(t.id) for t in deck}
    sports = sorted(goals, key=lambda s: s.value)
    groups: list[tuple[_Span, ...]] = []
    for sport in sports:
        existing = tuple(t for t in retained if t.discipline is sport)
        choices = tuple(
            t for t in deck if t.discipline is sport and t.id not in excluded
        )
        cap = target.discipline_caps.get(sport)
        ceiling = min(budget, Fraction(cap.value)) if cap is not None else budget
        initial_load = sum((loads[t.id] for t in existing), Fraction(0))
        low = sum((times[t.id][0] for t in existing), Fraction(0))
        high = sum((times[t.id][1] for t in existing), Fraction(0))
        options: dict[int, list[_Option]] = {}

        def extend(
            added: tuple[V6Template, ...],
            start: int,
            total: Fraction,
            low: Fraction,
            high: Fraction,
        ) -> None:
            work.step()
            if total > ceiling:
                return
            count = len(existing) + len(added)
            # The sport will not receive more rows after this option is joined.
            if high * 5 <= low + high and (
                required_composition is None
                or count == required_composition.get(sport, 0)
            ):
                options.setdefault(count, []).append(
                    _Option(
                        added,
                        total,
                        count,
                        min(count, frequencies[sport].requested)
                        if sport in frequencies
                        else 0,
                        tuple(sorted(identities[t.id] for t in existing + added)),
                    )
                )
            if count >= desired[sport] or (
                required_composition is not None
                and count >= required_composition.get(sport, 0)
            ):
                return
            for i in range(start, len(choices)):
                t = choices[i]
                if uses[t.id] >= limits.get(t.id, MAX_OCCURRENCES):
                    continue
                uses[t.id] += 1
                extend(
                    (*added, t),
                    i,
                    total + loads[t.id],
                    low + times[t.id][0],
                    high + times[t.id][1],
                )
                uses[t.id] -= 1

        extend((), 0, initial_load, low, high)
        groups.append(
            tuple(
                _Span(
                    tuple(sorted(values, key=lambda o: (o.load, o.identities))),
                    0,
                    len(values),
                )
                for _, values in sorted(options.items())
            )
        )
    weights = tuple(TARGET[s] for s in sports) if goals == frozenset(Discipline) else ()
    heap: list[tuple[Rank, int, tuple[_Span, ...]]] = []
    serial = count()

    def enqueue(box: tuple[_Span, ...]) -> None:
        work.step()
        bound = _bound(box, budget, weights)
        if bound is not None:
            heappush(heap, (bound, next(serial), box))

    # Each count-stratified root is disjoint. All are admitted before yielding.
    for box in product(*groups):
        enqueue(box)
    while heap:
        _, _, box = heappop(heap)
        axis = max(range(len(box)), key=lambda i: box[i].stop - box[i].first)
        span = box[axis]
        if span.stop - span.first == 1:
            yield retained + tuple(
                t for part in box for t in part.options[part.first].added
            )
        else:
            middle = (span.first + span.stop) // 2
            for first, stop in ((span.first, middle), (middle, span.stop)):
                enqueue(
                    box[:axis] + (_Span(span.options, first, stop),) + box[axis + 1 :]
                )
