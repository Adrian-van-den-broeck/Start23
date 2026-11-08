import { Modal, ScrollView, StyleSheet, Text, View } from 'react-native';

import { useLanguage } from '../i18n/LanguageProvider';
import type { PlannedWorkout, WorkoutSegment } from '../api/types';
import { colors, radius, spacing } from '../theme/tokens';
import { MotionPressable as Pressable } from './MotionPressable';

function segmentTarget(segment: WorkoutSegment): string {
  if (segment.zone_target !== null) return `Zone ${segment.zone_target}`;
  const target = segment.rpe_target ?? segment.protocol_target;
  if (target) {
    const range = target.target_rpe_min === target.target_rpe_max
      ? String(target.target_rpe_min)
      : `${target.target_rpe_min}–${target.target_rpe_max}`;
    return `RPE ${range}`;
  }
  return `RPE ${segment.expected_rpe}`;
}

export function WorkoutDetail({ workout, onClose }: {
  workout: PlannedWorkout | null;
  onClose: () => void;
}) {
  const { t } = useLanguage();
  return (
    <Modal animationType="slide" onRequestClose={onClose} visible={workout !== null}>
      {workout ? (
        <View style={styles.page}>
          <Pressable accessibilityRole="button" onPress={onClose} style={styles.close}>
            <Text style={styles.closeText}>Sluiten</Text>
          </Pressable>
          <ScrollView contentContainerStyle={styles.content}>
            <Text style={styles.title}>{workout.name}</Text>
            <Text style={styles.description}>{workout.description}</Text>
            <Text style={styles.meta}>
              {workout.duration_minutes !== null
                ? `${Number(workout.duration_minutes)} min`
                : `${workout.distance_meters} m · afstandgestuurd`}
              {workout.source_prescription ? '' : ` · RPE ${workout.expected_rpe_min}`}
              {workout.source_prescription || workout.expected_rpe_max === workout.expected_rpe_min
                ? '' : `–${workout.expected_rpe_max}`}
            </Text>
            {workout.source_prescription ? <>
              <Text style={styles.meta}>{t('detail.sessionEffort', { value: workout.source_prescription.session_effort })}</Text>
              <Text style={styles.segmentTitle}>{t('detail.originalSource')}</Text>
              <Text style={styles.description}>{workout.source_prescription.original_text}</Text>
              {workout.source_prescription.estimated_active_minutes !== null ? <Text style={styles.description}>{t('detail.estimatedActive', { value: workout.source_prescription.estimated_active_minutes })}</Text> : null}
              {workout.source_prescription.blocks.map((block) => <View key={block.sequence} style={styles.segment}>
                <Text style={styles.segmentTitle}>{block.sequence}. {block.text}</Text>
                <Text style={styles.meta}>{block.kind === 'stationary_wall_rest' ? t('detail.wallRest') : t('detail.zone', { value: block.zone! })}</Text>
                {block.seconds !== null ? <Text style={styles.meta}>{t('detail.seconds', { value: block.seconds })}</Text> : null}
                {block.meters !== null ? <Text style={styles.meta}>{t('detail.meters', { value: block.meters })}</Text> : null}
              </View>)}
            </> : workout.segments.map((segment) => (
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
                  {segment.is_swim_technique ? ' · techniek' : ''}
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
