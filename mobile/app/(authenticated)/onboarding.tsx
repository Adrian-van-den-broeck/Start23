import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

export default function OnboardingRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <OnboardingScreen
      accessToken={session.access_token}
      onOpenCalibration={() => router.push('/calibration')}
      onOpenPlanning={() => router.push('/planning')}
      onSignOut={signOut}
    />
  );
}
