import { createContext, useContext, useRef, useState, type PropsWithChildren } from 'react';
import type { PlannedWorkout } from '../api/types';
import { useCalendarNavigation } from '../features/calendar/useCalendarNavigation';
import { usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { useUiVersion } from '../ui/UiVersionProvider';

function usePresentationOwner() {
  const flow = usePlanningFlow();
  const { effectiveVersion } = useUiVersion();
  const [rootVersion, setRootVersion] = useState(() => effectiveVersion('week'));
  const [calendarVersion, setCalendarVersion] = useState(() => effectiveVersion('calendar'));
  const [task, setTask] = useState<'prepare' | 'creation' | 'review' | 'existing' | null>(null);
  const [reviewWorkoutId, setReviewWorkoutId] = useState<string | null>(null);
  // Navigation choices only; draft, revision and placements belong to flow.
  const [creationStep, setCreationStep] = useState<'selection' | 'placement'>('selection');
  const [placementMode, setPlacementMode] = useState<'automatic' | 'manual'>('automatic');
  const [detailWorkout, setDetailWorkout] = useState<PlannedWorkout | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [calendarVisited, setCalendarVisited] = useState(false);
  const [activityBusy, setActivityBusy] = useState(false);
  const [transientBusy, setTransientBusy] = useState(false);
  const weekScroll = useRef(0);
  const calendarPositions = useRef<Record<string, number>>({});
  const calendarNavigation = useCalendarNavigation(flow.plan?.week_start ?? flow.weekStart, calendarVisited);
  const locked = flow.busy || transientBusy || !!flow.pendingMove || Object.values(flow.pendingWorkouts.editors).some((slot) => slot.loading);
  return {
    rootVersion, setRootVersion, calendarVersion, setCalendarVersion, task, setTask,
    reviewWorkoutId, setReviewWorkoutId,
    creationStep, setCreationStep, placementMode, setPlacementMode,
    detailWorkout, setDetailWorkout, sheetOpen, setSheetOpen, weekScroll, calendarPositions,
    calendarNavigation, setCalendarVisited, activityBusy, setActivityBusy, setTransientBusy,
    locked, navigationLocked: locked || activityBusy || !!task || !!detailWorkout || sheetOpen
  };
}

const Context = createContext<ReturnType<typeof usePresentationOwner> | null>(null);
export function PlanningPresentationProvider({ children }: PropsWithChildren) {
  const value = usePresentationOwner();
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function usePlanningPresentation() {
  const value = useContext(Context);
  if (!value) throw new Error('Planning presentation requires its shared host');
  return value;
}
export function useOptionalPlanningPresentation() {
  return useContext(Context);
}
