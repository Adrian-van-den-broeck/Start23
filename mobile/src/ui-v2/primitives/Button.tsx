import { useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View, type AccessibilityRole, type AccessibilityState } from 'react-native';
import { colors, layout, radius, space, states } from '../tokens';
import { Text } from './Text';
import { Icon, type IconName } from './Icon';

type Props = {
  label: string;
  accessibilityLabel?: string;
  accessibilityRole?: AccessibilityRole;
  onPress: () => void | Promise<void>;
  variant?: 'primary' | 'secondary' | 'outline' | 'tertiary';
  trailingIcon?: IconName;
  busy?: boolean;
  disabled?: boolean;
  disabledReason?: string;
  accessibilityState?: AccessibilityState;
};

export function Button({ label, accessibilityLabel = label, accessibilityRole = 'button', onPress, variant = 'primary', busy = false,
  disabled = false, disabledReason, accessibilityState, trailingIcon }: Props) {
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
      <Pressable accessibilityRole={accessibilityRole} accessibilityLabel={accessibilityLabel}
        accessibilityHint={disabledReason}
        accessibilityState={{ ...accessibilityState, busy: isBusy, disabled: blocked }}
        disabled={blocked} onPress={() => { void press(); }}
        onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
        onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
        style={[styles.button, variant === 'primary' ? styles.primary : variant === 'secondary' ? styles.secondary : variant === 'outline' ? styles.outline : styles.tertiary,
        pressed && (variant === 'primary' ? states.pressed : states.selected),
        (accessibilityState?.checked === true || accessibilityState?.selected === true) && { borderColor: colors.focus },
        blocked && styles.disabled]}>
        {isBusy ? <ActivityIndicator accessible={false} color={color} /> : null}
        {(accessibilityState?.checked === true || accessibilityState?.selected === true) ? <Icon name="check" size={20} color={color} /> : null}
        <Text variant="button" accessible={false} importantForAccessibility="no" style={{ color, flexShrink: 1 }}>{label}</Text>
        {trailingIcon ? <Icon name={trailingIcon} color={color} /> : null}
        {focused ? <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" style={[styles.focusRing, { borderColor: variant === 'primary' && !blocked ? colors.textInverse : colors.focus }]} /> : null}
      </Pressable>
      {disabledReason ? <Text variant="supporting">{disabledReason}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    minWidth: layout.touch, minHeight: layout.touch, borderRadius: radius.button,
    borderWidth: layout.controlEdge, borderColor: 'transparent', paddingHorizontal: space[16],
    paddingVertical: space[16], flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: space[8]
  },
  primary: { minHeight: layout.primaryButton, backgroundColor: colors.primary },
  secondary: { minHeight: layout.secondaryButton, backgroundColor: colors.secondary },
  outline: { minHeight: layout.secondaryButton, backgroundColor: colors.surface, borderColor: colors.borderControl },
  focusRing: { ...StyleSheet.absoluteFill, margin: layout.focusOutline, borderWidth: layout.focusOutline, borderRadius: radius.button, borderColor: colors.focus },
  tertiary: { backgroundColor: colors.background },
  disabled: { backgroundColor: colors.surfaceSubtle },
});
