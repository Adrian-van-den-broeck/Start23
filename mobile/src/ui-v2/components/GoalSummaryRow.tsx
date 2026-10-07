import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Text } from '../primitives/Text';
import { Icon } from '../primitives/Icon';
import { IconTile } from '../primitives/IconTile';
import { colors, layout, radius, space } from '../tokens';

export function GoalSummaryRow({ label, name, accessibilityLabel, onAction, disabled = false }: {
  label: string; name: string; accessibilityLabel: string; onAction: () => void; disabled?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  return <Pressable testID="week-goal-row" accessibilityRole="button" accessibilityLabel={accessibilityLabel}
    accessibilityState={{ disabled }} disabled={disabled} onPress={onAction}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    style={[styles.row, pressed && styles.pressed, disabled && styles.disabled, focused && styles.focused]}>
    <IconTile name="goal" />
    <View style={styles.copy} accessible={false} importantForAccessibility="no-hide-descendants">
      <Text variant="supporting" tone={disabled ? 'text' : 'textMuted'}>{label}</Text>
      <Text variant="cardTitle">{name}</Text>
    </View>
    <Icon name="chevron" color={colors.textMuted} />
  </Pressable>;
}
const styles = StyleSheet.create({
  row: {
    minHeight: layout.touch, flexDirection: 'row', alignItems: 'center', gap: space[12],
    paddingVertical: space[12], borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: 'transparent'
  },
  copy: { flex: 1, gap: space[4] },
  pressed: { backgroundColor: colors.primarySoft },
  disabled: { backgroundColor: colors.surfaceSubtle },
  focused: { borderColor: colors.focus },
});
