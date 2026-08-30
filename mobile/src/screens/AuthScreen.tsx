import { useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { FadeInView } from '../components/FadeInView';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { getSupabaseClient } from '../lib/supabase';
import { colors, radius, shadows, spacing } from '../theme/tokens';

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
      <LinearGradient
        colors={[colors.brandSoft, 'rgba(220, 235, 227, 0)']}
        end={{ x: 0.15, y: 1 }}
        pointerEvents="none"
        start={{ x: 0.85, y: 0 }}
        style={styles.glowTop}
      />
      <View pointerEvents="none" style={styles.glowBottom} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboard}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <FadeInView style={styles.hero}>
            <View style={styles.brandLockup}>
              <View style={styles.brandMark}>
                <Text style={styles.brandMarkText}>23</Text>
              </View>
              <View>
                <Text style={styles.eyebrow}>Start23</Text>
                <Text style={styles.brandCaption}>Train bewust</Text>
              </View>
            </View>
            <Text style={styles.title}>Train met richting.{'\n'}Beslis zelf.</Text>
            <Text style={styles.subtitle}>
              {mode === 'sign-in'
                ? 'Alles wat je nodig hebt voor een doordachte trainingsweek, afgestemd op jouw ritme.'
                : 'Maak je persoonlijke trainingsruimte en bouw stap voor stap aan een plan dat bij je past.'}
            </Text>
          </FadeInView>

          <FadeInView delay={90} style={styles.card}>
            <View style={styles.cardHeading}>
              <View>
                <Text style={styles.cardEyebrow}>
                  {mode === 'sign-in' ? 'Welkom terug' : 'Klaar voor je start?'}
                </Text>
                <Text style={styles.cardTitle}>
                  {mode === 'sign-in' ? 'Aanmelden' : 'Account maken'}
                </Text>
              </View>
              <View style={styles.secureBadge}>
                <View style={styles.secureDot} />
                <Text style={styles.secureText}>Veilig</Text>
              </View>
            </View>
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
              haptic="light"
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
          </FadeInView>

          <FadeInView delay={170} style={styles.privacyRow}>
            <View style={styles.privacyIcon}>
              <Text style={styles.privacyIconText}>i</Text>
            </View>
            <Text style={styles.privacy}>
              Je sessie blijft versleuteld op dit apparaat. Trainingswijzigingen
              worden nooit zonder jouw bevestiging toegepast.
            </Text>
          </FadeInView>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.canvas,
    flex: 1,
    overflow: 'hidden',
  },
  keyboard: {
    flex: 1,
  },
  content: {
    gap: spacing.xl,
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.lg,
    paddingBottom: spacing.xl,
    paddingTop: spacing.xl,
  },
  glowTop: {
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    height: 310,
    opacity: 0.82,
    position: 'absolute',
    right: -155,
    top: -145,
    width: 310,
  },
  glowBottom: {
    backgroundColor: colors.accentSoft,
    borderRadius: radius.pill,
    bottom: -155,
    height: 280,
    left: -150,
    opacity: 0.7,
    position: 'absolute',
    width: 280,
  },
  hero: {
    alignSelf: 'center',
    maxWidth: 520,
    width: '100%',
  },
  brandLockup: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  brandMark: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    height: 46,
    justifyContent: 'center',
    transform: [{ rotate: '-4deg' }],
    width: 46,
  },
  brandMarkText: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  eyebrow: {
    color: colors.brand,
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 1.6,
    textTransform: 'uppercase',
  },
  brandCaption: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '700',
    marginTop: 1,
  },
  title: {
    color: colors.ink,
    fontSize: 42,
    fontWeight: '900',
    letterSpacing: -1.8,
    lineHeight: 45,
    marginTop: spacing.lg,
  },
  subtitle: {
    color: colors.inkMuted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: spacing.md,
    maxWidth: 420,
  },
  card: {
    ...shadows.floating,
    alignSelf: 'center',
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.lg,
    gap: spacing.md,
    padding: spacing.lg,
    width: '100%',
    maxWidth: 520,
  },
  cardHeading: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  cardEyebrow: {
    color: colors.accent,
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: -0.5,
    marginTop: 3,
  },
  secureBadge: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radius.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  secureDot: {
    backgroundColor: colors.success,
    borderRadius: radius.pill,
    height: 6,
    width: 6,
  },
  secureText: {
    color: colors.brand,
    fontSize: 10,
    fontWeight: '800',
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    minHeight: 50,
    justifyContent: 'center',
    marginTop: spacing.xs,
    ...shadows.card,
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
  privacyRow: {
    alignItems: 'center',
    alignSelf: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
    justifyContent: 'center',
    maxWidth: 440,
    paddingHorizontal: spacing.sm,
  },
  privacyIcon: {
    alignItems: 'center',
    borderColor: colors.lineStrong,
    borderRadius: radius.pill,
    borderWidth: 1,
    height: 22,
    justifyContent: 'center',
    width: 22,
  },
  privacyIconText: {
    color: colors.inkMuted,
    fontSize: 11,
    fontWeight: '900',
  },
  privacy: {
    color: colors.inkMuted,
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },
});
