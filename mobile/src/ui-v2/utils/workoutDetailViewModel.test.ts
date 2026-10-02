import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { workoutDetailViewModel } from './workoutDetailViewModel';
import { sourceSegment, sourceWorkout } from './workout.test-fixtures';

test('preserves supplied array order, names, meaningful breaks and historical values without mutation', () => {
  const input = { ...sourceWorkout, segments: [{ ...sourceSegment, sequence: 4 }, { ...sourceSegment, sequence: 1 }] };
  const before = JSON.stringify(input);
  const model = workoutDetailViewModel(input);
  expect(model.segments.map((segment) => segment.sequence)).toEqual([4, 1]);
  expect(model.segments[0].instructions).toBe(sourceSegment.instructions);
  expect(model.summary.date).toBe('2020-01-02');
  expect(model.summary.status).toBe('cancelled');
  expect(model.description).toBe(sourceWorkout.description);
  expect(JSON.stringify(input)).toBe(before);
});

test('target precedence is zone, RPE, protocol, then expected; additional source targets survive explicitly', () => {
  const targets = [sourceSegment,
    { ...sourceSegment, zone_target: null },
    { ...sourceSegment, zone_target: null, rpe_target: null },
    { ...sourceSegment, zone_target: null, rpe_target: null, protocol_target: null }];
  const model = workoutDetailViewModel({ ...sourceWorkout, segments: targets });
  expect(model.segments.map((segment) => segment.target)).toEqual([
    { kind: 'zone', zone: 2 }, { kind: 'rpe', range: { min: 3, max: 4 } },
    { kind: 'protocol', range: { min: 6, max: 7 } }, { kind: 'expected', range: { min: 5, max: 5 } },
  ]);
  expect(model.segments[0].rpeTarget).toEqual({ min: 3, max: 4 });
  expect(model.segments[0].protocolTarget).toEqual({ min: 6, max: 7 });
  expect(model.segments[0].heartRateObservationRequired).toBe(true);
});

test.each([
  ['25.75', null], [null, 1250], ['25.75', 1250], [null, null],
] as const)('copies independent measures %s / %s and never estimates swim time', (duration, distance) => {
  const model = workoutDetailViewModel({
    ...sourceWorkout, duration_minutes: duration,
    distance_meters: distance, segments: [{ ...sourceSegment, duration_minutes: duration, distance_meters: distance }]
  });
  expect(model.summary.measures).toEqual({ durationMinutes: duration, distanceMeters: distance });
  expect(model.segments[0].measures).toEqual({ durationMinutes: duration, distanceMeters: distance });
});

test('sparse snapshot has no invented segments, targets, equipment or measures', () => {
  const model = workoutDetailViewModel({
    ...sourceWorkout, segments: [], rpe_zones: [], description: '',
    duration_minutes: null, distance_meters: null
  });
  expect(model.segments).toEqual([]);
  expect(model.rpeReference).toEqual([]);
  expect(model.description).toBe('');
  expect(model.expectedRpe).toEqual({ min: 2, max: 3 });
});

test('recursive explicit allowlist drops hidden fields at every level', () => {
  const hidden = {
    tss: 987.654, planned_load: 987.654, realized_load: 987.654,
    private_load: 987.654, physiological_private: { secret: 987.654 }
  };
  const input = {
    ...sourceWorkout, ...hidden,
    segments: [{
      ...sourceSegment, ...hidden, rpe_target: { ...sourceSegment.rpe_target!, ...hidden },
      protocol_target: { ...sourceSegment.protocol_target!, ...hidden }
    }],
    rpe_zones: [{ ...sourceWorkout.rpe_zones[0], ...hidden }], warnings: []
  };
  const encoded = JSON.stringify(workoutDetailViewModel(input));
  expect(encoded).not.toMatch(/tss|planned_load|realized_load|private_load|physiological_private|987\.654/i);
});


test('adapters depend only on public DTO types, safe formatting and local pure models', () => {
  const allowed = ['../../api/types', '../../lib/workoutPresentation', './workoutSummaryViewModel'];
  for (const name of ['workoutDetailViewModel.ts', 'workoutSummaryViewModel.ts']) {
    const source = readFileSync(join(__dirname, name), 'utf8');
    for (const [, dependency] of source.matchAll(/from ['"]([^'"]+)['"]/g)) expect(allowed).toContain(dependency);
    expect(source).not.toMatch(/console\.|fetch\(|Date\.now|Math\.random|useEffect|\.sort\(/);
  }
});
