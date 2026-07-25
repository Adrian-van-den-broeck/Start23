import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '../theme/tokens';

type StatusPillProps = {
  label: string;
  tone?: 'brand' | 'accent' | 'neutral';
};

const toneStyles = {
  brand: {
    backgroundColor: colors.brandSoft,
    color: colors.brand,
  },
  accent: {
    backgroundColor: colors.accentSoft,
    color: colors.accent,
  },
  neutral: {
    backgroundColor: colors.surfaceMuted,
    color: colors.inkMuted,
  },
} as const;

export function StatusPill({
  label,
  tone = 'neutral',
}: StatusPillProps) {
  const toneStyle = toneStyles[tone];

  return (
    <View
      accessibilityLabel={label}
      style={[styles.container, { backgroundColor: toneStyle.backgroundColor }]}
    >
      <Text style={[styles.label, { color: toneStyle.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
});
