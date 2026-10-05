import { draft, occurrence, warning } from '../../features/planning/planning.test-fixtures';
import { planningCreationViewModel, selectionWorkoutViewModel } from './planningCreationViewModel';

test('candidate retains exact source, template version and distinct occurrence identity', () => {
  expect(selectionWorkoutViewModel(occurrence)).toEqual({
    templateId: occurrence.id, templateKey: occurrence.template_key, templateVersion: occurrence.version,
    occurrenceId: occurrence.occurrence_id, name: occurrence.name, discipline: occurrence.discipline,
    durationMinutes: occurrence.duration_minutes, distanceMeters: null, intensity: occurrence.intensity_bucket,
    description: expect.any(String),
  });
});
test('repeated templates retain server order, both measures and individual placement identities', () => {
  const repeat = { ...occurrence, occurrence_id: 'repeat', distance_meters: 1500 };
  const model = planningCreationViewModel({
    ...draft, accepted_workouts: [repeat, occurrence],
    placements: [{ occurrence_id: 'repeat', scheduled_date: '2026-10-07' }]
  });
  expect(model.accepted.map((workout) => workout.occurrenceId)).toEqual(['repeat', occurrence.occurrence_id]);
  expect(model.accepted.map((workout) => workout.templateId)).toEqual([occurrence.id, occurrence.id]);
  expect(model.accepted[0]).toMatchObject({ durationMinutes: occurrence.duration_minutes, distanceMeters: 1500 });
  expect(model.placements).toEqual([{ occurrenceId: 'repeat', date: '2026-10-07' }]);
});
test('distance-only measures stay distance-only and absent measures stay absent', () => {
  expect(selectionWorkoutViewModel({ ...occurrence, duration_minutes: null, distance_meters: 2500 }))
    .toMatchObject({ durationMinutes: null, distanceMeters: 2500 });
  expect(selectionWorkoutViewModel({ ...occurrence, duration_minutes: null, distance_meters: null }))
    .toMatchObject({ durationMinutes: null, distanceMeters: null });
});
test('public allowlist drops poison fields recursively and suppresses planning-card RPE description', () => {
  const poisoned = {
    ...occurrence, description: 'Public purpose. Verwachte RPE: 2-4.', tss: 99,
    planned_load: 100, realized_private_load: 88, selector_diagnostics: { hidden: true }
  };
  const model = planningCreationViewModel({
    ...draft, current_candidate: poisoned, accepted_workouts: [poisoned],
    ...{ tss: 99, selector_diagnostics: { hidden: true } }
  });
  expect(JSON.stringify(model)).not.toMatch(/tss|planned_load|realized_private_load|selector_diagnostics|Verwachte RPE/i);
  expect(model.candidate?.description).toBe('Public purpose.');
  expect(model.warnings).toEqual([{ title: 'Weekcombinatie vraagt aandacht', message: expect.any(String) }]);
  expect(model.warnings[0]).not.toHaveProperty('rule_id');
  expect(warning.code).toBe('target_outside_catalog_capacity');
});
test('server collecting/exhaustion/placement state is copied without composition inference', () => {
  expect(planningCreationViewModel({
    ...draft, accepted_workouts: [occurrence], current_candidate: null,
    exhausted: true
  })).toMatchObject({ state: 'collecting', candidate: null, exhausted: true });
  expect(planningCreationViewModel({ ...draft, state: 'placement', accepted_workouts: [] })).toMatchObject({ state: 'placement', accepted: [] });
});
