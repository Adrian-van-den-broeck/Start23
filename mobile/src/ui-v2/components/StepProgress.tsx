import { studioPresentation } from '../../ui-v3/presentation';
import { identity } from '../../ui-v3/tokens';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Text } from '../primitives/Text';
import { colors, radius, space } from '../tokens';

// `navigation` holds controls that sit beside the step count. It stays outside
// the summary element so screen readers can still reach each control.
export function StepProgress({ current, steps, completed, navigation }: {
  current: string; steps: readonly { step: string; label: string }[]; completed: ReadonlySet<string>;
  navigation?: ReactNode;
}) {
  const { t } = useLanguage();
  const index = steps.findIndex((item) => item.step === current);
  if (index < 0) return null;
  const label = t('onboarding.stepOf', { current: index + 1, total: steps.length });
  const completedLabels = steps.filter((item) => completed.has(item.step)).map((item) => item.label).join(', ');
  const summary = label + '. ' + steps[index].label + '.' + (completedLabels ? ' ' + t('onboarding.completedSteps', { steps: completedLabels }) : '');
  if (studioPresentation) return <View style={styles.progress}>
    <View style={styles.head}>
      <View accessible accessibilityLabel={summary} style={styles.count}>
        <Text variant="caption" tone="primary" accessible={false}>{label}</Text>
      </View>
      {navigation}
    </View>
    <View style={styles.rail} accessible={false} importantForAccessibility="no-hide-descendants">
      {steps.map(item => <View key={item.step} style={[styles.stage, { backgroundColor: item.step === current ? identity.orange : completed.has(item.step) ? colors.primary : colors.border }]} />)}
    </View>
  </View>;
  return <View style={styles.head}>
    <View accessible accessibilityLabel={summary} style={styles.capsule}>
      <View accessible={false} importantForAccessibility="no-hide-descendants" style={styles.dots}>
        {steps.map((item) => <View key={item.step} style={[styles.dot, (item.step === current || completed.has(item.step)) && { backgroundColor: colors.primary }]} />)}
      </View>
      <Text tone="primary" accessible={false}>{label}</Text>
    </View>
    {navigation}
  </View>;
}
const styles = StyleSheet.create({
  progress: { gap: space[8] },
  head: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', columnGap: space[12], rowGap: space[4] },
  count: { flexShrink: 1 },
  rail: { flexDirection: 'row', gap: 3 }, stage: { flex: 1, height: 4, borderRadius: 2 },
  capsule: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: space[12], paddingHorizontal: space[16], paddingVertical: space[12], borderRadius: radius.pill, backgroundColor: colors.primarySoft },
  dots: { flexDirection: 'row', gap: space[8] },
  dot: { width: 8, height: 8, borderRadius: radius.pill, backgroundColor: colors.borderControl },
});
