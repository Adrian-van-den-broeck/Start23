"""Framework-independent deterministic weekly planning policies."""

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from itertools import combinations, permutations
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
from app.modules.physiology.intensity import (
    STANDARD_RACE_INTENSITY_TARGET,
    IntensitySegment,
    WorkoutIntensity,
    calculate_time_distribution,
)
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


@dataclass(frozen=True, slots=True)
class PlanningTarget:
    """Hidden weekly load target plus public phase context."""

    phase: TrainingPhase
    basis: PlanningTargetBasis
    target: InternalLoad = field(repr=False)
    taper_period: TaperPeriod | None = None
    desired_high_fraction: Fraction = STANDARD_RACE_INTENSITY_TARGET.high_fraction
    manual_review_required: bool = False


@dataclass(frozen=True, slots=True)
class SelectedWorkout:
    """One catalog snapshot selected for the proposed revision."""

    discipline: Discipline
    snapshot: PlannedWorkoutSnapshot


@dataclass(frozen=True, slots=True)
class ProposedWorkout:
    """One selected immutable workout on an athlete-local calendar date."""

    discipline: Discipline
    snapshot: PlannedWorkoutSnapshot
    scheduled_date: date


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
    if weeks_before_race in {1, 2}:
        return WeekPhase.TAPER
    return WeekPhase.RECOVERY if weeks_before_race % 5 == 0 else WeekPhase.BUILD


def resolve_target(
    *,
    week_start: date,
    race_date: date,
    prior_loads: tuple[PlanLoadSample, ...],
    initial_catalog_load: InternalLoad,
    maintenance_active: bool = False,
) -> PlanningTarget:
    """Resolve taper, recovery, and fail-safe pre-Phase-7 target context."""
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

    race_week_start = race_date - timedelta(days=race_date.weekday())
    weeks_before_race = (race_week_start - week_start).days // 7
    taper_period = {
        2: TaperPeriod.A_T_MINUS_2,
        1: TaperPeriod.A_T_MINUS_1,
    }.get(weeks_before_race)
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
    phase = _training_phase(week_phase, first_plan=not prior_loads)
    if week_phase is WeekPhase.RECOVERY:
        if not prior_loads:
            raise PlanningConstraintError(
                "recovery_baseline_unavailable",
                "A recovery week requires a prior planned-load snapshot.",
            )
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
            latest.week_start == week_start - timedelta(days=7)
            and latest.completed_activity_count == 0
        ):
            restart_samples = prior_loads[-4:]
            if len(restart_samples) != 4 or any(
                sample.realized_load is None for sample in restart_samples
            ):
                raise PlanningConstraintError(
                    "inactive_restart_baseline_unavailable",
                    "Restart planning requires four complete local training weeks.",
                )
            restart_target = InternalLoad(
                sum(
                    (
                        sample.realized_load.value
                        for sample in restart_samples
                        if sample.realized_load is not None
                    ),
                    Decimal(0),
                )
                / Decimal(4)
            )
            return PlanningTarget(
                phase=phase,
                basis=PlanningTargetBasis.INACTIVE_RESTART,
                target=restart_target,
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


def eligible_workouts(
    *,
    catalog: tuple[WorkoutTemplate, ...],
    phase: TrainingPhase,
    goal_disciplines: frozenset[Discipline],
    confirmed_injuries: frozenset[Discipline],
    low_only_disciplines: frozenset[Discipline] = frozenset(),
    zone_capabilities: Mapping[Discipline, ZoneCapability],
) -> tuple[WorkoutTemplate, ...]:
    """Filter immutable catalog versions by phase, injury, goal, and zones."""
    eligible: list[WorkoutTemplate] = []
    for template in catalog:
        if (
            template.discipline not in goal_disciplines
            or template.discipline in confirmed_injuries
            or phase not in template.training_phases
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
        if not capability.rpe_guided and not set(template.zone_requirements).issubset(
            capability.requirements
        ):
            continue
        eligible.append(
            as_rpe_guided_template(template) if capability.rpe_guided else template
        )
    return tuple(
        sorted(
            eligible,
            key=lambda item: (
                item.discipline.value,
                item.internal_planned_load.value,
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
        (template.internal_planned_load.value for template in selection),
        Decimal(0),
    )
    total_duration = sum(
        (template.duration_minutes for template in selection), Decimal(0)
    )
    high_duration = sum(
        (
            template.duration_minutes
            for template in selection
            if template.intensity_bucket is IntensityBucket.HIGH
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


def select_workouts(
    *,
    deck: tuple[WorkoutTemplate, ...],
    required_disciplines: frozenset[Discipline],
    target: InternalLoad,
    desired_high_fraction: Fraction = STANDARD_RACE_INTENSITY_TARGET.high_fraction,
    selected_template_ids: Collection[UUID] | None = None,
    maintenance_active: bool = False,
) -> tuple[SelectedWorkout, ...]:
    """Select an explicit valid deck or the closest discipline-covering subset."""
    by_id = {template.id: template for template in deck}
    if selected_template_ids is not None:
        if len(set(selected_template_ids)) != len(selected_template_ids):
            raise PlanningConstraintError(
                "duplicate_template_selection",
                "A template can be selected only once per revision.",
            )
        missing = set(selected_template_ids) - set(by_id)
        if missing:
            raise PlanningConstraintError(
                "template_not_eligible",
                "One or more selected workout templates are not eligible.",
            )
        chosen = tuple(by_id[template_id] for template_id in selected_template_ids)
    else:
        deck = tuple(
            template for template in deck if not template.explicit_scheduling_only
        )
        candidates: list[tuple[WorkoutTemplate, ...]] = []
        for count in range(1, len(deck) + 1):
            for selection in combinations(deck, count):
                if {item.discipline for item in selection} >= required_disciplines:
                    candidates.append(selection)
        if not candidates:
            raise PlanningConstraintError(
                "catalog_coverage_unsatisfied",
                "The current workout catalog cannot cover every eligible discipline.",
            )
        chosen = min(
            candidates,
            key=lambda selection: _selection_key(
                selection,
                target=target,
                desired_high_fraction=desired_high_fraction,
            ),
        )
    if {item.discipline for item in chosen} < required_disciplines:
        raise PlanningConstraintError(
            "discipline_selection_incomplete",
            "The selected workouts do not cover every eligible discipline.",
        )
    return tuple(
        SelectedWorkout(
            discipline=template.discipline,
            snapshot=snapshot_template(template),
        )
        for template in chosen
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
            by_id[template_id].internal_planned_load.value
            for template_id in selected_template_ids
        ),
        Decimal(0),
    )
    return tuple(
        template
        for template in deck
        if template.id not in selected_template_ids
        and selected_load + template.internal_planned_load.value <= target.value
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
) -> tuple[ProposedWorkout, ...]:
    """Place deterministic snapshots on explicit athlete-local dates."""
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
    selected_ids = {workout.snapshot.template_id for workout in selected}
    if not set(fixed) <= selected_ids:
        raise PlanningConstraintError(
            "fixed_template_not_selected",
            "A fixed workout date must reference an explicitly selected template.",
        )
    if len(set(fixed.values())) != len(fixed):
        raise PlanningConstraintError(
            "fixed_dates_conflict",
            "Two fixed workouts cannot use the same training date.",
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
    if len(available_dates) < len(ordered):
        raise PlanningConstraintError(
            "availability_unsatisfied",
            "The selected workouts require availability on more training days.",
        )

    for assigned_days in permutations(sorted(available_dates), len(ordered)):
        if any(
            fixed.get(workout.snapshot.template_id, assigned_day) != assigned_day
            for workout, assigned_day in zip(ordered, assigned_days, strict=True)
        ):
            continue
        proposed = [
            ProposedWorkout(
                discipline=workout.discipline,
                snapshot=workout.snapshot,
                scheduled_date=assigned_day,
            )
            for workout, assigned_day in zip(ordered, assigned_days, strict=True)
        ]
        training_days = {workout.scheduled_date for workout in proposed}
        consecutive_rest = 0
        maximum_rest = 0
        for offset in range(7):
            if week_start + timedelta(days=offset) in training_days:
                consecutive_rest = 0
            else:
                consecutive_rest += 1
                maximum_rest = max(maximum_rest, consecutive_rest)
        if maximum_rest > 3:
            continue
        violations = find_anti_stack_violations(
            tuple(
                ScheduledWorkout(
                    workout_id=str(workout.snapshot.template_id),
                    disciplines=frozenset({workout.discipline}),
                    intensity=workout.snapshot.intensity_bucket,
                    starts_at=canonical_schedule_instant(
                        workout.scheduled_date,
                        timezone_name=timezone_name,
                    ),
                )
                for workout in proposed
            )
        )
        if not violations:
            return tuple(sorted(proposed, key=lambda item: item.scheduled_date))
    raise PlanningConstraintError(
        "rest_or_anti_stack_unsatisfied",
        "The generated schedule cannot satisfy rest-day and anti-stack constraints.",
    )


def _workout_intensity(workout: ProposedWorkout) -> WorkoutIntensity:
    # The imported catalog bucket owns the complete workout's weekly 80/20
    # allocation. Segment zones remain execution detail only.
    return WorkoutIntensity(
        (
            IntensitySegment(
                duration=DurationMinutes(workout.snapshot.duration_minutes),
                zone=(
                    TrainingZone.ZONE_3
                    if workout.snapshot.intensity_bucket is IntensityBucket.HIGH
                    else TrainingZone.ZONE_1
                ),
            ),
        )
    )


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
    zone_capabilities: Mapping[Discipline, ZoneCapability],
    available_dates: tuple[date, ...],
    selected_template_ids: Collection[UUID] | None = None,
    fixed_template_dates: Mapping[UUID, date] | None = None,
    maintenance_active: bool = False,
) -> WeeklyPlanDraft:
    """Build a deterministic, TSS-private plan ready to remain pending."""
    uninjured = goal_disciplines - confirmed_injuries
    if not uninjured:
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

    # The first target must be seeded without fabricating realized load. Use the
    # latest eligible catalog's hidden load as a deterministic bootstrap.
    initial_candidates = tuple(
        as_rpe_guided_template(template)
        if zone_capabilities[template.discipline].rpe_guided
        else template
        for template in catalog
        if template.discipline in uninjured
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
            key=lambda item: (item.internal_planned_load.value, str(item.id)),
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
                template.internal_planned_load.value
                for template in cheapest_by_discipline.values()
            ),
            Decimal(0),
        )
    )
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
    )
    deck = eligible_workouts(
        catalog=catalog,
        phase=target.phase,
        goal_disciplines=goal_disciplines,
        confirmed_injuries=confirmed_injuries,
        low_only_disciplines=low_only_disciplines,
        zone_capabilities=zone_capabilities,
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
        required_disciplines=uninjured,
        target=target.target,
        desired_high_fraction=target.desired_high_fraction,
        selected_template_ids=selected_template_ids,
    )
    proposed = schedule_workouts(
        selected=selected,
        available_dates=available_dates,
        week_start=week_start,
        timezone_name=timezone_name,
        fixed_template_dates=fixed_dates,
    )
    distribution = calculate_time_distribution(
        tuple(_workout_intensity(workout) for workout in proposed)
    )
    assert distribution.low_fraction is not None
    assert distribution.high_fraction is not None
    planned_load = InternalLoad(
        sum(
            (workout.snapshot.internal_planned_load.value for workout in proposed),
            Decimal(0),
        )
    )
    warnings: list[PlanningWarning] = []
    if distribution.high_fraction.value != target.desired_high_fraction.value:
        warnings.append(
            PlanningWarning(
                rule_id=RuleId.TIME_INTENSITY,
                code="intensity_distribution_outside_target",
                message=(
                    "The available workout deck does not exactly match the standard "
                    "low/high time distribution for this week."
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
        (workout.snapshot.duration_minutes for workout in proposed),
        Decimal(0),
    )
    return WeeklyPlanDraft(
        target=target,
        workouts=proposed,
        warnings=tuple(warnings),
        total_duration_minutes=total_duration,
        low_intensity_percent=distribution.low_fraction.value * Decimal(100),
        high_intensity_percent=distribution.high_fraction.value * Decimal(100),
        planned_load=planned_load,
    )


def validate_manual_schedule(
    *,
    workouts: tuple[ScheduledWorkout, ...],
    moved_workout_id: str | None,
) -> tuple[PlanningWarning, ...]:
    """Return non-blocking qualitative anti-stack warnings for a direct edit."""
    violations = find_anti_stack_violations(workouts)
    return tuple(
        PlanningWarning(
            rule_id=RuleId.ANTI_STACK,
            code="anti_stack_violation",
            message=(
                (
                    "Keep two complete athlete-local rest dates between "
                    f"high-intensity {violation.discipline.value} workouts."
                )
                if violation.required_complete_rest_dates is not None
                else (
                    f"Keep at least {violation.required_hours} hours between "
                    f"high-intensity {violation.discipline.value} workouts."
                )
            ),
        )
        for violation in violations
        if moved_workout_id is None
        or moved_workout_id
        in {violation.earlier_workout_id, violation.later_workout_id}
    )


def as_utc(value: datetime) -> datetime:
    """Normalize persisted instants while retaining timezone-aware semantics."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Schedule instants must be timezone-aware.")
    return value.astimezone(timezone.utc)
