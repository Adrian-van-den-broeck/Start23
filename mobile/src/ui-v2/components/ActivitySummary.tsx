import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { ActivityViewModel } from '../utils/activityViewModel';
import { SportIndicator } from './SportIndicator';

export function ActivitySummary({ activity }: { activity: ActivityViewModel }) {
  const { t } = useLanguage();
  return <View style={styles.stack} testID={`activity-summary-${activity.id}`}>
    <SportIndicator discipline={activity.discipline} />
    <Text variant="label">{activity.date}</Text>
    {activity.durationMinutes !== null ? <Text accessibilityLabel={t('detail.minutesSpoken', { value: activity.durationMinutes })}>
      {t('common.durationMinutes', { minutes: activity.durationMinutes })}</Text> : null}
    {activity.distanceMeters !== null ? <Text accessibilityLabel={t('detail.metersSpoken', { value: activity.distanceMeters })}>
      {t('detail.meters', { value: activity.distanceMeters })}</Text> : null}
    {activity.pace !== null ? <Text>{t('activities.pace', { value: activity.pace })}</Text> : null}
    {activity.source ? <Text variant="supporting" tone="textMuted">{t('activities.source')}</Text> : null}
    <Text>{t(`activity.result.${activity.result}`)}</Text>
    {activity.rpe !== null ? <Text>{`${activity.rpeDescription} (RPE ${activity.rpe})`}</Text> : null}
    {activity.averageHeartRate !== null ? <Text>{t('activities.storedHeartRate', { value: activity.averageHeartRate })}</Text> : null}
    <Text>{activity.publicMessage ?? (activity.result === 'awaiting_rpe' ? t('rpe.awaiting') : t(`activity.message.${activity.result}`))}</Text>
    {activity.distanceOnly ? <Text variant="supporting">{t('activities.distanceOnly')}</Text> : null}
    {activity.partialCoverage ? <Text variant="supporting">{t('activities.partialCoverage')}</Text> : null}
    {activity.correctionProposal ? <Text>{t('activities.correctionProposal')}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({ stack: { gap: space[8] } });
