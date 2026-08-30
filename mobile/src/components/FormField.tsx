import type { ReactNode } from 'react';
import {
  StyleSheet,
  Text,
  TextInput,
  type TextInputProps,
  View,
} from 'react-native';
import Animated, {
  interpolateColor,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { colors, motion, radius, spacing } from '../theme/tokens';

type FormFieldProps = TextInputProps & {
  label: string;
  hint?: string;
  suffix?: ReactNode;
};

const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

export function FormField({
  label,
  hint,
  suffix,
  onBlur,
  onFocus,
  style,
  ...inputProps
}: FormFieldProps) {
  const focusProgress = useSharedValue(0);
  const focusStyle = useAnimatedStyle(() => ({
    borderColor: interpolateColor(
      focusProgress.value,
      [0, 1],
      [colors.line, colors.brand],
    ),
  }));

  return (
    <View style={styles.group}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>{label}</Text>
        {suffix}
      </View>
      <AnimatedTextInput
        accessibilityLabel={label}
        onBlur={(event) => {
          focusProgress.value = withTiming(0, {
            duration: motion.duration.fast,
          });
          onBlur?.(event);
        }}
        onFocus={(event) => {
          focusProgress.value = withTiming(1, {
            duration: motion.duration.fast,
          });
          onFocus?.(event);
        }}
        placeholderTextColor={colors.inkFaint}
        selectionColor={colors.accent}
        style={[styles.input, focusStyle, style]}
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
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.line,
    borderRadius: radius.md,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    minHeight: 54,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  hint: {
    color: colors.inkMuted,
    fontSize: 12,
    lineHeight: 17,
  },
});
