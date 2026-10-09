import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getPioneerRedemption, redeemPioneerAccess } from '../api/client';
import type { PioneerRedemption } from '../api/types';
import { AppHeader } from '../ui-v2/components/AppHeader';
import { Button } from '../ui-v2/primitives/Button';
import { Card } from '../ui-v2/primitives/Card';
import { Input } from '../ui-v2/primitives/Input';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout, space } from '../ui-v2/tokens';

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

  return <SafeAreaView edges={['top', 'bottom']} style={styles.safeArea}>
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag" automaticallyAdjustKeyboardInsets={Platform.OS === 'ios'}>
        <AppHeader title="WOMBO" onBack={onBack} backLabel="Profiel" landscape="ridges" />
        <Card elevated padding="form" style={{ gap: layout.fieldGroupGap }}>
          <Text variant="supporting" tone="primary">PIONEER BETA</Text>
          <Text variant="sectionTitle" accessibilityRole="header">Toegang met jouw code</Text>
          <Text tone="textMuted">De server controleert geldigheid, vervaldatum, intrekking en eenmalig gebruik. Je code wordt niet in de app bewaard.</Text>
          {loading ? <ActivityIndicator color={colors.primary} /> : null}
          {redemption ? <View accessibilityRole="summary"><Notice tone="success" title="Pioneer toegang actief">
            {`Ingewisseld op ${new Date(redemption.redeemed_at).toLocaleString()}.`}
          </Notice></View> : <>
            <Input autoCapitalize="characters" label="Pioneer access-code" maxLength={32}
              onChangeText={(value) => setCode(value.toUpperCase())} placeholder="PIONEER-XXXX" value={code} icon="document" />
            <Button label="Code inwisselen" busy={submitting} disabled={submitting || code.trim().length < 8} onPress={() => void redeem()} />
          </>}
          {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
});
