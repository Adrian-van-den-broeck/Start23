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
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const submit = async (mode: 'sign-in' | 'sign-up') => {
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const supabase = getSupabaseClient();
      const result =
        mode === 'sign-in'
          ? await supabase.auth.signInWithPassword({ email, password })
          : await supabase.auth.signUp({ email, password });
      if (result.error) {
        throw result.error;
      }
      if (mode === 'sign-up' && !result.data.session) {
        setNotice('Controleer je e-mail om je account te bevestigen.');
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
              Meld je aan om je veilige, hervatbare intake te starten.
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
              autoComplete="current-password"
              label="Wachtwoord"
              onChangeText={setPassword}
              placeholder="Minimaal 6 tekens"
              secureTextEntry
              value={password}
            />

            {error ? <Text style={styles.error}>{error}</Text> : null}
            {notice ? <Text style={styles.notice}>{notice}</Text> : null}

            <Pressable
              accessibilityRole="button"
              disabled={loading || !email || !password}
              onPress={() => void submit('sign-in')}
              style={({ pressed }) => [
                styles.primaryButton,
                (loading || !email || !password) && styles.disabled,
                pressed && styles.pressed,
              ]}
            >
              {loading ? (
                <ActivityIndicator color={colors.white} />
              ) : (
                <Text style={styles.primaryButtonText}>Aanmelden</Text>
              )}
            </Pressable>
            <Pressable
              accessibilityRole="button"
              disabled={loading || !email || !password}
              onPress={() => void submit('sign-up')}
              style={styles.linkButton}
            >
              <Text style={styles.linkText}>Nieuw? Maak een account</Text>
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
