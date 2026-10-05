import { addDays, isoDate } from '../planning/planningDates';

export type CalendarMode = 'week' | 'month';
export type CalendarRange = Readonly<{ fromDate: string; toDate: string; }>;
export const parseCalendarDate = (value: string): Date => new Date(`${value}T12:00:00`);

export function calendarWeekStart(value: string): string {
  const weekday = parseCalendarDate(value).getDay() || 7;
  return isoDate(addDays(value, 1 - weekday));
}

export function calendarDatesBetween(fromDate: string, toDate: string): string[] {
  const dates: string[] = [];
  for (let date = fromDate; date < toDate; date = isoDate(addDays(date, 1))) dates.push(date);
  return dates;
}

export function visibleCalendarDates(anchor: string, mode: CalendarMode): string[] {
  if (mode === 'week') {
    const start = calendarWeekStart(anchor);
    return calendarDatesBetween(start, isoDate(addDays(start, 7)));
  }
  const date = parseCalendarDate(anchor);
  const first = isoDate(new Date(date.getFullYear(), date.getMonth(), 1, 12));
  const last = isoDate(new Date(date.getFullYear(), date.getMonth() + 1, 0, 12));
  return calendarDatesBetween(calendarWeekStart(first), isoDate(addDays(calendarWeekStart(last), 7)));
}

export function calendarRangeFor(dates: readonly string[]): CalendarRange {
  return { fromDate: dates[0], toDate: isoDate(addDays(dates[dates.length - 1], 1)) };
}

export function moveCalendarAnchor(anchor: string, mode: CalendarMode, direction: -1 | 1): string {
  if (mode === 'week') return isoDate(addDays(anchor, direction * 7));
  const date = parseCalendarDate(anchor);
  return isoDate(new Date(date.getFullYear(), date.getMonth() + direction, 1, 12));
}
