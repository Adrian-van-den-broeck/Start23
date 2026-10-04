import { activePlan, draft, pendingPlan, workout } from '../../features/planning/planning.test-fixtures';
import { currentWeekStart, weekHomeViewModel } from './weekHomeViewModel';

const base = { plan: null, activePlan: null, draft: null, today: '2026-10-05', resumeState: 'ready' as const, activeReadState: 'ready' as const };
test('no plan uses current Monday-Sunday, not the next-week generation default', () => {
  expect(weekHomeViewModel(base)).toMatchObject({ weekStart: '2026-10-05', weekEnd: '2026-10-11', state: 'noPlan', mainAction: 'prepare', progress: null });
  expect(currentWeekStart('2026-10-11')).toBe('2026-10-05');
  expect(currentWeekStart('2026-03-29')).toBe('2026-03-23');
});
test.each(['loading', 'failed'] as const)('%s does not claim an empty plan', (resumeState) => {
  expect(weekHomeViewModel({ ...base, resumeState })).toMatchObject({ state: resumeState, empty: null, mainAction: null, progress: null });
});
test('pending-only has no scheduled sessions or progress; exact review remains the next action', () => {
  const plan = { ...pendingPlan, active_revision: null };
  expect(weekHomeViewModel({ ...base, plan })).toMatchObject({ state: 'pending', sessions: [], progress: null, mainAction: 'review' });
});
test('active plus pending keeps only authoritative active occurrences and separate attention', () => {
  const pending = { ...pendingPlan, workouts: [{ ...workout, id: 'proposed-only', scheduled_date: base.today }] };
  const model = weekHomeViewModel({ ...base, plan: pending, activePlan });
  expect(model.state).toBe('activePending');
  expect(model.sessions.map((item) => item.id)).toEqual([workout.id]);
  expect(model.sessionDate).toBe('2026-10-07');
  expect(model.attention.map((item) => item.kind)).toEqual(['proposal', 'warnings']);
});
test('repeated templates on today remain independently reachable in stable supplied order', () => {
  const plan = { ...activePlan, workouts: [{ ...workout, scheduled_date: base.today }, { ...workout, id: 'repeat-b', scheduled_date: base.today }] };
  const model = weekHomeViewModel({ ...base, plan, activePlan: plan });
  expect(model.sessions.map((item) => item.id)).toEqual([workout.id, 'repeat-b']);
  expect(model.isToday).toBe(true); expect(model.progress).toEqual({ completed: 0, planned: 2 });
});
test('completion is literal and excludes cancelled rows; activities are not inputs', () => {
  const plan = { ...activePlan, workouts: [{ ...workout, status: 'completed' as const }, workout, { ...workout, id: 'cancelled', status: 'cancelled' as const }] };
  expect(weekHomeViewModel({ ...base, plan, activePlan: plan }).progress).toEqual({ completed: 1, planned: 2 });
});
test('unidentified active revision omits progress and schedule', () => {
  const plan = { ...activePlan, active_revision: null };
  expect(weekHomeViewModel({ ...base, plan, activePlan: plan })).toMatchObject({ progress: null, sessions: [] });
});
test.each(['collecting', 'placement'] as const)('resumed %s draft preserves identity outside a display-only mapper', (state) => {
  const model = weekHomeViewModel({ ...base, draft: { ...draft, state } });
  expect(model.state).toBe(state === 'placement' ? 'placement' : 'draft');
  expect(model.mainAction).toBe('draft'); expect(model.progress).toBeNull();
  expect(model.attention.map((item) => item.kind)).toEqual(['draft', 'warnings']);
});
test.each(['rejected', 'expired', 'superseded'] as const)('%s remains a real V1 task entry', (revision_state) => {
  expect(weekHomeViewModel({ ...base, plan: { ...pendingPlan, revision_state } }).mainAction).toBe('planning');
});
test('approved restriction rest-only plan is not an unplanned empty week', () => {
  const plan = { ...activePlan, workouts: [], rest_days: [{ date: base.today, reason: 'restriction_rest' as const }] };
  expect(weekHomeViewModel({ ...base, plan, activePlan: plan })).toMatchObject({ state: 'active', empty: 'restrictedRest', progress: { completed: 0, planned: 0 } });
});
test('no future sessions is truthful without inventing prescribed rest', () => {
  const model = weekHomeViewModel({ ...base, plan: activePlan, activePlan, today: '2026-10-11' });
  expect(model).toMatchObject({ sessionDate: null, empty: 'noFuture' });
});
test('distance-only swim remains distance-only and card descriptions suppress RPE', () => {
  const plan = { ...activePlan, workouts: [{ ...workout, discipline: 'swim' as const, duration_minutes: null, distance_meters: 1500, description: 'Swim smoothly. RPE 3.' }] };
  const summary = weekHomeViewModel({ ...base, plan, activePlan: plan }).sessions[0].summary;
  expect(summary.measures).toEqual({ durationMinutes: null, distanceMeters: 1500 });
  expect(summary.description).not.toContain('RPE');
});
test('known last snapshot survives a read failure; mismatched proposal identity cannot reuse it', () => {
  expect(weekHomeViewModel({ ...base, plan: pendingPlan, activePlan, activeReadState: 'failed' })).toMatchObject({ state: 'activePending', readState: 'failed' });
  expect(weekHomeViewModel({ ...base, plan: { ...pendingPlan, id: 'other' }, activePlan }).progress).toBeNull();
});
test('mapper allowlists output and does not mutate frozen server snapshots', () => {
  const plan = Object.freeze({ ...activePlan, selector_diagnostics: 'PRIVATE_POISON' });
  const before = JSON.stringify(plan);
  const model = weekHomeViewModel({ ...base, plan, activePlan: plan });
  expect(JSON.stringify(model)).not.toContain('PRIVATE_POISON');
  expect(JSON.stringify(model)).not.toContain('selector_diagnostics');
  expect(JSON.stringify(plan)).toBe(before);
});
