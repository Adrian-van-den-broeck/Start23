import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { backToPreviousOrPlanning } from '@/lib/navigation';
import { CalibrationScreen } from '@/screens/CalibrationScreen';

export default function TestsRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <CalibrationScreen
      accessToken={session.access_token}
      onBack={() => backToPreviousOrPlanning(router)}
      onSignOut={signOut}
    />
  );
}
