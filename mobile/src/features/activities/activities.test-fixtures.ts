import type { CompletedActivity, OnboardingState, PlannedExternalActivity } from '../../api/types';

export const pendingActivity: CompletedActivity = {
  id: 'activity-a', planned_workout_id: null, discipline: 'run', source: 'canonical_summary',
  started_at: '2026-10-06T10:00:00Z', timezone: 'Europe/Amsterdam', duration_minutes: '45',
  distance_meters: null, elevation_gain_meters: null, rpe: null, rpe_submitted_at: null,
  match_status: 'unmatched', processing_state: 'awaiting_rpe', qualitative_result: 'awaiting_rpe',
  public_message: 'RPE nodig.', correction_proposal_id: null, metrics: null,
  created_at: '2026-10-06T10:45:00Z', updated_at: '2026-10-06T10:45:00Z',
};
export const completeActivity: CompletedActivity = {
  ...pendingActivity, rpe: 7, rpe_submitted_at: '2026-10-06T11:00:00Z',
  processing_state: 'complete', qualitative_result: 'unplanned',
};
export const activityOnboarding = {
  current_step: 'completed', profile: { timezone: 'Europe/Amsterdam', timezone_confirmed_at: '2026-09-01T00:00:00Z' },
} as OnboardingState;
export const externalActivity = {
  id: 'external-a', discipline: 'bike', duration_minutes: '60.00', status: 'planned',
} as PlannedExternalActivity;
