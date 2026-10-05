import { useEffect, useRef, useState, type ReactNode } from 'react';
import type { PlannedWorkout } from '../api/types';
import { usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { ProposalAlternativesScreen, ProposalReviewScreen } from '../ui-v2/screens/ProposalReviewScreens';
import { proposalAlternativesViewModel, proposalReviewViewModel } from '../ui-v2/utils/proposalReviewViewModel';

export function PlanningProposalTask({ controls, busy, workoutId, onEdit, onBack }: {
  controls: ReactNode; busy: boolean; workoutId: string | null; onEdit: (id: string | null) => void; onBack: () => void;
}) {
  const flow = usePlanningFlow();
  // Retain only the render reference to detect a changed reviewed snapshot.
  const previousPlan = useRef(flow.plan);
  const changed = previousPlan.current !== flow.plan;
  useEffect(() => {
    if (previousPlan.current !== flow.plan) { previousPlan.current = flow.plan; onEdit(null); }
  }, [flow.plan, onEdit]);
  if (!flow.plan) return null;
  const model = proposalReviewViewModel(flow.plan);
  const workout = !changed && model.pending ? flow.plan.workouts.find((item) => item.id === workoutId) : undefined;
  return workout ? <PendingAlternativesTask controls={controls} busy={busy} workout={workout} onBack={() => onEdit(null)} />
    : <ProposalReviewScreen controls={controls} busy={busy} error={flow.error} model={model}
      onBack={onBack} onApprove={flow.approve} onReject={flow.reject} onEdit={onEdit} />;
}

function PendingAlternativesTask({ controls, busy, workout, onBack }: {
  controls: ReactNode; busy: boolean; workout: PlannedWorkout; onBack: () => void;
}) {
  const flow = usePlanningFlow();
  const { load, apply, release } = flow.pendingWorkouts;
  const slot = flow.pendingWorkouts.editors[workout.id];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  useEffect(() => { void load(workout.id, () => setSelectedId(null)); }, [load, workout.id]);
  useEffect(() => () => release(workout.id), [release, workout.id]);
  if (!flow.plan) return null;
  const model = proposalReviewViewModel(flow.plan);
  const edit = async (replacement: string | null) => { if (await apply(workout.id, replacement)) onBack(); };
  return <ProposalAlternativesScreen controls={controls} busy={busy} loading={slot?.loading ?? false} error={flow.error}
    model={model} workout={model.workouts.find((item) => item.id === workout.id)!}
    options={slot?.options ? proposalAlternativesViewModel({ ...slot.options, alternatives: slot.options.alternatives.filter((item) => item.id !== workout.template_id) }) : null}
    selectedId={selectedId} onSelect={setSelectedId} onBack={onBack}
    onRetry={() => { void load(workout.id, () => setSelectedId(null)); }}
    onReplace={() => { if (selectedId) void edit(selectedId); }} onRemove={() => { void edit(null); }} />;
}
