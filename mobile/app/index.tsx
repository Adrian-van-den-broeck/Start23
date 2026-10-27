import { Redirect } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { ScreenState } from '@/components/ScreenState';
import { AuthScreen } from '@/screens/AuthScreen';
import { AuthRecoveryState } from '@/auth/AuthRecoveryState';

export default function IndexRoute() {
  const { configurationError, loading, session, recovery } = useAuth();

  if (loading) return <ScreenState loading title="Wombo wordt klaargezet" />;
  if (configurationError) {
    return <ScreenState message={configurationError} title="Configuratie ontbreekt" />;
  }
  if (session) return <Redirect href="/onboarding" />;
  if (recovery) return <AuthRecoveryState />;
  return <AuthScreen />;
}
