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
import { colors as finalColors } from '@/ui-v2/tokens';
import { ShellInsets } from '@/ui-v2/components/ShellInsets';
import { PendingRpeBanner } from '@/ui-v2/components/PendingRpeBanner';
import { useUiVersion } from '@/ui/UiVersionProvider';

export default function AuthenticatedLayout() {
  const { configurationError, loading, session } = useAuth();
  if (loading) return <ScreenState loading title="Je sessie wordt gecontroleerd" />;
  if (configurationError || !session) return <Redirect href="/" />;

  return (
    <View style={styles.shell}>
      <ActivityFlowProvider accessToken={session.access_token} athleteIdentity={session.user.id}>
      <TrainingFlowHost key={session.user.id} accessToken={session.access_token} athleteIdentity={session.user.id}>
        <AuthenticatedContent accessToken={session.access_token} />
      </TrainingFlowHost>
      </ActivityFlowProvider>
    </View>
  );
}

function AuthenticatedContent({ accessToken }: { accessToken: string }) {
  const { pendingRpe } = useActivityFlow();
  const presentation = useOptionalPlanningPresentation();
  const { effectiveVersion } = useUiVersion();
  const v2 = (presentation?.rootVersion ?? effectiveVersion('week')) === 'v2';
  return <View style={[styles.shell, v2 && { backgroundColor: finalColors.background }]}>
    <PendingRpeReminder accessToken={accessToken} v2={v2} />
    <ShellInsets top={v2 && pendingRpe.length > 0}>
      <Stack screenOptions={{ animation: 'fade_from_bottom', animationDuration: 220,
        contentStyle: { backgroundColor: v2 ? finalColors.background : colors.canvas }, headerShown: false }} />
    </ShellInsets>
  </View>;
}

function PendingRpeReminder({ accessToken, v2 }: { accessToken: string; v2: boolean }) {
  const { pendingRpe, refreshPendingRpe } = useActivityFlow();
  const count = pendingRpe.length;
  const pathname = usePathname();
  useEffect(() => { void refreshPendingRpe(pathname); }, [pathname, accessToken, refreshPendingRpe]);
  const { language, t } = useLanguage();
  const router = useRouter();
  const presentation = useOptionalPlanningPresentation();
  const label = t('rpe.reminder', { count, suffix: count === 1 ? '' : language === 'nl' ? 'en' : 's', verbSuffix: count === 1 ? '' : 'en' });
  const openFeedback = () => { if (presentation?.rootVersion === 'v2') { presentation.setActivityView('feedback'); presentation.setActivityCorrectionId(null); router.navigate('/activities'); } else router.push('/activities'); };
  if (count > 0 && v2) return <PendingRpeBanner label={label} disabled={!!presentation?.navigationLocked} onPress={openFeedback} />;
  return count > 0 ? (
    <SafeAreaView edges={['top']}>
      <MotionPressable
        accessibilityRole="button"
        haptic="selection"
        disabled={presentation?.navigationLocked}
        onPress={openFeedback}
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
