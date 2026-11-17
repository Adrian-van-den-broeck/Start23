import { FlashList } from '@shopify/flash-list';
import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { ShellSafeArea } from '../components/ShellInsets';
import { HeaderAction, ProfileAction } from '../components/AppHeader';
import { HeaderLandscape } from '../assets/HeaderLandscape';
import { ActionLandscape } from '../assets/ActionLandscape';
import { useLanguage } from '../../i18n/LanguageProvider';
import { ActivitySummary } from '../components/ActivitySummary';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { Icon } from '../primitives/Icon';
import { Notice } from '../primitives/Notice';
import { Divider } from '../primitives/Divider';
import { colors, layout, radius, shadows, space, states } from '../tokens';
import type { ActivityViewModel } from '../utils/activityViewModel';

export type ActivityRow = Readonly<{
  activity: ActivityViewModel; canCorrect: boolean;
  match: Readonly<{ id: string; name: string }> | null;
}>;

export function ActivityStatus({ busy, error }: { busy: boolean; error: string | null }) {
  const { t } = useLanguage();
  return <>
    {busy ? <Text accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>{t('common.loading')}</Text> : null}
    {error ? <View accessible accessibilityRole="alert" accessibilityLabel={error} accessibilityLiveRegion="polite">
      <Notice tone="error">{error}</Notice>
    </View> : null}
  </>;
}

export function ActivitiesScreen({ rows, pending, busy, error, controls, onBack, onProfile, onAdd, onFeedback, onCorrect, onMatch }: {
  rows: readonly ActivityRow[]; pending: ActivityViewModel | null; busy: boolean; error: string | null;
  controls: ReactNode; onBack: () => void; onProfile: () => void; onAdd: () => void;
  onFeedback: () => void; onCorrect: (id: string) => void; onMatch: (id: string, workoutId: string) => Promise<void>;
}) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 390 || fontScale >= 1.5;
  return <ShellSafeArea style={styles.frame} testID="v2-activities">
    <FlashList data={rows} keyExtractor={row => row.activity.id} keyboardShouldPersistTaps="handled"
      contentContainerStyle={styles.content} extraData={busy}
      ItemSeparatorComponent={() => <View style={{ height: space[16] }} />}
      ListHeaderComponent={<View style={styles.stack}>
        <View>
          <View style={[styles.heading, stacked && styles.stacked]}>
            <Text variant="display" accessibilityRole="header" style={!stacked && styles.title}>{t('shell.activities')}</Text>
            <ProfileAction label={t('planning.profile')} onPress={onProfile} disabled={busy} />
          </View>
          <View pointerEvents="none" style={styles.landscape}><HeaderLandscape compact variant="treesRiver" /></View>
        </View>
        <ActivityStatus busy={busy} error={error} />
        {pending ? <Card elevated style={styles.card} testID="activity-pending">
          <Text variant="sectionTitle" accessibilityRole="header">{t('rpe.awaiting')}</Text>
          <ActivitySummary activity={pending} />
          <Button label={t('activities.continueFeedback')} trailingIcon="forward" busy={busy} onPress={onFeedback} />
        </Card> : null}
        <AddActivityBanner label={t('activities.add')} disabled={busy || !!pending}
          disabledReason={pending ? t('activities.blocked') : undefined} onPress={onAdd} />
        <Text variant="sectionTitle" accessibilityRole="header">{t('activity.recent')}</Text>
        {!busy && !error && rows.length === 0 ? <Card elevated><Text tone="textMuted">{t('activity.noRecent')}</Text></Card> : null}
      </View>}
      renderItem={({ item: row }) => <Card elevated style={styles.card} testID={`activity-row-${row.activity.id}`}>
        <ActivitySummary activity={row.activity} />
        {row.match ? <><Divider />
          <Text variant="label">{t('activities.matchHeading')}</Text>
          <Text>{t('activities.matchHint', { name: row.match.name })}</Text>
          <Button label={t('activities.confirmMatch')} busy={busy} variant="secondary"
            accessibilityLabel={`${t('activities.confirmMatch')} · ${row.match.name} · ${row.activity.date}`}
            onPress={() => row.match ? onMatch(row.activity.id, row.match.id) : Promise.resolve()} />
        </> : null}
        {row.canCorrect ? <Button label={t('activity.correction')} trailingIcon="forward" disabled={busy}
          accessibilityLabel={`${t('activity.correction')} · ${t(`common.${row.activity.discipline}`)} · ${row.activity.date}`}
          onPress={() => onCorrect(row.activity.id)} /> : null}
      </Card>}
      ListFooterComponent={<View style={styles.footer}>
        <HeaderAction label={t('week.return')} disabled={busy} onPress={onBack} />
        {controls}
      </View>} />
  </ShellSafeArea>;
}
function AddActivityBanner({ label, disabled, disabledReason, onPress }: {
  label: string; disabled: boolean; disabledReason?: string; onPress: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  return <View style={styles.card}>
    <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityHint={disabledReason}
      accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
      style={[styles.banner, pressed && states.pressed, disabled && styles.disabled]}>
      {!disabled ? <ActionLandscape /> : null}
      <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.plus}><Icon name="add" /></View>
      <Text variant="button" accessible={false} style={[styles.title, { color: disabled ? colors.text : colors.textInverse }]}>{label}</Text>
      <Icon name="forward" color={disabled ? colors.text : colors.textInverse} />
      {focused ? <View pointerEvents="none" accessible={false} style={[styles.focus, { borderColor: disabled ? colors.focus : colors.textInverse }]} /> : null}
    </Pressable>
    {disabledReason ? <Text variant="supporting" tone="textMuted">{disabledReason}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({
  frame: { flex: 1, backgroundColor: colors.background },
  content: { padding: layout.phoneGutter, paddingBottom: space[32], maxWidth: layout.readingWidth, alignSelf: 'center', width: '100%' },
  stack: { gap: space[24], paddingBottom: space[16] }, card: { gap: space[16] },
  heading: { flexDirection: 'row', alignItems: 'center', gap: space[8], zIndex: 1, backgroundColor: colors.background }, stacked: { flexDirection: 'column', alignItems: 'stretch' },
  title: { flex: 1 }, landscape: { marginHorizontal: -layout.phoneGutter, marginTop: -space[24], marginBottom: -space[24] },
  footer: { gap: space[24], paddingTop: space[24] },
  banner: { minHeight: layout.primaryButton, minWidth: layout.touch, padding: space[16], gap: space[16], flexDirection: 'row', alignItems: 'center',
    borderRadius: radius.button, overflow: 'hidden', backgroundColor: colors.primary, ...shadows.card },
  plus: { width: 40, height: 40, borderRadius: radius.pill, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  disabled: { backgroundColor: colors.surfaceSubtle }, focus: { ...StyleSheet.absoluteFill, margin: layout.focusOutline, borderRadius: radius.button, borderWidth: layout.focusOutline },
});
