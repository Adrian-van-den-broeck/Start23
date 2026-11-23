import { Pressable, StyleSheet, View } from 'react-native';

import { colors, layout, radius, space } from '../tokens';
import { Icon } from './Icon';
import { Text } from './Text';

// Short independent on/off choices that sit side by side, e.g. block status.
export function ToggleChip({ label, checked, onPress, disabled = false }: {
  label: string; checked: boolean; onPress: () => void; disabled?: boolean;
}) {
  return <Pressable accessibilityRole="checkbox" accessibilityLabel={label}
    accessibilityState={{ checked, disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [styles.chip, checked && styles.checked, disabled && styles.disabled, pressed && styles.pressed]}>
    <View accessible={false} importantForAccessibility="no-hide-descendants" style={[styles.box, checked && styles.boxChecked]}>
      {checked ? <Icon name="check" size={20} color={colors.textInverse} /> : null}
    </View>
    <Text variant="label" accessible={false} style={styles.label}>{label}</Text>
  </Pressable>;
}

const styles = StyleSheet.create({
  chip: { minHeight: layout.touch, flexGrow: 1, flexDirection: 'row', alignItems: 'center', gap: space[8],
    paddingHorizontal: space[12], paddingVertical: space[8], borderRadius: radius.pill,
    borderWidth: layout.controlEdge, borderColor: colors.borderControl, backgroundColor: colors.surface },
  checked: { backgroundColor: colors.primarySoft, borderColor: colors.primary },
  disabled: { backgroundColor: colors.surfaceSubtle },
  pressed: { opacity: 0.72 },
  box: { width: 24, height: 24, borderRadius: radius.pill, borderWidth: layout.controlEdge, borderColor: colors.primary,
    alignItems: 'center', justifyContent: 'center' },
  boxChecked: { backgroundColor: colors.primary },
  label: { flexShrink: 1 },
});
