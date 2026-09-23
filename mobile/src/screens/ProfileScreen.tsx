import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { getOnboarding, saveProfile } from '../api/client';
import type { AthleteProfile } from '../api/types';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { colors, radius, spacing } from '../theme/tokens';
import { ProfileStep } from './OnboardingScreen';

type Props = {
  accessToken: string;
  onBack: () => void;
  onOpenPioneerAccess: () => void;
  onOpenTests: () => void;
  onSignOut: () => Promise<void>;
};

export function ProfileScreen({
  accessToken,
  onBack,
  onOpenPioneerAccess,
  onOpenTests,
  onSignOut,
}: Props) {
  const [profile, setProfile] = useState<AthleteProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const onboarding = await getOnboarding(accessToken);
    setProfile(onboarding.profile);
  };

  useEffect(() => {
    let mounted = true;
    getOnboarding(accessToken)
      .then((onboarding) => {
        if (mounted) setProfile(onboarding.profile);
      })
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error ? caught.message : 'Profiel laden is mislukt.',
          );
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" onPress={onBack} style={styles.headerButton}>
          <Text style={styles.headerButtonText}>{'<'} Week</Text>
        </Pressable>
        <View>
          <Text style={styles.logo}>WOMBO</Text>
          <Text style={styles.caption}>Mijn profiel</Text>
        </View>
        <Pressable
          accessibilityLabel="Afmelden"
          accessibilityRole="button"
          onPress={() => void onSignOut()}
          style={styles.headerButton}
        >
          <Text style={styles.headerButtonText}>Uit</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        {loading ? <ActivityIndicator color={colors.brand} /> : null}
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {!loading && profile ? (
          <ProfileStep
            profile={profile}
            saving={saving}
            onSave={async (input) => {
              setSaving(true);
              setError(null);
              try {
                await saveProfile(accessToken, input);
                await load();
              } catch (caught) {
                setError(
                  caught instanceof Error
                    ? caught.message
                    : 'Profiel opslaan is mislukt.',
                );
              } finally {
                setSaving(false);
              }
            }}
          />
        ) : null}
        <View style={styles.links}>
          <Pressable accessibilityRole="button" onPress={onOpenTests} style={styles.link}>
            <Text style={styles.linkTitle}>Testen en kalibratie</Text>
            <Text style={styles.linkText}>Open de huidige, uitvoerbare protocollen.</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={onOpenPioneerAccess}
            style={styles.link}
          >
            <Text style={styles.linkTitle}>Pioneer toegang</Text>
            <Text style={styles.linkText}>Wissel je persoonlijke beta-code in.</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  headerButton: { minWidth: 58, paddingVertical: spacing.sm },
  headerButtonText: { color: colors.brand, fontWeight: '800' },
  logo: { color: colors.brand, fontSize: 18, fontWeight: '900', textAlign: 'center' },
  caption: { color: colors.inkMuted, fontSize: 12, textAlign: 'center' },
  content: { gap: spacing.lg, padding: spacing.lg, paddingBottom: spacing.xxl },
  error: { color: colors.danger, lineHeight: 20 },
  links: { gap: spacing.md },
  link: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    padding: spacing.lg,
  },
  linkTitle: { color: colors.ink, fontSize: 17, fontWeight: '800' },
  linkText: { color: colors.inkMuted, lineHeight: 20 },
});
