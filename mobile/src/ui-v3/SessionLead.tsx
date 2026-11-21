import { Image, StyleSheet, View } from 'react-native';
import { useLanguage } from '../i18n/LanguageProvider';
import { Button } from '../ui-v2/primitives/Button';
import { Icon } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import type { WorkoutSummaryViewModel } from '../ui-v2/utils/workoutSummaryViewModel';
import { palette, identity } from './tokens';

// Without onOpen the lead is a read-only header, as on workout detail, where the
// kicker already carries the status so the caption below is not repeated.
export function SessionLead({ summary, heading, date, count, onOpen, headingTestID, statusInKicker = false, showDescription = true }: {
  summary: WorkoutSummaryViewModel; heading: string; date: string; count?: string; onOpen?: () => void;
  headingTestID?: string; statusInKicker?: boolean; showDescription?: boolean;
}) {
  const { t } = useLanguage();
  const { durationMinutes, distanceMeters } = summary.measures;
  return <View style={styles.lead}>
    <View style={[styles.cover, summary.discipline === 'run' && styles.trackCover]}>
      {summary.discipline === 'run' && <Image accessible={false} source={require('../../assets/wombo-track.jpg')}
        resizeMode="cover" style={styles.photo} />}
      <View style={styles.kicker}>
        <View style={styles.signal} /><Text variant="caption" style={styles.kickerText}>{heading}</Text>
      </View>
      <View style={styles.sport}>
        <Icon name={summary.discipline} size={20} color={palette.textInverse} />
        <Text variant="label" tone="textInverse">{t(`common.${summary.discipline}`)}</Text>
      </View>
    </View>
    <View style={styles.body}>
      <View style={styles.meta}>
        {date ? <Text variant="supporting" style={styles.soft}>{date}</Text> : null}
        {count && <Text variant="caption" style={styles.soft}>{count}</Text>}
      </View>
      <Text variant="display" accessibilityRole="header" tone="textInverse" testID={headingTestID}>{summary.name}</Text>
      <View style={styles.facts}>
        {durationMinutes !== null && <Text variant="numeric" tone="textInverse" accessibilityLabel={t('detail.minutesSpoken', { value: durationMinutes })}>{t('common.durationMinutes', { minutes: durationMinutes })}</Text>}
        {distanceMeters !== null && <Text variant="numeric" tone="textInverse" accessibilityLabel={t('detail.metersSpoken', { value: distanceMeters })}>{t('detail.meters', { value: distanceMeters })}</Text>}
        <Text variant="label" style={styles.soft}>{t(`detail.intensity.${summary.intensity}`)}</Text>
      </View>
      {statusInKicker ? null : <Text variant="caption" style={styles.soft}>{t(`detail.status.${summary.status}`)}</Text>}
      {showDescription && summary.description ? <Text variant="supporting" style={styles.soft}>{summary.description}</Text> : null}
      {onOpen ? <Button variant="secondary" label={t('week.viewWorkoutLabel')} accessibilityLabel={t('week.viewWorkout', { name: summary.name })} trailingIcon="forward" onPress={onOpen} /> : null}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  lead: { backgroundColor: identity.ink, borderRadius: 20, overflow: 'hidden' },
  cover: { backgroundColor: palette.primary, minHeight: 84, justifyContent: 'space-between',
    alignItems: 'flex-start', padding: 16, gap: 12 },
  trackCover: { minHeight: 128 },
  photo: { ...StyleSheet.absoluteFill, width: '100%', height: '100%' },
  kicker: { flexDirection: 'row', alignItems: 'center', gap: 7, borderRadius: 16,
    backgroundColor: identity.ink, paddingHorizontal: 10, paddingVertical: 4 },
  signal: { width: 7, height: 7, borderRadius: 4, backgroundColor: identity.orange },
  kickerText: { color: palette.textInverse, textTransform: 'uppercase', letterSpacing: 1 },
  sport: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 8,
    paddingVertical: 3, borderRadius: 6, backgroundColor: identity.ink },
  body: { padding: 18, gap: 8 },
  meta: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'space-between' },
  soft: { color: palette.primarySoft },
  facts: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'baseline', columnGap: 12 },
});
