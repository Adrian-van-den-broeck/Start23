import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { ActivityScreen } from '@/screens/ActivityScreen';

export default function ActivitiesRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <ActivityScreen
      accessToken={session.access_token}
      onBack={() => router.replace('/planning')}
      onSignOut={signOut}
    />
  );
}
