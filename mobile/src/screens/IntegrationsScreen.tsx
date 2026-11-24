import { studioPresentation } from '../ui-v3/presentation';
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
import { type TranslationKey, useLanguage } from '../i18n/LanguageProvider';
import { BrandedFormHeader } from '../ui-v2/components/FormComposition';
import { QuickActionRow } from '../ui-v2/components/QuickActionRow';
import { Button } from '../ui-v2/primitives/Button';
import { IconTile } from '../ui-v2/primitives/IconTile';
import { Notice } from '../ui-v2/primitives/Notice';
import { Text } from '../ui-v2/primitives/Text';

import { colors, layout, space } from '../ui-v2/tokens';
import { ChoiceChips, formatDate, Group, Heading, LinkRow, Panel, screenGap, Tag } from '../ui-v3/screens/support';

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

const statusLabels: Record<PolarConnection['status'], TranslationKey> = {
  connected: 'integrations.status.connected',
  disconnected: 'integrations.status.disconnected',
  revoked: 'integrations.status.revoked',
  reconnect_required: 'integrations.status.reconnect_required',
  error: 'integrations.status.error',
};

function statusLabel(connection: PolarConnection | null): TranslationKey {
  if (!connection) return 'integrations.status.none';
  return statusLabels[connection.status];
}

// The import state is shown in the interface language, never as its API code.
const importStatusNames: Record<PolarImportRun['status'], TranslationKey> = { running: 'integrations.importStatus.running', completed: 'integrations.importStatus.completed', failed: 'integrations.importStatus.failed' };

export function IntegrationsScreen({
  accessToken,
  onBack,
  onOpenActivities,
  onSignOut,
}: IntegrationsScreenProps) {
  const { t, locale } = useLanguage();
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
        setError(caught instanceof Error ? caught.message : t('integrations.loadFailed')),
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
      setError(caught instanceof Error ? caught.message : t('integrations.actionFailed'));
    } finally {
      try {
        await load();
      } catch (caught) {
        if (!actionFailed) {
          setError(caught instanceof Error ? caught.message : t('integrations.loadFailed'));
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
      t('integrations.disconnect.title'),
      t('integrations.disconnect.message'),
      [
        { text: t('integrations.disconnect.cancel'), style: 'cancel' },
        {
          text: t('integrations.disconnect.confirm'),
          style: 'destructive',
          onPress: () => void run(() => disconnectPolar(accessToken)),
        },
      ],
    );
  };

  const status = connection?.status;
  const shortDate = (value: string) => formatDate(value, locale, { day: 'numeric', month: 'short', year: 'numeric' });
  // A webhook import covers one activity and has no date range.
  const importTitle = (item: PolarImportRun) => item.range_start && item.range_end
    ? t('integrations.imports.range', { start: shortDate(item.range_start), end: shortDate(item.range_end) })
    : `${item.range_start ? shortDate(item.range_start) : t('integrations.imports.webhook')} – ${item.range_end ? shortDate(item.range_end) : t('integrations.imports.activity')}`;
  return <SafeAreaView edges={['top']} style={styles.safeArea}>
    <ScrollView contentContainerStyle={styles.content}>
      <BrandedFormHeader caption={t('integrations.title')} backLabel={t('activity.back')} onBack={onBack} onSignOut={onSignOut} />
      {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error}><Notice tone="error">{error}</Notice></View> : null}
      {busy ? <ActivityIndicator color={colors.primary} /> : null}
      <Panel divided={false}>
        <View style={styles.identity}>
          <IconTile name="activities" size={studioPresentation ? 'field' : 'row'} />
          <Text variant="sectionTitle" accessibilityRole="header" style={styles.grow}>Polar</Text>
          <Tag label={t(statusLabel(connection))} tone={status === 'connected' ? 'success' : status === 'reconnect_required' || status === 'error' ? 'warning' : 'neutral'} />
        </View>
        {studioPresentation ? <Text variant="supporting" tone="textMuted">{t('integrations.polar.notice')}</Text> : <Notice>{t('integrations.polar.notice')}</Notice>}
        {status === 'connected' ? <>
          <Group label={t('integrations.history.title')} hint={t('integrations.history.hint')}>
            <ChoiceChips mode="radio" accessibilityLabel={t('integrations.history.title')} isSelected={value => days === value} onPress={setDays}
              options={([7, 14, 30] as const).map(value => ({ value, label: t('integrations.history.days', { days: value }) }))} />
          </Group>
          <Button label={t('integrations.history.start')} disabled={busy} onPress={() => void run(() => importPolarHistory(accessToken, newIdempotencyKey(), days))} />
          <Button label={t('integrations.disconnect.confirm')} variant="outline" onPress={disconnect} />
        </> : <Button label={status === 'reconnect_required' ? t('integrations.reconnect') : t('integrations.connect')} disabled={busy} onPress={() => void connect()} />}
        {studioPresentation ? <Button label={t('integrations.refresh')} variant="tertiary" trailingIcon="refresh" disabled={busy} onPress={() => void run(load)} />
          : <QuickActionRow label={t('integrations.refresh')} icon="refresh" disabled={busy} onAction={() => void run(load)} />}
      </Panel>
      <Panel>
        <Heading title={t('integrations.imports.title')} />
        {imports.length === 0 ? <Text variant={studioPresentation ? 'supporting' : 'body'} tone="textMuted">{t('integrations.imports.empty')}</Text> : null}
        {imports.map(item => <View key={item.id} style={styles.importRow}>
          <View style={styles.identity}>
            <Text variant="label" style={styles.grow}>{importTitle(item)}</Text>
            <Tag label={t(importStatusNames[item.status])}
              tone={item.status === 'failed' ? 'destructive' : item.status === 'completed' ? 'success' : 'neutral'} />
          </View>
          <Text variant="supporting" tone="textMuted">{t('integrations.imports.counts', { imported: item.imported_count, skipped: item.skipped_count })}</Text>
          {item.status === 'failed' && item.failure_code !== 'reconnect_required' && item.retry_count < item.max_attempts - 1
            ? studioPresentation
              ? <Button label={t('integrations.imports.retry')} variant="secondary" trailingIcon="refresh" disabled={busy} onPress={() => void run(() => retryPolarImport(accessToken, item.id))} />
              : <QuickActionRow label={t('integrations.imports.retry')} icon="refresh" disabled={busy} onAction={() => void run(() => retryPolarImport(accessToken, item.id))} />
            : null}
        </View>)}
        <LinkRow icon="activities" label={t('integrations.imports.view')} onPress={onOpenActivities} />
      </Panel>
      <Panel>
        <Heading title={t('integrations.privacy.title')} description={t('integrations.privacy.body')} />
      </Panel>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  content: { alignSelf: 'center', width: '100%', maxWidth: layout.readingWidth, gap: screenGap, padding: layout.phoneGutter, paddingBottom: space[48] },
  grow: { flex: 1, minWidth: 0 },
  identity: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[12] },
  importRow: { borderTopColor: colors.border, borderTopWidth: StyleSheet.hairlineWidth, gap: space[8], paddingTop: space[12] },
});
