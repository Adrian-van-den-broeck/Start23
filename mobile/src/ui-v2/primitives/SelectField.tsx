import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useLanguage } from '../../i18n/LanguageProvider';
import { colors, layout, radius, space } from '../tokens';
import { FormField } from './FormField';
import { Icon } from './Icon';
import { BottomSheet } from './BottomSheet';
import { Text } from './Text';

export type SelectOption<T extends string | number> = {
  value: T;
  label: string;
  accessibilityLabel?: string;
  leading?: (selected: boolean) => ReactNode;
};

// A compact field that opens a sheet of options. Choosing an option only
// reports it to the owner, which decides whether and when anything is saved.
export function SelectField<T extends string | number>({ label, value, options, onChange, placeholder, hint, error,
  disabled = false, renderValue }: {
  label: string; value: T | null; options: readonly SelectOption<T>[]; onChange: (value: T) => void;
  placeholder: string; hint?: string; error?: string; disabled?: boolean;
  renderValue?: (option: SelectOption<T>) => ReactNode;
}) {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value) ?? null;
  const spokenValue = selected ? selected.accessibilityLabel ?? selected.label : placeholder;
  return <FormField label={label} hint={hint} error={error}>
    {() => <>
      <Pressable accessibilityRole="button" accessibilityLabel={`${label}: ${spokenValue}`}
        accessibilityHint={t('select.openHint')} accessibilityState={{ disabled, expanded: open }}
        disabled={disabled} onPress={() => setOpen(true)}
        style={({ pressed }) => [styles.trigger, error && styles.triggerError, disabled && styles.locked, pressed && styles.pressed]}>
        <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.triggerBody}>
          {selected ? renderValue?.(selected) ?? <>
            {selected.leading?.(true)}
            <Text variant="label" style={styles.flex}>{selected.label}</Text>
          </> : <Text tone="textMuted" style={styles.flex}>{placeholder}</Text>}
        </View>
        <Icon name="chevronDown" size={20} color={colors.textMuted} />
      </Pressable>
      <BottomSheet visible={open} title={label} closeLabel={t('common.close')} onClose={() => setOpen(false)}>
        <View accessibilityRole="radiogroup" accessibilityLabel={label} style={styles.options}>
          {options.map((option) => {
            const isSelected = option.value === value;
            return <Pressable key={String(option.value)} accessibilityRole="radio"
              accessibilityLabel={option.accessibilityLabel ?? option.label} accessibilityState={{ checked: isSelected }}
              onPress={() => { onChange(option.value); setOpen(false); }}
              style={({ pressed }) => [styles.option, isSelected && styles.optionSelected, pressed && styles.pressed]}>
              {option.leading?.(isSelected)}
              <Text variant={isSelected ? 'label' : 'body'} accessible={false} style={styles.flex}>{option.label}</Text>
              {isSelected ? <Icon name="check" size={20} color={colors.primary} /> : null}
            </Pressable>;
          })}
        </View>
      </BottomSheet>
    </>}
  </FormField>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  trigger: { minHeight: layout.fieldHeight, flexDirection: 'row', alignItems: 'center', gap: space[8],
    paddingHorizontal: space[12], paddingVertical: space[8], backgroundColor: colors.surface,
    borderColor: colors.borderControl, borderWidth: layout.controlEdge, borderRadius: radius.control },
  triggerError: { borderColor: colors.destructive, borderWidth: layout.focusOutline },
  triggerBody: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: space[12] },
  locked: { backgroundColor: colors.surfaceSubtle },
  pressed: { opacity: 0.72 },
  options: { gap: space[4] },
  option: { minHeight: layout.touch, flexDirection: 'row', alignItems: 'center', gap: space[12],
    paddingHorizontal: space[12], paddingVertical: space[8], borderRadius: radius.control },
  optionSelected: { backgroundColor: colors.primarySoft },
});
