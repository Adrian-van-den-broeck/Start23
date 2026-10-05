import { effectiveUiVersion, initialUiVersion, implementedSlices } from './uiVersion';

describe('development UI resolution', () => {
  test.each([undefined, 'v1', 'invalid', 'V2', ''])('defaults %s to V1', (value) => {
    expect(initialUiVersion(true, value)).toBe('v1');
  });
  test('valid V2 is development-only and implemented slices are allowlisted', () => {
    expect(initialUiVersion(true, 'v2')).toBe('v2');
    expect(effectiveUiVersion(true, 'v2', 'workoutDetail')).toBe('v2');
    expect(effectiveUiVersion(true, 'v2', 'week')).toBe('v2');
    expect(effectiveUiVersion(false, 'v2', 'week')).toBe('v1');
    expect(effectiveUiVersion(true, 'v2', 'calendar')).toBe('v2');
    expect(effectiveUiVersion(false, 'v2', 'calendar')).toBe('v1');
    expect(effectiveUiVersion(true, 'v2', 'planningCreation')).toBe('v2');
    expect(effectiveUiVersion(false, 'v2', 'planningCreation')).toBe('v1');
    expect(effectiveUiVersion(true, 'v2', 'proposalReview')).toBe('v2');
    expect(effectiveUiVersion(false, 'v2', 'proposalReview')).toBe('v1');
    expect(Object.keys(implementedSlices)).toEqual(['workoutDetail', 'week', 'calendar', 'planningCreation', 'proposalReview']);
    for (const slice of ['activity', 'planning', 'profile', 'onboarding', 'zones', 'toString', '']) {
      expect(effectiveUiVersion(true, 'v2', slice)).toBe('v1');
    }
    expect(effectiveUiVersion(true, 'v1', 'workoutDetail')).toBe('v1');
  });
  test.each([undefined, 'v1', 'v2', 'invalid'])('release always forces V1 for %s', (value) => {
    expect(initialUiVersion(false, value)).toBe('v1');
    expect(effectiveUiVersion(false, 'v2', 'workoutDetail')).toBe('v1');
  });
});
