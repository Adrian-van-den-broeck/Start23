import { useIsFocused, useRouter } from 'expo-router';
import { useEffect } from 'react';
import { BackHandler } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { ActivityScreen } from '@/screens/ActivityScreen';
import { usePlanningPresentation } from '@/navigation/PlanningPresentationProvider';

export default function ActivitiesRoute() {
  const router = useRouter();
  const active = useIsFocused();
  const { rootVersion, activityBusy, setActivityBusy } = usePlanningPresentation();
  const { session, signOut } = useAuth();
  useEffect(() => {
    if (!active || !activityBusy) return;
    const handler = BackHandler.addEventListener('hardwareBackPress', () => true);
    return () => handler.remove();
  }, [active, activityBusy]);
  if (!session) return null;
  return (
    <ActivityScreen
      accessToken={session.access_token}
      onBack={() => { if (!activityBusy) { if (rootVersion === 'v2') router.navigate('/planning'); else router.replace('/planning'); } }}
      onNavigationBusyChange={setActivityBusy}
      onOpenProfile={rootVersion === 'v2' ? () => router.push('/profile') : undefined}
      onSignOut={signOut}
    />
  );
}
