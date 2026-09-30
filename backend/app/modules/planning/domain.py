"""Framework-independent deterministic weekly planning policies."""

from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from itertools import combinations
from uuid import UUID
from zoneinfo import ZoneInfo

from app.modules.physiology.anti_stack import (
    ScheduledWorkout,
    find_anti_stack_violations,
)
from app.modules.physiology.debt import (
    calculate_reliable_intensity_debt,
    calculate_volume_debt,
)
from app.modules.physiology.injury import redistribute_confirmed_injury_load
from app.modules.physiology.intensity import (
    STANDARD_RACE_INTENSITY_TARGET,
    IntensitySegment,
    WorkoutIntensity,
    calculate_time_distribution,
)
from app.modules.physiology.joren import StartingBaseline, is_taper_day
from app.modules.physiology.models import (
    Discipline,
    DurationMinutes,
    Fraction,
    IntensityBucket,
    InternalLoad,
    RuleId,
    TrainingZone,
)
from app.modules.physiology.progression import (
    ProgressionBasis,
    WeeklyLoad,
    calculate_42_day_average,
    calculate_progressive_target,
)
from app.modules.physiology.recovery import (
    WeekPhase,
    calculate_recovery_target,
)
from app.modules.physiology.taper import (
    RacePriority,
    TaperPeriod,
    calculate_taper_baseline,
    calculate_taper_target,
)
from app.modules.workouts.catalog import (
    FallbackCompatibility,
    PlannedWorkoutSnapshot,
    TrainingPhase,
    WorkoutTemplate,
    ZoneRequirement,
    as_rpe_guided_template,
    require_planned_load,
    snapshot_template,
)


class PlanningConstraintError(ValueError):
    """A generated schedule cannot satisfy a hard or generated-plan constraint."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PlanningTargetBasis(str, Enum):
    """Auditable, qualitative source for the hidden target."""

    INITIAL_CATALOG_BASELINE = "initial_catalog_baseline"
    PRIOR_PLANNED_HOLD = "prior_planned_hold"
    REALIZED_PROGRESSION = "realized_progression"
    REALIZED_BASELINE = "realized_baseline"
    INACTIVE_RESTART = "inactive_restart"
    MAINTENANCE_HOLD = "maintenance_hold"
    PHYSIOLOGICAL_DEBT = "physiological_debt"
    MANUAL_REVIEW_RECOVERY = "manual_review_recovery"
    ACTIVITY_CORRECTION = "activity_correction"
    RECOVERY_FACTOR = "recovery_factor"
    TAPER_FACTOR = "taper_factor"
    INJURY_REST_ONLY = "injury_rest_only"


@dataclass(frozen=True, slots=True)
class ZoneCapability:
    """The template-driving capabilities of one active discipline zone."""

    requirements: frozenset[ZoneRequirement]
    fallback_active: bool = False
    protocol_ids: frozenset[str] = frozenset()
    rpe_guided: bool = False
    calibration_evidence: bool = False


@dataclass(frozen=True, slots=True)
class PlanLoadSample:
    """Private historical plan load used only by the deterministic engine."""

    week_start: date
    load: InternalLoad = field(repr=False)
    phase: TrainingPhase
    realized_load: InternalLoad | None = field(default=None, repr=False)
    target_basis: PlanningTargetBasis | None = None
    planned_high_minutes: DurationMinutes | None = None
    planned_total_minutes: DurationMinutes | None = None
    realized_high_minutes: DurationMinutes | None = None
    realized_classified_minutes: DurationMinutes | None = None
    realized_total_minutes: DurationMinutes | None = None
    completed_activity_count: int | None = None
    sick_week: bool = False
    reduced_realized_progression: bool = False
    discipline_loads: Mapping[Discipline, InternalLoad] = field(
        default_factory=dict, repr=False
    )


@dataclass(frozen=True, slots=True)
class PlanningTarget:
    """Hidden weekly load target plus public phase context."""

    phase: TrainingPhase
    basis: PlanningTargetBasis
    target: InternalLoad = field(repr=False)
    taper_period: TaperPeriod | None = None
    desired_high_fraction: Fraction = STANDARD_RACE_INTENSITY_TARGET.high_fraction
    manual_review_required: bool = False
    build_week: int | None = None
    discipline_caps: Mapping[Discipline, InternalLoad] = field(
        default_factory=dict, repr=False
    )
    replacement_disciplines: frozenset[Discipline] = frozenset()
    injury_load_unallocated: bool = False
    cross_training_consent_required: bool = False


@dataclass(frozen=True, slots=True)
class SelectedWorkout:
    """One catalog snapshot selected for the proposed revision."""

    discipline: Discipline
    snapshot: PlannedWorkoutSnapshot
    occurrence_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ProposedWorkout:
    """One selected immutable workout on an athlete-local calendar date."""

    discipline: Discipline
    snapshot: PlannedWorkoutSnapshot
    scheduled_date: date
    occurrence_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PlanningWarning:
    """TSS-free qualitative result safe for a public response."""

    rule_id: RuleId
    code: str
    message: str
    severity: str = "warning"
    affected_template_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class WeeklyPlanDraft:
    """Complete deterministic result ready for pending persistence."""

    target: PlanningTarget
    workouts: tuple[ProposedWorkout, ...]
    warnings: tuple[PlanningWarning, ...]
    total_duration_minutes: Decimal
    low_intensity_percent: Decimal
    high_intensity_percent: Decimal
    planned_load: InternalLoad = field(repr=False)


def _training_phase(phase: WeekPhase, *, first_plan: bool) -> TrainingPhase:
    if phase is WeekPhase.TAPER:
        return TrainingPhase.TAPER
    if phase is WeekPhase.RECOVERY:
        return TrainingPhase.RECOVERY
    return TrainingPhase.BASE if first_plan else TrainingPhase.BUILD


def _race_anchored_phase(*, week_start: date, race_date: date) -> WeekPhase:
    """Resolve the 4+1 position only from the dated race anchor."""
    race_week_start = race_date - timedelta(days=race_date.weekday())
    weeks_before_race = (race_week_start - week_start).days // 7
    if any(is_taper_day(week_start + timedelta(days=i), race_date) for i in range(7)):
        return WeekPhase.TAPER
    return WeekPhase.RECOVERY if weeks_before_race % 5 == 0 else WeekPhase.BUILD


def _build_week(*, week_start: date, race_date: date) -> int:
    """Position inside the race-anchored four-build/one-recovery rhythm."""
    race_week_start = race_date - timedelta(days=race_date.weekday())
    weeks_before_race = (race_week_start - week_start).days // 7
    return 5 - weeks_before_race % 5


def resolve_target(
    *,
    week_start: date,
    race_date: date,
    prior_loads: tuple[PlanLoadSample, ...],
    initial_catalog_load: InternalLoad,
    maintenance_active: bool = False,
) -> PlanningTarget:
    """Resolve current targets with historical records explicitly filtered."""
    prior_loads = tuple(sample for sample in prior_loads if not sample.sick_week)
    if week_start.weekday() != 0:
        raise ValueError("The training week must start on Monday.")
    if race_date < week_start and not maintenance_active:
        raise PlanningConstraintError(
            "race_date_before_week",
            "The primary race date is before the requested training week.",
        )

    if maintenance_active:
        if not prior_loads:
            raise PlanningConstraintError(
                "maintenance_baseline_unavailable",
                "Maintenance requires a prior approved weekly plan baseline.",
            )
        week_phase = (
            WeekPhase.RECOVERY if (len(prior_loads) + 1) % 5 == 0 else WeekPhase.BUILD
        )
        if week_phase is WeekPhase.RECOVERY:
            recovery = calculate_recovery_target(week_four_planned=prior_loads[-1].load)
            return PlanningTarget(
                phase=TrainingPhase.RECOVERY,
                basis=PlanningTargetBasis.RECOVERY_FACTOR,
                target=recovery.target,
            )
        return PlanningTarget(
            phase=TrainingPhase.BUILD,
            basis=PlanningTargetBasis.MAINTENANCE_HOLD,
            target=prior_loads[-1].load,
        )

    overlapping_taper = any(
        is_taper_day(week_start + timedelta(days=i), race_date) for i in range(7)
    )
    if overlapping_taper and race_date != week_start + timedelta(days=7):
        raise PlanningConstraintError(
            "partial_week_taper_rule_required",
            "A reviewed target for this exact pre-race date window is required.",
        )
    taper_period = TaperPeriod.A_T_MINUS_1 if overlapping_taper else None
    if taper_period is not None:
        baseline = calculate_taper_baseline(
            tuple(
                WeeklyLoad(
                    week_start=sample.week_start,
                    load=sample.load,
                    is_recovery_week=sample.phase is TrainingPhase.RECOVERY,
                )
                for sample in prior_loads
            ),
            as_of=week_start - timedelta(days=1),
        )
        if baseline is None:
            raise PlanningConstraintError(
                "taper_baseline_unavailable",
                "A taper week requires an available prior build-load baseline.",
            )
        taper = calculate_taper_target(
            priority=RacePriority.A,
            period=taper_period,
            baseline=baseline,
        )
        assert taper is not None
        return PlanningTarget(
            phase=TrainingPhase.TAPER,
            basis=PlanningTargetBasis.TAPER_FACTOR,
            target=taper.target,
            taper_period=taper_period,
        )

    week_phase = _race_anchored_phase(week_start=week_start, race_date=race_date)
    if week_phase is WeekPhase.RECOVERY and not prior_loads:
        # A race anchor may place a brand-new athlete at a nominal recovery
        # position before any recovery baseline exists. Start the first valid
        # week from the already-approved onboarding/catalog baseline; never
        # fabricate the missing prior week that the recovery formula requires.
        return PlanningTarget(
            phase=TrainingPhase.BASE,
            basis=PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
            target=initial_catalog_load,
        )
    phase = _training_phase(week_phase, first_plan=not prior_loads)
    if week_phase is WeekPhase.RECOVERY:
        recovery = calculate_recovery_target(
            week_four_planned=prior_loads[-1].load,
        )
        return PlanningTarget(
            phase=phase,
            basis=PlanningTargetBasis.RECOVERY_FACTOR,
            target=recovery.target,
        )
    if prior_loads and prior_loads[-1].realized_load is not None:
        latest = prior_loads[-1]
        assert latest.realized_load is not None
        if (
            latest.reduced_realized_progression or latest.completed_activity_count == 0
        ) and latest.realized_load.value < latest.load.value:
            return PlanningTarget(
                phase=phase,
                basis=PlanningTargetBasis.REALIZED_PROGRESSION,
                target=InternalLoad(latest.realized_load.value * Decimal("1.10")),
            )
        debt = calculate_volume_debt(
            prior_planned=latest.load,
            prior_realized=latest.realized_load,
        )
        if debt.activated:
            if debt.corrected_target is None:
                if latest.target_basis is PlanningTargetBasis.MANUAL_REVIEW_RECOVERY:
                    raise PlanningConstraintError(
                        "physiological_debt_escalation_required",
                        "Repeated unsafe load requires review by a qualified person.",
                    )
                recovery = calculate_recovery_target(week_four_planned=latest.load)
                return PlanningTarget(
                    phase=TrainingPhase.RECOVERY,
                    basis=PlanningTargetBasis.MANUAL_REVIEW_RECOVERY,
                    target=recovery.target,
                    manual_review_required=True,
                )
            return PlanningTarget(
                phase=phase,
                basis=PlanningTargetBasis.PHYSIOLOGICAL_DEBT,
                target=debt.corrected_target,
            )
        baseline = calculate_42_day_average(
            tuple(
                WeeklyLoad(
                    week_start=sample.week_start,
                    load=sample.realized_load,
                    is_recovery_week=sample.phase is TrainingPhase.RECOVERY,
                )
                for sample in prior_loads
                if sample.realized_load is not None
            ),
            as_of=week_start - timedelta(days=1),
            exclude_recovery_weeks=True,
        )
        progression = calculate_progressive_target(
            prior_planned=latest.load,
            prior_realized=latest.realized_load,
            baseline=baseline,
        )
        return PlanningTarget(
            phase=phase,
            basis=(
                PlanningTargetBasis.REALIZED_PROGRESSION
                if progression.basis is ProgressionBasis.REGULAR
                else PlanningTargetBasis.REALIZED_BASELINE
            ),
            target=progression.target,
        )
    if prior_loads:
        # Missing realized data is not interpreted as adherence or non-adherence.
        return PlanningTarget(
            phase=phase,
            basis=PlanningTargetBasis.PRIOR_PLANNED_HOLD,
            target=prior_loads[-1].load,
        )
    return PlanningTarget(
        phase=phase,
        basis=PlanningTargetBasis.INITIAL_CATALOG_BASELINE,
        target=initial_catalog_load,
    )


def _desired_high_fraction(
    *,
    target: PlanningTarget,
    prior_loads: tuple[PlanLoadSample, ...],
) -> Fraction:
    """Apply intensity debt once, on the first following non-recovery week."""
    standard = STANDARD_RACE_INTENSITY_TARGET.high_fraction
    if target.phase in {TrainingPhase.RECOVERY, TrainingPhase.TAPER} or not prior_loads:
        return standard
    candidate = prior_loads[-1]
    if candidate.phase is TrainingPhase.RECOVERY:
        if len(prior_loads) < 2:
            return standard
        candidate = prior_loads[-2]
    if candidate.phase in {TrainingPhase.RECOVERY, TrainingPhase.TAPER}:
        return standard
    required = (
        candidate.planned_high_minutes,
        candidate.planned_total_minutes,
        candidate.realized_high_minutes,
        candidate.realized_classified_minutes,
        candidate.realized_total_minutes,
    )
    if any(value is None for value in required):
        return standard
    planned_high, planned_total, realized_high, realized_classified, realized_total = (
        value for value in required if value is not None
    )
    evaluation = calculate_reliable_intensity_debt(
        planned_high=planned_high,
        planned_total=planned_total,
        realized_high=realized_high,
        realized_classified=realized_classified,
        realized_total=realized_total,
        base_next_high_fraction=standard,
    )
    if not evaluation.evaluated or evaluation.result is None:
        return standard
    return evaluation.result.corrected_high_fraction


def _injury_adjusted_target(
    *,
    target: PlanningTarget,
    prior_loads: tuple[PlanLoadSample, ...],
    onboarding_baseline: StartingBaseline | None,
    blocked: frozenset[Discipline],
    goal_disciplines: frozenset[Discipline],
    eligible_recipients: frozenset[Discipline],
    cross_training_opt_ins: frozenset[Discipline],
    desired_high_fraction: Fraction,
) -> tuple[PlanningTarget, frozenset[Discipline], frozenset[Discipline]]:
    """Bound new recipient load by the existing per-sport 10% progression cap."""
    if not blocked:
        return target, frozenset(), frozenset()
    basis = next(
        (
            sample.discipline_loads
            for sample in reversed(prior_loads)
            if sample.discipline_loads
        ),
        onboarding_baseline.by_discipline if onboarding_baseline else {},
    )
    if not basis or sum((load.value for load in basis.values()), Decimal(0)) == 0:
        raise PlanningConstraintError(
            "injury_discipline_basis_unavailable",
            "A reviewed discipline load basis is required for this restriction.",
        )
    basis_total = sum((load.value for load in basis.values()), Decimal(0))
    normal = {
        sport: InternalLoad(target.target.value * load.value / basis_total)
        for sport, load in basis.items()
    }
    caps = {
        sport: InternalLoad(max(normal[sport].value, load.value * Decimal("1.10")))
        for sport, load in basis.items()
    }
    result = redistribute_confirmed_injury_load(
        pre_injury_targets=normal,
        recipient_safe_caps={
            sport: cap for sport, cap in caps.items() if sport in eligible_recipients
        },
        blocked_disciplines=blocked,
        cross_training_opt_ins=cross_training_opt_ins,
    )
    unblocked_normal = sum(
        (
            load.value
            for sport, load in normal.items()
            if sport not in blocked
            and (sport in goal_disciplines or sport in eligible_recipients)
        ),
        Decimal(0),
    )
    replacement = {
        allocation.discipline: allocation.load for allocation in result.allocations
    }
    new_total = unblocked_normal + result.redistributed_load.value
    recipient_caps = {
        sport: InternalLoad(
            normal[sport].value + replacement.get(sport, InternalLoad(Decimal(0))).value
        )
        for sport in normal
        if sport not in blocked
        and (sport in goal_disciplines or sport in eligible_recipients)
    }
    adjusted_fraction = Fraction(
        min(
            Decimal(1),
            unblocked_normal * desired_high_fraction.value / new_total,
        )
        if new_total > 0
        else Decimal(0)
    )
    return (
        PlanningTarget(
            phase=target.phase,
            basis=target.basis,
            target=InternalLoad(new_total),
            taper_period=target.taper_period,
            desired_high_fraction=adjusted_fraction,
            manual_review_required=target.manual_review_required,
            build_week=target.build_week,
            discipline_caps=recipient_caps,
            replacement_disciplines=frozenset(replacement),
            injury_load_unallocated=(
                result.redistributed_load.value
                < result.removed_load.value * Decimal("0.80")
            ),
            cross_training_consent_required=(result.cross_training_consent_required),
        ),
        frozenset(sport for sport, load in recipient_caps.items() if load.value > 0),
        frozenset(replacement),
    )


def eligible_workouts(
    *,
    catalog: tuple[WorkoutTemplate, ...],
    phase: TrainingPhase,
    goal_disciplines: frozenset[Discipline],
    confirmed_injuries: frozenset[Discipline],
    low_only_disciplines: frozenset[Discipline] = frozenset(),
    zone_capabilities: Mapping[Discipline, ZoneCapability],
    build_week: int | None = None,
) -> tuple[WorkoutTemplate, ...]:
    """Filter immutable catalog versions by phase, injury, goal, and zones."""
    eligible: list[WorkoutTemplate] = []
    for template in catalog:
        if template.internal_planned_load is None:
            continue
        zone_numbers = {
            segment.zone_target
            for segment in template.segments
            if segment.zone_target is not None
        }
        low_only_phase = phase in {
            TrainingPhase.BASE,
            TrainingPhase.RECOVERY,
            TrainingPhase.TAPER,
        }
        if (
            template.discipline not in goal_disciplines
            or template.discipline in confirmed_injuries
            or (
                phase not in template.training_phases
                and not (
                    phase is TrainingPhase.TAPER
                    and template.source_catalog == "start23-v0.1"
                    and template.intensity_bucket is IntensityBucket.LOW
                )
            )
            or (
                low_only_phase
                and any(zone > TrainingZone.ZONE_2 for zone in zone_numbers)
            )
            or (low_only_phase and template.intensity_bucket is IntensityBucket.HIGH)
            or (
                phase is TrainingPhase.BUILD
                and build_week != 4
                and TrainingZone.ZONE_5 in zone_numbers
            )
            or (
                template.discipline in low_only_disciplines
                and template.intensity_bucket is IntensityBucket.HIGH
            )
        ):
            continue
        capability = zone_capabilities.get(template.discipline)
        if capability is None:
            continue
        protocol_ids = {
            segment.protocol_target.protocol_id
            for segment in template.segments
            if segment.protocol_target is not None
        }
        if protocol_ids and not protocol_ids.issubset(capability.protocol_ids):
            continue
        if (
            capability.fallback_active
            and not capability.rpe_guided
            and (
                template.fallback_compatibility is not FallbackCompatibility.COMPATIBLE
            )
        ):
            continue
        requirements_supported = set(template.zone_requirements).issubset(
            capability.requirements
        )
        if capability.rpe_guided:
            eligible.append(as_rpe_guided_template(template))
        elif requirements_supported:
            eligible.append(template)
        elif capability.requirements and not capability.fallback_active:
            # A confirmed profile can use the catalog's already-reviewed textual
            # RPE projection when its numeric metric differs from this template.
            # This changes execution guidance only; the authoritative catalog
            # load, version, phase tags, and physiological rules remain unchanged.
            eligible.append(as_rpe_guided_template(template))
    return tuple(
        sorted(
            eligible,
            key=lambda item: (
                item.discipline.value,
                require_planned_load(item).value,
                str(item.id),
            ),
        )
    )


def _selection_key(
    selection: tuple[WorkoutTemplate, ...],
    *,
    target: InternalLoad,
    desired_high_fraction: Fraction,
) -> tuple[Decimal, Decimal, int, tuple[str, ...]]:
    planned = sum(
        (require_planned_load(template).value for template in selection),
        Decimal(0),
    )
    total_duration = sum(
        (
            template.duration_minutes
            for template in selection
            if template.duration_minutes is not None
        ),
        Decimal(0),
    )
    high_duration = sum(
        (
            template.duration_minutes
            for template in selection
            if template.intensity_bucket is IntensityBucket.HIGH
            and template.duration_minutes is not None
        ),
        Decimal(0),
    )
    actual_high_fraction = (
        high_duration / total_duration if total_duration > 0 else Decimal(0)
    )
    return (
        abs(planned - target.value),
        abs(actual_high_fraction - desired_high_fraction.value),
        len(selection),
        tuple(str(template.id) for template in selection),
    )


def _selection_policy_valid(
    selection: tuple[WorkoutTemplate, ...],
    *,
    target: InternalLoad,
    phase: TrainingPhase,
    build_week: int | None,
    desired_high_fraction: Fraction,
    high_available: bool,
    z5_available: bool,
    minimum_load: Decimal,
    discipline_caps: Mapping[Discipline, InternalLoad] | None = None,
) -> bool:
    if discipline_caps is not None and any(
        sum(
            (
                require_planned_load(item).value
                for item in selection
                if item.discipline is sport
            ),
            Decimal(0),
        )
        > cap.value
        for sport, cap in discipline_caps.items()
    ):
        return False
    total = sum((require_planned_load(item).value for item in selection), Decimal(0))
    if abs(target.value - total) >= minimum_load:
        return False
    high = sum(
        (
            require_planned_load(item).value
            for item in selection
            if item.intensity_bucket is IntensityBucket.HIGH
        ),
        Decimal(0),
    )
    if phase is not TrainingPhase.BUILD:
        return high == 0
    budget = target.value * desired_high_fraction.value
    if high > budget:
        return False
    if not high_available:
        return high == 0
    if build_week != 4:
        return budget * Decimal("0.70") <= high <= budget * Decimal("0.90")
    return high > 0 and (
        not z5_available or any(_has_zone_five(item) for item in selection)
    )


def _has_zone_five(template: WorkoutTemplate) -> bool:
    return TrainingZone.ZONE_5 in template.reviewed_zone_numbers or any(
        segment.zone_target is TrainingZone.ZONE_5 for segment in template.segments
    )


def _bounded_selection(
    *,
    deck: tuple[WorkoutTemplate, ...],
    prefix: tuple[WorkoutTemplate, ...],
    required_disciplines: frozenset[Discipline],
    target: InternalLoad,
    phase: TrainingPhase,
    build_week: int | None,
    desired_high_fraction: Fraction,
    required_count: int | None = None,
    required_composition: Mapping[Discipline, int] | None = None,
    maximum_uses: Mapping[UUID, int] | None = None,
    discipline_caps: Mapping[Discipline, InternalLoad] | None = None,
    feasible: Callable[[tuple[WorkoutTemplate, ...]], bool] | None = None,
) -> tuple[WorkoutTemplate, ...] | None:
    """Fit a bounded multiset by exact private load, bucket and sport counts.

    Catalog rows with the same load, sport, bucket and Z5 status are equivalent
    for composition. The smallest immutable ID represents each equivalence
    class in the automatic prescription; the swipe deck retains every row.
    """
    if not deck or len(prefix) > 24:
        return None
    if maximum_uses is not None and any(
        sum(item.id == template_id for item in prefix) > limit
        for template_id, limit in maximum_uses.items()
    ):
        return None
    minimum_load = min(require_planned_load(item).value for item in deck)
    budget = target.value * desired_high_fraction.value
    high_available = phase is TrainingPhase.BUILD and any(
        item.intensity_bucket is IntensityBucket.HIGH
        and require_planned_load(item).value <= budget
        for item in deck
    )
    z5_available = build_week == 4 and any(
        item.intensity_bucket is IntensityBucket.HIGH
        and require_planned_load(item).value <= budget
        and _has_zone_five(item)
        for item in deck
    )
    groups: dict[
        tuple[Discipline, Decimal, IntensityBucket, bool], WorkoutTemplate
    ] = {}
    for item in deck:
        key = (
            item.discipline,
            require_planned_load(item).value,
            item.intensity_bucket,
            _has_zone_five(item),
        )
        prior = groups.get(key)
        if prior is None or str(item.id) < str(prior.id):
            groups[key] = item
    options = tuple(
        sorted(
            deck if maximum_uses is not None else groups.values(),
            key=lambda item: (
                require_planned_load(item).value,
                item.discipline.value,
                str(item.id),
            ),
        )
    )
    sports = tuple(Discipline)
    prefix_counts = tuple(
        sum(item.discipline is sport for item in prefix) for sport in sports
    )
    prefix_high_counts = tuple(
        sum(
            item.discipline is sport and item.intensity_bucket is IntensityBucket.HIGH
            for item in prefix
        )
        for sport in sports
    )
    limited_ids = tuple(
        sorted(
            (
                template_id
                for template_id, limit in (maximum_uses or {}).items()
                if limit < (required_count or 24)
            ),
            key=str,
        )
    )
    prefix_limited_counts = tuple(
        sum(item.id == template_id for item in prefix) for template_id in limited_ids
    )
    prefix_total = sum(
        (require_planned_load(item).value for item in prefix), Decimal(0)
    )
    prefix_high = sum(
        (
            require_planned_load(item).value
            for item in prefix
            if item.intensity_bucket is IntensityBucket.HIGH
        ),
        Decimal(0),
    )
    prefix_z5 = any(_has_zone_five(item) for item in prefix)
    if prefix_high > budget and phase is TrainingPhase.BUILD:
        return None
    states: dict[
        tuple[
            Decimal,
            Decimal,
            tuple[int, ...],
            tuple[int, ...],
            tuple[int, ...],
            bool,
        ],
        tuple[WorkoutTemplate, ...],
    ] = {
        (
            prefix_total,
            prefix_high,
            prefix_counts,
            prefix_high_counts,
            prefix_limited_counts,
            prefix_z5,
        ): prefix
    }
    best: tuple[WorkoutTemplate, ...] | None = None
    best_key: tuple[Decimal, Decimal, int, tuple[str, ...]] | None = None
    max_count = required_count if required_count is not None else 24
    max_total = target.value + max(require_planned_load(item).value for item in deck)
    for count in range(len(prefix), max_count + 1):
        for (
            total,
            high,
            counts,
            high_counts,
            limited_counts,
            has_z5,
        ), selection in states.items():
            if required_count is not None and count != required_count:
                continue
            if not all(
                counts[sports.index(sport)] > 0 for sport in required_disciplines
            ):
                continue
            if required_composition is not None and any(
                counts[index] != required_composition.get(sport, 0)
                for index, sport in enumerate(sports)
            ):
                continue
            if not _selection_policy_valid(
                selection,
                target=target,
                phase=phase,
                build_week=build_week,
                desired_high_fraction=desired_high_fraction,
                high_available=high_available,
                z5_available=z5_available,
                minimum_load=minimum_load,
                discipline_caps=discipline_caps,
            ):
                continue
            score = (
                abs(total - target.value),
                abs(high - budget) if phase is TrainingPhase.BUILD else Decimal(0),
                count,
                tuple(str(item.id) for item in selection),
            )
            if (best_key is None or score < best_key) and (
                feasible is None or feasible(selection)
            ):
                best, best_key = selection, score
        if count == max_count or (best_key is not None and best_key[0] == 0):
            break
        next_states: dict[
            tuple[
                Decimal,
                Decimal,
                tuple[int, ...],
                tuple[int, ...],
                tuple[int, ...],
                bool,
            ],
            tuple[WorkoutTemplate, ...],
        ] = {}
        for (
            total,
            high,
            counts,
            high_counts,
            limited_counts,
            has_z5,
        ), selection in states.items():
            for item in options:
                if maximum_uses is not None and sum(
                    existing.id == item.id for existing in selection
                ) >= maximum_uses.get(item.id, 24):
                    continue
                new_total = total + require_planned_load(item).value
                if new_total > max_total:
                    continue
                new_high = high + (
                    require_planned_load(item).value
                    if item.intensity_bucket is IntensityBucket.HIGH
                    else Decimal(0)
                )
                if phase is TrainingPhase.BUILD and new_high > budget:
                    continue
                index = sports.index(item.discipline)
                new_counts = counts[:index] + (counts[index] + 1,) + counts[index + 1 :]
                new_high_counts = (
                    high_counts[:index]
                    + (
                        high_counts[index]
                        + (item.intensity_bucket is IntensityBucket.HIGH),
                    )
                    + high_counts[index + 1 :]
                )
                if required_composition is not None and new_counts[
                    index
                ] > required_composition.get(item.discipline, 0):
                    continue
                if discipline_caps is not None and item.discipline in discipline_caps:
                    sport_total = (
                        sum(
                            (
                                require_planned_load(existing).value
                                for existing in selection
                                if existing.discipline is item.discipline
                            ),
                            Decimal(0),
                        )
                        + require_planned_load(item).value
                    )
                    if sport_total > discipline_caps[item.discipline].value:
                        continue
                new_z5 = has_z5 or _has_zone_five(item)
                new_limited_counts = tuple(
                    value + (item.id == template_id)
                    for template_id, value in zip(
                        limited_ids, limited_counts, strict=True
                    )
                )
                state = (
                    new_total,
                    new_high,
                    new_counts,
                    new_high_counts,
                    new_limited_counts,
                    new_z5,
                )
                path = selection + (item,)
                previous = next_states.get(state)
                if previous is None or tuple(str(value.id) for value in path) < tuple(
                    str(value.id) for value in previous
                ):
                    next_states[state] = path
        states = next_states
        if not states:
            break
    return best


def select_workouts(
    *,
    deck: tuple[WorkoutTemplate, ...],
    required_disciplines: frozenset[Discipline],
    target: InternalLoad,
    desired_high_fraction: Fraction = STANDARD_RACE_INTENSITY_TARGET.high_fraction,
    selected_template_ids: Collection[UUID] | None = None,
    maintenance_active: bool = False,
    phase: TrainingPhase = TrainingPhase.BASE,
    build_week: int | None = None,
    required_count: int | None = None,
    required_composition: Mapping[Discipline, int] | None = None,
    selected_occurrence_ids: Collection[UUID] | None = None,
    discipline_caps: Mapping[Discipline, InternalLoad] | None = None,
    feasible: Callable[[tuple[WorkoutTemplate, ...]], bool] | None = None,
) -> tuple[SelectedWorkout, ...]:
    """Select an explicit valid deck or the closest discipline-covering subset."""
    by_id = {template.id: template for template in deck}
    if selected_template_ids is not None:
        missing = set(selected_template_ids) - set(by_id)
        if missing:
            raise PlanningConstraintError(
                "template_not_eligible",
                "One or more selected workout templates are not eligible.",
            )
        chosen = tuple(by_id[template_id] for template_id in selected_template_ids)
        automatic = tuple(item for item in deck if not item.explicit_scheduling_only)
        if not automatic or not _selection_policy_valid(
            chosen,
            target=target,
            phase=phase,
            build_week=build_week,
            desired_high_fraction=desired_high_fraction,
            high_available=any(
                item.intensity_bucket is IntensityBucket.HIGH
                and require_planned_load(item).value
                <= target.value * desired_high_fraction.value
                for item in automatic
            ),
            z5_available=build_week == 4
            and any(
                item.intensity_bucket is IntensityBucket.HIGH
                and require_planned_load(item).value
                <= target.value * desired_high_fraction.value
                and _has_zone_five(item)
                for item in automatic
            ),
            minimum_load=min(require_planned_load(item).value for item in automatic),
            discipline_caps=discipline_caps,
        ):
            raise PlanningConstraintError(
                "swipe_selection_invalid",
                "The selected workout combination does not fit this week.",
            )
    else:
        deck = tuple(
            template for template in deck if not template.explicit_scheduling_only
        )
        fitted = _bounded_selection(
            deck=deck,
            prefix=(),
            required_disciplines=required_disciplines,
            target=target,
            phase=phase,
            build_week=build_week,
            desired_high_fraction=desired_high_fraction,
            required_count=required_count,
            required_composition=required_composition,
            discipline_caps=discipline_caps,
            feasible=feasible,
        )
        if fitted is None:
            raise PlanningConstraintError(
                "catalog_capacity_unsatisfied",
                "No safe workout combination fits the current week.",
            )
        chosen = fitted
    if {item.discipline for item in chosen} < required_disciplines:
        raise PlanningConstraintError(
            "discipline_selection_incomplete",
            "The selected workouts do not cover every eligible discipline.",
        )
    occurrence_ids = tuple(selected_occurrence_ids or ())
    if occurrence_ids and len(occurrence_ids) != len(chosen):
        raise PlanningConstraintError(
            "swipe_selection_invalid",
            "The selected card identities do not match the workout selection.",
        )
    if len(set(occurrence_ids)) != len(occurrence_ids):
        raise PlanningConstraintError(
            "swipe_selection_invalid",
            "Workout card identities must be distinct.",
        )
    return tuple(
        SelectedWorkout(
            discipline=template.discipline,
            snapshot=snapshot_template(template),
            occurrence_id=occurrence_ids[index] if occurrence_ids else None,
        )
        for index, template in enumerate(chosen)
    )


def remaining_workout_deck(
    *,
    deck: tuple[WorkoutTemplate, ...],
    target: InternalLoad,
    selected_template_ids: Collection[UUID],
) -> tuple[WorkoutTemplate, ...]:
    """Recalculate the remaining deck against an exact authoritative selection."""
    if len(set(selected_template_ids)) != len(selected_template_ids):
        raise PlanningConstraintError(
            "duplicate_template_selection",
            "A template can be selected only once per revision.",
        )
    by_id = {template.id: template for template in deck}
    if not set(selected_template_ids) <= set(by_id):
        raise PlanningConstraintError(
            "template_not_eligible",
            "One or more selected workout templates are not eligible.",
        )
    selected_load = sum(
        (
            require_planned_load(by_id[template_id]).value
            for template_id in selected_template_ids
        ),
        Decimal(0),
    )
    return tuple(
        template
        for template in deck
        if template.id not in selected_template_ids
        and selected_load + require_planned_load(template).value <= target.value
    )


def canonical_schedule_instant(
    scheduled_date: date,
    *,
    timezone_name: str,
) -> datetime:
    """Return an internal noon projection for legacy elapsed-hour comparisons.

    The athlete-facing schedule owns only ``scheduled_date``. Noon is not a
    prescribed training time; it is a stable internal projection that lets the
    separately approved 72-hour rule remain elapsed-time based.
    """

    return datetime.combine(scheduled_date, time(hour=12), ZoneInfo(timezone_name))


def schedule_workouts(
    *,
    selected: tuple[SelectedWorkout, ...],
    available_dates: tuple[date, ...],
    week_start: date,
    timezone_name: str,
    fixed_template_dates: Mapping[UUID, date] | None = None,
    fixed_occurrence_dates: Mapping[UUID, date] | None = None,
) -> tuple[ProposedWorkout, ...]:
    """Place deterministic snapshots on explicit athlete-local dates.

    Available dates describe when the athlete can train, not a one-workout-per-
    day capacity. Automatic placement spreads workouts as evenly as possible;
    constrained availability and explicit fixed placements may consolidate
    multiple workouts on one date.
    """
    if not available_dates:
        raise PlanningConstraintError(
            "availability_required",
            "At least one available date is required for auto-scheduling.",
        )
    if len(set(available_dates)) != len(available_dates):
        raise PlanningConstraintError(
            "duplicate_available_date",
            "Available dates must be unique.",
        )
    fixed = dict(fixed_template_dates or {})
    fixed.update(fixed_occurrence_dates or {})
    selected_ids = {
        identity
        for workout in selected
        for identity in (workout.snapshot.template_id, workout.occurrence_id)
        if identity is not None
    }
    if not set(fixed) <= selected_ids:
        raise PlanningConstraintError(
            "fixed_template_not_selected",
            "A fixed workout date must reference an accepted workout.",
        )
    week_dates = {week_start + timedelta(days=offset) for offset in range(7)}
    if not set(available_dates) <= week_dates:
        raise PlanningConstraintError(
            "availability_outside_week",
            "Available dates must fall inside the requested athlete week.",
        )
    if not set(fixed.values()) <= set(available_dates):
        raise PlanningConstraintError(
            "fixed_date_unavailable",
            "Every fixed workout date must be one of the available dates.",
        )

    ordered = sorted(
        selected,
        key=lambda item: (
            item.snapshot.intensity_bucket is not IntensityBucket.HIGH,
            item.discipline.value,
            str(item.snapshot.template_id),
        ),
    )
    sorted_dates = tuple(sorted(available_dates))

    def maximum_consecutive_rest_days(training_days: set[date]) -> int:
        consecutive_rest = 0
        maximum_rest = 0
        for offset in range(7):
            if week_start + timedelta(days=offset) in training_days:
                consecutive_rest = 0
            else:
                consecutive_rest += 1
                maximum_rest = max(maximum_rest, consecutive_rest)
        return maximum_rest

    def rest_limit_is_feasible(workout_count: int) -> bool:
        """Return whether this selection can occupy enough available dates.

        Availability alone is not sufficient: a one-workout prescription cannot
        use three available dates. Treating every available date as a training
        date made ordinary low-volume weeks fail before workout selection even
        though the approved rule is best-effort when the requested week cannot
        realize the spacing.
        """

        maximum_training_days = min(workout_count, len(sorted_dates))
        return any(
            maximum_consecutive_rest_days(set(training_dates)) <= 3
            for count in range(1, maximum_training_days + 1)
            for training_dates in combinations(sorted_dates, count)
        )

    # Do not reject a plan when its selected workout count and confirmed
    # availability cannot realize the rest spacing. A manual fixed placement is
    # also an explicit athlete choice and may intentionally consolidate the week.
    enforce_rest_limit = not fixed and rest_limit_is_feasible(len(ordered))
    assigned: list[ProposedWorkout] = []
    usage = {scheduled_date: 0 for scheduled_date in sorted_dates}

    def find_schedule(index: int) -> tuple[ProposedWorkout, ...] | None:
        if index == len(ordered):
            if (
                enforce_rest_limit
                and maximum_consecutive_rest_days(
                    {workout.scheduled_date for workout in assigned}
                )
                > 3
            ):
                return None
            return tuple(sorted(assigned, key=lambda item: item.scheduled_date))

        workout = ordered[index]
        fixed_date = fixed.get(workout.occurrence_id or workout.snapshot.template_id)
        candidate_dates = (
            (fixed_date,)
            if fixed_date is not None
            else tuple(
                sorted(
                    sorted_dates,
                    key=lambda value: (
                        usage[value],
                        maximum_consecutive_rest_days(
                            {item.scheduled_date for item in assigned} | {value}
                        ),
                        value,
                    ),
                )
            )
        )
        for assigned_day in candidate_dates:
            proposal = ProposedWorkout(
                discipline=workout.discipline,
                snapshot=workout.snapshot,
                scheduled_date=assigned_day,
                occurrence_id=workout.occurrence_id,
            )
            candidate = (*assigned, proposal)
            violations = find_anti_stack_violations(
                tuple(
                    ScheduledWorkout(
                        workout_id=str(item.occurrence_id or item.snapshot.template_id),
                        disciplines=frozenset({item.discipline}),
                        intensity=item.snapshot.intensity_bucket,
                        starts_at=canonical_schedule_instant(
                            item.scheduled_date,
                            timezone_name=timezone_name,
                        ),
                    )
                    for item in candidate
                )
            )
            if violations:
                continue
            assigned.append(proposal)
            usage[assigned_day] += 1
            result = find_schedule(index + 1)
            usage[assigned_day] -= 1
            assigned.pop()
            if result is not None:
                return result
        return None

    proposed = find_schedule(0)
    if proposed is not None:
        return proposed
    raise PlanningConstraintError(
        "rest_or_anti_stack_unsatisfied",
        "The generated schedule cannot satisfy rest-day and anti-stack constraints.",
    )


def _workout_intensity(workout: ProposedWorkout) -> WorkoutIntensity | None:
    # The imported catalog bucket owns the complete workout's weekly 80/20
    # allocation. Segment zones remain execution detail only.
    duration = workout.snapshot.duration_minutes
    if duration is None:
        return None
    return WorkoutIntensity(
        (
            IntensitySegment(
                duration=DurationMinutes(duration),
                zone=(
                    TrainingZone.ZONE_3
                    if workout.snapshot.intensity_bucket is IntensityBucket.HIGH
                    else TrainingZone.ZONE_1
                ),
            ),
        )
    )


def _schedule_is_feasible(
    *,
    selection: tuple[WorkoutTemplate, ...],
    week_start: date,
    available_dates: tuple[date, ...],
    timezone_name: str,
) -> bool:
    try:
        schedule_workouts(
            selected=tuple(
                SelectedWorkout(item.discipline, snapshot_template(item))
                for item in selection
            ),
            available_dates=available_dates,
            week_start=week_start,
            timezone_name=timezone_name,
        )
    except PlanningConstraintError:
        return False
    return True


def build_weekly_plan(
    *,
    week_start: date,
    timezone_name: str,
    race_date: date,
    catalog: tuple[WorkoutTemplate, ...],
    prior_loads: tuple[PlanLoadSample, ...],
    goal_disciplines: frozenset[Discipline],
    confirmed_injuries: frozenset[Discipline],
    low_only_disciplines: frozenset[Discipline] = frozenset(),
    cross_training_opt_ins: frozenset[Discipline] = frozenset(),
    zone_capabilities: Mapping[Discipline, ZoneCapability],
    available_dates: tuple[date, ...],
    selected_template_ids: Collection[UUID] | None = None,
    fixed_template_dates: Mapping[UUID, date] | None = None,
    selected_occurrence_ids: Collection[UUID] | None = None,
    fixed_occurrence_dates: Mapping[UUID, date] | None = None,
    maintenance_active: bool = False,
    onboarding_baseline: StartingBaseline | None = None,
) -> WeeklyPlanDraft:
    """Build a deterministic, TSS-private plan ready to remain pending."""
    prior_loads = tuple(sample for sample in prior_loads if not sample.sick_week)
    uninjured = goal_disciplines - confirmed_injuries
    historical_recipients = frozenset(
        sport
        for sport in (Discipline.BIKE, Discipline.SWIM)
        if sport not in confirmed_injuries
        and sport in zone_capabilities
        and (
            any(
                sample.discipline_loads.get(sport, InternalLoad(Decimal(0))).value > 0
                for sample in prior_loads
            )
            or (
                onboarding_baseline is not None
                and onboarding_baseline.by_discipline.get(
                    sport, InternalLoad(Decimal(0))
                ).value
                > 0
            )
        )
    )
    if not uninjured and not historical_recipients:
        phase = _training_phase(
            _race_anchored_phase(week_start=week_start, race_date=race_date),
            first_plan=not prior_loads,
        )
        return WeeklyPlanDraft(
            target=PlanningTarget(
                phase=phase,
                basis=PlanningTargetBasis.INJURY_REST_ONLY,
                target=InternalLoad(Decimal(0)),
            ),
            workouts=(),
            warnings=(
                PlanningWarning(
                    rule_id=RuleId.INJURY_REDISTRIBUTION,
                    code="all_disciplines_blocked_rest_only",
                    message=(
                        "Every goal discipline is currently blocked. This pending "
                        "revision contains rest only and requires your confirmation."
                    ),
                ),
            ),
            total_duration_minutes=Decimal(0),
            low_intensity_percent=Decimal(0),
            high_intensity_percent=Decimal(0),
            planned_load=InternalLoad(Decimal(0)),
        )

    if (
        not prior_loads
        and onboarding_baseline is not None
        and not onboarding_baseline.zero_base
        and any(
            onboarding_baseline.by_discipline[sport].value == 0 for sport in uninjured
        )
    ):
        raise PlanningConstraintError(
            "zero_history_discipline_baseline_unavailable",
            "The catalog cannot fill this composition without an approved "
            "starting target for the untrained discipline.",
        )

    # The first target must be seeded without fabricating realized load. Use the
    # latest eligible catalog's hidden load as a deterministic bootstrap.
    initial_candidates = tuple(
        as_rpe_guided_template(template)
        if zone_capabilities[template.discipline].rpe_guided
        else template
        for template in catalog
        if template.internal_planned_load is not None
        and template.discipline in uninjured | historical_recipients
        and not template.explicit_scheduling_only
        and not (
            template.discipline in low_only_disciplines
            and template.intensity_bucket is IntensityBucket.HIGH
        )
        and template.discipline in zone_capabilities
        and {
            segment.protocol_target.protocol_id
            for segment in template.segments
            if segment.protocol_target is not None
        }.issubset(zone_capabilities[template.discipline].protocol_ids)
        and (
            zone_capabilities[template.discipline].rpe_guided
            or (
                set(template.zone_requirements).issubset(
                    zone_capabilities[template.discipline].requirements
                )
                and (
                    not zone_capabilities[template.discipline].fallback_active
                    or template.fallback_compatibility
                    is FallbackCompatibility.COMPATIBLE
                )
            )
        )
    )
    if not initial_candidates:
        raise PlanningConstraintError(
            "catalog_empty",
            "No workout templates match the confirmed athlete configuration.",
        )
    cheapest_by_discipline = {
        discipline: min(
            (
                template
                for template in initial_candidates
                if template.discipline is discipline
            ),
            key=lambda item: (require_planned_load(item).value, str(item.id)),
        )
        for discipline in uninjured
        if any(template.discipline is discipline for template in initial_candidates)
    }
    if set(cheapest_by_discipline) != set(uninjured):
        raise PlanningConstraintError(
            "catalog_coverage_unsatisfied",
            "The current catalog cannot cover every uninjured goal discipline.",
        )
    initial_load = InternalLoad(
        sum(
            (
                require_planned_load(template).value
                for template in cheapest_by_discipline.values()
            ),
            Decimal(0),
        )
    )
    if onboarding_baseline is not None:
        if not prior_loads and confirmed_injuries and onboarding_baseline.zero_base:
            raise PlanningConstraintError(
                "restricted_zero_base_allocation_unavailable",
                "A reviewed starting allocation is required for this restricted "
                "introduction week.",
            )
        initial_load = onboarding_baseline.total
    target = resolve_target(
        week_start=week_start,
        race_date=race_date,
        prior_loads=prior_loads,
        initial_catalog_load=initial_load,
        maintenance_active=maintenance_active,
    )
    desired_high_fraction = _desired_high_fraction(
        target=target,
        prior_loads=prior_loads,
    )
    target = PlanningTarget(
        phase=target.phase,
        basis=target.basis,
        target=target.target,
        taper_period=target.taper_period,
        desired_high_fraction=desired_high_fraction,
        manual_review_required=target.manual_review_required,
        build_week=(
            _build_week(week_start=week_start, race_date=race_date)
            if target.phase is TrainingPhase.BUILD
            else None
        ),
    )
    planning_disciplines = uninjured
    replacement_disciplines: frozenset[Discipline] = frozenset()
    if confirmed_injuries:
        eligible_recipients = frozenset(
            template.discipline
            for template in eligible_workouts(
                catalog=catalog,
                phase=target.phase,
                goal_disciplines=frozenset({Discipline.BIKE, Discipline.SWIM}),
                confirmed_injuries=confirmed_injuries,
                low_only_disciplines=frozenset({Discipline.BIKE, Discipline.SWIM}),
                zone_capabilities=zone_capabilities,
                build_week=target.build_week,
            )
            if not template.explicit_scheduling_only
        )
        target, planning_disciplines, replacement_disciplines = _injury_adjusted_target(
            target=target,
            prior_loads=prior_loads,
            onboarding_baseline=onboarding_baseline,
            blocked=confirmed_injuries,
            goal_disciplines=goal_disciplines,
            eligible_recipients=eligible_recipients,
            cross_training_opt_ins=cross_training_opt_ins,
            desired_high_fraction=desired_high_fraction,
        )
        if target.target.value == 0:
            return WeeklyPlanDraft(
                target=PlanningTarget(
                    phase=target.phase,
                    basis=PlanningTargetBasis.INJURY_REST_ONLY,
                    target=InternalLoad(Decimal(0)),
                ),
                workouts=(),
                warnings=(
                    PlanningWarning(
                        rule_id=RuleId.INJURY_REDISTRIBUTION,
                        code="all_disciplines_blocked_rest_only",
                        message=(
                            "No safe training remains under the confirmed restriction."
                        ),
                    ),
                ),
                total_duration_minutes=Decimal(0),
                low_intensity_percent=Decimal(0),
                high_intensity_percent=Decimal(0),
                planned_load=InternalLoad(Decimal(0)),
            )
    restricted_low_only = low_only_disciplines | replacement_disciplines
    deck = eligible_workouts(
        catalog=catalog,
        phase=target.phase,
        goal_disciplines=planning_disciplines,
        confirmed_injuries=confirmed_injuries,
        low_only_disciplines=restricted_low_only,
        zone_capabilities=zone_capabilities,
        build_week=target.build_week,
    )
    covered_disciplines = {template.discipline for template in deck}
    missing_disciplines = planning_disciplines - covered_disciplines
    if missing_disciplines:
        missing_labels = ", ".join(
            sorted(discipline.value for discipline in missing_disciplines)
        )
        if target.phase is TrainingPhase.TAPER:
            raise PlanningConstraintError(
                "taper_catalog_coverage_unavailable",
                "No reviewed taper workout is available for: "
                f"{missing_labels}. This pre-race week cannot be generated yet.",
            )
        raise PlanningConstraintError(
            "catalog_phase_coverage_unavailable",
            f"No reviewed {target.phase.value} workout is available for: "
            f"{missing_labels}.",
        )
    fixed_dates = dict(fixed_template_dates or {})
    if selected_template_ids is not None:
        selected_ids = set(selected_template_ids)
        explicit_ids = {
            template.id
            for template in deck
            if template.id in selected_ids and template.explicit_scheduling_only
        }
        if not explicit_ids <= set(fixed_dates):
            raise PlanningConstraintError(
                "explicit_test_date_required",
                "Every explicitly scheduled field test requires an exact date.",
            )
    selected = select_workouts(
        deck=deck,
        required_disciplines=planning_disciplines,
        target=target.target,
        desired_high_fraction=target.desired_high_fraction,
        selected_template_ids=selected_template_ids,
        selected_occurrence_ids=selected_occurrence_ids,
        phase=target.phase,
        build_week=target.build_week,
        discipline_caps=target.discipline_caps,
        feasible=(
            (
                lambda selection: _schedule_is_feasible(
                    selection=selection,
                    week_start=week_start,
                    available_dates=available_dates,
                    timezone_name=timezone_name,
                )
            )
            if target.phase is TrainingPhase.BUILD
            else None
        ),
    )
    proposed = schedule_workouts(
        selected=selected,
        available_dates=available_dates,
        week_start=week_start,
        timezone_name=timezone_name,
        fixed_template_dates=fixed_dates,
        fixed_occurrence_dates=fixed_occurrence_dates,
    )
    timed_intensities = tuple(
        intensity
        for workout in proposed
        if (intensity := _workout_intensity(workout)) is not None
    )
    distribution = calculate_time_distribution(timed_intensities)
    low_intensity_percent = (
        distribution.low_fraction.value * Decimal(100)
        if distribution.low_fraction is not None
        else Decimal(0)
    )
    high_intensity_percent = (
        distribution.high_fraction.value * Decimal(100)
        if distribution.high_fraction is not None
        else Decimal(0)
    )
    planned_load = InternalLoad(
        sum(
            (require_planned_load(workout.snapshot).value for workout in proposed),
            Decimal(0),
        )
    )
    warnings: list[PlanningWarning] = []
    if any(workout.snapshot.duration_minutes is None for workout in proposed):
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.SOFT_BOUNDARIES,
                code="distance_only_swim_excluded_from_time_ratio",
                message=(
                    "Afstandsgestuurde zwemtrainingen staan in meters in het plan; "
                    "de 80/20-tijdverdeling bevat alleen trainingen met een "
                    "vastgelegde duur."
                ),
                severity="info",
            )
        )
    if len({workout.scheduled_date for workout in proposed}) < len(proposed):
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.SOFT_BOUNDARIES,
                code="workouts_consolidated_on_available_dates",
                message=(
                    "Multiple workouts share a confirmed training date so the "
                    "weekly training combination still fits your availability."
                ),
            )
        )
    if (
        target.desired_high_fraction.value
        < STANDARD_RACE_INTENSITY_TARGET.high_fraction.value
    ):
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.SOFT_BOUNDARIES,
                code="realized_intensity_debt_applied",
                message=(
                    "Reliable activity data reduced the high-intensity target for "
                    "this first eligible week."
                ),
            )
        )
    if target.manual_review_required:
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.SOFT_BOUNDARIES,
                code="manual_review_required",
                message=(
                    "No safe positive regular target was available. This recovery "
                    "proposal requires your confirmation or qualified review."
                ),
            )
        )
    if planned_load.value != target.target.value:
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.PROGRESSIVE_LOAD,
                code="target_outside_catalog_capacity",
                message=(
                    "The reviewed workout deck does not exactly match the weekly "
                    "target."
                ),
            )
        )
    if confirmed_injuries:
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.INJURY_REDISTRIBUTION,
                code="injured_disciplines_excluded",
                message="Confirmed injured disciplines were excluded from this plan.",
            )
        )
        if target.injury_load_unallocated:
            warnings.append(
                PlanningWarning(
                    rule_id=RuleId.INJURY_REDISTRIBUTION,
                    code="injury_replacement_capacity_limited",
                    message=(
                        "Only the alternative training that fits your current "
                        "training history was included."
                    ),
                    severity="info",
                )
            )
        if target.cross_training_consent_required:
            warnings.append(
                PlanningWarning(
                    rule_id=RuleId.INJURY_REDISTRIBUTION,
                    code="cross_training_choice_available",
                    message=(
                        "You can explicitly choose an available alternative "
                        "sport for cross-training; a safe starting capacity "
                        "is still required."
                    ),
                    severity="info",
                )
            )
    if low_only_disciplines:
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.INJURY_REDISTRIBUTION,
                code="restricted_disciplines_low_only",
                message=(
                    "High-intensity workouts were excluded for disciplines limited "
                    "to low-intensity training."
                ),
            )
        )
    total_duration = sum(
        (
            workout.snapshot.duration_minutes
            for workout in proposed
            if workout.snapshot.duration_minutes is not None
        ),
        Decimal(0),
    )
    return WeeklyPlanDraft(
        target=target,
        workouts=proposed,
        warnings=tuple(warnings),
        total_duration_minutes=total_duration,
        low_intensity_percent=low_intensity_percent,
        high_intensity_percent=high_intensity_percent,
        planned_load=planned_load,
    )


def validate_manual_schedule(
    *,
    workouts: tuple[ScheduledWorkout, ...],
    moved_workout_id: str | None,
) -> tuple[PlanningWarning, ...]:
    """Reject hard spacing violations for generated and direct placements."""
    violations = find_anti_stack_violations(workouts)
    if any(
        moved_workout_id is None
        or moved_workout_id
        in {violation.earlier_workout_id, violation.later_workout_id}
        for violation in violations
    ):
        raise PlanningConstraintError(
            "anti_stack_violation",
            "High-intensity workouts need more time between sessions.",
        )
    return ()


def as_utc(value: datetime) -> datetime:
    """Normalize persisted instants while retaining timezone-aware semantics."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Schedule instants must be timezone-aware.")
    return value.astimezone(timezone.utc)
