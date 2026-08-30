import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { CheckInScreen } from '@/screens/CheckInScreen';

export default function CheckInRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <CheckInScreen
      accessToken={session.access_token}
      onBack={() => router.replace('/planning')}
      onSignOut={signOut}
    />
  );
}
