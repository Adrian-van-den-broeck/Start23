import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { FormField } from '../components/FormField';
import { getSupabaseClient } from '../lib/supabase';
import { colors, radius, spacing } from '../theme/tokens';

export function AuthScreen() {
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

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboard}
      >
        <View style={styles.content}>
          <View>
            <Text style={styles.eyebrow}>Start23</Text>
            <Text style={styles.title}>Train met richting.{'\n'}Beslis zelf.</Text>
            <Text style={styles.subtitle}>
              {mode === 'sign-in'
                ? 'Meld je aan om je veilige, hervatbare intake te starten.'
                : 'Maak een account en begin daarna met je veilige intake.'}
            </Text>
          </View>

          <View style={styles.card}>
            <FormField
              autoCapitalize="none"
              autoComplete="email"
              inputMode="email"
              keyboardType="email-address"
              label="E-mailadres"
              onChangeText={setEmail}
              placeholder="jij@voorbeeld.nl"
              value={email}
            />
            <FormField
              autoCapitalize="none"
              autoComplete={
                mode === 'sign-in' ? 'current-password' : 'new-password'
              }
              label="Wachtwoord"
              onChangeText={setPassword}
              placeholder="Minimaal 6 tekens"
              secureTextEntry
              value={password}
            />
            {mode === 'sign-up' ? (
              <FormField
                autoCapitalize="none"
                autoComplete="new-password"
                label="Herhaal wachtwoord"
                onChangeText={setPasswordConfirmation}
                placeholder="Nogmaals je wachtwoord"
                secureTextEntry
                value={passwordConfirmation}
              />
            ) : null}

            {error ? <Text style={styles.error}>{error}</Text> : null}
            {notice ? <Text style={styles.notice}>{notice}</Text> : null}

            <Pressable
              accessibilityRole="button"
              disabled={loading || !canSubmit}
              onPress={() => void submit()}
              style={({ pressed }) => [
                styles.primaryButton,
                (loading || !canSubmit) && styles.disabled,
                pressed && styles.pressed,
              ]}
            >
              {loading ? (
                <ActivityIndicator color={colors.white} />
              ) : (
                <Text style={styles.primaryButtonText}>
                  {mode === 'sign-in' ? 'Aanmelden' : 'Account maken'}
                </Text>
              )}
            </Pressable>
            <Pressable
              accessibilityRole="button"
              disabled={loading}
              onPress={() =>
                selectMode(mode === 'sign-in' ? 'sign-up' : 'sign-in')
              }
              style={({ pressed }) => [
                styles.linkButton,
                loading && styles.disabled,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.linkText}>
                {mode === 'sign-in'
                  ? 'Nieuw? Maak een account'
                  : 'Al een account? Aanmelden'}
              </Text>
            </Pressable>
          </View>

          <Text style={styles.privacy}>
            Je sessie blijft versleuteld op dit apparaat. Trainingswijzigingen
            worden nooit zonder jouw bevestiging toegepast.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.canvas,
    flex: 1,
  },
  keyboard: {
    flex: 1,
  },
  content: {
    flex: 1,
    gap: spacing.xl,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  eyebrow: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 1.6,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 38,
    fontWeight: '900',
    letterSpacing: -1.5,
    lineHeight: 42,
    marginTop: spacing.sm,
  },
  subtitle: {
    color: colors.inkMuted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: spacing.md,
    maxWidth: 340,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    gap: spacing.md,
    padding: spacing.lg,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    minHeight: 50,
    justifyContent: 'center',
    marginTop: spacing.xs,
  },
  primaryButtonText: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '800',
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    opacity: 0.8,
  },
  linkButton: {
    alignItems: 'center',
    padding: spacing.sm,
  },
  linkText: {
    color: colors.brand,
    fontSize: 13,
    fontWeight: '700',
  },
  error: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.sm,
    color: colors.danger,
    fontSize: 13,
    lineHeight: 18,
    padding: spacing.sm,
  },
  notice: {
    color: colors.success,
    fontSize: 13,
    lineHeight: 18,
  },
  privacy: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },
});
