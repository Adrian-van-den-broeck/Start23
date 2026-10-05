import { type Href, useRouter, useIsFocused } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { PlanningBoundary } from '@/screens/PlanningScreen';

export default function PlanningRoute({ destination = 'week' }: { destination?: 'week' | 'calendar'; }) {
  const router = useRouter();
  const active = useIsFocused();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <PlanningBoundary
      active={active}
      destination={destination}
      onCalendarRoot={() => router.navigate('/calendar')}
      onWeekRoot={() => router.navigate('/planning')}
      onBackToOnboarding={() => router.push('/onboarding')}
      onOpenActivities={() => router.push('/activities')}
      onOpenCheckIn={() => router.push('/check-in')}
      onOpenIntegrations={() => router.push('/integrations')}
      onOpenProfile={() => router.push('/profile' as Href)}
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
