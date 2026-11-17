import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { Divider } from '../primitives/Divider';
import { IconTile } from '../primitives/IconTile';
import { Notice } from '../primitives/Notice';
import type { IconName } from '../primitives/Icon';
import { space } from '../tokens';
import type { ActivityViewModel } from '../utils/activityViewModel';
import { SportIndicator } from './SportIndicator';

export function ActivitySummary({ activity }: { activity: ActivityViewModel }) {
  const { t } = useLanguage();
  return <View style={styles.stack} testID={`activity-summary-${activity.id}`}>
    <SportIndicator discipline={activity.discipline}>
      <Text tone="textMuted">{activity.date}</Text>
    </SportIndicator>
    <Divider />
    {activity.durationMinutes !== null ? <ActivityFact icon="clock" label={t('common.durationMinutes', { minutes: activity.durationMinutes })}
      accessibilityLabel={t('detail.minutesSpoken', { value: activity.durationMinutes })} /> : null}
    {activity.distanceMeters !== null ? <ActivityFact icon="location" label={t('detail.meters', { value: activity.distanceMeters })}
      accessibilityLabel={t('detail.metersSpoken', { value: activity.distanceMeters })} /> : null}
    {activity.pace !== null ? <ActivityFact icon="clock" label={t('activities.pace', { value: activity.pace })} /> : null}
    {activity.source ? <ActivityFact icon="activities" label={t('activities.source')} /> : null}
    <Divider />
    <View style={styles.fact}>
      <IconTile name="document" size="field" />
      <View style={styles.copy}>
        <Text variant="cardTitle" accessibilityRole="header">{t(`activity.result.${activity.result}`)}</Text>
        {activity.rpe !== null ? <Text tone="textMuted">{`${activity.rpeDescription} (RPE ${activity.rpe})`}</Text> : null}
      </View>
    </View>
    {activity.averageHeartRate !== null ? <ActivityFact icon="heartRate" label={t('activities.storedHeartRate', { value: activity.averageHeartRate })} /> : null}
    <Notice>{activity.publicMessage ?? (activity.result === 'awaiting_rpe' ? t('rpe.awaiting') : t(`activity.message.${activity.result}`))}</Notice>
    {activity.distanceOnly ? <Notice>{t('activities.distanceOnly')}</Notice> : null}
    {activity.partialCoverage ? <Notice>{t('activities.partialCoverage')}</Notice> : null}
    {activity.correctionProposal ? <Notice>{t('activities.correctionProposal')}</Notice> : null}
  </View>;
}
function ActivityFact({ icon, label, accessibilityLabel }: { icon: IconName; label: string; accessibilityLabel?: string }) {
  return <View style={styles.fact}>
    <IconTile name={icon} size="field" />
    <Text accessibilityLabel={accessibilityLabel} style={styles.copy}>{label}</Text>
  </View>;
}
const styles = StyleSheet.create({ stack: { gap: space[16] }, fact: { flexDirection: 'row', alignItems: 'center', gap: space[12] }, copy: { flex: 1, gap: space[8] } });
