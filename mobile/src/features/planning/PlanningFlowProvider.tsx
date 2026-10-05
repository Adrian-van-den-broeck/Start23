import { createContext, type PropsWithChildren, useContext, useEffect } from 'react';

import { useLanguage } from '../../i18n/LanguageProvider';
import type { OnboardingState } from '../../api/types';
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
  const { invalidateCalendarRange } = calendar;
  // Approved calendar data is reusable across roots, but a changed approved
  // plan context invalidates it. Pending draft edits alone do not reload it.
  useEffect(() => {
    invalidateCalendarRange();
  }, [controller.plan?.id, controller.plan?.active_revision, invalidateCalendarRange]);
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
