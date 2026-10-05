import { BlurView } from 'expo-blur';
import { Redirect, Stack, usePathname, useRouter } from 'expo-router';
import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { TrainingFlowHost } from '@/navigation/TrainingFlowHost';
import { useOptionalPlanningPresentation } from '@/navigation/PlanningPresentationProvider';

import { ActivityFlowProvider, useActivityFlow } from '@/features/activities/ActivityFlowProvider';
import { useAuth } from '@/auth/AuthProvider';
import { MotionPressable } from '@/components/MotionPressable';
import { useLanguage } from '@/i18n/LanguageProvider';
import { ScreenState } from '@/components/ScreenState';
import { colors, spacing } from '@/theme/tokens';

export default function AuthenticatedLayout() {
  const { configurationError, loading, session } = useAuth();
  if (loading) return <ScreenState loading title="Je sessie wordt gecontroleerd" />;
  if (configurationError || !session) return <Redirect href="/" />;

  return (
    <View style={styles.shell}>
      <ActivityFlowProvider accessToken={session.access_token} athleteIdentity={session.user.id}>
      <TrainingFlowHost key={session.user.id} accessToken={session.access_token} athleteIdentity={session.user.id}>
        <PendingRpeReminder accessToken={session.access_token} />
        <Stack
          screenOptions={{
            animation: 'fade_from_bottom',
            animationDuration: 220,
            contentStyle: { backgroundColor: colors.canvas },
            headerShown: false,
          }}
        />
      </TrainingFlowHost>
      </ActivityFlowProvider>
    </View>
  );
}

function PendingRpeReminder({ accessToken }: { accessToken: string; }) {
  const { pendingRpe, refreshPendingRpe } = useActivityFlow();
  const count = pendingRpe.length;
  const pathname = usePathname();
  useEffect(() => { void refreshPendingRpe(pathname); }, [pathname, accessToken, refreshPendingRpe]);
  const { language, t } = useLanguage();
  const router = useRouter();
  const presentation = useOptionalPlanningPresentation();
  return count > 0 ? (
    <SafeAreaView edges={['top']}>
      <MotionPressable
        accessibilityRole="button"
        haptic="selection"
        disabled={presentation?.navigationLocked}
        onPress={() => { if (presentation?.rootVersion === 'v2') router.navigate('/activities'); else router.push('/activities'); }}
      >
        <BlurView intensity={55} style={styles.reminder} tint="light">
          <Text style={styles.reminderText}>
            {t('rpe.reminder', {
              count,
              suffix: count === 1 ? '' : language === 'nl' ? 'en' : 's',
              verbSuffix: count === 1 ? '' : 'en',
            })}
          </Text>
        </BlurView>
      </MotionPressable>
    </SafeAreaView>
  ) : null;
}

const styles = StyleSheet.create({
  shell: { backgroundColor: colors.canvas, flex: 1 },
  reminder: {
    minHeight: 48,
    justifyContent: 'center',
    backgroundColor: 'rgba(253, 229, 221, 0.78)',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  reminderText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '800',
    textAlign: 'center',
  },
});
