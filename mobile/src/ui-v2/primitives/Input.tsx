import { useId } from 'react';
import { StyleSheet, TextInput, View, type TextInputProps } from 'react-native';
import { colors, layout, radius, space } from '../tokens';
import { Text } from './Text';

export function Input({ label, hint, disabled = false, ...props }: TextInputProps & {
  label: string; hint?: string; disabled?: boolean;
}) {
  const id = useId();
  return <View style={styles.field}>
    <Text nativeID={id} variant="label">{label}</Text>
    <TextInput {...props} accessibilityLabel={label} accessibilityLabelledBy={id}
      accessibilityHint={hint} accessibilityState={{ disabled }} editable={!disabled}
      allowFontScaling multiline style={[styles.input, props.style]} />
    {hint ? <Text variant="supporting" tone="textMuted">{hint}</Text> : null}
  </View>;
}
const styles = StyleSheet.create({
  field: { gap: space[8] },
  input: {
    minHeight: layout.primaryButton, color: colors.text, backgroundColor: colors.surface,
    borderColor: colors.borderControl, borderWidth: layout.focusOutline, borderRadius: radius.control,
    padding: space[12], fontSize: 16, textAlignVertical: 'top',
  },
});
