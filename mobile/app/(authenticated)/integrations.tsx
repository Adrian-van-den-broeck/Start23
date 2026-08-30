import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { IntegrationsScreen } from '@/screens/IntegrationsScreen';

export default function IntegrationsRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <IntegrationsScreen
      accessToken={session.access_token}
      onBack={() => router.replace('/planning')}
      onOpenActivities={() => router.push('/activities')}
      onSignOut={signOut}
    />
  );
}
