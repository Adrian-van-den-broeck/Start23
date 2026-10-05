import { createContext, useContext, type PropsWithChildren } from 'react';
import { useActivityController, type ActivityController } from './useActivityController';

const ActivityContext = createContext<ActivityController | null>(null);

export function ActivityFlowProvider({ accessToken, athleteIdentity, children }: PropsWithChildren<{
  accessToken: string; athleteIdentity: string;
}>) {
  if (useContext(ActivityContext)) throw new Error('ActivityFlowProvider must not be nested');
  return <ActivityOwner key={athleteIdentity} accessToken={accessToken}>{children}</ActivityOwner>;
}

function ActivityOwner({ accessToken, children }: PropsWithChildren<{ accessToken: string }>) {
  const value = useActivityController(accessToken);
  return <ActivityContext.Provider value={value}>{children}</ActivityContext.Provider>;
}

export function useActivityFlow(): ActivityController {
  const value = useContext(ActivityContext);
  if (!value) throw new Error('Activity flow requires ActivityFlowProvider');
  return value;
}
