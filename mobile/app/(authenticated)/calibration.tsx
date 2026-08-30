import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { CalibrationScreen } from '@/screens/CalibrationScreen';

export default function CalibrationRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <CalibrationScreen
      accessToken={session.access_token}
      onBack={() => router.replace('/onboarding')}
      onSignOut={signOut}
    />
  );
}
