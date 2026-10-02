import type { PlannedWorkout } from '../../api/types';
import { workoutCardDescription } from '../../lib/workoutPresentation';

export type WorkoutMeasures = Readonly<{
  durationMinutes: string | null;
  distanceMeters: number | null;
}>;
export type WorkoutSummaryViewModel = Readonly<{
  discipline: PlannedWorkout['discipline'];
  name: string;
  description: string;
  measures: WorkoutMeasures;
  intensity: PlannedWorkout['intensity_bucket'];
  date: string;
  status: PlannedWorkout['status'];
}>;

export function workoutSummaryViewModel(workout: PlannedWorkout): WorkoutSummaryViewModel {
  return {
    discipline: workout.discipline,
    name: workout.name,
    description: workoutCardDescription(workout.description),
    measures: {
      durationMinutes: workout.duration_minutes ?? null,
      distanceMeters: workout.distance_meters ?? null,
    },
    intensity: workout.intensity_bucket,
    date: workout.scheduled_date,
    status: workout.status,
  };
}
