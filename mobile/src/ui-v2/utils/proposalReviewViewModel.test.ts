import { pendingPlan, proposal, warning, workout } from '../../features/planning/planning.test-fixtures';
import { proposalAlternativesViewModel, proposalReviewViewModel } from './proposalReviewViewModel';
import { occurrence } from '../../features/planning/planning.test-fixtures';

test('pending review preserves exact proposal/revision and repeated source occurrences in server order', () => {
  const repeat = { ...workout, id: 'second', scheduled_date: '2026-10-10', distance_meters: 4500 };
  const model = proposalReviewViewModel({ ...pendingPlan, active_revision: null, workouts: [repeat, workout] });
  expect(model).toMatchObject({ planId: pendingPlan.id, proposalId: proposal.id, revision: 3, baseRevision: 2, pending: true, activeRevision: null });
  expect(model.workouts.map(item => item.id)).toEqual(['second', workout.id]);
  expect(model.workouts.map(item => item.templateId)).toEqual([workout.template_id, workout.template_id]);
  expect(model.workouts[0].summary).toMatchObject({ date: '2026-10-10', measures: { durationMinutes: workout.duration_minutes, distanceMeters: 4500 } });
});
test('active plus pending keeps proposed rows separate and retains actual warning severity and relation', () => {
  const model = proposalReviewViewModel({ ...pendingPlan, workouts: [{ ...workout, warnings: [{ ...warning, severity: 'info', planned_workout_id: workout.id }] }] });
  expect(model.activeRevision).toBe(2); expect(model.pending).toBe(true);
  expect(model.warnings).toHaveLength(1);
  expect(model.workouts[0].warnings[0]).toMatchObject({ severity: 'info', workoutId: workout.id });
});
test.each(['expired', 'superseded', 'active', 'rejected'] as const)('%s revision cannot authorize a pending decision', state => {
  expect(proposalReviewViewModel({ ...pendingPlan, revision_state: state }).pending).toBe(false);
});
test('allowlists drop poison data recursively and preserve safe description suppression', () => {
  const poisoned = { ...pendingPlan, target_fit: 800, selector_diagnostics: 'hidden', workouts: [{ ...workout, tss: 88, description: 'Purpose. RPE 4.' }] };
  const model = proposalReviewViewModel(poisoned);
  const output = JSON.stringify(model);
  expect(output).not.toMatch(/tss|target_fit|selector_diagnostics|RPE 4/);
  expect(model.workouts[0].summary.description).toBe('Purpose.');
});
test.each([true, false, undefined])('remove capability %s is explicit and alternative IDs/measures are supplied only', can_remove => {
  const model = proposalAlternativesViewModel({ plan_id: pendingPlan.id, workout_id: workout.id, revision: 3, proposal_id: proposal.id, can_remove: can_remove as boolean, alternatives: [{ ...occurrence, distance_meters: 5000 }] });
  expect(model.canRemove).toBe(can_remove === true);
  expect(model.alternatives[0]).toMatchObject({ id: occurrence.id, durationMinutes: occurrence.duration_minutes, distanceMeters: 5000 });
  expect(model.alternatives[0]).not.toHaveProperty('occurrence_id');
});
