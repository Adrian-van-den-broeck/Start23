import { useLocalSearchParams, useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { ZoneProfileScreen } from '@/screens/ZoneProfileScreen';

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default function ZoneProfileRoute() {
  const router = useRouter();
  const params = useLocalSearchParams<{ planId?: string; revision?: string }>();
  const { session, signOut } = useAuth();
  if (!session) return null;
  const planId = first(params.planId);
  const revisionValue = Number(first(params.revision));
  const planContext =
    planId && Number.isInteger(revisionValue) && revisionValue > 0
      ? { planId, revision: revisionValue }
      : null;
  return (
    <ZoneProfileScreen
      accessToken={session.access_token}
      onBack={() => router.replace('/planning')}
      onSignOut={signOut}
      planContext={planContext}
    />
  );
}
