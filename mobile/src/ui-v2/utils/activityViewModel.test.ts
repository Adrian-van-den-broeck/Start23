import type { CompletedActivity } from '../../api/types';
import { completeActivity, pendingActivity } from '../../features/activities/activities.test-fixtures';
import { localWeekKey, suggestedWorkout } from '../../features/activities/activityPresentation';
import { workout } from '../../features/planning/planning.test-fixtures';
import { observedRunPace } from '../../lib/runPace';
import { activityViewModel } from './activityViewModel';

test.each([['45', null], [null, 1500], ['45', 5000], [null, null]] as const)(
  'independent supplied measures %s/%s do not infer missing swim duration', (duration, distance) => {
    const activity = { ...pendingActivity, discipline: 'swim' as const, duration_minutes: duration, distance_meters: distance };
    const before = JSON.stringify(activity); const model = activityViewModel(activity, 'en-GB', 'en');
    expect(model.durationMinutes).toBe(duration); expect(model.distanceMeters).toBe(distance); expect(model.pace).toBeNull();
    expect(JSON.stringify(activity)).toBe(before);
  });
test('run pace preserves existing shared rounding/empty behavior; no new parser', () => {
  const model = activityViewModel({ ...completeActivity, distance_meters: 8123 }, 'en-GB', 'en');
  expect(model.pace).toBe(observedRunPace('45', 8123));
  expect(activityViewModel(pendingActivity, 'en-GB', 'en').pace).toBeNull();
});
test('supplied public run pace uses shared formatter even without duration, without estimating time', () => {
  const model = activityViewModel({
    ...pendingActivity, duration_minutes: null, distance_meters: 5000,
    metrics: { average_pace_seconds_per_km: '333' }
  } as CompletedActivity, 'en-GB', 'en');
  expect(model.pace).toBe('5:33 /km'); expect(model.durationMinutes).toBeNull();
});
test('full historical date uses supplied activity timezone; public messages retain existing language semantics', () => {
  const activity = { ...completeActivity, started_at: '2020-01-01T23:45:00Z' };
  expect(activityViewModel(activity, 'en-GB', 'en').date).toBe('Thursday, 2 January 2020 at 00:45');
  expect(activityViewModel(activity, 'nl-NL', 'nl').publicMessage).toBe(activity.public_message);
  expect(activityViewModel(activity, 'en-GB', 'en').publicMessage).toBeNull();
  expect(activityViewModel(pendingActivity, 'en-GB', 'en').publicMessage).toBe(pendingActivity.public_message);
});
test('canonical source is truthful; unavailable provider provenance is not invented', () => {
  expect(activityViewModel(completeActivity, 'en-GB', 'en').source).toBe('canonical_summary');
  expect(activityViewModel({ ...completeActivity, source: undefined } as unknown as CompletedActivity, 'en-GB', 'en').source).toBeNull();
});
test('recursive public adapter drops unrecognized fields and never transports full metrics', () => {
  const hidden = { tss: 987.654, private_load: 987.654, planned_load: 987.654, realized_load: 987.654, selector_diagnostics: 'hidden', access_token: 'hidden' };
  const model = activityViewModel({ ...completeActivity, ...hidden, metrics: { average_heart_rate_bpm: 151, ...hidden } } as unknown as CompletedActivity, 'en-GB', 'en');
  expect(model.averageHeartRate).toBe(151);
  expect(JSON.stringify(model)).not.toMatch(/tss|private_load|planned_load|realized_load|selector_diagnostics|access_token|hidden|987\.654/i);
});
test('shared matching suggestion and local-week helper retain the exact V1 boundary', () => {
  const activity = { ...pendingActivity, started_at: `${workout.scheduled_date}T10:00:00Z` };
  const sibling = { ...workout, id: 'sibling' };
  expect(suggestedWorkout(activity, [workout, sibling])).toBe(workout);
  expect(suggestedWorkout({ ...activity, discipline: 'swim' }, [workout])).toBeNull();
  expect(suggestedWorkout({ ...activity, started_at: '2020-01-01T10:00:00Z' }, [workout])).toBeNull();
  expect(localWeekKey(new Date('2026-10-04T23:00:00Z'), 'Europe/Amsterdam')).toBe('2026-10-05');
});
