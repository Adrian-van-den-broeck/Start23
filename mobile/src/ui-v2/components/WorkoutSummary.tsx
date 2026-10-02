import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Card } from '../primitives/Card';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import type { WorkoutSummaryViewModel } from '../utils/workoutSummaryViewModel';
import { SportIndicator } from './SportIndicator';

export function WorkoutSummary({ summary, showDescription = true }: { summary: WorkoutSummaryViewModel; showDescription?: boolean }) {
  const { t, locale } = useLanguage();
  const { durationMinutes, distanceMeters } = summary.measures;
  const date = summary.date ? new Date(`${summary.date}T12:00:00`) : null;
  return <Card style={styles.summary}>
    <SportIndicator discipline={summary.discipline} />
    <Text variant="screenTitle" accessibilityRole="header" testID="workout-detail-heading">{summary.name}</Text>
    <View style={styles.meta}>
      {date ? <Text variant="supporting" tone="textMuted">{date.toLocaleDateString(locale, {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
      })}</Text> : null}
      <Text variant="label">{t(`detail.status.${summary.status}`)}</Text>
    </View>
    {durationMinutes !== null ? <Text variant="numeric" accessibilityLabel={t('detail.minutesSpoken', { value: durationMinutes })}>
      {t('common.durationMinutes', { minutes: durationMinutes })}
    </Text> : null}
    {distanceMeters !== null ? <Text variant={durationMinutes === null ? 'numeric' : 'supporting'}
      accessibilityLabel={t('detail.metersSpoken', { value: distanceMeters })}>
      {t('detail.meters', { value: distanceMeters })}
    </Text> : null}
    <Text variant="label" tone={summary.intensity === 'high' ? 'warning' : 'text'}>{t(`detail.intensity.${summary.intensity}`)}</Text>
    {showDescription && summary.description ? <Text variant="supporting">{summary.description}</Text> : null}
  </Card>;
}
const styles = StyleSheet.create({
  summary: { gap: space[12] }, meta: { gap: space[8] },
});
