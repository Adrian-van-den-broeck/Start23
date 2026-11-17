import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';
import { colors, layout, radius, space } from '../tokens';
import { Icon } from './Icon';
import { Text } from './Text';

export function ChoiceRow({ label, hint, selected, onPress, disabled = false, busy = false, disabledReason, mode = 'radio', accessibilityLabel = label }: {
  label: string; accessibilityLabel?: string; hint?: string; selected: boolean; onPress: () => void;
  disabled?: boolean; busy?: boolean; disabledReason?: string; mode?: 'radio' | 'checkbox';
}) {
  const [focused, setFocused] = useState(false);
  return <View style={{ gap: space[4] }}>
    <Pressable accessibilityRole={mode} accessibilityLabel={accessibilityLabel} accessibilityHint={disabledReason ?? hint}
      accessibilityState={{ checked: selected, disabled: disabled || busy, busy }} disabled={disabled || busy}
      onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      style={[styles.row, selected && styles.selected, (disabled || busy) && styles.disabled]}>
      <View accessible={false} importantForAccessibility="no-hide-descendants" style={[styles.indicator, mode === 'checkbox' && { borderRadius: radius.inset }]}>
        {busy ? <ActivityIndicator accessible={false} color={colors.primary} /> : selected ? <Icon name="check" size={20} /> : null}
      </View>
      <View style={{ flex: 1, gap: space[4] }}>
        <Text variant="label" accessible={false}>{label}</Text>
        {hint ? <Text variant="supporting" tone="textMuted" accessible={false}>{hint}</Text> : null}
      </View>
      {selected ? <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" style={styles.selectionRing} /> : null}
      {focused ? <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" style={styles.focus} /> : null}
    </Pressable>
    {disabledReason ? <Text variant="supporting" tone="textMuted">{disabledReason}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({
  row: { minWidth: layout.touch, minHeight: layout.touch, padding: space[12], gap: space[12],
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface,
    borderRadius: radius.control, borderWidth: layout.controlEdge, borderColor: colors.borderControl },
  selected: { backgroundColor: colors.primarySoft, borderColor: colors.primary },
  disabled: { backgroundColor: colors.surfaceSubtle },
  indicator: { width: 24, height: 24, borderRadius: radius.pill, borderWidth: layout.controlEdge,
    borderColor: colors.primary, justifyContent: 'center', alignItems: 'center' },
  selectionRing: { ...StyleSheet.absoluteFill, top: -layout.controlEdge, left: -layout.controlEdge, right: -layout.controlEdge, bottom: -layout.controlEdge,
    borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: colors.primary },
  focus: { ...StyleSheet.absoluteFill, margin: layout.focusOutline, borderRadius: radius.control,
    borderWidth: layout.focusOutline, borderColor: colors.focus },
});
