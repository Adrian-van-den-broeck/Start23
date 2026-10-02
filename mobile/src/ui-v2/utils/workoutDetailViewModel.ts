import type { PlannedWorkout, WorkoutSegment } from '../../api/types';
import { workoutSummaryViewModel, type WorkoutMeasures, type WorkoutSummaryViewModel } from './workoutSummaryViewModel';

export type RpeRange = Readonly<{ min: number; max: number }>;
export type SegmentTarget =
  | Readonly<{ kind: 'zone'; zone: number }>
  | Readonly<{ kind: 'rpe' | 'protocol' | 'expected'; range: RpeRange }>;
export type SegmentViewModel = Readonly<{
  sequence: number;
  name: string;
  instructions: string;
  measures: WorkoutMeasures;
  target: SegmentTarget;
  rpeTarget: RpeRange | null;
  protocolTarget: RpeRange | null;
  heartRateObservationRequired: boolean;
  optionalProtocol: boolean;
  technique: boolean;
}>;
export type WorkoutDetailViewModel = Readonly<{
  summary: WorkoutSummaryViewModel;
  description: string;
  expectedRpe: RpeRange;
  segments: readonly SegmentViewModel[];
  rpeReference: readonly Readonly<{ label: string; trainingType: string; description: string; range: RpeRange }>[];
}>;

function segmentViewModel(segment: WorkoutSegment): SegmentViewModel {
  const rpeTarget = segment.rpe_target ? {
    min: segment.rpe_target.target_rpe_min, max: segment.rpe_target.target_rpe_max,
  } : null;
  const protocolTarget = segment.protocol_target ? {
    min: segment.protocol_target.target_rpe_min, max: segment.protocol_target.target_rpe_max,
  } : null;
  const target: SegmentTarget = segment.zone_target != null
    ? { kind: 'zone', zone: segment.zone_target }
    : rpeTarget ? { kind: 'rpe', range: rpeTarget }
      : protocolTarget ? { kind: 'protocol', range: protocolTarget }
        : { kind: 'expected', range: { min: segment.expected_rpe, max: segment.expected_rpe } };
  return {
    sequence: segment.sequence, name: segment.name, instructions: segment.instructions,
    measures: { durationMinutes: segment.duration_minutes ?? null, distanceMeters: segment.distance_meters ?? null },
    target, rpeTarget, protocolTarget,
    heartRateObservationRequired: segment.rpe_target?.heart_rate_observation_required === true,
    optionalProtocol: segment.protocol_target?.optional === true,
    technique: segment.is_swim_technique,
  };
}

export function workoutDetailViewModel(workout: PlannedWorkout): WorkoutDetailViewModel {
  return {
    summary: workoutSummaryViewModel(workout),
    description: workout.description,
    expectedRpe: { min: workout.expected_rpe_min, max: workout.expected_rpe_max },
    segments: workout.segments.map(segmentViewModel),
    rpeReference: workout.rpe_zones.map((zone) => ({
      label: zone.display_label, trainingType: zone.training_type, description: zone.description,
      range: { min: zone.target_rpe_min, max: zone.target_rpe_max },
    })),
  };
}
