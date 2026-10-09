import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
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
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { QuickActionRow } from '../ui-v2/components/QuickActionRow';
import { Button } from '../ui-v2/primitives/Button';
import { Card } from '../ui-v2/primitives/Card';
import { ChoiceRow } from '../ui-v2/primitives/ChoiceRow';
import { IconTile } from '../ui-v2/primitives/IconTile';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';

import { colors, layout, radius, space } from '../ui-v2/tokens';

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

  return <SafeAreaView edges={['top']} style={styles.safeArea}>
    <ScrollView contentContainerStyle={styles.content}>
      <BrandedFormHeader caption="Integraties" backLabel="Weekplanning" onBack={onBack} onSignOut={onSignOut} />
      {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
      {busy ? <ActivityIndicator color={colors.primary} /> : null}
      <Card elevated padding="form" style={styles.panel}>
        <View style={styles.identity}><IconTile name="activities" /><Text variant="sectionTitle" accessibilityRole="header">Polar</Text></View>
        <View style={styles.chip}><Text variant="supporting" tone="primary">{statusLabel(connection)}</Text></View>
        <Notice>Polar is de eerste provider. Productie blijft uit totdat juridische, privacy- en providervoorwaarden zijn goedgekeurd.</Notice>
        {connection?.status === 'connected' ? <>
          <Text variant="label">Historie importeren</Text>
          <View accessibilityRole="radiogroup" accessibilityLabel="Historie importeren" style={{ gap: space[12] }}>
            {([7, 14, 30] as const).map(value => <ChoiceRow key={value} label={`${value} dagen`} selected={days === value} onPress={() => setDays(value)} />)}
          </View>
          <Text variant="supporting" tone="textMuted">Standaard 14 dagen. Meer dan 30 dagen is via deze koppeling niet beschikbaar.</Text>
          <Button label="Import starten" disabled={busy} onPress={() => void run(() => importPolarHistory(accessToken, newIdempotencyKey(), days))} />
          <Button label="Ontkoppelen" variant="outline" onPress={disconnect} />
        </> : <Button label={connection?.status === 'reconnect_required' ? 'Opnieuw toestemming geven' : 'Polar koppelen'} disabled={busy} onPress={() => void connect()} />}
        <QuickActionRow label="Status vernieuwen" icon="refresh" disabled={busy} onAction={() => void run(load)} />
      </Card>
      <Card elevated style={styles.panel}>
        <Text variant="sectionTitle" accessibilityRole="header">Imports</Text>
        {imports.length === 0 ? <Text tone="textMuted">Nog geen imports.</Text> : null}
        {imports.map(item => <View key={item.id} style={styles.importRow}>
          <Text variant="label">{item.range_start ?? 'Webhook'} – {item.range_end ?? 'activiteit'}</Text>
          <View style={styles.chip}><Text variant="supporting">{item.status}</Text></View>
          <Text variant="supporting" tone="textMuted">{item.imported_count} geïmporteerd · {item.skipped_count} overgeslagen</Text>
          {item.status === 'failed' && item.failure_code !== 'reconnect_required' && item.retry_count < item.max_attempts - 1 ?
            <QuickActionRow label="Nu opnieuw proberen" icon="refresh" disabled={busy} onAction={() => void run(() => retryPolarImport(accessToken, item.id))} /> : null}
        </View>)}
        <QuickActionRow label="Geïmporteerde activiteiten bekijken" icon="activities" onAction={onOpenActivities} />
      </Card>
      <Card elevated style={styles.panel}>
        <Text variant="sectionTitle" accessibilityRole="header">Privacy</Text>
        <Text tone="textMuted">Ontkoppelen stopt nieuwe toegang en verwijdert de credentials. Het is geen verwijderverzoek: bestaande activiteiten blijven behouden. Ruwe FIT-bestanden blijven backend-only; Wombo toont geen filemanager of downloadscherm in de MVP. Bewaartermijnen en verwijder-/exportprocessen moeten vóór productie formeel zijn vastgelegd.</Text>
      </Card>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: space[24], padding: layout.phoneGutter, paddingBottom: space[48] },
  panel: { gap: space[16] }, identity: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[12] },
  chip: { alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] },
  importRow: { borderTopColor: colors.border, borderTopWidth: layout.decorativeLine, gap: space[8], paddingTop: space[16] },
});
