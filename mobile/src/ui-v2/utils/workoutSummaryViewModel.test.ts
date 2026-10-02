import { workoutSummaryViewModel } from './workoutSummaryViewModel';
import { sourceWorkout } from './workout.test-fixtures';

test('summary allows source name, sport, independent measures, intensity, date/status and safe card description only', () => {
  const input = { ...sourceWorkout, tss: 42, planned_load: 43 };
  expect(workoutSummaryViewModel(input)).toEqual({
    discipline: 'swim', name: sourceWorkout.name, description: 'Exact source description.',
    measures: { durationMinutes: '30.5', distanceMeters: 1200 }, intensity: 'low',
    date: '2020-01-02', status: 'cancelled',
  });
  expect(workoutSummaryViewModel({ ...input, duration_minutes: null }).measures).toEqual({ durationMinutes: null, distanceMeters: 1200 });
});
