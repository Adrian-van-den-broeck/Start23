import { StyleSheet, View } from 'react-native';
import type { SelectionWorkout } from '../ui-v2/utils/planningCreationViewModel';
import { useLanguage } from '../i18n/LanguageProvider';
import { Icon } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout } from '../ui-v2/tokens';

// One chosen workout as a single compact row. The candidate card above already
// showed the full description, so the list repeats only what tells choices apart.
export function ChosenRow({ occurrenceId, position, name, discipline, durationMinutes, distanceMeters, intensity }:
  Pick<SelectionWorkout, 'occurrenceId' | 'name' | 'discipline' | 'durationMinutes' | 'distanceMeters' | 'intensity'> & { position: number }) {
  const { t } = useLanguage();
  return <View testID={`selection-occurrence-${occurrenceId}`} style={styles.row}>
    <View style={[styles.tile, { backgroundColor: colors.sport[discipline].soft }]}>
      <Icon name={discipline} color={colors.sport[discipline].text} />
    </View>
    <View style={styles.text}>
      <Text variant="caption" tone="textMuted">{t('creation.choiceNumber', { number: position })} {'·'} {t(`common.${discipline}`)}</Text>
      <Text variant="label" accessibilityRole="header">{name}</Text>
      <View style={styles.measures}>
        {durationMinutes !== null && <Text variant="supporting">{t('common.durationMinutes', { minutes: durationMinutes })}</Text>}
        {distanceMeters !== null && <Text variant="supporting">{t('detail.meters', { value: distanceMeters })}</Text>}
        <Text variant="supporting" tone="textMuted">{t(`detail.intensity.${intensity}`)}</Text>
      </View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: layout.touch, paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  tile: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  text: { flex: 1, gap: 2 },
  measures: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 8 },
});
