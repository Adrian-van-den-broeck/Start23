import type { PlannedWorkout, WorkoutSegment } from '../../api/types';

export const sourceSegment: WorkoutSegment = {
  sequence: 1, name: 'Source segment', instructions: '4 × 200 m.\nRest exactly as instructed in source.',
  duration_minutes: '12.5', distance_meters: 800, zone_target: 2,
  protocol_target: {
    protocol_id: 'historical-protocol', segment_id: 'original', target_rpe_min: 6,
    target_rpe_max: 7, intensity_bucket: 'high', optional: false
  },
  rpe_target: { target_rpe_min: 3, target_rpe_max: 4, intensity_bucket: 'low', heart_rate_observation_required: true },
  expected_rpe: 5, is_swim_technique: false,
};
export const sourceWorkout: PlannedWorkout = {
  id: 'snapshot-1', template_id: 'template-1', template_key: 'source-template', template_version: 1,
  discipline: 'swim', name: 'Exact source workout', description: 'Exact source description. RPE 2–3.',
  duration_minutes: '30.5', distance_meters: 1200, intensity_bucket: 'low',
  expected_rpe_min: 2, expected_rpe_max: 3, segments: [sourceSegment], rpe_zones: [{
    zone_number: 2, target_rpe_min: 2, target_rpe_max: 3, display_label: 'Exact source reference',
    training_type: 'Exact training type', description: 'Exact reference description.',
  }], scheduled_date: '2020-01-02', source: 'auto_planned', status: 'cancelled', warnings: [],
};
