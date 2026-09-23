import { type Href, useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { backToPreviousOrPlanning } from '@/lib/navigation';
import { ProfileScreen } from '@/screens/ProfileScreen';

export default function ProfileRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) return null;
  return (
    <ProfileScreen
      accessToken={session.access_token}
      onBack={() => backToPreviousOrPlanning(router)}
      onOpenPioneerAccess={() => router.push('/pioneer-access' as Href)}
      onOpenTests={() => router.push('/tests' as Href)}
      onSignOut={signOut}
    />
  );
}
