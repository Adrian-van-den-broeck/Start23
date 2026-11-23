import { studioPresentation } from '../../ui-v3/presentation';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { Divider } from '../primitives/Divider';
import { IconTile } from '../primitives/IconTile';
import { Notice } from '../primitives/Notice';
import { Icon, type IconName } from '../primitives/Icon';
import { colors, space } from '../tokens';
import type { ActivityViewModel } from '../utils/activityViewModel';
import { SportIndicator } from './SportIndicator';

export function ActivitySummary({ activity }: { activity: ActivityViewModel }) {
  const { t } = useLanguage();
  const message = activity.publicMessage ?? (activity.result === 'awaiting_rpe' ? t('rpe.awaiting') : t(`activity.message.${activity.result}`));
  const outcome = t(`activity.result.${activity.result}`);
  const feedback = activity.rpe !== null ? `${activity.rpeDescription} (RPE ${activity.rpe})` : null;
  return <View style={styles.stack} testID={`activity-summary-${activity.id}`}>
    {studioPresentation ? <View style={styles.header}>
      <View style={[styles.tile, { backgroundColor: colors.sport[activity.discipline].soft }]}>
        <Icon name={activity.discipline} color={colors.sport[activity.discipline].text} />
      </View>
      <View style={styles.headerText}>
        <Text variant="caption" tone="textMuted">{t(`common.${activity.discipline}`)}</Text>
        <Text variant="label">{activity.date}</Text>
      </View>
    </View> : <>
      <SportIndicator discipline={activity.discipline}>
        <Text tone="textMuted">{activity.date}</Text>
      </SportIndicator>
      <Divider />
    </>}
    <View style={studioPresentation ? styles.measures : styles.stack}>
    {activity.durationMinutes !== null ? <ActivityFact icon="clock" label={t('common.durationMinutes', { minutes: activity.durationMinutes })}
      accessibilityLabel={t('detail.minutesSpoken', { value: activity.durationMinutes })} /> : null}
    {activity.distanceMeters !== null ? <ActivityFact icon="location" label={t('detail.meters', { value: activity.distanceMeters })}
      accessibilityLabel={t('detail.metersSpoken', { value: activity.distanceMeters })} /> : null}
    </View>
    {activity.pace !== null ? <ActivityFact icon="clock" label={t('activities.pace', { value: activity.pace })} /> : null}
    {activity.source ? <ActivityFact icon="activities" label={t('activities.source')} /> : null}
    {/* V3 reads the outcome as plain lines under one rule; V2 keeps its icon row and notices. */}
    {studioPresentation ? <View style={styles.outcome}>
      <Text variant="label" accessibilityRole="header">{outcome}</Text>
      {feedback ? <Text variant="supporting" tone="textMuted">{feedback}</Text> : null}
      {activity.averageHeartRate !== null ? <ActivityFact icon="heartRate" label={t('activities.storedHeartRate', { value: activity.averageHeartRate })} /> : null}
      {/* An activity that only waits for RPE has the same words as its outcome; say them once. */}
      {message !== outcome ? <Text variant="supporting" tone="textMuted">{message}</Text> : null}
      {activity.distanceOnly ? <Text variant="supporting" tone="textMuted">{t('activities.distanceOnly')}</Text> : null}
      {activity.partialCoverage ? <Text variant="supporting" tone="textMuted">{t('activities.partialCoverage')}</Text> : null}
    </View> : <>
      <Divider />
      <View style={styles.fact}>
        <IconTile name="document" size="field" />
        <View style={styles.copy}>
          <Text variant="cardTitle" accessibilityRole="header">{outcome}</Text>
          {feedback ? <Text tone="textMuted">{feedback}</Text> : null}
        </View>
      </View>
      {activity.averageHeartRate !== null ? <ActivityFact icon="heartRate" label={t('activities.storedHeartRate', { value: activity.averageHeartRate })} /> : null}
      <Notice>{message}</Notice>
      {activity.distanceOnly ? <Notice>{t('activities.distanceOnly')}</Notice> : null}
      {activity.partialCoverage ? <Notice>{t('activities.partialCoverage')}</Notice> : null}
    </>}
    {activity.correctionProposal ? <Notice>{t('activities.correctionProposal')}</Notice> : null}
  </View>;
}
function ActivityFact({ icon, label, accessibilityLabel }: { icon: IconName; label: string; accessibilityLabel?: string }) {
  if (studioPresentation) return <View style={styles.compactFact}><Icon name={icon} size={20} /><Text variant={accessibilityLabel ? 'numericCompact' : 'supporting'} accessibilityLabel={accessibilityLabel} style={{ flexShrink: 1 }}>{label}</Text></View>;
  return <View style={styles.fact}>
    <IconTile name={icon} size="field" />
    <Text accessibilityLabel={accessibilityLabel} style={styles.copy}>{label}</Text>
  </View>;
}
const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', gap: space[12] }, headerText: { flex: 1, gap: 2 },
  tile: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  measures: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[24] },
  compactFact: { flexDirection: 'row', alignItems: 'center', gap: space[8], flexShrink: 1 },
  outcome: { gap: space[4], paddingTop: space[12], borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  stack: { gap: studioPresentation ? space[12] : space[16] }, fact: { flexDirection: 'row', alignItems: 'center', gap: space[12] }, copy: { flex: 1, gap: space[8] } });
