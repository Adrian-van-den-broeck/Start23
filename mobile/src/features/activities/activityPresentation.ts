import type { CompletedActivity, PlannedWorkout } from '../../api/types';

export function localWeekKey(instant: Date, timezoneName: string): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    day: '2-digit',
    month: '2-digit',
    timeZone: timezoneName,
    year: 'numeric',
  }).formatToParts(instant);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const local = new Date(
    Date.UTC(Number(value.year), Number(value.month) - 1, Number(value.day)),
  );
  const weekday = local.getUTCDay() || 7;
  local.setUTCDate(local.getUTCDate() - weekday + 1);
  return local.toISOString().slice(0, 10);
}

export function suggestedWorkout(
  activity: CompletedActivity,
  workouts: PlannedWorkout[],
): PlannedWorkout | null {
  const candidates = workouts
    .filter(
      (workout) =>
        workout.discipline === activity.discipline &&
        workout.status === 'scheduled',
    )
    .map((workout) => ({
      workout,
      difference: Math.abs(
        new Date(`${workout.scheduled_date}T12:00:00`).getTime() -
        new Date(activity.started_at).getTime(),
      ),
    }))
    .filter(({ difference }) => difference <= 24 * 60 * 60 * 1000)
    .sort((left, right) => left.difference - right.difference);
  return candidates[0]?.workout ?? null;
}
