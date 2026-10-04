import { createContext, type PropsWithChildren, useContext } from 'react';

import { useLanguage } from '../../i18n/LanguageProvider';
import { useCalendarController } from '../calendar/useCalendarController';
import { type PlanningController, usePlanningController } from './usePlanningController';

const PlanningContext = createContext<PlanningController | null>(null);
const CalendarContext = createContext<ReturnType<typeof useCalendarController> | null>(null);

type PlanningFlowProps = PropsWithChildren<{
  accessToken: string;
  // Local lifetime isolation only; never sent to the planning API.
  athleteIdentity?: string;
}>;

function PlanningOwner({ accessToken, children }: PlanningFlowProps) {
  const controller = usePlanningController(accessToken);
  const { language } = useLanguage();
  const calendar = useCalendarController(accessToken, language, controller.setError);
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
