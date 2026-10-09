import { effectiveUiVersion, initialUiVersion, implementedSlices } from './uiVersion';

describe('user-selectable UI resolution', () => {
  test.each([undefined, 'v1', 'invalid', 'V2', ''])('defaults %s to V1', value => {
    expect(initialUiVersion(value)).toBe('v1');
  });
  test('an explicit V2 build default is supported', () => {
    expect(initialUiVersion('v2')).toBe('v2');
  });
  test.each(Object.keys(implementedSlices))('both presentations remain available for %s', slice => {
    expect(effectiveUiVersion('v2', slice)).toBe('v2');
    expect(effectiveUiVersion('v1', slice)).toBe('v1');
  });
  test.each(['activity', 'planning', 'profile', 'onboarding', 'zones', 'toString', ''])('unknown/shared slice %s falls back to V1', slice => {
    expect(effectiveUiVersion('v2', slice)).toBe('v1');
  });
});
