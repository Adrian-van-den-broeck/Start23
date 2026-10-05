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
  const calendarRequestRef = useRef(0);

  const loadCalendarRange = useCallback(
    (fromDate: string, toDate: string) => {
      const requestNumber = ++calendarRequestRef.current;
      setCalendarLoading(true);
      setError(null);
      getCalendar(accessToken, fromDate, toDate)
        .then((result) => {
          if (requestNumber !== calendarRequestRef.current) return;
          setCalendarWorkouts(result.workouts);
          setCalendarRestDays(result.rest_days);
          setCalendarRange({ fromDate: result.from_date, toDate: result.to_date });
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
          if (requestNumber === calendarRequestRef.current) setCalendarLoading(false);
        });
    },
    [accessToken, language, setError],
  );

  return { calendarWorkouts, calendarRestDays, calendarLoading, calendarRange, loadCalendarRange };
}
