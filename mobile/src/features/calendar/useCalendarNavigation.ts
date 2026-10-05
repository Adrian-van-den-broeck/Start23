import { useEffect, useMemo, useState } from 'react';
import { isoDate } from '../planning/planningDates';
import { calendarRangeFor, moveCalendarAnchor, visibleCalendarDates, type CalendarMode } from './calendarDates';

type CalendarSelection = Readonly<{ mode: CalendarMode; anchor: string; selectedDate: string; }>;
const initialSelection = (date: string): CalendarSelection => ({ mode: 'week', anchor: date, selectedDate: date });

// This is local presentation context, not a range reader. It lives above both UIs.
export function useCalendarNavigation(initialDate: string, active = true) {
  const [saved, setSaved] = useState<CalendarSelection | null>(null);
  const selection = saved ?? initialSelection(initialDate);
  useEffect(() => {
    if (active && saved === null) setSaved(initialSelection(initialDate));
  }, [active, initialDate, saved]);
  const dates = useMemo(() => visibleCalendarDates(selection.anchor, selection.mode), [selection.anchor, selection.mode]);
  const range = calendarRangeFor(dates);
  return {
    ...selection, dates, range,
    selectDate: (date: string) => setSaved((current) => ({ ...(current ?? initialSelection(initialDate)), selectedDate: date })),
    changeMode: (mode: CalendarMode) => setSaved((current) => {
      const value = current ?? initialSelection(initialDate);
      return { ...value, mode, anchor: mode === 'week' ? value.selectedDate : value.anchor };
    }),
    move: (direction: -1 | 1) => setSaved((current) => {
      const value = current ?? initialSelection(initialDate);
      const anchor = moveCalendarAnchor(value.anchor, value.mode, direction);
      return { ...value, anchor, selectedDate: anchor };
    }),
    goToday: () => setSaved((current) => {
      const date = isoDate(new Date());
      return { ...(current ?? initialSelection(date)), anchor: date, selectedDate: date };
    }),
  };
}
export type CalendarNavigation = ReturnType<typeof useCalendarNavigation>;
