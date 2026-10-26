import { act, render } from '@testing-library/react-native';
import { getCalendar } from '../../api/client';
import type { CalendarResponse } from '../../api/types';
import { activePlan, workout } from '../planning/planning.test-fixtures';
import { useCalendarController } from './useCalendarController';
jest.mock('../../api/client', () => ({ getCalendar: jest.fn() }));
function deferred() {
  let resolve!: (value: CalendarResponse) => void; let reject!: (reason: Error) => void;
  const promise = new Promise<CalendarResponse>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
let owner: ReturnType<typeof useCalendarController>;
const setError = jest.fn();
function Probe() { owner = useCalendarController('verified-token', 'en', setError); return null; }
const response = (date: string): CalendarResponse => ({ from_date: date, to_date: '2026-11-02', workouts: [{ ...workout, id: date }], rest_days: [] });
beforeEach(() => { jest.clearAllMocks(); });

test.each(['success', 'failure'] as const)('task handoff replaces the complete affected week and ignores an obsolete %s', async outcome => {
  const late = deferred();
  const retained = { ...workout, id: 'retained-other-week', scheduled_date: '2026-10-14' };
  const result = { from_date: '2026-10-05', to_date: '2026-10-19', workouts: [workout, retained], rest_days: [] };
  jest.mocked(getCalendar).mockResolvedValueOnce(result).mockReturnValueOnce(late.promise);
  await render(<Probe />);
  await act(() => owner.loadCalendarRange(result.from_date, result.to_date));
  await act(() => owner.loadCalendarRange(result.from_date, result.to_date));
  const replacement = { ...workout, id: 'different-plan-occurrence', scheduled_date: '2026-10-08' };
  const approved = { ...activePlan, id: 'different-plan', workouts: [replacement] };
  await act(() => owner.acceptApprovedPlan(approved));
  await act(() => { if (outcome === 'success') late.resolve(result); else late.reject(new Error('Obsolete')); });
  expect(owner.calendarWorkouts).toEqual([retained, replacement]);
  expect(owner.calendarRange).toEqual({ fromDate: result.from_date, toDate: result.to_date });
  expect(setError).not.toHaveBeenCalledWith('Obsolete');
  await act(() => owner.ensureCalendarRange(result.from_date, result.to_date));
  expect(getCalendar).toHaveBeenCalledTimes(2);
});

test('task handoff preserves an unrelated in-flight range and a cached unaffected week', async () => {
  const unrelated = deferred();
  const result = { from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] };
  jest.mocked(getCalendar).mockResolvedValueOnce(result).mockReturnValueOnce(unrelated.promise);
  await render(<Probe />);
  await act(() => owner.loadCalendarRange(result.from_date, result.to_date));
  await act(() => owner.loadCalendarRange('2026-11-02', '2026-11-09'));
  await act(() => owner.acceptApprovedPlan({ ...activePlan, week_start: '2026-10-19', workouts: [], rest_days: [] }));
  expect(owner.calendarWorkouts).toEqual([workout]); expect(owner.calendarLoading).toBe(true);
  await act(() => unrelated.resolve({ from_date: '2026-11-02', to_date: '2026-11-09', workouts: [], rest_days: [] }));
  expect(owner.calendarRange).toEqual({ fromDate: '2026-11-02', toDate: '2026-11-09' });
  expect(owner.calendarWorkouts).toEqual([]); expect(getCalendar).toHaveBeenCalledTimes(2);
});

test('task handoff replaces empty/rest-only week rows without removing a neighboring week', async () => {
  const retained = { ...workout, id: 'neighbor', scheduled_date: '2026-10-14' };
  jest.mocked(getCalendar).mockResolvedValueOnce({ from_date: '2026-10-05', to_date: '2026-10-19', workouts: [workout, retained], rest_days: [] });
  await render(<Probe />);
  await act(() => owner.loadCalendarRange('2026-10-05', '2026-10-19'));
  const rest = { date: '2026-10-05', reason: 'planned_rest' as const };
  await act(() => owner.acceptApprovedPlan({ ...activePlan, workouts: [], rest_days: [rest] }));
  expect(owner.calendarWorkouts).toEqual([retained]); expect(owner.calendarRestDays).toEqual([rest]);
});
test.each(['success', 'failure'] as const)('A %s finishes after B success; B records and provenance remain displayed', async (outcome) => {
  const a = deferred(), b = deferred();
  jest.mocked(getCalendar).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
  const view = await render(<Probe />);
  await act(() => { owner.loadCalendarRange('2026-10-05', '2026-10-12'); owner.loadCalendarRange('2026-09-28', '2026-11-02'); });
  await act(() => b.resolve(response('2026-09-28')));
  await act(() => { if (outcome === 'success') a.resolve(response('2026-10-05')); else a.reject(new Error('Old error')); });
  expect(owner.calendarWorkouts[0].id).toBe('2026-09-28');
  expect(owner.calendarRange).toEqual({ fromDate: '2026-09-28', toDate: '2026-11-02' });
  expect(setError).not.toHaveBeenCalledWith('Old error'); expect(owner.calendarLoading).toBe(false);
  await view.rerender(<Probe />); expect(getCalendar).toHaveBeenCalledTimes(2);
});
test('old finally cannot clear current loading; latest failure retains the last successful range', async () => {
  const a = deferred(), b = deferred();
  jest.mocked(getCalendar).mockResolvedValueOnce(response('2026-09-28')).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
  await render(<Probe />);
  await act(() => owner.loadCalendarRange('2026-09-28', '2026-11-02'));
  await act(() => { owner.loadCalendarRange('2026-10-05', '2026-10-12'); owner.loadCalendarRange('2026-11-02', '2026-11-09'); });
  await act(() => a.resolve(response('2026-10-05')));
  expect(owner.calendarLoading).toBe(true); expect(owner.calendarRange?.fromDate).toBe('2026-09-28');
  await act(() => b.reject(new Error('Latest safe error')));
  expect(owner.calendarLoading).toBe(false); expect(setError).toHaveBeenLastCalledWith('Latest safe error');
  expect(owner.calendarRange?.fromDate).toBe('2026-09-28'); expect(owner.calendarWorkouts[0].id).toBe('2026-09-28');
});


test.each(['success', 'failure'] as const)('authoritative move supersedes old Calendar %s and same loaded range needs no second read', async outcome => {
  const late = deferred();
  jest.mocked(getCalendar).mockResolvedValueOnce({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] }).mockReturnValueOnce(late.promise);
  await render(<Probe />);
  await act(() => owner.loadCalendarRange('2026-10-05', '2026-10-12'));
  await act(() => owner.loadCalendarRange('2026-10-05', '2026-10-12'));
  const moved = { ...workout, scheduled_date: '2026-10-10' }; const updated = { ...activePlan, workouts: [moved], rest_days: [{ date: '2026-10-10', reason: 'planned_rest' as const }] };
  await act(() => owner.replaceApprovedPlan(activePlan, updated));
  await act(() => { if (outcome === 'success') late.resolve({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] }); else late.reject(new Error('Old range error')); });
  expect(owner.calendarWorkouts).toEqual([moved]); expect(owner.calendarRestDays).toEqual(updated.rest_days);
  expect(setError).not.toHaveBeenCalledWith('Old range error'); expect(owner.calendarLoading).toBe(false);
  await act(() => owner.ensureCalendarRange('2026-10-05', '2026-10-12')); expect(getCalendar).toHaveBeenCalledTimes(2);
});

test('move during a different range read retains provenance and allows one fresh current-range read', async () => {
  const late = deferred(); const fresh = deferred();
  jest.mocked(getCalendar).mockResolvedValueOnce({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] }).mockReturnValueOnce(late.promise).mockReturnValueOnce(fresh.promise);
  await render(<Probe />); await act(() => owner.loadCalendarRange('2026-10-05', '2026-10-12'));
  await act(() => owner.loadCalendarRange('2026-11-02', '2026-11-09'));
  await act(() => owner.replaceApprovedPlan(activePlan, { ...activePlan, workouts: [{ ...workout, scheduled_date: '2026-10-10' }] }));
  expect(owner.calendarRange).toEqual({ fromDate: '2026-10-05', toDate: '2026-10-12' });
  await act(() => { owner.ensureCalendarRange('2026-11-02', '2026-11-09'); owner.ensureCalendarRange('2026-11-02', '2026-11-09'); });
  expect(getCalendar).toHaveBeenCalledTimes(3);
  await act(() => late.resolve(response('2026-10-05'))); expect(owner.calendarLoading).toBe(true);
  await act(() => fresh.resolve(response('2026-11-02'))); expect(owner.calendarRange?.fromDate).toBe('2026-11-02');
});


test('range response already seeing renewed server IDs is reconciled without duplicate occurrences', async () => {
  const moved = { ...workout, id: 'renewed-a', scheduled_date: '2026-10-10' };
  const updated = { ...activePlan, revision: 3, active_revision: 3, workouts: [moved] };
  jest.mocked(getCalendar).mockResolvedValueOnce({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [moved], rest_days: [] });
  await render(<Probe />); await act(() => owner.loadCalendarRange('2026-10-05', '2026-10-12'));
  await act(() => owner.replaceApprovedPlan(activePlan, updated));
  expect(owner.calendarWorkouts).toEqual([moved]); expect(getCalendar).toHaveBeenCalledTimes(1);
});
