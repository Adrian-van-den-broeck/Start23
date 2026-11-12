"""Bounded canonical multiset enumeration for explicitly requested sessions.

Only nonnegative load/cap/repetition excesses are pruned during construction.
HIGH is checked after a sport is complete: a LOW continuation can dilute it.
No state merging loses template identity, dates or scheduling distinctions.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
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
) -> tuple[tuple[V6Template, ...], ...]:
    from .v6_selection import active_times

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
        return ()
    budget = Fraction(target.target.value)
    loads = {t.id: Fraction(t.official.value) for t in deck}
    times = {t.id: active_times(t, controls) for t in deck}
    uses = Counter(t.id for t in retained)
    limits = dict(controls.maximum_uses)
    if any(uses[k] > n for k, n in controls.maximum_uses):
        return ()
    retained_load = sum((loads[t.id] for t in retained), Fraction(0))
    if retained_load > budget:
        return ()
    groups: list[tuple[tuple[V6Template, ...], ...]] = []
    for sport in sorted(goals, key=lambda s: s.value):
        existing = tuple(t for t in retained if t.discipline is sport)
        choices = tuple(
            t for t in deck if t.discipline is sport and t.id not in excluded
        )
        cap = target.discipline_caps.get(sport)
        ceiling = min(budget, Fraction(cap.value)) if cap is not None else budget
        initial_load = sum((loads[t.id] for t in existing), Fraction(0))
        low = sum((times[t.id][0] for t in existing), Fraction(0))
        high = sum((times[t.id][1] for t in existing), Fraction(0))
        options: list[tuple[V6Template, ...]] = []

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
                options.append(added)
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
        groups.append(tuple(options))
    result: list[tuple[V6Template, ...]] = []

    def join(index: int, rows: tuple[V6Template, ...], total: Fraction) -> None:
        work.step()
        if total > budget:
            return
        if index == len(groups):
            result.append(rows)
            return
        for option in groups[index]:
            join(
                index + 1,
                rows + option,
                total + sum((loads[t.id] for t in option), Fraction(0)),
            )

    join(0, retained, retained_load)
    return tuple(result)
