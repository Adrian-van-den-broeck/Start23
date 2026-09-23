import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { getPioneerRedemption, redeemPioneerAccess } from '../api/client';
import type { PioneerRedemption } from '../api/types';
import { FormField } from '../components/FormField';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { colors, radius, spacing } from '../theme/tokens';

type Props = {
  accessToken: string;
  onBack: () => void;
};

function newIdempotencyKey(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (value) => {
    const random = Math.floor(Math.random() * 16);
    const digit = value === 'x' ? random : (random & 0x3) | 0x8;
    return digit.toString(16);
  });
}

export function PioneerAccessScreen({ accessToken, onBack }: Props) {
  const [code, setCode] = useState('');
  const [redemption, setRedemption] = useState<PioneerRedemption | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const idempotencyKeyRef = useRef(newIdempotencyKey());
  const inFlightRef = useRef(false);

  useEffect(() => {
    let mounted = true;
    getPioneerRedemption(accessToken)
      .then((current) => {
        if (mounted) setRedemption(current);
      })
      .catch((caught: unknown) => {
        if (mounted) {
          setError(
            caught instanceof Error
              ? caught.message
              : 'Pioneer-status laden is mislukt.',
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

  const redeem = async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const next = await redeemPioneerAccess(
        accessToken,
        idempotencyKeyRef.current,
        code,
      );
      setRedemption(next);
      setCode('');
      idempotencyKeyRef.current = newIdempotencyKey();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'De Pioneer-code kon niet worden ingewisseld.',
      );
    } finally {
      inFlightRef.current = false;
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" onPress={onBack} style={styles.back}>
          <Text style={styles.backText}>{'<'} Profiel</Text>
        </Pressable>
        <Text style={styles.logo}>WOMBO</Text>
        <View style={styles.headerSpacer} />
      </View>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.content}
      >
        <View style={styles.card}>
          <Text style={styles.eyebrow}>PIONEER BETA</Text>
          <Text style={styles.title}>Toegang met jouw code</Text>
          <Text style={styles.body}>
            De server controleert geldigheid, vervaldatum, intrekking en eenmalig
            gebruik. Je code wordt niet in de app bewaard.
          </Text>
          {loading ? <ActivityIndicator color={colors.brand} /> : null}
          {redemption ? (
            <View accessibilityRole="summary" style={styles.success}>
              <Text style={styles.successTitle}>Pioneer toegang actief</Text>
              <Text style={styles.body}>
                Ingewisseld op {new Date(redemption.redeemed_at).toLocaleString()}.
              </Text>
            </View>
          ) : (
            <>
              <FormField
                autoCapitalize="characters"
                label="Pioneer access-code"
                maxLength={32}
                onChangeText={(value) => setCode(value.toUpperCase())}
                placeholder="PIONEER-XXXX"
                value={code}
              />
              <Pressable
                accessibilityRole="button"
                disabled={submitting || code.trim().length < 8}
                onPress={() => void redeem()}
                style={[
                  styles.action,
                  (submitting || code.trim().length < 8) && styles.disabled,
                ]}
              >
                {submitting ? (
                  <ActivityIndicator color={colors.white} />
                ) : (
                  <Text style={styles.actionText}>Code inwisselen</Text>
                )}
              </Pressable>
            </>
          )}
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: spacing.lg,
  },
  back: { minWidth: 76, paddingVertical: spacing.sm },
  backText: { color: colors.brand, fontWeight: '800' },
  logo: { color: colors.brand, fontSize: 18, fontWeight: '900' },
  headerSpacer: { width: 76 },
  content: { flex: 1, justifyContent: 'center', padding: spacing.lg },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  eyebrow: { color: colors.accent, fontSize: 12, fontWeight: '900', letterSpacing: 1.2 },
  title: { color: colors.ink, fontSize: 28, fontWeight: '900' },
  body: { color: colors.inkMuted, lineHeight: 21 },
  action: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radius.pill,
    minHeight: 50,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  actionText: { color: colors.white, fontWeight: '900' },
  disabled: { opacity: 0.45 },
  error: { color: colors.danger, lineHeight: 20 },
  success: { backgroundColor: colors.brandSoft, borderRadius: radius.md, gap: spacing.xs, padding: spacing.lg },
  successTitle: { color: colors.success, fontSize: 18, fontWeight: '900' },
});
