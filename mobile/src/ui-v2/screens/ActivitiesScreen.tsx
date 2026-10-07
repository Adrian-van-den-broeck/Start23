import { FlashList } from '@shopify/flash-list';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { ShellSafeArea } from '../components/ShellInsets';
import { AppHeader } from '../components/AppHeader';
import { useLanguage } from '../../i18n/LanguageProvider';
import { ActivitySummary } from '../components/ActivitySummary';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { ActivityViewModel } from '../utils/activityViewModel';

export type ActivityRow = Readonly<{
  activity: ActivityViewModel; canCorrect: boolean;
  match: Readonly<{ id: string; name: string }> | null;
}>;

export function ActivityStatus({ busy, error }: { busy: boolean; error: string | null }) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('common.loading')}</Text> : null}
    {error ? <Text style={{ color: colors.destructive }} accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text> : null}
  </>;
}

export function ActivitiesScreen({ rows, pending, busy, error, controls, onBack, onProfile, onAdd, onFeedback, onCorrect, onMatch }: {
  rows: readonly ActivityRow[]; pending: ActivityViewModel | null; busy: boolean; error: string | null;
  controls: ReactNode; onBack: () => void; onProfile: () => void; onAdd: () => void;
  onFeedback: () => void; onCorrect: (id: string) => void; onMatch: (id: string, workoutId: string) => Promise<void>;
}) {
  const { t } = useLanguage();
  return <ShellSafeArea style={styles.frame} testID="v2-activities">
    <FlashList data={rows} keyExtractor={row => row.activity.id} keyboardShouldPersistTaps="handled"
      contentContainerStyle={styles.content} extraData={busy}
      ItemSeparatorComponent={() => <View style={{ height: space[16] }} />}
      ListHeaderComponent={<View style={styles.stack}>
        <AppHeader titleVariant="display" title={t('shell.activities')} onProfile={onProfile} profileLabel={t('planning.profile')} profileDisabled={busy} landscape="treesRiver" />
        {controls}
        <ActivityStatus busy={busy} error={error} />
        {pending ? <Card style={styles.stack} testID="activity-pending">
          <Text variant="sectionTitle" accessibilityRole="header">{t('rpe.awaiting')}</Text>
          <ActivitySummary activity={pending} />
          <Button label={t('activities.continueFeedback')} busy={busy} onPress={onFeedback} />
        </Card> : null}
        <Button label={t('activities.add')} disabled={busy || !!pending}
          disabledReason={pending ? t('activities.blocked') : undefined} onPress={onAdd} />
        <Text variant="sectionTitle" accessibilityRole="header">{t('activity.recent')}</Text>
        {!busy && !error && rows.length === 0 ? <Text>{t('activity.noRecent')}</Text> : null}
      </View>}
      renderItem={({ item: row }) => <Card style={styles.stack} testID={`activity-row-${row.activity.id}`}>
        <ActivitySummary activity={row.activity} />
        {row.match ? <>
          <Text variant="label">{t('activities.matchHeading')}</Text>
          <Text>{t('activities.matchHint', { name: row.match.name })}</Text>
          <Button label={t('activities.confirmMatch')} busy={busy} variant="secondary"
            accessibilityLabel={`${t('activities.confirmMatch')} · ${row.match.name} · ${row.activity.date}`}
            onPress={() => row.match ? onMatch(row.activity.id, row.match.id) : Promise.resolve()} />
        </> : null}
        {row.canCorrect ? <Button label={t('activity.correction')} variant="secondary" disabled={busy}
          accessibilityLabel={`${t('activity.correction')} · ${t(`common.${row.activity.discipline}`)} · ${row.activity.date}`}
          onPress={() => onCorrect(row.activity.id)} /> : null}
      </Card>}
      ListFooterComponent={<Button label={t('week.return')} variant="tertiary" disabled={busy} onPress={onBack} />} />
  </ShellSafeArea>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  content: { padding: layout.phoneGutter, paddingBottom: space[32] },
  stack: { gap: space[12], paddingBottom: space[16] },
});
