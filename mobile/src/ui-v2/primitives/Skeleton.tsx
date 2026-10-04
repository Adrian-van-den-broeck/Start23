import { StyleSheet, View } from 'react-native';
import { colors, radius, space } from '../tokens';
export function Skeleton() {
  return <View testID="week-skeleton" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.group}>
    <View style={styles.heading} /><View style={styles.card} /><View style={styles.heading} />
  </View>;
}
const styles = StyleSheet.create({
  group: { gap: space[24] }, heading: { height: 24, width: '65%', backgroundColor: colors.surfaceSubtle, borderRadius: radius.control },
  card: { height: 220, backgroundColor: colors.surfaceSubtle, borderRadius: radius.card }
});
