import { Redirect } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { ScreenState } from '@/components/ScreenState';
import { AuthScreen } from '@/screens/AuthScreen';

export default function IndexRoute() {
  const { configurationError, loading, session } = useAuth();

  if (loading) return <ScreenState loading title="Start23 wordt klaargezet" />;
  if (configurationError) {
    return <ScreenState message={configurationError} title="Configuratie ontbreekt" />;
  }
  if (session) return <Redirect href="/onboarding" />;
  return <AuthScreen />;
}
