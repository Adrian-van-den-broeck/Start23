import { BlurView } from 'expo-blur';
import { Redirect, Stack, usePathname, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { listActivities } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { MotionPressable } from '@/components/MotionPressable';
import { ScreenState } from '@/components/ScreenState';
import { colors, spacing } from '@/theme/tokens';

export default function AuthenticatedLayout() {
  const { configurationError, loading, session } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
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
  }, [pathname, session]);

  if (loading) return <ScreenState loading title="Je sessie wordt gecontroleerd" />;
  if (configurationError || !session) return <Redirect href="/" />;

  return (
    <View style={styles.shell}>
      {pendingRpeCount > 0 ? (
        <MotionPressable
          accessibilityRole="button"
          haptic="selection"
          onPress={() => router.push('/activities')}
        >
          <BlurView intensity={55} style={styles.reminder} tint="light">
            <Text style={styles.reminderText}>
              {pendingRpeCount} training{pendingRpeCount === 1 ? '' : 'en'} wacht
              {pendingRpeCount === 1 ? '' : 'en'} op RPE · open Training & RPE
            </Text>
          </BlurView>
        </MotionPressable>
      ) : null}
      <Stack
        screenOptions={{
          animation: 'fade_from_bottom',
          animationDuration: 220,
          contentStyle: { backgroundColor: colors.canvas },
          headerShown: false,
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { backgroundColor: colors.canvas, flex: 1 },
  reminder: {
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
