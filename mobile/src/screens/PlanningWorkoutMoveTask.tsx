import { useEffect, useRef, type ReactNode } from 'react';
import { Modal } from 'react-native';
import { usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { warningPresentation } from '../components/MoveWarningPanel';
import { WorkoutMoveScreen } from '../ui-v2/screens/WorkoutMoveScreen';
import { workoutSummaryViewModel } from '../ui-v2/utils/workoutSummaryViewModel';

// Only presentation selection lives here; validation and intent belong to flow.
export function PlanningWorkoutMoveTask({ workoutId, onClose, controls }: {
  workoutId: string; onClose: () => void; controls: ReactNode;
}) {
  const flow = usePlanningFlow();
  const origin = useRef(flow.plan).current;
  const workout = origin?.workouts.find(item => item.id === workoutId);
  const available = flow.plan === origin && origin?.revision_state === 'active' && workout?.status === 'scheduled';
  useEffect(() => {
    if (flow.plan !== origin && !flow.busy && !flow.pendingMove) onClose();
  }, [flow.plan, flow.busy, flow.pendingMove, origin, onClose]);
  const cancel = () => {
    if (flow.busy) return;
    flow.cancelWorkoutMove();
    onClose();
  };
  if (!workout || !origin) return null;
  const review = flow.pendingMove;
  return <Modal testID="workout-move-modal" visible animationType="none" onRequestClose={cancel}>
    <WorkoutMoveScreen summary={workoutSummaryViewModel(workout)} currentDate={workout.scheduled_date} weekStart={origin.week_start}
      available={!!available && (!review || review.reviewedPlan === origin && review.workout.id === workoutId)}
      targetDate={review?.scheduledDate ?? null} warnings={review ? review.warnings.map(warningPresentation) : null}
      busy={flow.busy} error={flow.error} controls={controls}
      onCancel={cancel} onConfirm={flow.confirmWorkoutMove} onReview={date => flow.requestWorkoutMove(workout, date)} />
  </Modal>;
}
