import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet } from 'react-native';
import { FormScrollView } from '../components/FormScrollView';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getOnboarding, saveProfile } from '../api/client';
import type { AthleteProfile } from '../api/types';
import { useLanguage } from '../i18n/LanguageProvider';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { ProfileForm } from '../ui-v2/components/ProfileForm';
import { Divider } from '../ui-v2/primitives/Divider';
import { Notice } from '../ui-v2/primitives/Notice';
import { colors, layout, space } from '../ui-v2/tokens';
import { LinkRow, Panel, screenGap } from '../ui-v3/screens/support';

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
    <FormScrollView contentContainerStyle={styles.content}>
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
        <Panel style={styles.links}>
          <LinkRow icon="document" label={t('integrations.account.tests')} hint={t('integrations.account.testsHint')} onPress={onOpenTests} />
          <Divider />
          <LinkRow icon="profile" label={t('integrations.account.pioneer')} hint={t('integrations.account.pioneerHint')} onPress={onOpenPioneerAccess} />
        </Panel>
      </FormScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: screenGap, padding: layout.phoneGutter, paddingBottom: space[48] },
  links: { gap: space[4] },
});
