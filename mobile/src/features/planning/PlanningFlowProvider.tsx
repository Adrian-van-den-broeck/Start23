import { createContext, type PropsWithChildren, useContext, useEffect, useRef } from 'react';

import { useOptionalActivityFlow } from '../activities/ActivityFlowProvider';
import { useLanguage } from '../../i18n/LanguageProvider';
import type { OnboardingState, WeeklyPlan } from '../../api/types';
import { useCalendarController } from '../calendar/useCalendarController';
import { type PlanningController, usePlanningController } from './usePlanningController';

const PlanningContext = createContext<PlanningController | null>(null);
const CalendarContext = createContext<ReturnType<typeof useCalendarController> | null>(null);

type PlanningFlowProps = PropsWithChildren<{
  accessToken: string;
  // Auth subject for local lifetime/storage isolation; never sent to the planning API.
  athleteIdentity: string;
  initialOnboarding?: OnboardingState;
}>;

function PlanningOwner({ accessToken, athleteIdentity, initialOnboarding, children }: PlanningFlowProps) {
  const controller = usePlanningController(accessToken, athleteIdentity, initialOnboarding);
  const { language } = useLanguage();
  const calendar = useCalendarController(accessToken, language, controller.setError);
  const { invalidateCalendarRange, replaceApprovedPlan, acceptApprovedPlan } = calendar;
  const previousPlan = useRef<WeeklyPlan | null>(null);
  const activityFlow = useOptionalActivityFlow();
  const invalidateActivities = activityFlow?.invalidateActivities;
  const active = controller.activePlan;
  const approvedIdentity = active ? `${active.id}:${active.revision_id}:${active.revision}` : null;
  const previousApprovedIdentity = useRef<string | null>(null);
  useEffect(() => {
    if (approvedIdentity && previousApprovedIdentity.current !== approvedIdentity &&
      (previousApprovedIdentity.current !== null || controller.taskHandoff?.plan === active)) invalidateActivities?.();
    if (approvedIdentity) previousApprovedIdentity.current = approvedIdentity;
  }, [approvedIdentity, active, controller.taskHandoff, invalidateActivities]);
  // Approved calendar data is reusable across roots, but a changed approved
  // plan context invalidates it. Pending draft edits alone do not reload it.
  useEffect(() => {
    const previous = previousPlan.current;
    const updated = controller.plan;
    if (updated?.revision_state === 'active' && controller.taskHandoff?.plan === updated) {
      acceptApprovedPlan(updated);
    } else if (previous?.revision_state === 'active' && updated?.revision_state === 'active' &&
      previous.id === updated.id && previous.week_start === updated.week_start && previous.active_revision !== updated.active_revision) {
      replaceApprovedPlan(previous, updated);
    } else invalidateCalendarRange();
    previousPlan.current = updated;
  }, [controller.plan?.id, controller.plan?.active_revision, controller.recoveryVersion, invalidateCalendarRange, replaceApprovedPlan, acceptApprovedPlan]);
  return (
    <PlanningContext.Provider value={controller}>
      <CalendarContext.Provider value={calendar}>{children}</CalendarContext.Provider>
    </PlanningContext.Provider>
  );
}

export function PlanningFlowProvider(props: PlanningFlowProps) {
  const existing = useContext(PlanningContext);
  if (existing) throw new Error('Planning flow already has an owner');
  return <PlanningOwner key={props.athleteIdentity} {...props} />;
}

export function usePlanningFlow(): PlanningController {
  const value = useContext(PlanningContext);
  if (!value) throw new Error('usePlanningFlow must be used inside PlanningFlowProvider');
  return value;
}

export function useOptionalPlanningFlow(): PlanningController | null {
  return useContext(PlanningContext);
}

export function usePlanningCalendar() {
  const value = useContext(CalendarContext);
  if (!value) throw new Error('usePlanningCalendar must be used inside PlanningFlowProvider');
  return value;
}
