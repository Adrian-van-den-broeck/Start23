import type { RefObject } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { colors, layout, radius, space } from '../tokens';
import { FormField } from './FormField';
import { Icon, type IconName } from './Icon';
import { IconTile } from './IconTile';
import { Text } from './Text';

// The closed state of a sheet picker: one tappable row with the current value,
// and a separate clear button when the value is optional.
export function PickerField({ label, required = false, display, placeholder, spokenValue, openHint, onOpen,
  clearLabel, onClear, icon, error, hint, focusRef }: {
  label: string; required?: boolean; display: string | null; placeholder: string; spokenValue: string;
  openHint: string; onOpen: () => void; clearLabel?: string; onClear?: () => void; icon?: IconName;
  error?: string; hint?: string; focusRef?: RefObject<View | null>;
}) {
  return <FormField label={required ? `${label} *` : label} hint={hint} error={error}>
    {() => <View style={[styles.field, error ? styles.fieldError : null]}>
      <Pressable ref={focusRef} accessibilityRole="button" accessibilityLabel={`${label}: ${spokenValue}`}
        accessibilityHint={openHint} onPress={onOpen}
        style={({ pressed }) => [styles.trigger, !icon && styles.triggerPlain, pressed && styles.pressed]}>
        {icon ? <IconTile name={icon} size="field" /> : null}
        {display ? <Text variant="numericCompact" accessible={false} numberOfLines={1} style={styles.value}>{display}</Text>
          : <Text tone="textMuted" accessible={false} numberOfLines={1} style={styles.value}>{placeholder}</Text>}
        {onClear ? null : <Icon name="chevronDown" size={20} color={colors.textMuted} />}
      </Pressable>
      {onClear ? <Pressable accessibilityRole="button" accessibilityLabel={clearLabel} onPress={onClear}
        style={({ pressed }) => [styles.clear, pressed && styles.pressed]}>
        <Icon name="close" size={20} color={colors.textMuted} />
      </Pressable> : null}
    </View>}
  </FormField>;
}

const styles = StyleSheet.create({
  field: { minHeight: layout.fieldHeight, flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface,
    borderColor: colors.borderControl, borderWidth: layout.controlEdge, borderRadius: radius.control },
  fieldError: { borderColor: colors.destructive, borderWidth: layout.focusOutline },
  trigger: { flex: 1, minHeight: layout.fieldHeight, flexDirection: 'row', alignItems: 'center', gap: space[12],
    paddingHorizontal: space[12] },
  triggerPlain: { gap: space[4] },
  value: { flex: 1 },
  clear: { width: layout.touch, height: layout.touch, alignItems: 'center', justifyContent: 'center' },
  pressed: { opacity: 0.72 },
});
