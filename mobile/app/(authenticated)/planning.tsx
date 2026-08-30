import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { PlanningScreen } from '@/screens/PlanningScreen';

export default function PlanningRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <PlanningScreen
      accessToken={session.access_token}
      onBackToOnboarding={() => router.push('/onboarding')}
      onOpenActivities={() => router.push('/activities')}
      onOpenCheckIn={() => router.push('/check-in')}
      onOpenIntegrations={() => router.push('/integrations')}
      onOpenZoneProfile={(planId, revision) =>
        router.push({
          pathname: '/zone-profile',
          params: {
            ...(planId ? { planId } : {}),
            ...(revision ? { revision: String(revision) } : {}),
          },
        })
      }
      onSignOut={signOut}
    />
  );
}
