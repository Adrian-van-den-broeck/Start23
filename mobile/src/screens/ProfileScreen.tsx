import { useEffect, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getOnboarding, saveProfile } from '../api/client';
import type { AthleteProfile } from '../api/types';
import { useLanguage } from '../i18n/LanguageProvider';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { ProfileForm } from '../ui-v2/components/ProfileForm';
import { QuickActionRow } from '../ui-v2/components/QuickActionRow';
import { Divider } from '../ui-v2/primitives/Divider';
import { Card } from '../ui-v2/primitives/Card';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, space } from '../ui-v2/tokens';

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
  const { t } = useLanguage();
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
            caught instanceof Error ? caught.message : t('integrations.account.profileLoadFailed'),
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

  return <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag" automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}>
        <BrandedFormHeader caption={t('integrations.account.profileTitle')} onBack={onBack} onSignOut={onSignOut} />
        {loading ? <ActivityIndicator color={colors.primary} /> : null}
        {error ? <Notice tone="error">{error}</Notice> : null}
        {!loading && profile ? <ProfileForm profile={profile} saving={saving}
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
                    : t('integrations.account.profileSaveFailed'),
                );
              } finally {
                setSaving(false);
              }
            }} /> : null}
        <Card elevated style={{ gap: space[16] }}>
          <View style={{ gap: space[4] }}><QuickActionRow label={t('integrations.account.tests')} onAction={onOpenTests} icon="document" /><Text variant="supporting" tone="textMuted">{t('integrations.account.testsHint')}</Text></View>
          <Divider />
          <View style={{ gap: space[4] }}><QuickActionRow label={t('integrations.account.pioneer')} onAction={onOpenPioneerAccess} icon="profile" /><Text variant="supporting" tone="textMuted">{t('integrations.account.pioneerHint')}</Text></View>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
});
