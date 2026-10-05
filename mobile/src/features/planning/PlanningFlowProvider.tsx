import { createContext, type PropsWithChildren, useContext, useEffect, useRef } from 'react';

import { useLanguage } from '../../i18n/LanguageProvider';
import type { OnboardingState, WeeklyPlan } from '../../api/types';
import { useCalendarController } from '../calendar/useCalendarController';
import { type PlanningController, usePlanningController } from './usePlanningController';

const PlanningContext = createContext<PlanningController | null>(null);
const CalendarContext = createContext<ReturnType<typeof useCalendarController> | null>(null);

type PlanningFlowProps = PropsWithChildren<{
  accessToken: string;
  // Local lifetime isolation only; never sent to the planning API.
  athleteIdentity?: string;
  initialOnboarding?: OnboardingState;
}>;

function PlanningOwner({ accessToken, initialOnboarding, children }: PlanningFlowProps) {
  const controller = usePlanningController(accessToken, initialOnboarding);
  const { language } = useLanguage();
  const calendar = useCalendarController(accessToken, language, controller.setError);
  const { invalidateCalendarRange, replaceApprovedPlan } = calendar;
  const previousPlan = useRef<WeeklyPlan | null>(null);
  // Approved calendar data is reusable across roots, but a changed approved
  // plan context invalidates it. Pending draft edits alone do not reload it.
  useEffect(() => {
    const previous = previousPlan.current;
    const updated = controller.plan;
    if (previous?.revision_state === 'active' && updated?.revision_state === 'active' &&
      previous.id === updated.id && previous.week_start === updated.week_start && previous.active_revision !== updated.active_revision) {
      replaceApprovedPlan(previous, updated);
    } else invalidateCalendarRange();
    previousPlan.current = updated;
  }, [controller.plan?.id, controller.plan?.active_revision, invalidateCalendarRange, replaceApprovedPlan]);
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

export function usePlanningCalendar() {
  const value = useContext(CalendarContext);
  if (!value) throw new Error('usePlanningCalendar must be used inside PlanningFlowProvider');
  return value;
}
