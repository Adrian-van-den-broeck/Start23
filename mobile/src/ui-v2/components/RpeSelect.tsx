import { StyleSheet, View } from 'react-native';

import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { rpeChoices, type CanonicalRpe } from '../../lib/rpe';
import { SelectField, type SelectOption } from '../primitives/SelectField';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';

const SCALE = 10;

// Compact RPE field: the chosen score and its meaning in one row, the full
// 1-10 scale in a sheet. It only reports the canonical value to its owner.
export function RpeSelect({ discipline, label, selectedValue, onSelect, disabled = false, error }: {
  discipline: Discipline; label: string; selectedValue: number | null;
  onSelect: (value: CanonicalRpe) => void; disabled?: boolean; error?: string;
}) {
  const { t } = useLanguage();
  const options: SelectOption<CanonicalRpe>[] = rpeChoices(discipline).map((choice) => ({
    value: choice.value,
    label: choice.description,
    accessibilityLabel: `${choice.description} (RPE ${choice.value})`,
    leading: (selected) => <RpeBadge value={choice.value} selected={selected} />,
  }));
  return <SelectField label={label} value={selectedValue as CanonicalRpe | null} options={options}
    onChange={onSelect} placeholder={t('rpe.choose')} disabled={disabled} error={error}
    renderValue={(option) => <>
      <RpeBadge value={option.value} selected />
      <View style={styles.summary}>
        <Text variant="label" numberOfLines={2}>{option.label}</Text>
        <RpeMeter value={option.value} />
      </View>
    </>} />;
}

function RpeBadge({ value, selected }: { value: number; selected: boolean }) {
  return <View accessible={false} style={[styles.badge, selected && styles.badgeSelected]}>
    <Text variant="label" tone={selected ? 'textInverse' : 'primary'}>{value}</Text>
  </View>;
}

function RpeMeter({ value }: { value: number }) {
  return <View accessible={false} style={styles.meter}>
    {Array.from({ length: SCALE }, (_, index) => <View key={index}
      style={[styles.meterStep, index < value && styles.meterStepFilled]} />)}
  </View>;
}

const styles = StyleSheet.create({
  summary: { flex: 1, gap: space[4] },
  badge: { width: 36, height: 36, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center',
    backgroundColor: colors.primarySoft },
  badgeSelected: { backgroundColor: colors.primary },
  meter: { flexDirection: 'row', gap: 2 },
  meterStep: { flex: 1, height: 4, borderRadius: radius.pill, backgroundColor: colors.border },
  meterStepFilled: { backgroundColor: colors.primary },
});
