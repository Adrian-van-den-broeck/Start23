import { StyleSheet, useWindowDimensions, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Divider } from '../primitives/Divider';
import { IconTile } from '../primitives/IconTile';
import { Text } from '../primitives/Text';
import { colors, layout, space } from '../tokens';
import type { WorkoutSummaryViewModel } from '../utils/workoutSummaryViewModel';

/** Present supplied measures only; missing time never becomes a calculated value. */
export function WorkoutFacts({ measures, intensity, variant = 'scheduled' }: Pick<WorkoutSummaryViewModel, 'measures' | 'intensity'> & {
  variant?: 'scheduled' | 'focus';
}) {
  const { t } = useLanguage();
  const { width, fontScale } = useWindowDimensions();
  const { durationMinutes, distanceMeters } = measures;
  const stacked = width < 360 || fontScale >= 1.5 || variant === 'scheduled' || durationMinutes === null;
  const hasMeasure = durationMinutes !== null || distanceMeters !== null;
  return <View style={[styles.facts, stacked && styles.stacked]}>
    {hasMeasure ? <>
      <View style={[styles.fact, stacked && styles.stackedFact]}>
        <IconTile name={durationMinutes !== null ? 'clock' : 'location'} size="field" />
        <View style={styles.value}>
          {durationMinutes !== null ? <Text variant={variant === 'focus' ? 'body' : 'numeric'} accessibilityLabel={t('detail.minutesSpoken', { value: durationMinutes })}>
            {t('common.durationMinutes', { minutes: durationMinutes })}
          </Text> : null}
          {distanceMeters !== null ? <Text variant={durationMinutes === null ? 'numeric' : 'body'}
            accessibilityLabel={t('detail.metersSpoken', { value: distanceMeters })}>
            {t('detail.meters', { value: distanceMeters })}
          </Text> : null}
        </View>
      </View>
      {stacked ? <Divider /> : <View accessible={false} accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants" style={styles.rule} />}
    </> : null}
    <View style={[styles.fact, stacked && styles.stackedFact]}>
      <IconTile name="intensity" size="field" />
      <Text variant="label" style={styles.value}>{t(`detail.intensity.${intensity}`)}</Text>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  facts: { flexDirection: 'row', gap: space[16] },
  stacked: { flexDirection: 'column' },
  fact: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: space[12] },
  stackedFact: { flex: 0 },
  rule: { width: layout.decorativeLine, backgroundColor: colors.border },
  value: { flex: 1, gap: space[4] },
});
