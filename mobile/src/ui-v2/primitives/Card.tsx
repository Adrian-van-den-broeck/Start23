import { studioPresentation } from '../../ui-v3/presentation';
import { StyleSheet, useWindowDimensions, View, type ViewProps } from 'react-native';
import { colors, focusCardPadding, layout, radius, shadows } from '../tokens';

export function Card({ children, style, padding = 'standard', elevated = false, ...props }: ViewProps & {
  padding?: 'standard' | 'focus' | 'form'; elevated?: boolean;
}) {
  const { width, fontScale } = useWindowDimensions();
  return <View {...props} style={[styles.card, padding !== 'standard' && { padding: focusCardPadding(width, fontScale) },
    studioPresentation ? styles.outline : elevated && shadows.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  outline: { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  card: { backgroundColor: colors.surface, borderRadius: radius.card, padding: layout.cardPadding },
});
