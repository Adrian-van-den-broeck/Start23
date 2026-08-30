import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  disconnectPolar,
  getPolarConnection,
  importPolarHistory,
  listPolarImports,
  retryPolarImport,
  startPolarOAuth,
} from '../api/client';
import type { PolarConnection, PolarImportRun } from '../api/types';
import { StatusPill } from '../components/StatusPill';
import { MotionPressable as Pressable } from '../components/MotionPressable';
import { colors, radius, spacing } from '../theme/tokens';

type IntegrationsScreenProps = {
  accessToken: string;
  onBack: () => void;
  onOpenActivities: () => void;
  onSignOut: () => Promise<void>;
};

function newIdempotencyKey(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (value) => {
    const random = Math.floor(Math.random() * 16);
    return (value === 'x' ? random : (random & 0x3) | 0x8).toString(16);
  });
}

function statusLabel(connection: PolarConnection | null): string {
  if (!connection) return 'Niet gekoppeld';
  return {
    connected: 'Verbonden',
    disconnected: 'Ontkoppeld',
    revoked: 'Toegang ingetrokken',
    reconnect_required: 'Opnieuw koppelen',
    error: 'Aandacht nodig',
  }[connection.status];
}

export function IntegrationsScreen({
  accessToken,
  onBack,
  onOpenActivities,
  onSignOut,
}: IntegrationsScreenProps) {
  const [connection, setConnection] = useState<PolarConnection | null>(null);
  const [imports, setImports] = useState<PolarImportRun[]>([]);
  const [days, setDays] = useState<7 | 14 | 30>(14);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const current = await getPolarConnection(accessToken);
    setConnection(current);
    setImports(current ? await listPolarImports(accessToken) : []);
  };

  useEffect(() => {
    setBusy(true);
    load()
      .catch((caught) =>
        setError(caught instanceof Error ? caught.message : 'Laden is mislukt.'),
      )
      .finally(() => setBusy(false));
    // load is intentionally local to this screen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    let actionFailed = false;
    try {
      await action();
    } catch (caught) {
      actionFailed = true;
      setError(caught instanceof Error ? caught.message : 'Actie is mislukt.');
    } finally {
      try {
        await load();
      } catch (caught) {
        if (!actionFailed) {
          setError(caught instanceof Error ? caught.message : 'Laden is mislukt.');
        }
      }
      setBusy(false);
    }
  };

  const connect = () =>
    run(async () => {
      const result = await startPolarOAuth(accessToken);
      await Linking.openURL(result.authorization_url);
    });

  const disconnect = () => {
    Alert.alert(
      'Polar ontkoppelen?',
      'De provider-toegang wordt verwijderd. Eerder geïmporteerde activiteiten en bestanden worden niet automatisch gewist.',
      [
        { text: 'Annuleren', style: 'cancel' },
        {
          text: 'Ontkoppelen',
          style: 'destructive',
          onPress: () => void run(() => disconnectPolar(accessToken)),
        },
      ],
    );
  };

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <View style={styles.header}>
        <Pressable accessibilityRole="button" onPress={onBack}>
          <Text style={styles.link}>Weekplanning</Text>
        </Pressable>
        <View>
          <Text style={styles.logo}>Start23</Text>
          <Text style={styles.caption}>Integraties</Text>
        </View>
        <Pressable accessibilityRole="button" onPress={() => void onSignOut()}>
          <Text style={styles.link}>Afmelden</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.brand} /> : null}

        <View style={styles.panel}>
          <View style={styles.row}>
            <Text style={styles.title}>Polar</Text>
            <StatusPill
              label={statusLabel(connection)}
              tone={connection?.status === 'connected' ? 'brand' : 'neutral'}
            />
          </View>
          <Text style={styles.body}>
            Polar is de eerste provider. Productie blijft uit totdat juridische,
            privacy- en providervoorwaarden zijn goedgekeurd.
          </Text>
          {connection?.status === 'connected' ? (
            <>
              <Text style={styles.label}>Historie importeren</Text>
              <View style={styles.choiceRow}>
                {([7, 14, 30] as const).map((value) => (
                  <Pressable
                    accessibilityRole="radio"
                    accessibilityState={{ checked: days === value }}
                    key={value}
                    onPress={() => setDays(value)}
                    style={[styles.choice, days === value && styles.choiceActive]}
                  >
                    <Text style={styles.choiceText}>{value} dagen</Text>
                  </Pressable>
                ))}
              </View>
              <Text style={styles.hint}>
                Standaard 14 dagen. Meer dan 30 dagen is via deze koppeling niet
                beschikbaar.
              </Text>
              <Pressable
                disabled={busy}
                onPress={() =>
                  void run(() =>
                    importPolarHistory(accessToken, newIdempotencyKey(), days),
                  )
                }
                style={[styles.action, busy && styles.disabled]}
              >
                <Text style={styles.actionText}>Import starten</Text>
              </Pressable>
              <Pressable onPress={disconnect} style={styles.secondaryAction}>
                <Text style={styles.secondaryText}>Ontkoppelen</Text>
              </Pressable>
            </>
          ) : (
            <Pressable
              disabled={busy}
              onPress={() => void connect()}
              style={[styles.action, busy && styles.disabled]}
            >
              <Text style={styles.actionText}>
                {connection?.status === 'reconnect_required'
                  ? 'Opnieuw toestemming geven'
                  : 'Polar koppelen'}
              </Text>
            </Pressable>
          )}
          <Pressable disabled={busy} onPress={() => void run(load)}>
            <Text style={styles.link}>Status vernieuwen</Text>
          </Pressable>
        </View>

        <View style={styles.panel}>
          <Text style={styles.title}>Imports</Text>
          {imports.length === 0 ? (
            <Text style={styles.body}>Nog geen imports.</Text>
          ) : null}
          {imports.map((item) => (
            <View key={item.id} style={styles.importRow}>
              <View style={styles.row}>
                <Text style={styles.label}>
                  {item.range_start ?? 'Webhook'} – {item.range_end ?? 'activiteit'}
                </Text>
                <StatusPill label={item.status} tone="neutral" />
              </View>
              <Text style={styles.hint}>
                {item.imported_count} geïmporteerd · {item.skipped_count} overgeslagen
              </Text>
              {item.status === 'failed' &&
              item.failure_code !== 'reconnect_required' &&
              item.retry_count < item.max_attempts - 1 ? (
                <Pressable
                  disabled={busy}
                  onPress={() => void run(() => retryPolarImport(accessToken, item.id))}
                >
                  <Text style={styles.link}>Nu opnieuw proberen</Text>
                </Pressable>
              ) : null}
            </View>
          ))}
          <Pressable onPress={onOpenActivities}>
            <Text style={styles.link}>Geïmporteerde activiteiten bekijken</Text>
          </Pressable>
        </View>

        <View style={styles.panel}>
          <Text style={styles.title}>Privacy</Text>
          <Text style={styles.body}>
            Ontkoppelen stopt nieuwe toegang en verwijdert de credentials. Het is
            geen verwijderverzoek: bestaande activiteiten blijven behouden. Ruwe
            FIT-bestanden blijven backend-only; Start23 toont geen filemanager of
            downloadscherm in de MVP. Bewaartermijnen en verwijder-/exportprocessen
            moeten vóór productie formeel zijn vastgelegd.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.canvas, flex: 1 },
  header: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', padding: spacing.lg },
  logo: { color: colors.brand, fontSize: 20, fontWeight: '900', textAlign: 'center' },
  caption: { color: colors.inkMuted, fontSize: 11, textAlign: 'center' },
  link: { color: colors.brand, fontSize: 12, fontWeight: '800' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: 80 },
  panel: { backgroundColor: colors.surface, borderRadius: radius.md, gap: spacing.md, padding: spacing.lg },
  row: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  title: { color: colors.ink, fontSize: 22, fontWeight: '900' },
  label: { color: colors.ink, fontSize: 14, fontWeight: '800' },
  body: { color: colors.inkMuted, fontSize: 13, lineHeight: 19 },
  hint: { color: colors.inkMuted, fontSize: 12, lineHeight: 18 },
  choiceRow: { flexDirection: 'row', gap: spacing.sm },
  choice: { borderColor: colors.line, borderRadius: radius.pill, borderWidth: 1, flex: 1, padding: spacing.sm },
  choiceActive: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  choiceText: { color: colors.ink, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  action: { alignItems: 'center', backgroundColor: colors.brand, borderRadius: radius.pill, padding: 14 },
  actionText: { color: colors.white, fontSize: 14, fontWeight: '900' },
  secondaryAction: { alignItems: 'center', borderColor: colors.line, borderRadius: radius.pill, borderWidth: 1, padding: 14 },
  secondaryText: { color: colors.brand, fontSize: 14, fontWeight: '900' },
  importRow: { borderTopColor: colors.line, borderTopWidth: 1, gap: spacing.xs, paddingTop: spacing.md },
  disabled: { opacity: 0.45 },
  error: { backgroundColor: colors.dangerSoft, borderRadius: radius.sm, color: colors.danger, padding: spacing.md },
});
