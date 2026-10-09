import { useState, type RefObject } from 'react';
import { StyleSheet, TextInput, useWindowDimensions, View, type TextInputProps } from 'react-native';
import { colors, layout, radius, space, typography } from '../tokens';
import { FormField, type FieldDetails } from './FormField';
import { type IconName } from './Icon';
import { IconTile } from './IconTile';
import { Text } from './Text';

export type InputProps = TextInputProps & FieldDetails & {
  disabled?: boolean; readOnly?: boolean; unit?: string; icon?: IconName; inputRef?: RefObject<TextInput | null>;
};

export function Input({ label, hint, error, optionalLabel, disabledReason, disabled = false,
  readOnly = false, unit, icon, multiline = false, style, onFocus, onBlur, editable = true,
  accessibilityLabel, accessibilityHint, accessibilityState, inputRef, ...props }: InputProps) {
  const [focused, setFocused] = useState(false);
  const { width, fontScale } = useWindowDimensions();
  const compact = width < 360 || fontScale >= 1.5;
  const locked = disabled || readOnly || !editable;
  const fullLabel = [accessibilityLabel ?? label, accessibilityLabel ? undefined : optionalLabel, unit].filter(Boolean).join(', ');
  return <FormField label={compact && unit ? `${label} (${unit})` : label} hint={hint} error={error}
    optionalLabel={optionalLabel} disabledReason={disabledReason}>
    {(labelId) => <View style={{ gap: space[8] }}>
      {icon && compact ? <IconTile name={icon} size="field" /> : null}
      <View style={[styles.control, locked && styles.locked, error && { borderColor: colors.destructive }]}>
        {icon && !compact ? <View style={{ paddingLeft: space[12] }}><IconTile name={icon} size="field" /></View> : null}
        {readOnly ? <Text accessibilityLabel={`${fullLabel}: ${props.value ?? ''}`} style={styles.readOnly}>{props.value}</Text> :
          <TextInput {...props} ref={inputRef} style={[styles.input, multiline && styles.multiline, style]}
            accessibilityLabel={fullLabel} accessibilityLabelledBy={!accessibilityLabel && compact && unit ? labelId : undefined}
            accessibilityHint={[accessibilityHint ?? hint, error, disabledReason].filter(Boolean).join('. ') || undefined}
            accessibilityState={{ ...accessibilityState, disabled: locked }} editable={!locked}
            placeholderTextColor={colors.textMuted} allowFontScaling multiline={multiline} aria-invalid={Boolean(error)}
            onFocus={(event) => { setFocused(true); onFocus?.(event); }}
            onBlur={(event) => { setFocused(false); onBlur?.(event); }} />}
        {unit && !compact ? <View style={styles.unit}><Text tone="textMuted">{unit}</Text></View> : null}
        {focused || error ? <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants"
          style={[styles.ring, { borderColor: error ? colors.destructive : colors.focus }]} /> : null}
      </View>
    </View>}
  </FormField>;
}
const styles = StyleSheet.create({
  control: { minHeight: layout.fieldHeight, flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderColor: colors.borderControl, borderWidth: layout.controlEdge,
    borderRadius: radius.control },
  locked: { backgroundColor: colors.surfaceSubtle },
  input: { ...typography.body, minHeight: layout.fieldHeight, minWidth: 0, flex: 1,
    color: colors.text, padding: space[12] },
  multiline: { minHeight: layout.multilineFieldHeight, textAlignVertical: 'top' },
  readOnly: { flex: 1, padding: space[12] },
  unit: { alignSelf: 'stretch', justifyContent: 'center', paddingHorizontal: space[12],
    borderLeftWidth: layout.controlEdge, borderColor: colors.borderControl, backgroundColor: colors.surfaceSubtle,
    borderTopRightRadius: radius.control, borderBottomRightRadius: radius.control },
  ring: { ...StyleSheet.absoluteFill, top: -layout.controlEdge, right: -layout.controlEdge, bottom: -layout.controlEdge, left: -layout.controlEdge, borderRadius: radius.control, borderWidth: layout.focusOutline },
});
