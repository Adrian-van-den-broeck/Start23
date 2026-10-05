import type { PlannedWorkout } from '../../api/types';
import { visibleCalendarDates } from '../../features/calendar/calendarDates';
import { workout } from '../../features/planning/planning.test-fixtures';
import { calendarViewModel } from './calendarViewModel';

const base = {
  dates: visibleCalendarDates('2026-10-07', 'week'), anchor: '2026-10-07', selectedDate: '2026-10-07', today: '2026-10-05',
  loadedRange: { fromDate: '2026-10-05', toDate: '2026-10-12' }, workouts: [workout], restDays: []
};
test('exact dates/order/occurrences and all supplied rest records coexist, without empty-to-rest inference', () => {
  const second = { ...workout, id: 'second', template_id: workout.template_id, status: 'cancelled' as const };
  const model = calendarViewModel({
    ...base, workouts: Object.freeze([Object.freeze(workout), Object.freeze(second)]),
    restDays: [{ date: workout.scheduled_date, reason: 'planned_rest' }, { date: workout.scheduled_date, reason: 'restriction_rest' }]
  });
  expect(model.days).toHaveLength(7); expect(model.days.at(-1)?.date).toBe('2026-10-11');
  expect(model.selectedDay.workouts.map((value) => value.id)).toEqual([workout.id, 'second']);
  expect(model.selectedDay.workouts[1].summary.status).toBe('cancelled');
  expect(model.selectedDay.restDays.map((value) => value.reason)).toEqual(['planned_rest', 'restriction_rest']);
  expect(model.days[0]).toMatchObject({ today: true, selected: false, workouts: [], restDays: [] });
  expect(model.selectedDay).toMatchObject({ today: false, selected: true });
});
test('month retains adjacent cells, independent today/selection and selected-date data', () => {
  const model = calendarViewModel({
    ...base, dates: visibleCalendarDates('2026-10-07', 'month'),
    loadedRange: { fromDate: '2026-09-28', toDate: '2026-11-02' }, selectedDate: '2026-11-01'
  });
  expect(model.days[0]).toMatchObject({ date: '2026-09-28', inMonth: false });
  expect(model.days.at(-1)).toMatchObject({ date: '2026-11-01', inMonth: false, selected: true });
  expect(model.selectedDay.workouts).toEqual([]);
  expect(model.days.find((day) => day.date === workout.scheduled_date)?.workouts).toHaveLength(1);
});
test('unloaded requested dates remain unknown; old records retain their actual loaded range and dates', () => {
  const model = calendarViewModel({ ...base, dates: visibleCalendarDates('2026-11-07', 'week') });
  expect(model.rangeKnown).toBe(false);
  expect(model.days.every((day) => !day.workouts.length && !day.restDays.length)).toBe(true);
  expect(model.loadedRange).toEqual(base.loadedRange);
  expect(model.retainedDays[0]).toMatchObject({ date: workout.scheduled_date, workouts: [{ id: workout.id }] });
  expect(calendarViewModel({ ...base, loadedRange: null }).retainedDays).toEqual([]);
});
test('public allowlist omits poison data recursively without rewriting supplied source fields or deriving missing measures', () => {
  const input = {
    ...workout, name: 'Exact source \uFFFD name', duration_minutes: null, distance_meters: 1200,
    tss: 999, planned_load: 888, realized_load: 777, selector_diagnostics: { secret: true }
  } as PlannedWorkout;
  const model = calendarViewModel({ ...base, workouts: [input] });
  const output = JSON.stringify(model);
  for (const key of ['tss', 'planned_load', 'realized_load', 'selector_diagnostics']) expect(output).not.toContain(key);
  expect(model.selectedDay.workouts[0].summary).toMatchObject({ name: input.name, measures: { durationMinutes: null, distanceMeters: 1200 } });
});
