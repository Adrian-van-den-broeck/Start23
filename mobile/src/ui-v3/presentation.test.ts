import { resolvePresentation } from './presentation';

test.each([
  [undefined, 'v3'],
  ['v2', 'v2'],
  ['v3', 'v3'],
  ['v1', 'v1'],
  ['', 'v1'],
  ['V3', 'v1'],
])('resolves build flag %s to %s', (flag, presentation) => {
  expect(resolvePresentation(flag)).toBe(presentation);
});
