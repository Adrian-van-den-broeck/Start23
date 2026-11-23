import { StyleSheet, View } from 'react-native';
import type { SegmentViewModel } from '../ui-v2/utils/workoutDetailViewModel';
import { identity, palette } from './tokens';

const segmentColors = [palette.primary, identity.orange, palette.textMuted] as const;

// A proportional strip of the supplied session sequence. Mixed or missing units
// have no honest common axis. The ordered text below remains the accessible chart.
export function SegmentProfile({ segments }: { segments: readonly SegmentViewModel[] }) {
  if (segments.length < 2) return null;
  const durations = segments.map(({ measures }) => Number(measures.durationMinutes));
  const distances = segments.map(({ measures }) => Number(measures.distanceMeters));
  const positive = (values: number[]) => values.every(value => Number.isFinite(value) && value > 0);
  const values = positive(durations) ? durations : positive(distances) ? distances : null;
  if (!values) return null;
  return <View testID="segment-profile" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.strip}>
    {values.map((value, index) => <View key={index} style={{ flexGrow: value, flexBasis: 0, backgroundColor: segmentColors[index % segmentColors.length] }} />)}
  </View>;
}
const styles = StyleSheet.create({ strip: { flexDirection: 'row', height: 8, gap: 2, borderRadius: 3, overflow: 'hidden' } });
