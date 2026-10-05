import type { PlannedWorkout, RestDay } from '../../api/types';
import { calendarDatesBetween, calendarRangeFor, type CalendarRange } from '../../features/calendar/calendarDates';
import { workoutSummaryViewModel, type WorkoutSummaryViewModel } from './workoutSummaryViewModel';

export type CalendarDay = Readonly<{
  date: string; selected: boolean; today: boolean; inMonth: boolean;
  workouts: readonly Readonly<{ id: string; summary: WorkoutSummaryViewModel; }>[];
  restDays: readonly Readonly<{ reason: RestDay['reason']; }>[];
}>;
export type CalendarViewModel = Readonly<{
  days: readonly CalendarDay[]; selectedDay: CalendarDay; rangeKnown: boolean;
  loadedRange: CalendarRange | null; retainedDays: readonly CalendarDay[];
}>;

export function calendarViewModel(input: {
  dates: readonly string[]; anchor: string; selectedDate: string; today: string;
  workouts: readonly PlannedWorkout[]; restDays: readonly RestDay[]; loadedRange: CalendarRange | null;
}): CalendarViewModel {
  const requested = calendarRangeFor(input.dates);
  const rangeKnown = input.loadedRange?.fromDate === requested.fromDate && input.loadedRange.toDate === requested.toDate;
  const workouts = new Map<string, { id: string; summary: WorkoutSummaryViewModel; }[]>();
  const rests = new Map<string, { reason: RestDay['reason']; }[]>();
  for (const workout of input.workouts) {
    const rows = workouts.get(workout.scheduled_date) ?? [];
    rows.push({ id: workout.id, summary: workoutSummaryViewModel(workout) });
    workouts.set(workout.scheduled_date, rows);
  }
  for (const rest of input.restDays) {
    const rows = rests.get(rest.date) ?? [];
    rows.push({ reason: rest.reason });
    rests.set(rest.date, rows);
  }
  const day = (date: string, known: boolean): CalendarDay => ({
    date, selected: date === input.selectedDate, today: date === input.today, inMonth: date.slice(0, 7) === input.anchor.slice(0, 7),
    workouts: known ? workouts.get(date) ?? [] : [], restDays: known ? rests.get(date) ?? [] : [],
  });
  return {
    days: input.dates.map((date) => day(date, rangeKnown)), selectedDay: day(input.selectedDate, rangeKnown), rangeKnown,
    loadedRange: input.loadedRange ? { fromDate: input.loadedRange.fromDate, toDate: input.loadedRange.toDate } : null,
    retainedDays: !rangeKnown && input.loadedRange
      ? calendarDatesBetween(input.loadedRange.fromDate, input.loadedRange.toDate).map((date) => day(date, true))
        .filter((value) => value.workouts.length || value.restDays.length) : [],
  };
}
