import { calendarRangeFor, calendarWeekStart, moveCalendarAnchor, parseCalendarDate, visibleCalendarDates } from './calendarDates';

test('Week contains all seven date-only days, Sunday, and an exclusive Monday end', () => {
  const dates = visibleCalendarDates('2026-10-11', 'week');
  expect(dates).toEqual(['2026-10-05', '2026-10-06', '2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10', '2026-10-11']);
  expect(calendarRangeFor(dates)).toEqual({ fromDate: '2026-10-05', toDate: '2026-10-12' });
});
test.each([
  ['2026-02-15', '2026-01-26', '2026-03-01', 35],
  ['2026-03-29', '2026-02-23', '2026-04-05', 42],
  ['2026-10-25', '2026-09-28', '2026-11-01', 35],
  ['2026-12-31', '2026-11-30', '2027-01-03', 35],
] as const)('Month %s is Monday-first with all adjacent days across boundaries/DST', (anchor, first, last, count) => {
  const dates = visibleCalendarDates(anchor, 'month');
  expect(dates[0]).toBe(first); expect(dates.at(-1)).toBe(last); expect(dates).toHaveLength(count);
  expect(parseCalendarDate(first).getDay()).toBe(1); expect(parseCalendarDate(last).getDay()).toBe(0);
  expect(new Set(dates).size).toBe(count);
});
test('month navigation from the 31st does not skip February; Week movement remains seven days', () => {
  expect(moveCalendarAnchor('2026-01-31', 'month', 1)).toBe('2026-02-01');
  expect(moveCalendarAnchor('2026-01-01', 'month', -1)).toBe('2025-12-01');
  expect(moveCalendarAnchor('2026-03-29', 'week', 1)).toBe('2026-04-05');
  expect(calendarWeekStart('2027-01-01')).toBe('2026-12-28');
  expect(parseCalendarDate('2026-10-25').getHours()).toBe(12);
});
