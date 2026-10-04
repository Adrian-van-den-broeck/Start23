import type { ChangeProposal, OnboardingState, PlanWarning, SwipeWeekDraft, SwipeWorkoutOccurrence, WeeklyPlan } from '../../api/types';
import { sourceWorkout } from '../../ui-v2/utils/workout.test-fixtures';

export const workout = { ...sourceWorkout, id: 'workout-a', discipline: 'run' as const, scheduled_date: '2026-10-07', status: 'scheduled' as const };
export const warning: PlanWarning = { id: 'warning', rule_id: 'supplied-rule', code: 'target_outside_catalog_capacity', severity: 'warning', message: 'Review the combination', planned_workout_id: null };
export const proposal: ChangeProposal = {
  id: 'proposal-a', kind: 'plan_revision', state: 'pending', reason_codes: [], public_explanation: 'Supplied explanation',
  ruleset_version: 'joren-planning-ruleset-2', created_at: '2026-10-05T00:00:00Z', decided_at: null, applied_at: null,
  decision_actor: null, target_plan_revision_id: 'revision-3', base_plan_revision: 2, target_zone_profile_id: null,
  base_zone_profile_id: null, target_test_assignment_id: null,
};
export const activePlan: WeeklyPlan = {
  id: 'plan-a', week_start: '2026-10-05', timezone: 'Europe/Amsterdam', state: 'active', active_revision: 2,
  revision_id: 'revision-2', revision: 2, revision_state: 'active', phase: 'base', target_basis: 'prior_planned_hold',
  taper_period: null, total_duration_minutes: '30.5', low_intensity_percent: '100', high_intensity_percent: '0',
  display_low_intensity_percent: 100, display_high_intensity_percent: 0, low_intensity_minutes: '30.5', high_intensity_minutes: '0',
  confirmed_injuries: ['run'], low_only_disciplines: [], available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
  availability_source: 'explicit', workouts: [workout], rest_days: [], warnings: [warning], proposal: null,
};
export const pendingPlan: WeeklyPlan = { ...activePlan, revision_id: 'revision-3', revision: 3, revision_state: 'pending_approval', proposal };
export const occurrence: SwipeWorkoutOccurrence = {
  id: workout.template_id, template_key: workout.template_key, version: workout.template_version, discipline: 'run',
  name: workout.name, description: workout.description, duration_minutes: workout.duration_minutes, distance_meters: null,
  intensity_bucket: 'low', expected_rpe_min: 2, expected_rpe_max: 3, segments: workout.segments, rpe_zones: workout.rpe_zones,
  workout_kind: 'standard', contributes_to_zone_calibration: false, occurrence_id: 'occurrence-a',
};
export const draft: SwipeWeekDraft = {
  id: 'draft-a', revision: 4, state: 'collecting', week_start: '2026-10-05', available_dates: ['2026-10-05', '2026-10-07'],
  availability_source: 'explicit', target_workout_count: 2, target_composition: { swim: 0, bike: 0, run: 2 },
  cross_training_opt_ins: ['bike'], accepted_workouts: [], current_candidate: occurrence, placements: [], warnings: [warning],
  passed_count: 0, exhausted: false, can_undo: false, ruleset_version: 'joren-planning-ruleset-2', plan_id: null, proposal_id: null,
};
export const onboarding = { primary_goal: null } as OnboardingState;
