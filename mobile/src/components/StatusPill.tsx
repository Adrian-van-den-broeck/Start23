import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '../theme/tokens';

type StatusPillProps = {
  label: string;
  tone?: 'brand' | 'accent' | 'neutral';
};

const toneStyles = {
  brand: {
    backgroundColor: colors.brandSoft,
    borderColor: '#C4DBD0',
    color: colors.brand,
  },
  accent: {
    backgroundColor: colors.accentSoft,
    borderColor: '#F6CFC3',
    color: colors.accent,
  },
  neutral: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.line,
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
      style={[
        styles.container,
        {
          backgroundColor: toneStyle.backgroundColor,
          borderColor: toneStyle.borderColor,
        },
      ]}
    >
      <View style={[styles.dot, { backgroundColor: toneStyle.color }]} />
      <Text style={[styles.label, { color: toneStyle.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: radius.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  dot: {
    borderRadius: radius.pill,
    height: 5,
    width: 5,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
});
