import type { SwipeWeekDraft, SwipeWorkoutOccurrence, WorkoutDeckItem } from '../../api/types';
import { workoutCardDescription } from '../../lib/workoutPresentation';
import { warningPresentation } from '../../components/MoveWarningPanel';

// Public allowlist. Template identity and occurrence identity are independent.
export function selectionWorkoutViewModel(workout: SwipeWorkoutOccurrence) {
  return {
    templateId: workout.id,
    templateKey: workout.template_key,
    templateVersion: workout.version,
    occurrenceId: workout.occurrence_id,
    name: workout.name,
    discipline: workout.discipline,
    durationMinutes: workout.duration_minutes,
    distanceMeters: workout.distance_meters,
    intensity: workout.intensity_bucket,
    description: workoutCardDescription(workout.description),
  };
}
export type SelectionWorkout = ReturnType<typeof selectionWorkoutViewModel>;

// A previewed card has no occurrence yet; the saved transition assigns one.
function previewWorkoutViewModel(workout: WorkoutDeckItem | null | undefined): SelectionWorkout | null {
  return workout ? selectionWorkoutViewModel({ ...workout, occurrence_id: `preview:${workout.id}` }) : null;
}

export function planningCreationViewModel(draft: SwipeWeekDraft) {
  return {
    id: draft.id,
    revision: draft.revision,
    state: draft.state,
    weekStart: draft.week_start,
    availableDates: [...draft.available_dates],
    candidate: draft.current_candidate ? selectionWorkoutViewModel(draft.current_candidate) : null,
    upcoming: {
      accept: previewWorkoutViewModel(draft.upcoming_candidates?.after_accept),
      pass: previewWorkoutViewModel(draft.upcoming_candidates?.after_pass),
    },
    accepted: draft.accepted_workouts.map(selectionWorkoutViewModel),
    placements: draft.placements.map((placement) => ({
      occurrenceId: placement.occurrence_id, date: placement.scheduled_date,
    })),
    canUndo: draft.can_undo,
    passedCount: draft.passed_count,
    exhausted: draft.exhausted,
    warnings: draft.warnings.map(warningPresentation),
  };
}
export type PlanningCreationModel = ReturnType<typeof planningCreationViewModel>;
