import type { createActivity } from '../../api/client';
import type { Discipline, PlannedExternalActivity, PlannedWorkout } from '../../api/types';
import { translate } from '../../i18n/runtime';

export function newIdempotencyKey(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (value) => {
    const random = Math.floor(Math.random() * 16);
    const digit = value === 'x' ? random : (random & 0x3) | 0x8;
    return digit.toString(16);
  });
}

export function activityCreateInput({ discipline, duration, distance, startedAt, athleteTimezone, selectedWorkout, selectedExternal }: {
  discipline: Discipline; duration: string; distance: string; startedAt: string; athleteTimezone: string;
  selectedWorkout: PlannedWorkout | null; selectedExternal: PlannedExternalActivity | null;
}): Parameters<typeof createActivity>[2] {
  if (!athleteTimezone) {
    throw new Error(translate('activities.timezoneMissing'));
  }
  const numericDuration = duration.trim() === '' ? null : Number(duration);
  const numericDistance = distance ? Number(distance) : undefined;
  if (
    numericDuration === null
      ? discipline !== 'swim' || numericDistance === undefined
      : !Number.isFinite(numericDuration) || numericDuration <= 0
  ) {
    throw new Error(translate('activityText.invalidDuration'));
  }
  if (
    numericDistance !== undefined &&
    (!Number.isInteger(numericDistance) || numericDistance <= 0)
  ) {
    throw new Error(translate('activityText.invalidDistance'));
  }
  if (Number.isNaN(new Date(startedAt).getTime())) {
    throw new Error(translate('activityText.invalidStartedAt'));
  }
  return {
    ...(selectedWorkout
      ? { planned_workout_id: selectedWorkout.id }
      : {}),
    ...(selectedExternal
      ? { planned_external_activity_id: selectedExternal.id }
      : {}),
    discipline,
    started_at: startedAt,
    timezone: athleteTimezone,
    duration_minutes: numericDuration === null ? null : String(numericDuration),
    ...(numericDistance === undefined
      ? {}
      : { distance_meters: numericDistance }),
  };
}
