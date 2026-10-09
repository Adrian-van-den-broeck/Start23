import { useIsFocused, useRouter } from 'expo-router';
import { useEffect } from 'react';
import { BackHandler } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { ActivityBoundary } from '@/ui/ActivityBoundary';
import { effectiveUiVersion } from '@/ui/uiVersion';
import { usePlanningPresentation } from '@/navigation/PlanningPresentationProvider';

export default function ActivitiesRoute() {
  const router = useRouter();
  const active = useIsFocused();
  const { rootVersion, setRootVersion, setCalendarVersion, navigationLocked,
    activityBusy, setActivityBusy, activityView, setActivityView, activityCorrectionId, setActivityCorrectionId,
  } = usePlanningPresentation();
  const { session, signOut } = useAuth();
  const version = effectiveUiVersion(rootVersion, 'activities');
  const taskOpen = version === 'v2' && (activityView !== 'history' || !!activityCorrectionId);
  useEffect(() => {
    if (!active || (!activityBusy && !taskOpen)) return;
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!activityBusy) { setActivityView('history'); setActivityCorrectionId(null); }
      return true;
    });
    return () => handler.remove();
  }, [active, activityBusy, taskOpen, setActivityView, setActivityCorrectionId]);
  if (!session) return null;
  return (
    <ActivityBoundary version={version} view={activityView} onView={setActivityView}
      correctionId={activityCorrectionId} onCorrection={setActivityCorrectionId} switchLocked={navigationLocked}
      onVersion={next => {
        if (!navigationLocked) {
          setRootVersion(effectiveUiVersion(next, 'week'));
          setCalendarVersion(effectiveUiVersion(next, 'calendar'));
        }
      }}
      onBack={() => { if (!activityBusy) { if (rootVersion === 'v2') router.navigate('/planning'); else router.replace('/planning'); } }}
      onNavigationBusyChange={setActivityBusy}
      onOpenProfile={rootVersion === 'v2' ? () => router.push('/profile') : undefined}
      onSignOut={signOut}
    />
  );
}
