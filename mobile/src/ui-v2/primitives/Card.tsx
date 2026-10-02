import { StyleSheet, View, type ViewProps } from 'react-native';
import { colors, layout, radius } from '../tokens';

export function Card({ children, style, ...props }: ViewProps) {
  return <View {...props} style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderRadius: radius.card, padding: layout.cardPadding },
});
