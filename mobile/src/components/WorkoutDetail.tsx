import { Modal, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { PlannedWorkout, WorkoutSegment } from '../api/types';
import { translate } from '../i18n/runtime';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

function segmentTarget(segment: WorkoutSegment): string {
  if (segment.zone_target !== null) return translate('detail.zone', { value: segment.zone_target });
  const target = segment.rpe_target ?? segment.protocol_target;
  if (target) {
    const range = target.target_rpe_min === target.target_rpe_max
      ? String(target.target_rpe_min)
      : `${target.target_rpe_min}–${target.target_rpe_max}`;
    return `RPE ${range}`;
  }
  return `RPE ${segment.expected_rpe}`;
}

// WorkoutDetailBoundary calls this as a plain function, so it must stay hook-free:
// text uses the runtime translator, which follows the provider's current language.
export function WorkoutDetail({ workout, onClose }: {
  workout: PlannedWorkout | null;
  onClose: () => void;
}) {
  return (
    <Modal animationType="slide" onRequestClose={onClose} visible={workout !== null}>
      {workout ? (
        <View style={styles.page}>
          <Pressable accessibilityRole="button" onPress={onClose} style={styles.close}>
            <Text style={styles.closeText}>{translate('common.close')}</Text>
          </Pressable>
          <ScrollView contentContainerStyle={styles.content}>
            <Text style={styles.title}>{workout.name}</Text>
            <Text style={styles.description}>{workout.description}</Text>
            <Text style={styles.meta}>
              {workout.duration_minutes !== null
                ? `${Number(workout.duration_minutes)} min`
                : translate('planning.distanceBased', { distance: String(workout.distance_meters) })}
              {' · '}RPE {workout.expected_rpe_min}
              {workout.expected_rpe_max === workout.expected_rpe_min
                ? '' : `–${workout.expected_rpe_max}`}
            </Text>
            {workout.segments.map((segment) => (
              <View key={segment.sequence} style={styles.segment}>
                <Text style={styles.segmentTitle}>{segment.sequence}. {segment.name}</Text>
                <Text style={styles.description}>{segment.instructions}</Text>
                <Text style={styles.meta}>
                  {segment.duration_minutes !== null
                    ? `${Number(segment.duration_minutes)} min`
                    : segment.distance_meters !== null
                      ? `${segment.distance_meters} m`
                      : ''}
                  {' · '}{segmentTarget(segment)}
                  {segment.is_swim_technique ? ` · ${translate('planning.detail.technique')}` : ''}
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
      ) : null}
    </Modal>
  );
}

const styles = StyleSheet.create({
  page: { backgroundColor: colors.surface, flex: 1, paddingTop: spacing.xl },
  close: { alignSelf: 'flex-end', padding: spacing.md },
  closeText: { color: colors.brand, fontWeight: '800' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: spacing.xl },
  title: { color: colors.ink, fontSize: 24, fontWeight: '900' },
  description: { color: colors.ink, fontSize: 14, lineHeight: 21 },
  meta: { color: colors.inkMuted, fontSize: 12 },
  segment: { borderColor: colors.line, borderRadius: radius.md, borderWidth: 1, gap: spacing.xs, padding: spacing.md },
  segmentTitle: { color: colors.ink, fontSize: 15, fontWeight: '800' },
});
