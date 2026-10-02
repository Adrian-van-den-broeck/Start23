import { useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View, type AccessibilityState } from 'react-native';
import { colors, layout, radius, space, states } from '../tokens';
import { Text } from './Text';

type Props = {
  label: string;
  onPress: () => void | Promise<void>;
  variant?: 'primary' | 'secondary' | 'tertiary';
  busy?: boolean;
  disabled?: boolean;
  disabledReason?: string;
  accessibilityState?: AccessibilityState;
};

export function Button({ label, onPress, variant = 'primary', busy = false,
  disabled = false, disabledReason, accessibilityState }: Props) {
  const lock = useRef(false);
  const [pending, setPending] = useState(false);
  const [pressed, setPressed] = useState(false);
  const [focused, setFocused] = useState(false);
  const isBusy = busy || pending;
  const blocked = disabled || isBusy;
  async function press() {
    if (blocked || lock.current) return;
    lock.current = true;
    try {
      const result = onPress();
      if (result) { setPending(true); await result; }
    } finally {
      lock.current = false;
      setPending(false);
    }
  }
  const color = blocked ? colors.text : variant === 'primary' ? colors.textInverse : colors.primary;
  return (
    <View>
      <Pressable accessibilityRole="button" accessibilityLabel={label}
        accessibilityHint={disabledReason}
        accessibilityState={{ ...accessibilityState, busy: isBusy, disabled: blocked }}
        disabled={blocked} onPress={() => { void press(); }}
        onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
        onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
        style={[styles.button, variant === 'primary' ? styles.primary : variant === 'secondary' ? styles.secondary : styles.tertiary,
        pressed && (variant === 'primary' ? states.pressed : states.selected),
        blocked && styles.disabled, focused && { borderColor: variant === 'primary' ? colors.textInverse : colors.focus }]}>
        {isBusy ? <ActivityIndicator accessible={false} color={color} /> : null}
        <Text variant="button" accessible={false} importantForAccessibility="no" style={{ color, flexShrink: 1 }}>{label}</Text>
      </Pressable>
      {disabledReason ? <Text variant="supporting">{disabledReason}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    minWidth: layout.touch, minHeight: layout.touch, borderRadius: radius.control,
    borderWidth: layout.focusOutline, borderColor: 'transparent', paddingHorizontal: space[16],
    paddingVertical: space[12], flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: space[8]
  },
  primary: { minHeight: layout.primaryButton, backgroundColor: colors.primary },
  secondary: { backgroundColor: colors.secondary },
  tertiary: { backgroundColor: colors.background },
  disabled: { backgroundColor: colors.surfaceSubtle },
});
