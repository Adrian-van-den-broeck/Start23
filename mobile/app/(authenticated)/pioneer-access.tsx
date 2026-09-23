import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { backToPreviousOrPlanning } from '@/lib/navigation';
import { PioneerAccessScreen } from '@/screens/PioneerAccessScreen';

export default function PioneerAccessRoute() {
  const router = useRouter();
  const { session } = useAuth();
  if (!session) return null;
  return (
    <PioneerAccessScreen
      accessToken={session.access_token}
      onBack={() => backToPreviousOrPlanning(router)}
    />
  );
}
