import type { ReactNode } from 'react';
import {
  StyleSheet,
  Text,
  TextInput,
  type TextInputProps,
  View,
} from 'react-native';

import { colors, radius, spacing } from '../theme/tokens';

type FormFieldProps = TextInputProps & {
  label: string;
  hint?: string;
  suffix?: ReactNode;
};

export function FormField({
  label,
  hint,
  suffix,
  style,
  ...inputProps
}: FormFieldProps) {
  return (
    <View style={styles.group}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>{label}</Text>
        {suffix}
      </View>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={colors.inkFaint}
        style={[styles.input, style]}
        {...inputProps}
      />
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  group: {
    gap: spacing.xs,
  },
  labelRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  label: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  hint: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 17,
  },
});
