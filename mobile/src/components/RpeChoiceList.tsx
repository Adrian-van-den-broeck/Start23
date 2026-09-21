import { StyleSheet, Text, View } from 'react-native';

import type { Discipline } from '../api/types';
import { type CanonicalRpe, rpeChoices } from '../lib/rpe';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

type RpeChoiceListProps = {
  disabled?: boolean;
  discipline: Discipline;
  label: string;
  onSelect: (value: CanonicalRpe) => void;
  selectedValue?: number | null;
};

export function RpeChoiceList({
  disabled = false,
  discipline,
  label,
  onSelect,
  selectedValue = null,
}: RpeChoiceListProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <View accessibilityLabel={label} accessibilityRole="radiogroup" style={styles.list}>
        {rpeChoices(discipline).map((choice) => {
          const selected = selectedValue === choice.value;
          return (
            <Pressable
              accessibilityLabel={`${choice.description} (RPE ${choice.value})`}
              accessibilityRole="radio"
              accessibilityState={{ checked: selected, disabled }}
              disabled={disabled}
              haptic="selection"
              key={choice.value}
              onPress={() => onSelect(choice.value)}
              style={({ pressed }) => [
                styles.choice,
                selected && styles.choiceSelected,
                disabled && styles.disabled,
                pressed && styles.pressed,
              ]}
            >
              <View style={[styles.value, selected && styles.valueSelected]}>
                <Text style={[styles.valueText, selected && styles.valueTextSelected]}>
                  {choice.value}
                </Text>
              </View>
              <Text style={[styles.description, selected && styles.descriptionSelected]}>
                {choice.description}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: spacing.sm },
  label: { color: colors.ink, fontSize: 13, fontWeight: '800' },
  list: { gap: spacing.xs },
  choice: {
    alignItems: 'center',
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.lineStrong,
    borderRadius: radius.sm,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.sm,
    minHeight: 48,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  choiceSelected: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  value: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  valueSelected: { backgroundColor: colors.brand },
  valueText: { color: colors.brand, fontSize: 12, fontWeight: '900' },
  valueTextSelected: { color: colors.white },
  description: { color: colors.ink, flex: 1, fontSize: 13, lineHeight: 18 },
  descriptionSelected: { fontWeight: '800' },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.78 },
});
