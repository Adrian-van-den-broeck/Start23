import { type Href, useIsFocused, useRouter } from 'expo-router';
import { useCallback } from 'react';

import { useAuth } from '@/auth/AuthProvider';
import { useOnboardingSnapshot } from '@/navigation/TrainingFlowHost';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

export default function OnboardingRoute() {
  const router = useRouter();
  const active = useIsFocused();
  const { session, signOut } = useAuth();
  const takeOnboardingSnapshot = useOnboardingSnapshot();
  const openPlanning = useCallback(() => router.replace('/planning'), [router]);
  if (!session) return null;
  return (
    <OnboardingScreen
      accessToken={session.access_token}
      active={active}
      takeOnboardingSnapshot={takeOnboardingSnapshot}
      onOpenCalibration={() => router.push('/tests' as Href)}
      onOpenPlanning={openPlanning}
      onSignOut={signOut}
    />
  );
}
