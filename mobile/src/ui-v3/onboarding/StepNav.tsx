import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Icon } from '../../ui-v2/primitives/Icon';
import { Text } from '../../ui-v2/primitives/Text';
import { colors, layout, radius, space } from '../../ui-v2/tokens';

export type StepLink = Readonly<{
  label: string; accessibilityLabel: string; hint: string; onPress: () => void;
}>;

// Moves the view between onboarding steps the athlete has already reached. It
// only changes which step is shown; saving stays with each step's own action.
export function StepNav({ previous, next, disabled = false }: {
  previous?: StepLink; next?: StepLink; disabled?: boolean;
}) {
  if (!previous && !next) return null;
  return <View style={styles.nav}>
    {previous ? <StepLinkButton link={previous} direction={-1} disabled={disabled} /> : null}
    {next ? <StepLinkButton link={next} direction={1} disabled={disabled} /> : null}
  </View>;
}

function StepLinkButton({ link, direction, disabled }: { link: StepLink; direction: -1 | 1; disabled: boolean }) {
  const [focused, setFocused] = useState(false);
  const chevron = <Icon name={direction === -1 ? 'chevronLeft' : 'chevron'} size={20} color={colors.primary} />;
  return <Pressable accessibilityRole="button" accessibilityLabel={link.accessibilityLabel} accessibilityHint={link.hint}
    accessibilityState={{ disabled }} disabled={disabled} onPress={link.onPress}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={({ pressed }) => [styles.link, pressed && styles.pressed, disabled && styles.disabled, focused && styles.focused]}>
    {direction === -1 ? chevron : null}
    <Text variant="label" tone="primary" accessible={false} importantForAccessibility="no">{link.label}</Text>
    {direction === 1 ? chevron : null}
  </Pressable>;
}

const styles = StyleSheet.create({
  // The chevron's own padding would otherwise leave the row short of the gutter.
  nav: { flexDirection: 'row', alignItems: 'center', gap: space[4], marginRight: -space[8] },
  link: { minHeight: layout.touch, minWidth: layout.touch, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: space[4], paddingHorizontal: space[8], borderRadius: radius.pill,
    borderWidth: layout.focusOutline, borderColor: 'transparent' },
  pressed: { backgroundColor: colors.primarySoft },
  disabled: { opacity: 0.6 },
  focused: { borderColor: colors.focus },
});
