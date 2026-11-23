import type { ReactNode } from 'react';
import { TrackCover } from '../ui-v3/TrackCover';
import { Wordmark } from '../ui-v3/Masthead';
import { studioPresentation } from '../ui-v3/presentation';
import { useState } from 'react';
import Constants from 'expo-constants';
import { Keyboard, StyleSheet, View } from 'react-native';
import { FormScrollView } from '../components/FormScrollView';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../i18n/LanguageProvider';
import { getSupabaseClient } from '../lib/supabase';
import { AppHeader } from '../ui-v2/components/AppHeader';
import { Button } from '../ui-v2/primitives/Button';
import { Card } from '../ui-v2/primitives/Card';
import { Input } from '../ui-v2/primitives/Input';
import { Notice } from '../ui-v2/primitives/Notice';
import { SegmentedControl } from '../ui-v2/primitives/SegmentedControl';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, space } from '../ui-v2/tokens';

export function AuthScreen() {
  const { t } = useLanguage();
  const verificationHost = 'r6-api-r6-staging.up.railway.app';
  const showVerificationBuild =
    process.env.EXPO_PUBLIC_VERIFICATION_BUILD === '1' &&
    process.env.EXPO_PUBLIC_API_BASE_URL === `https://${verificationHost}` &&
    process.env.EXPO_PUBLIC_SUPABASE_URL ===
      'https://isfumhgqphieoayqahjv.supabase.co';
  const [mode, setMode] = useState<'sign-in' | 'sign-up'>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const normalizedEmail = email.trim().toLowerCase();
  const canSubmit =
    normalizedEmail.length > 0 &&
    password.length > 0 &&
    (mode === 'sign-in' || passwordConfirmation.length > 0);

  const selectMode = (nextMode: 'sign-in' | 'sign-up') => {
    setMode(nextMode);
    setPasswordConfirmation('');
    setError(null);
    setNotice(null);
  };

  const submit = async () => {
    if (mode === 'sign-up' && password.length < 6) {
      setError(t('auth.passwordTooShort'));
      return;
    }
    if (mode === 'sign-up' && password !== passwordConfirmation) {
      setError(t('auth.passwordMismatch'));
      return;
    }

    Keyboard.dismiss();
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const supabase = getSupabaseClient();
      const result =
        mode === 'sign-in'
          ? await supabase.auth.signInWithPassword({
              email: normalizedEmail,
              password,
            })
          : await supabase.auth.signUp({
              email: normalizedEmail,
              password,
            });
      if (result.error) {
        throw result.error;
      }
      if (mode === 'sign-up' && !result.data.session) {
        setMode('sign-in');
        setPassword('');
        setPasswordConfirmation('');
        setNotice(t('auth.accountCreated'));
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : t('auth.signInFailed'),
      );
    } finally {
      setLoading(false);
    }
  };

  return <SafeAreaView style={styles.safeArea}>
    <FormScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {studioPresentation ? <TrackCover>
          <Wordmark inverse />
          <Text variant="screenTitle" tone="textInverse" accessibilityRole="header">{t('auth.tagline')}</Text>
        </TrackCover> : <>
          <AppHeader title="WOMBO" landscape="ridges" />
          <View style={{ gap: space[12] }}>
            <Text variant="supporting" tone="primary">{t('auth.eyebrow')}</Text>
            <Text variant="display">{t('auth.tagline')}</Text>
            <Text tone="textMuted">{mode === 'sign-in'
              ? t('auth.introSignIn')
              : t('auth.introSignUp')}</Text>
          </View>
        </>}
        <FormSurface>
          <SegmentedControl role="tab" accessibilityLabel={t('auth.modeLabel')} disabled={loading}
            options={[{value: 'sign-in', label: t('auth.signIn')}, {value: 'sign-up', label: t('auth.signUp')}]}
            value={mode} onChange={selectMode} />
          {!studioPresentation && <View style={{ gap: space[4] }}>
            <Text variant="supporting" tone="primary">{mode === 'sign-in' ? t('auth.welcomeBack') : t('auth.readyToStart')}</Text>
            <Text variant="sectionTitle" accessibilityRole="header">{mode === 'sign-in' ? t('auth.signIn') : t('auth.createAccount')}</Text>
          </View>}
          <Input autoCapitalize="none" autoComplete="email" inputMode="email" keyboardType="email-address"
            label={t('auth.email')} onChangeText={setEmail} placeholder={t('auth.emailPlaceholder')} value={email} icon="profile" />
          <Input autoCapitalize="none" autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
            label={t('auth.password')} onChangeText={setPassword} placeholder={t('auth.passwordPlaceholder')} secureTextEntry value={password} />
          {mode === 'sign-up' ? <Input autoCapitalize="none" autoComplete="new-password" label={t('auth.passwordRepeat')}
            onChangeText={setPasswordConfirmation} placeholder={t('auth.passwordRepeatPlaceholder')} secureTextEntry value={passwordConfirmation} /> : null}
          {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
          {notice ? <View accessibilityLiveRegion="polite"><Notice tone="info">{notice}</Notice></View> : null}
          <Button label={mode === 'sign-in' ? t('auth.signIn') : t('auth.createAccount')} busy={loading} disabled={loading || !canSubmit} onPress={submit} />
        </FormSurface>
        <Notice>{t('auth.sessionNotice')}</Notice>
        {showVerificationBuild ? <View accessibilityLabel={t('auth.stagingDiagnostics')} style={{ gap: space[4] }}>
          <Text variant="caption" tone="textMuted">{t('auth.stagingCandidate')} {Constants.expoConfig?.version ?? 'unknown'}
            {' · build '}{process.env.EXPO_PUBLIC_BUILD_NUMBER ?? 'unknown'}{' · '}{process.env.EXPO_PUBLIC_BUILD_GIT_SHA ?? 'unknown'}</Text>
          <Text variant="caption" tone="textMuted">API: {verificationHost}</Text>
        </View> : null}
      </FormScrollView>
  </SafeAreaView>;
}
function FormSurface({ children }: { children: ReactNode }) {
  return studioPresentation ? <View style={{ gap: space[16] }}>{children}</View>
    : <Card elevated padding="form" style={{ gap: layout.fieldGroupGap }}>{children}</Card>;
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
});
