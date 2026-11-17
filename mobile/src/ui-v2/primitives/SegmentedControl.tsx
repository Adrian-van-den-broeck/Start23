import { useState } from 'react';
import { Pressable, StyleSheet, useWindowDimensions, View } from 'react-native';
import { colors, layout, radius, space } from '../tokens';
import { Icon } from './Icon';
import { Text } from './Text';

export function SegmentedControl<T extends string>({ options, value, onChange, accessibilityLabel, disabled = false, role = 'radio' }: {
  options: readonly { value: T; label: string; disabled?: boolean }[];
  value: T; onChange: (value: T) => void; accessibilityLabel: string; disabled?: boolean; role?: 'radio' | 'tab';
}) {
  const { fontScale } = useWindowDimensions();
  const [width, setWidth] = useState(0);
  const [focused, setFocused] = useState<T | null>(null);
  const [labels, setLabels] = useState<Record<string, number>>({});
  const available = (width - layout.segmentedInset * 2 - space[4] * Math.max(options.length - 1, 0)) / Math.max(options.length, 1);
  const stacked = fontScale >= 1.5 || available < layout.touch || options.some((option) =>
    labels[option.value] === undefined || labels[option.value] + space[24] + 24 + space[8] > available);
  return <View testID="segmented-control" accessibilityRole={role === 'tab' ? 'tablist' : 'radiogroup'} accessibilityLabel={accessibilityLabel}
    onLayout={(event) => setWidth(event.nativeEvent.layout.width)} style={[styles.track, stacked ? { borderRadius: radius.card } : styles.horizontal]}>
    <View pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
      style={styles.measure}>
      {options.map((option) => <Text key={option.value} variant="label" onLayout={(event) => {
        const measured = event.nativeEvent.layout.width;
        setLabels((previous) => previous[option.value] === measured ? previous : { ...previous, [option.value]: measured });
      }}>{option.label}</Text>)}
    </View>
    {options.map((option) => {
      const selected = option.value === value;
      const blocked = disabled || option.disabled === true;
      return <Pressable key={option.value} accessibilityRole={role} accessibilityLabel={option.label}
        accessibilityState={{ ...(role === 'tab' ? { selected } : { checked: selected }), disabled: blocked }} disabled={blocked}
        onPress={() => onChange(option.value)} onFocus={() => setFocused(option.value)} onBlur={() => setFocused(null)}
        style={[styles.segment, !stacked && { flex: 1 }, selected && styles.selected, blocked && styles.disabled]}>
        {selected ? <Icon name="check" size={20} color={blocked ? colors.text : colors.textInverse} /> : null}
        <Text variant="label" accessible={false} style={{ flexShrink: 1, color: blocked ? colors.text : selected ? colors.textInverse : colors.primary }}>{option.label}</Text>
        {focused === option.value ? <View pointerEvents="none" style={[styles.focus, { borderColor: selected && !blocked ? colors.textInverse : colors.focus }]} /> : null}
      </Pressable>;
    })}
  </View>;
}
const styles = StyleSheet.create({
  track: { backgroundColor: colors.primarySoft, borderRadius: radius.pill,
    minHeight: layout.segmentedHeight, padding: layout.segmentedInset, gap: space[4] },
  horizontal: { flexDirection: 'row' },
  segment: { minHeight: layout.touch, minWidth: layout.touch, borderRadius: radius.pill,
    padding: space[12], flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: space[8] },
  selected: { backgroundColor: colors.primary },
  disabled: { backgroundColor: colors.surfaceSubtle },
  focus: { ...StyleSheet.absoluteFill, margin: layout.focusOutline, borderRadius: radius.pill,
    borderWidth: layout.focusOutline },
  measure: { position: 'absolute', opacity: 0, alignItems: 'flex-start' },
});
