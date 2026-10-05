import { act, render } from '@testing-library/react-native';
import { getCalendar } from '../../api/client';
import type { CalendarResponse } from '../../api/types';
import { workout } from '../planning/planning.test-fixtures';
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
