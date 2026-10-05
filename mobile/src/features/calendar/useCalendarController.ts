import { useCallback, useRef, useState } from 'react';
import { getCalendar } from '../../api/client';
import type { PlannedWorkout, RestDay } from '../../api/types';
import type { CalendarRange } from './calendarDates';

export function useCalendarController(
  accessToken: string,
  language: 'nl' | 'en',
  setError: (message: string | null) => void,
) {
  const [calendarWorkouts, setCalendarWorkouts] = useState<PlannedWorkout[]>([]);
  const [calendarRestDays, setCalendarRestDays] = useState<RestDay[]>([]);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [calendarRange, setCalendarRange] = useState<CalendarRange | null>(null);
  const [calendarGeneration, setCalendarGeneration] = useState(0);
  const calendarRequestRef = useRef(0);
  const requestedRangeRef = useRef<CalendarRange | null>(null);
  const loadedRangeRef = useRef<CalendarRange | null>(null);

  const loadCalendarRange = useCallback(
    (fromDate: string, toDate: string) => {
      const requestNumber = ++calendarRequestRef.current;
      requestedRangeRef.current = { fromDate, toDate };
      setCalendarLoading(true);
      setError(null);
      getCalendar(accessToken, fromDate, toDate)
        .then((result) => {
          if (requestNumber !== calendarRequestRef.current) return;
          setCalendarWorkouts(result.workouts);
          setCalendarRestDays(result.rest_days);
          setCalendarRange({ fromDate: result.from_date, toDate: result.to_date });
          loadedRangeRef.current = { fromDate: result.from_date, toDate: result.to_date };
        })
        .catch((caught) => {
          if (requestNumber !== calendarRequestRef.current) return;
          setError(
            caught instanceof Error
              ? caught.message
              : language === 'nl'
                ? 'De kalender kon niet worden geladen.'
                : 'The calendar could not be loaded.',
          );
        })
        .finally(() => {
          if (requestNumber === calendarRequestRef.current) {
            requestedRangeRef.current = null;
            setCalendarLoading(false);
          }
        });
    },
    [accessToken, language, setError],
  );

  const ensureCalendarRange = useCallback((fromDate: string, toDate: string) => {
    const matches = (range: CalendarRange | null) => range?.fromDate === fromDate && range.toDate === toDate;
    if (matches(requestedRangeRef.current)) return;
    // An outstanding different range must be superseded even if the requested
    // range is the retained successful range. Keep the latest-request guard.
    if (!requestedRangeRef.current && matches(loadedRangeRef.current)) return;
    loadCalendarRange(fromDate, toDate);
  }, [loadCalendarRange, calendarGeneration]);

  const invalidateCalendarRange = useCallback(() => {
    ++calendarRequestRef.current;
    requestedRangeRef.current = null;
    loadedRangeRef.current = null;
    setCalendarLoading(false);
    setCalendarGeneration((value) => value + 1);
  }, []);

  return { calendarWorkouts, calendarRestDays, calendarLoading, calendarRange, loadCalendarRange, ensureCalendarRange, invalidateCalendarRange };
}
