import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../i18n/LanguageProvider';
import { Button } from '../ui-v2/primitives/Button';
import { Icon } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import type { WorkoutSummaryViewModel } from '../ui-v2/utils/workoutSummaryViewModel';
import { palette, identity } from './tokens';

export function SessionLead({ summary, heading, date, count, onOpen }: {
  summary: WorkoutSummaryViewModel; heading: string; date: string; count?: string; onOpen: () => void;
}) {
  const { t } = useLanguage();
  const { durationMinutes, distanceMeters } = summary.measures;
  return <View style={styles.lead}>
    <View style={styles.top}>
      <Text variant="label" tone="textInverse">{heading}</Text>
      {count && <Text variant="caption" style={styles.soft}>{count}</Text>}
    </View>
    <View style={styles.sport}>
      <Icon name={summary.discipline} color={identity.orange} />
      <Text variant="label" style={styles.soft}>{t(`common.${summary.discipline}`)}</Text>
    </View>
    <Text variant="screenTitle" accessibilityRole="header" tone="textInverse">{summary.name}</Text>
    <View style={styles.meta}>
      <Text variant="supporting" style={styles.soft}>{date}</Text>
      <Text variant="supporting" style={styles.soft}>{t(`detail.status.${summary.status}`)}</Text>
    </View>
    <View style={styles.facts}>
      {durationMinutes !== null && <Text variant="numeric" tone="textInverse" accessibilityLabel={t('detail.minutesSpoken', { value: durationMinutes })}>{t('common.durationMinutes', { minutes: durationMinutes })}</Text>}
      {distanceMeters !== null && <Text variant="numeric" tone="textInverse" accessibilityLabel={t('detail.metersSpoken', { value: distanceMeters })}>{t('detail.meters', { value: distanceMeters })}</Text>}
      <Text variant="label" style={styles.soft}>{t(`detail.intensity.${summary.intensity}`)}</Text>
    </View>
    {summary.description ? <Text variant="supporting" style={styles.soft}>{summary.description}</Text> : null}
    <Button variant="secondary" label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })} trailingIcon="forward" onPress={onOpen} />
  </View>;
}
const styles = StyleSheet.create({
  lead: { backgroundColor: identity.ink, borderRadius: 16, padding: 20, gap: 12 },
  top: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 8,
    paddingBottom: 12, borderBottomColor: '#476152', borderBottomWidth: StyleSheet.hairlineWidth },
  meta: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between' },
  sport: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  soft: { color: palette.primarySoft },
  facts: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'baseline', gap: 12 },
});
