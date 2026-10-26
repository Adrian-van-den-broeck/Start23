import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { CheckInScreen } from '@/screens/CheckInScreen';
import { useOptionalPlanningFlow } from '@/features/planning/PlanningFlowProvider';
import { TrainingReadiness } from '@/navigation/TrainingFlowHost';

export default function CheckInRoute() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  const planning = useOptionalPlanningFlow();
  if (!session) return null;
  if (!planning) return <TrainingReadiness />;
  return (
    <CheckInScreen
      athleteIdentity={session.user.id}
      accessToken={session.access_token}
      onBack={() => router.replace('/planning')}
      onSignOut={signOut}
    />
  );
}
