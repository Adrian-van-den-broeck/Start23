import { type Href, useIsFocused, useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

export default function OnboardingRoute() {
  const router = useRouter();
  const active = useIsFocused();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <OnboardingScreen
      accessToken={session.access_token}
      active={active}
      onOpenCalibration={() => router.push('/tests' as Href)}
      onOpenPlanning={() => router.push('/planning')}
      onSignOut={signOut}
    />
  );
}
