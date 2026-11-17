import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MotionPressable } from '../../components/MotionPressable';
import { Icon } from '../primitives/Icon';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';

export function PendingRpeBanner({ label, disabled, onPress }: { label: string; disabled: boolean; onPress: () => void }) {
  const [focused, setFocused] = useState(false);
  return <SafeAreaView edges={['top']} style={styles.safe}>
    <MotionPressable haptic="selection" accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }}
      disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} style={styles.banner}>
      <Icon name="info" color={colors.primary} />
      <Text variant="supporting" accessible={false} style={styles.label}>{label}</Text>
      <Icon name="chevron" size={20} color={colors.primary} />
      {focused ? <View pointerEvents="none" style={styles.focus} /> : null}
    </MotionPressable>
    <View style={{ height: space[8] }} />
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  safe: { backgroundColor: colors.background, paddingHorizontal: layout.phoneGutter },
  banner: { minHeight: layout.touch, backgroundColor: colors.primarySoft, borderRadius: radius.control,
    flexDirection: 'row', alignItems: 'center', gap: space[8], padding: space[12] },
  label: { flex: 1, color: colors.primary },
  focus: { ...StyleSheet.absoluteFill, borderRadius: radius.control, borderWidth: layout.focusOutline, borderColor: colors.focus },
});
