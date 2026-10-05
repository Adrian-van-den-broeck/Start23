import type { PendingWorkoutAlternatives, PlanWarning, WeeklyPlan, WorkoutDeckItem } from '../../api/types';
import { warningPresentation } from '../../components/MoveWarningPanel';
import { workoutCardDescription } from '../../lib/workoutPresentation';
import { workoutSummaryViewModel } from './workoutSummaryViewModel';

function publicWarning(warning: PlanWarning) {
  return { id: warning.id, workoutId: warning.planned_workout_id, severity: warning.severity, ...warningPresentation(warning) };
}

export function proposalReviewViewModel(plan: WeeklyPlan) {
  return {
    planId: plan.id, revision: plan.revision, revisionId: plan.revision_id,
    proposalId: plan.proposal?.id ?? null, baseRevision: plan.proposal?.base_plan_revision ?? null,
    weekStart: plan.week_start, activeRevision: plan.active_revision,
    pending: plan.revision_state === 'pending_approval' && plan.proposal?.state === 'pending',
    state: plan.revision_state, explanation: plan.proposal?.public_explanation ?? '',
    warnings: plan.warnings.map(publicWarning),
    workouts: plan.workouts.map((workout) => ({
      id: workout.id, templateId: workout.template_id, templateKey: workout.template_key,
      templateVersion: workout.template_version, source: workout.source,
      summary: workoutSummaryViewModel(workout), warnings: workout.warnings.map(publicWarning),
    })),
  };
}
export type ProposalReviewModel = ReturnType<typeof proposalReviewViewModel>;

function alternative(workout: WorkoutDeckItem) {
  return {
    id: workout.id, templateKey: workout.template_key, templateVersion: workout.version,
    name: workout.name, discipline: workout.discipline, durationMinutes: workout.duration_minutes,
    distanceMeters: workout.distance_meters, intensity: workout.intensity_bucket,
    description: workoutCardDescription(workout.description),
  };
}
export function proposalAlternativesViewModel(options: PendingWorkoutAlternatives) {
  return {
    planId: options.plan_id, revision: options.revision, proposalId: options.proposal_id,
    workoutId: options.workout_id, canRemove: options.can_remove === true,
    alternatives: options.alternatives.map(alternative),
  };
}
export type ProposalAlternativesModel = ReturnType<typeof proposalAlternativesViewModel>;
