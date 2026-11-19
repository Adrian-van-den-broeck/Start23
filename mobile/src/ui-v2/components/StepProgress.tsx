import { studioPresentation } from '../../ui-v3/presentation';
import { identity } from '../../ui-v3/tokens';
import { StyleSheet, View } from 'react-native';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';

export function StepProgress({ current, steps, completed }: {
  current: string; steps: readonly { step: string; label: string }[]; completed: ReadonlySet<string>;
}) {
  const index = steps.findIndex((item) => item.step === current);
  if (index < 0) return null;
  const label = 'Stap ' + (index + 1) + ' van ' + steps.length;
  const completedLabels = steps.filter((item) => completed.has(item.step)).map((item) => item.label).join(', ');
  if (studioPresentation) return <View accessible accessibilityLabel={[label, steps[index].label, completedLabels].filter(Boolean).join('. ')} style={{ gap: space[8] }}>
    <Text variant="caption" tone="primary" accessible={false}>{label}</Text>
    <View style={styles.rail} accessible={false} importantForAccessibility="no-hide-descendants">
      {steps.map(item => <View key={item.step} style={[styles.stage, { backgroundColor: item.step === current ? identity.orange : completed.has(item.step) ? colors.primary : colors.border }]} />)}
    </View>
  </View>;
  return <View accessible accessibilityLabel={label + '. ' + steps[index].label + '.' + (completedLabels ? ' Afgerond: ' + completedLabels + '.' : '')} style={styles.capsule}>
    <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.dots}>
      {steps.map((item) => <View key={item.step} style={[styles.dot, (item.step === current || completed.has(item.step)) && { backgroundColor: colors.primary }]} />)}
    </View>
    <Text tone="primary" accessible={false}>{label}</Text>
  </View>;
}
const styles = StyleSheet.create({
  rail: { flexDirection: 'row', gap: 3 }, stage: { flex: 1, height: 4, borderRadius: 2 },
  capsule: { alignSelf: 'flex-start', flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[12], paddingHorizontal: space[16], paddingVertical: space[12], borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  dots: { flexDirection: 'row', gap: space[8] },
  dot: { width: 8, height: 8, borderRadius: radius.pill, backgroundColor: colors.borderControl },
});
