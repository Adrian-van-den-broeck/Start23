import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  initialWindowMetrics,
  SafeAreaProvider,
} from 'react-native-safe-area-context';

import { AuthProvider, useAuth } from './src/auth/AuthProvider';
import { listActivities } from './src/api/client';
import { AuthScreen } from './src/screens/AuthScreen';
import { ActivityScreen } from './src/screens/ActivityScreen';
import { CalibrationScreen } from './src/screens/CalibrationScreen';
import { CheckInScreen } from './src/screens/CheckInScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { PlanningScreen } from './src/screens/PlanningScreen';
import { colors, spacing } from './src/theme/tokens';

function AppContent() {
  const { configurationError, loading, session, signOut } = useAuth();
  const [authenticatedView, setAuthenticatedView] = useState<
    'onboarding' | 'planning' | 'activities' | 'checkin' | 'calibration'
  >('onboarding');
  const [pendingRpeCount, setPendingRpeCount] = useState(0);

  useEffect(() => {
    if (!session) {
      setPendingRpeCount(0);
      return;
    }
    let mounted = true;
    listActivities(session.access_token, true)
      .then((activities) => {
        if (mounted) setPendingRpeCount(activities.length);
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [session]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.brand} size="large" />
      </View>
    );
  }

  if (configurationError) {
    return (
      <View style={styles.centered}>
        <Text style={styles.configurationTitle}>Configuratie ontbreekt</Text>
        <Text style={styles.configurationText}>{configurationError}</Text>
      </View>
    );
  }

  if (!session) {
    return <AuthScreen />;
  }

  let screen;
  if (authenticatedView === 'planning') {
    screen = (
      <PlanningScreen
        accessToken={session.access_token}
        onBackToOnboarding={() => setAuthenticatedView('onboarding')}
        onOpenActivities={() => setAuthenticatedView('activities')}
        onOpenCheckIn={() => setAuthenticatedView('checkin')}
        onSignOut={signOut}
      />
    );
  } else if (authenticatedView === 'activities') {
    screen = (
      <ActivityScreen
        accessToken={session.access_token}
        onBack={() => setAuthenticatedView('planning')}
        onPendingRpeChange={setPendingRpeCount}
        onSignOut={signOut}
      />
    );
  } else if (authenticatedView === 'checkin') {
    screen = (
      <CheckInScreen
        accessToken={session.access_token}
        onBack={() => setAuthenticatedView('planning')}
        onSignOut={signOut}
      />
    );
  } else if (authenticatedView === 'calibration') {
    screen = (
      <CalibrationScreen
        accessToken={session.access_token}
        onBack={() => setAuthenticatedView('onboarding')}
        onSignOut={signOut}
      />
    );
  } else {
    screen = (
      <OnboardingScreen
        accessToken={session.access_token}
        onOpenCalibration={() => setAuthenticatedView('calibration')}
        onOpenPlanning={() => setAuthenticatedView('planning')}
        onSignOut={signOut}
      />
    );
  }

  return (
    <View style={styles.appShell}>
      {pendingRpeCount > 0 ? (
        <Pressable
          accessibilityRole="button"
          onPress={() => setAuthenticatedView('activities')}
          style={styles.feedbackReminder}
        >
          <Text style={styles.feedbackReminderText}>
            {pendingRpeCount} training{pendingRpeCount === 1 ? '' : 'en'} wacht
            {pendingRpeCount === 1 ? '' : 'en'} op RPE · open Training & RPE
          </Text>
        </Pressable>
      ) : null}
      <View style={styles.screen}>{screen}</View>
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      <StatusBar style="dark" />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  appShell: { backgroundColor: colors.canvas, flex: 1 },
  screen: { flex: 1 },
  feedbackReminder: {
    backgroundColor: colors.accentSoft,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  feedbackReminderText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '800',
    textAlign: 'center',
  },
  centered: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    flex: 1,
    gap: spacing.md,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  configurationTitle: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: '800',
  },
  configurationText: {
    color: colors.inkMuted,
    lineHeight: 20,
    textAlign: 'center',
  },
});
