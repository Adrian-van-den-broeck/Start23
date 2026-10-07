import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { Text } from '../primitives/Text';
import { Icon, type IconName } from '../primitives/Icon';
import { IconTile } from '../primitives/IconTile';
import { colors, layout, radius, space } from '../tokens';

export function QuickActionRow({ label, onAction, disabled = false, busy = false, accessibilityLabel = label, style, icon }: {
  label: string; onAction: () => void; disabled?: boolean; busy?: boolean; accessibilityLabel?: string; style?: StyleProp<ViewStyle>; icon?: IconName;
}) {
  const blocked = disabled || busy;
  const [focused, setFocused] = useState(false);
  const [pressed, setPressed] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={accessibilityLabel}
    accessibilityState={{ disabled: blocked, busy }} disabled={blocked} onPress={onAction}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    style={[styles.row, pressed && styles.pressed, blocked && styles.disabled, focused && styles.focused, style]}>
    {icon ? <IconTile name={icon} /> : null}
    <Text variant="label" tone="primary" accessible={false} importantForAccessibility="no" style={styles.label}>{label}</Text>
    {busy ? <ActivityIndicator accessible={false} color={colors.text} /> : null}
    <Icon name="chevron" color={colors.textMuted} />
  </Pressable>;
}
const styles = StyleSheet.create({
  row: {
    minHeight: layout.touch, minWidth: layout.touch, flexDirection: 'row', alignItems: 'center',
    gap: space[12], paddingVertical: space[12], borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: 'transparent'
  },
  label: { flex: 1, flexShrink: 1 },
  pressed: { backgroundColor: colors.primarySoft },
  disabled: { backgroundColor: colors.surfaceSubtle },
  focused: { borderColor: colors.focus },
});
