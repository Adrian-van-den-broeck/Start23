import { useState } from 'react';
import Constants from 'expo-constants';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
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
      setError('Kies een wachtwoord van minimaal 6 tekens.');
      return;
    }
    if (mode === 'sign-up' && password !== passwordConfirmation) {
      setError('De wachtwoorden zijn niet gelijk.');
      return;
    }

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
        setNotice(
          'Je account is aangemaakt. Controleer je e-mail en meld je daarna aan.',
        );
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Aanmelden is niet gelukt.',
      );
    } finally {
      setLoading(false);
    }
  };

  return <SafeAreaView style={styles.safeArea}>
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
      <ScrollView automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'} contentContainerStyle={styles.content}
        keyboardDismissMode="on-drag" keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <AppHeader title="WOMBO" landscape="ridges" />
        <View style={{ gap: space[12] }}>
          <Text variant="supporting" tone="primary">Train bewust</Text>
          <Text variant="display">Train met richting.{'\n'}Beslis zelf.</Text>
          <Text tone="textMuted">{mode === 'sign-in'
            ? 'Alles wat je nodig hebt voor een doordachte trainingsweek, afgestemd op jouw ritme.'
            : 'Maak je persoonlijke trainingsruimte en bouw stap voor stap aan een plan dat bij je past.'}</Text>
        </View>
        <Card elevated padding="form" style={{ gap: layout.fieldGroupGap }}>
          <SegmentedControl role="tab" accessibilityLabel="Account" disabled={loading}
            options={[{value: 'sign-in', label: 'Aanmelden'}, {value: 'sign-up', label: 'Registreren'}]}
            value={mode} onChange={selectMode} />
          <View style={{ gap: space[4] }}>
            <Text variant="supporting" tone="primary">{mode === 'sign-in' ? 'Welkom terug' : 'Klaar voor je start?'}</Text>
            <Text variant="sectionTitle" accessibilityRole="header">{mode === 'sign-in' ? 'Aanmelden' : 'Account maken'}</Text>
          </View>
          <Input autoCapitalize="none" autoComplete="email" inputMode="email" keyboardType="email-address"
            label="E-mailadres" onChangeText={setEmail} placeholder="jij@voorbeeld.nl" value={email} icon="profile" />
          <Input autoCapitalize="none" autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
            label="Wachtwoord" onChangeText={setPassword} placeholder="Minimaal 6 tekens" secureTextEntry value={password} />
          {mode === 'sign-up' ? <Input autoCapitalize="none" autoComplete="new-password" label="Herhaal wachtwoord"
            onChangeText={setPasswordConfirmation} placeholder="Nogmaals je wachtwoord" secureTextEntry value={passwordConfirmation} /> : null}
          {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
          {notice ? <View accessibilityLiveRegion="polite"><Notice tone="info">{notice}</Notice></View> : null}
          <Button label={mode === 'sign-in' ? 'Aanmelden' : 'Account maken'} busy={loading} disabled={loading || !canSubmit} onPress={() => void submit()} />
        </Card>
        <Notice>Je sessie blijft versleuteld op dit apparaat. Trainingswijzigingen worden nooit zonder jouw bevestiging toegepast.</Notice>
        {showVerificationBuild ? <View accessibilityLabel="Staging build diagnostics" style={{ gap: space[4] }}>
          <Text variant="caption" tone="textMuted">Staging candidate {Constants.expoConfig?.version ?? 'unknown'}
            {' · build '}{process.env.EXPO_PUBLIC_BUILD_NUMBER ?? 'unknown'}{' · '}{process.env.EXPO_PUBLIC_BUILD_GIT_SHA ?? 'unknown'}</Text>
          <Text variant="caption" tone="textMuted">API: {verificationHost}</Text>
        </View> : null}
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
});
