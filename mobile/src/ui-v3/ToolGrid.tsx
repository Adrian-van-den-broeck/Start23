import { useState } from 'react';
import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import { IconTile } from '../ui-v2/primitives/IconTile';
import type { IconName } from '../ui-v2/primitives/Icon';
import { Text } from '../ui-v2/primitives/Text';
import { colors, layout } from '../ui-v2/tokens';

export type Tool = Readonly<{ key: string; icon: IconName; label: string; onPress: () => void }>;

// Secondary tools as two columns of equal tiles. Large text falls back to one
// column so labels never truncate.
export function ToolGrid({ tools, disabled }: { tools: readonly Tool[]; disabled: boolean }) {
  const { fontScale } = useWindowDimensions();
  const single = fontScale > 1.3;
  return <View style={styles.grid}>
    {tools.map((tool) => <ToolTile key={tool.key} tool={tool} disabled={disabled} single={single} />)}
  </View>;
}

function ToolTile({ tool, disabled, single }: { tool: Tool; disabled: boolean; single: boolean }) {
  const [pressed, setPressed] = useState(false);
  const [focused, setFocused] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={tool.label} accessibilityState={{ disabled }}
    disabled={disabled} onPress={tool.onPress} onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)}
    onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={[styles.tile, single && styles.single, pressed && styles.pressed, disabled && styles.disabled, focused && styles.focused]}>
    <IconTile name={tool.icon} size="field" />
    <Text variant="label" tone="primary" accessible={false} importantForAccessibility="no">{tool.label}</Text>
  </Pressable>;
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  tile: { flexBasis: '47%', flexGrow: 1, minHeight: 96, gap: 10, padding: 14, borderRadius: 16,
    backgroundColor: colors.surface, borderWidth: layout.focusOutline, borderColor: 'transparent', justifyContent: 'space-between' },
  single: { flexBasis: '100%' },
  pressed: { backgroundColor: colors.primarySoft },
  disabled: { opacity: 0.6 },
  focused: { borderColor: colors.focus },
});
