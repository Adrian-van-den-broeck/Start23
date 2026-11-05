"""Prospective, bounded exhaustive V6 selection and whole-week replacements.

Initial scope: at most one new workout per goal sport; retained occurrences can
repeat. Every finite option is examined before a globally optimal result is
claimed. No production registration, cache, persistence, or legacy score.
"""

from collections import Counter
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from itertools import product
from math import prod
from uuid import NAMESPACE_URL, UUID, uuid5

from app.modules.physiology.joren import StartingBaseline
from app.modules.physiology.models import (
    Discipline,
    IntensityBucket,
    InternalLoad,
    RuleId,
)
from app.modules.physiology.planned_v6 import sum_official
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    TrainingPhase,
    WorkoutTemplate,
    as_rpe_guided_template,
    snapshot_template,
)
from app.modules.workouts.joren_draft import TimedZone, WallRest
from app.modules.workouts.joren_v6_official import V6Template
from app.modules.workouts.planned_swim_estimate import estimate_swim

from .domain import (
    PlanLoadSample,
    PlanningConstraintError,
    PlanningTarget,
    PlanningWarning,
    ProposedWorkout,
    SelectedWorkout,
    WeeklyPlanDraft,
    ZoneCapability,
    _build_week,
    _injury_adjusted_target,
    resolve_target,
    schedule_workouts,
)

VERSION = "joren-v6-automatic-selection-1"
ALLOCATION = "selected-total-share-l1-unrenormalized-1"
TARGET = {
    Discipline.BIKE: Fraction(1, 2),
    Discipline.RUN: Fraction(3, 10),
    Discipline.SWIM: Fraction(1, 5),
}


@dataclass(frozen=True, slots=True)
class V6Controls:
    """Trusted server controls, never accepted as client-supplied authorization."""

    # Local inactive preview may use estimates; release acceptance remains open.
    estimate_swim_for_preview: bool = True
    occurrence_namespace: UUID | None = None
    athlete_scope: UUID | None = None
    week_scope: date | None = None
    duration_evidence: tuple[tuple[UUID, str], ...] = ()
    maximum_uses: tuple[tuple[UUID, int], ...] = ()
    prescribed_swim_seconds: tuple[tuple[UUID, tuple[Decimal, ...], str], ...] = ()
    maximum_combinations: int = 20000
    # Used only by an already authorized private caller, e.g. a stored week.
    authorized_target: PlanningTarget | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if (self.duration_evidence or self.prescribed_swim_seconds) and (
            self.athlete_scope is None or self.week_scope is None
        ):
            raise ValueError("individual_evidence_requires_athlete_week_scope")
        if self.maximum_combinations <= 0 or any(n < 0 for _, n in self.maximum_uses):
            raise ValueError("invalid_v6_computation_controls")
        for values in (
            self.duration_evidence,
            self.maximum_uses,
            self.prescribed_swim_seconds,
        ):
            if len({r[0] for r in values}) != len(values):
                raise ValueError("duplicate_v6_control_identity")
        if any(not ref.strip() for _, ref in self.duration_evidence):
            raise ValueError("duration_evidence_requires_reference")


@dataclass(frozen=True, slots=True, repr=False)
class V6Plan(WeeklyPlanDraft):
    templates: tuple[V6Template, ...]
    estimated_sports: frozenset[Discipline]
    exclusions: tuple[tuple[UUID, str], ...]
    examined: int
    optimality: str
    controls: V6Controls
    policy_version: str = field(default=VERSION, init=False)
    allocation_version: str = field(default=ALLOCATION, init=False)
    activation_status: str = field(default="INACTIVE_PREVIEW", init=False)


def eligible_v6(
    *,
    catalog: tuple[WorkoutTemplate, ...],
    phase: TrainingPhase,
    goal_disciplines: frozenset[Discipline],
    confirmed_injuries: frozenset[Discipline],
    zone_capabilities: Mapping[Discipline, ZoneCapability],
    low_only_disciplines: frozenset[Discipline] = frozenset(),
    build_week: int | None = None,
    controls: V6Controls = V6Controls(),
) -> tuple[V6Template, ...]:
    result = []
    for template in catalog:
        if not isinstance(template, V6Template):
            raise ValueError("v6_requires_official_source_revision")
        if exclusion(
            template,
            phase,
            goal_disciplines,
            confirmed_injuries,
            low_only_disciplines,
            zone_capabilities,
            build_week,
            controls,
        ):
            continue
        capability = zone_capabilities[template.discipline]
        if (
            capability.rpe_guided
            or not set(template.zone_requirements) <= capability.requirements
        ):
            projected = as_rpe_guided_template(template)
            assert isinstance(projected, V6Template)
            result.append(projected)
        else:
            result.append(template)
    return tuple(sorted(result, key=lambda t: str(t.id)))


def exclusion(
    t: V6Template,
    phase: TrainingPhase,
    goals: frozenset[Discipline],
    injuries: frozenset[Discipline],
    low_only: frozenset[Discipline],
    capabilities: Mapping[Discipline, ZoneCapability],
    build_week: int | None,
    controls: V6Controls,
) -> str | None:
    if t.discipline not in goals:
        return "sport_outside_goal"
    if t.discipline in injuries:
        return "confirmed_injury"
    if phase not in t.source_revision.phases:
        return "source_phase_not_allowed"
    capability = capabilities.get(t.discipline)
    if capability is None or not (capability.requirements or capability.rpe_guided):
        return "missing_sport_capability"
    if (
        capability.fallback_active
        and not capability.rpe_guided
        and t.fallback_compatibility is FallbackCompatibility.INCOMPATIBLE
    ):
        return "incompatible_fallback_capability"
    if t.discipline in low_only and t.intensity_bucket is IntensityBucket.HIGH:
        return "low_only_restriction"
    if (
        phase is TrainingPhase.BUILD
        and build_week != 4
        and any(
            not isinstance(e, WallRest) and e.zone == 5
            for e in t.source_revision.predecessor.events
        )
    ):
        return "existing_z5_build_occurrence_restriction"
    if t.source_workout_id == "TR-BIKE-013" and t.id not in dict(
        controls.duration_evidence
    ):
        return "individual_420_minute_duration_evidence_missing"
    if (
        t.discipline is Discipline.SWIM
        and not controls.estimate_swim_for_preview
        and t.id not in {r[0] for r in controls.prescribed_swim_seconds}
    ):
        return "authoritative_swim_duration_missing"
    return None


def active_times(
    t: V6Template, controls: V6Controls
) -> tuple[Fraction, Fraction, bool]:
    record = t.source_revision.predecessor
    if t.discipline is Discipline.SWIM:
        prescribed = next(
            (r for r in controls.prescribed_swim_seconds if r[0] == t.id), None
        )
        if prescribed is None:
            estimate = estimate_swim(record)
            return estimate.low_minutes * 60, estimate.high_minutes * 60, True
        _, values, reference = prescribed
        if (
            not reference
            or len(values) != len(record.events)
            or any(not v.is_finite() or v <= 0 for v in values)
        ):
            raise ValueError("invalid_authoritative_swim_prescription")
        low = sum(
            (
                Fraction(v)
                for e, v in zip(record.events, values)
                if not isinstance(e, WallRest) and e.zone <= 2
            ),
            Fraction(0),
        )
        high = sum(
            (
                Fraction(v)
                for e, v in zip(record.events, values)
                if not isinstance(e, WallRest) and e.zone > 2
            ),
            Fraction(0),
        )
        return low, high, False
    low = sum(
        (
            Fraction(e.seconds)
            for e in record.events
            if isinstance(e, TimedZone) and e.zone <= 2
        ),
        Fraction(0),
    )
    high = sum(
        (
            Fraction(e.seconds)
            for e in record.events
            if isinstance(e, TimedZone) and e.zone > 2
        ),
        Fraction(0),
    )
    return low, high, False


def week_valid(
    rows: tuple[V6Template, ...], target: PlanningTarget, controls: V6Controls
) -> bool:
    total = sum((Fraction(t.official.value) for t in rows), Fraction(0))
    if total > Fraction(target.target.value):
        return False
    uses = Counter(t.id for t in rows)
    if any(uses[k] > n for k, n in controls.maximum_uses):
        return False
    for sport in Discipline:
        members = tuple(t for t in rows if t.discipline is sport)
        low = sum((active_times(t, controls)[0] for t in members), Fraction(0))
        high = sum((active_times(t, controls)[1] for t in members), Fraction(0))
        if high * 5 > low + high:
            return False
        cap = target.discipline_caps.get(sport)
        if cap is not None and sum(
            (Fraction(t.official.value) for t in members), Fraction(0)
        ) > Fraction(cap.value):
            return False
    return True


def ranking(
    rows: tuple[V6Template, ...], goals: frozenset[Discipline]
) -> tuple[int, Fraction, Fraction, tuple[str, ...]]:
    total = sum((Fraction(t.official.value) for t in rows), Fraction(0))
    shares = {
        s: sum(
            (Fraction(t.official.value) for t in rows if t.discipline is s), Fraction(0)
        )
        for s in Discipline
    }
    distance = (
        sum((abs(shares[s] / total - TARGET[s]) for s in Discipline), Fraction(0))
        if total and goals == frozenset(Discipline)
        else Fraction(0)
    )
    return (
        -len({t.discipline for t in rows}),
        distance,
        -total,
        tuple(sorted(str(t.id) for t in rows)),
    )


def resolve_v6_target(
    *,
    week_start: date,
    race_date: date,
    prior_loads: tuple[PlanLoadSample, ...],
    onboarding_baseline: StartingBaseline | None,
    maintenance_active: bool,
    controls: V6Controls,
) -> PlanningTarget:
    if controls.authorized_target is not None:
        return controls.authorized_target
    if not prior_loads and onboarding_baseline is None:
        raise PlanningConstraintError(
            "authorized_budget_required", "An authorized weekly budget is required."
        )
    target = resolve_target(
        week_start=week_start,
        race_date=race_date,
        prior_loads=tuple(s for s in prior_loads if not s.sick_week),
        initial_catalog_load=onboarding_baseline.total
        if onboarding_baseline
        else InternalLoad(Decimal(0)),
        maintenance_active=maintenance_active,
        prior_approved_plan_exists=any(s.has_prior_approved_plan for s in prior_loads),
    )
    return replace(
        target,
        build_week=_build_week(week_start=week_start, race_date=race_date)
        if target.phase is TrainingPhase.BUILD
        else None,
    )


def build_v6_plan(
    *,
    week_start: date,
    timezone_name: str,
    race_date: date,
    catalog: tuple[WorkoutTemplate, ...],
    prior_loads: tuple[PlanLoadSample, ...],
    goal_disciplines: frozenset[Discipline],
    confirmed_injuries: frozenset[Discipline],
    zone_capabilities: Mapping[Discipline, ZoneCapability],
    available_dates: tuple[date, ...],
    low_only_disciplines: frozenset[Discipline] = frozenset(),
    cross_training_opt_ins: frozenset[Discipline] = frozenset(),
    selected_template_ids: Collection[UUID] | None = None,
    fixed_template_dates: Mapping[UUID, date] | None = None,
    selected_occurrence_ids: Collection[UUID] | None = None,
    fixed_occurrence_dates: Mapping[UUID, date] | None = None,
    maintenance_active: bool = False,
    onboarding_baseline: StartingBaseline | None = None,
    controls: V6Controls = V6Controls(),
    prefix: tuple[UUID, ...] = (),
    excluded: frozenset[UUID] = frozenset(),
    required_composition: Mapping[Discipline, int] | None = None,
) -> V6Plan:
    target = resolve_v6_target(
        week_start=week_start,
        race_date=race_date,
        prior_loads=prior_loads,
        onboarding_baseline=onboarding_baseline,
        maintenance_active=maintenance_active,
        controls=controls,
    )
    if controls.week_scope is not None and controls.week_scope != week_start:
        raise PlanningConstraintError(
            "v6_evidence_scope_mismatch", "Individual evidence belongs to another week."
        )
    if week_start.weekday() != 0 or not goal_disciplines:
        raise ValueError("invalid_v6_week_scope")
    deck = eligible_v6(
        catalog=catalog,
        phase=target.phase,
        goal_disciplines=goal_disciplines,
        confirmed_injuries=confirmed_injuries,
        low_only_disciplines=low_only_disciplines,
        zone_capabilities=zone_capabilities,
        build_week=target.build_week,
        controls=controls,
    )
    if confirmed_injuries and controls.authorized_target is None:
        # Reuse the approved injury allocation/cap behavior, never the soft target
        # as an invented injury redistribution allowance.
        target, _, _ = _injury_adjusted_target(
            target=target,
            prior_loads=prior_loads,
            onboarding_baseline=onboarding_baseline,
            blocked=confirmed_injuries,
            goal_disciplines=goal_disciplines,
            eligible_recipients=frozenset(t.discipline for t in deck),
            cross_training_opt_ins=cross_training_opt_ins,
            desired_high_fraction=target.desired_high_fraction,
        )
    by_id = {t.id: t for t in deck}
    needed = (
        tuple(selected_template_ids or ())
        if selected_template_ids is not None
        else prefix
    )
    if not set(needed) <= set(by_id):
        raise PlanningConstraintError(
            "template_not_eligible", "A selected workout is not eligible for this week."
        )
    combinations: tuple[tuple[V6Template, ...], ...]
    if selected_template_ids is not None:
        combinations = (tuple(by_id[k] for k in needed),)
        space = 1
    else:
        retained = tuple(by_id[k] for k in prefix)
        groups = tuple(
            tuple(t for t in deck if t.discipline is sport and t.id not in excluded)
            + (None,)
            for sport in sorted(goal_disciplines, key=lambda s: s.value)
            if sport not in {t.discipline for t in retained}
        )
        space = prod(map(len, groups))
        if space > controls.maximum_combinations:
            raise PlanningConstraintError(
                "v6_search_incomplete",
                "The bounded selection search did not complete; no optimum is claimed.",
            )
        combinations = tuple(
            retained + tuple(t for t in combo if t is not None)
            for combo in product(*groups)
        )
    viable = tuple(
        rows
        for rows in combinations
        if week_valid(rows, target, controls)
        and (
            required_composition is None
            or all(
                sum(t.discipline is s for t in rows) == required_composition.get(s, 0)
                for s in Discipline
            )
        )
    )
    ordered = sorted(viable, key=lambda rows: ranking(rows, goal_disciplines))
    chosen: tuple[V6Template, ...] | None = None
    workouts: tuple[ProposedWorkout, ...] = ()
    for rows in ordered:
        ordered_rows = (
            rows
            if selected_template_ids is not None or prefix
            else tuple(sorted(rows, key=lambda t: (t.discipline.value, str(t.id))))
        )
        supplied = tuple(selected_occurrence_ids or ())
        if supplied and (
            len(supplied) != len(ordered_rows) or len(set(supplied)) != len(supplied)
        ):
            raise PlanningConstraintError(
                "invalid_occurrence_identities",
                "Workout occurrence identities must be distinct and complete.",
            )
        ids = supplied or tuple(
            uuid5(
                controls.occurrence_namespace or NAMESPACE_URL,
                f"{VERSION}:{week_start}:{i}:{t.id}",
            )
            for i, t in enumerate(ordered_rows)
        )
        selected = tuple(
            SelectedWorkout(t.discipline, snapshot_template(t), occurrence)
            for t, occurrence in zip(ordered_rows, ids)
        )
        try:
            placed = (
                schedule_workouts(
                    selected=selected,
                    available_dates=available_dates,
                    week_start=week_start,
                    timezone_name=timezone_name,
                    fixed_template_dates=fixed_template_dates,
                    fixed_occurrence_dates=fixed_occurrence_dates,
                )
                if rows
                else ()
            )
        except PlanningConstraintError:
            continue
        chosen, workouts = ordered_rows, placed
        break
    if chosen is None:
        raise PlanningConstraintError(
            "v6_selection_invalid",
            "No eligible complete week satisfies this selection.",
        )
    estimates = frozenset(t.discipline for t in chosen if active_times(t, controls)[2])
    warnings = []
    if estimates:
        warnings.append(
            PlanningWarning(
                RuleId.SOFT_BOUNDARIES,
                "swim_time_estimated_preview",
                "Geplande actieve zwemtijd is geschat op basis van referentietempo; "
                "individuele tijd is niet geverifieerd.",
                "info",
            )
        )
    if len({t.discipline for t in chosen}) < len(goal_disciplines):
        warnings.append(
            PlanningWarning(
                RuleId.SOFT_BOUNDARIES,
                "partial_week" if chosen else "no_feasible_workouts_rest",
                "Een gedeeltelijke week is voorgesteld."
                if chosen
                else "Geen passende trainingen beschikbaar; deze week bevat rust.",
            )
        )
    # Public duration percentages describe known prescribed time only. Estimates
    # remain separate private provenance and never fill authoritative duration.
    known = tuple(t for t in chosen if t.duration_minutes is not None)
    kt = sum((sum(active_times(t, controls)[:2]) for t in known), Fraction(0))
    kh = sum((active_times(t, controls)[1] for t in known), Fraction(0))
    exclusions = tuple(
        (t.id, reason)
        for t in catalog
        if isinstance(t, V6Template)
        if (
            reason := exclusion(
                t,
                target.phase,
                goal_disciplines,
                confirmed_injuries,
                low_only_disciplines,
                zone_capabilities,
                target.build_week,
                controls,
            )
        )
    )
    from decimal import Context, localcontext

    with localcontext(Context(prec=50)):
        high_percent = (
            Decimal(kh.numerator)
            / Decimal(kh.denominator)
            / (Decimal(kt.numerator) / Decimal(kt.denominator))
            * 100
            if kt
            else Decimal(0)
        )
    return V6Plan(
        target,
        workouts,
        tuple(warnings),
        sum_official(
            tuple(t.duration_minutes for t in chosen if t.duration_minutes is not None)
        ),
        Decimal(100) - high_percent if kt else Decimal(0),
        high_percent,
        InternalLoad(sum_official(tuple(t.official.value for t in chosen))),
        chosen,
        estimates,
        exclusions,
        space,
        "EXHAUSTIVE_GLOBAL_OPTIMUM"
        if selected_template_ids is None
        else "EXPLICIT_WEEK_VALIDATED",
        controls,
    )
