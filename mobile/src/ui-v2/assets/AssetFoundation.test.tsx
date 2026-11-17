import { act, render } from '@testing-library/react-native';
import { StyleSheet, View } from 'react-native';

import DevAssetsRoute from '../../../app/dev-assets';
import { Icon, iconNames } from '../primitives/Icon';
import { HeaderLandscape } from './HeaderLandscape';
import { ActionLandscape } from './ActionLandscape';
import { DecorativeSvgFallback } from './LandscapeArtwork';

jest.mock('expo-router', () => {
  const { Text } = jest.requireActual('react-native');
  return { Redirect: () => <Text>Root redirect</Text> };
});
const Native = jest.requireActual<typeof import('react-native')>('react-native');
afterEach(() => jest.restoreAllMocks());

test('every semantic glyph renders and decorative duplicates add no image announcement', async () => {
  for (const name of iconNames) {
    const view = await render(<Icon name={name} />);
    expect(view.queryByRole('image')).toBeNull();
    await view.unmount();
  }
});

test('an informative icon exposes exactly the supplied localized label', async () => {
  const view = await render(<Icon name="warning" decorative={false} accessibilityLabel="Let op" />);
  expect(view.getAllByRole('image', { name: 'Let op' })).toHaveLength(1);
});

test('art remains inaccessible and noninteractive, and compact mode follows measured width and text scale', async () => {
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width: 393, height: 829, fontScale: 1, scale: 1 });
  const view = await render(<View style={{ width: 393 }}><HeaderLandscape variant="treesRiver" /></View>);
  const art = view.getByTestId('header-landscape', { includeHiddenElements: true });
  expect(art.props).toMatchObject({ pointerEvents: 'none', accessible: false, accessibilityElementsHidden: true, importantForAccessibility: 'no-hide-descendants' });
  // Layout is not a user action; directly deliver the native measurement to
  // the noninteractive subtree rather than firing a touch on hidden art.
  expect(StyleSheet.flatten(view.getByTestId('header-landscape', { includeHiddenElements: true }).props.style).height).toBe(140);
  await view.rerender(<View style={{ width: 320 }}><HeaderLandscape variant="treesRiver" /></View>);
  await act(() => art.props.onLayout({ nativeEvent: { layout: { width: 320 } } }));
  expect(StyleSheet.flatten(view.getByTestId('header-landscape', { includeHiddenElements: true }).props.style).height).toBe(96);
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width: 412, height: 829, fontScale: 2, scale: 1 });
  await view.rerender(<View style={{ width: 412 }}><HeaderLandscape /></View>);
  await act(() => art.props.onLayout({ nativeEvent: { layout: { width: 412 } } }));
  expect(StyleSheet.flatten(view.getByTestId('header-landscape', { includeHiddenElements: true }).props.style).height).toBe(96);
  await view.rerender(<ActionLandscape />);
  expect(view.getByTestId('action-landscape', { includeHiddenElements: true }).props).toMatchObject({ pointerEvents: 'none', accessible: false, importantForAccessibility: 'no-hide-descendants' });
});

test('a failed decorative SVG yields no replacement status or content', async () => {
  function BrokenSvg(): never { throw new Error('Test render failure'); }
  jest.spyOn(console, 'error').mockImplementation(() => undefined);
  const view = await render(<DecorativeSvgFallback><BrokenSvg /></DecorativeSvgFallback>);
  expect(view.toJSON()).toBeNull();
});

test('direct gallery navigation redirects in a release runtime', async () => {
  const original = __DEV__;
  try {
    Object.assign(globalThis, { __DEV__: false });
    const view = await render(<DevAssetsRoute />);
    expect(view.getByText('Root redirect')).toBeTruthy();
    expect(view.queryByText('Wombo asset proof')).toBeNull();
  } finally { Object.assign(globalThis, { __DEV__: original }); }
});
