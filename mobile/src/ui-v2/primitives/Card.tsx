import { StyleSheet, useWindowDimensions, View, type ViewProps } from 'react-native';
import { colors, focusCardPadding, layout, radius, shadows } from '../tokens';

export function Card({ children, style, padding = 'standard', elevated = false, ...props }: ViewProps & {
  padding?: 'standard' | 'focus' | 'form'; elevated?: boolean;
}) {
  const { width, fontScale } = useWindowDimensions();
  return <View {...props} style={[styles.card, padding !== 'standard' && { padding: focusCardPadding(width, fontScale) },
    elevated && shadows.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderRadius: radius.card, padding: layout.cardPadding },
});
