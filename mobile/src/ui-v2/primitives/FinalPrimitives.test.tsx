import { act, fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import DevPrimitivesRoute from '../../../app/dev-primitives';
import { PrimitiveGallery } from '../dev/PrimitiveGallery';
import { Card } from './Card';
import { ChoiceRow } from './ChoiceRow';
import { IconTile } from './IconTile';
import { Input } from './Input';
import { Notice } from './Notice';
import { SegmentedControl } from './SegmentedControl';
import { Divider } from './Divider';
import { Skeleton } from './Skeleton';
import { colors } from '../tokens';

const Native = jest.requireActual<typeof import('react-native')>('react-native');
jest.mock('expo-router', () => {
  const { Text } = jest.requireActual('react-native');
  return { Redirect: () => <Text>Root redirect</Text>, useLocalSearchParams: () => ({}) };
});
afterEach(() => jest.restoreAllMocks());

test('Input preserves native editability, focus callbacks, value and accessible unit/error; the ring never shifts content', async () => {
  const focus = jest.fn(); const blur = jest.fn(); const change = jest.fn();
  const view = await render(<Input label="Heart rate" unit="bpm" value="58" hint="Measured value" error="Check value"
    onFocus={focus} onBlur={blur} onChangeText={change} />);
  const field = view.getByDisplayValue('58');
  expect(field.props.accessibilityLabel).toBe('Heart rate, bpm');
  expect(field.props.accessibilityHint).toBe('Measured value. Check value');
  expect(field.props.allowFontScaling).toBe(true);
  expect(field.props.maxFontSizeMultiplier).toBeUndefined();
  const before = StyleSheet.flatten(field.props.style);
  await fireEvent(field, 'focus', {});
  expect(focus).toHaveBeenCalledTimes(1);
  expect(StyleSheet.flatten(field.props.style)).toEqual(before);
  await fireEvent.changeText(field, '59');
  expect(change).toHaveBeenCalledWith('59');
  await fireEvent(field, 'blur', {});
  expect(blur).toHaveBeenCalledTimes(1);
  expect(view.getByRole('alert').props.children).toBe('Check value');
  await view.rerender(<Input label="Read-only" value="58" readOnly />);
  expect(view.queryByDisplayValue('58')).toBeNull();
  expect(view.getByLabelText('Read-only: 58')).toBeTruthy();
  await view.rerender(<Input label="Locked" value="58" editable={false} />);
  expect(view.getByDisplayValue('58').props.editable).toBe(false);
});

test('320dp and 200% type put units in persistent labels and reduce focus-card padding without font clamping', async () => {
  for (const [width, fontScale] of [[320, 1], [393, 2]]) {
    jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width, height: 829, fontScale, scale: 1 });
    const view = await render(<Card padding="form" testID="card"><Input label="Heart rate" unit="bpm" value="58" icon="heartRate" /></Card>);
    expect(view.getByText('Heart rate (bpm)')).toBeTruthy();
    expect(view.queryByText('bpm')).toBeNull();
    expect(view.getByDisplayValue('58').props.accessibilityLabel).toBe('Heart rate, bpm');
    expect(StyleSheet.flatten(view.getByTestId('card').props.style).padding).toBe(16);
    await view.unmount();
  }
});

test('ChoiceRow exposes real radio/checkbox checked state and disabled controls cannot select', async () => {
  const press = jest.fn();
  const view = await render(<><ChoiceRow label="Monday" selected onPress={press} />
    <ChoiceRow label="Tuesday" selected={false} onPress={press} />
    <ChoiceRow label="Unavailable" selected disabled mode="checkbox" onPress={press} disabledReason="Reason" /></>);
  expect(view.getByRole('radio', { name: 'Monday' }).props.accessibilityState.checked).toBe(true);
  expect(view.getByRole('radio', { name: 'Tuesday' }).props.accessibilityState.checked).toBe(false);
  await fireEvent.press(view.getByRole('checkbox'));
  expect(press).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('radio', { name: 'Tuesday' }));
  expect(press).toHaveBeenCalledTimes(1);
  for (const radio of view.getAllByRole('radio')) {
    expect(StyleSheet.flatten(radio.props.style).minHeight).toBeGreaterThanOrEqual(48);
    expect(StyleSheet.flatten(radio.props.style).minWidth).toBeGreaterThanOrEqual(48);
  }
});

test('exclusive segments stack at large text and when localized labels do not fit measured thirds', async () => {
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width: 393, height: 829, fontScale: 1, scale: 1 });
  const change = jest.fn();
  const options = [{ value: 'week', label: 'Week' }, { value: 'month', label: 'Long month label' }];
  const view = await render(<SegmentedControl options={options} value="week" onChange={change} accessibilityLabel="Mode" />);
  const group = view.getByTestId('segmented-control');
  await fireEvent(group, 'layout', { nativeEvent: { layout: { width: 320 } } });
  for (const text of view.getAllByText(/Week|Long month label/, { includeHiddenElements: true })) {
    if (text.props.onLayout) await act(() => text.props.onLayout({ nativeEvent: { layout: { width: 40 } } }));
  }
  expect(StyleSheet.flatten(view.getByTestId('segmented-control').props.style).flexDirection).toBe('row');
  await fireEvent.press(view.getByRole('radio', { name: 'Long month label' }));
  expect(change).toHaveBeenCalledWith('month');
  const measurement = view.getAllByText('Long month label', { includeHiddenElements: true }).find((node) => node.props.onLayout)!;
  await act(() => measurement.props.onLayout({ nativeEvent: { layout: { width: 220 } } }));
  expect(StyleSheet.flatten(view.getByTestId('segmented-control').props.style).flexDirection).toBeUndefined();
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width: 393, height: 829, fontScale: 2, scale: 1 });
  await view.rerender(<SegmentedControl options={options} value="week" onChange={change} accessibilityLabel="Mode" disabled />);
  expect(StyleSheet.flatten(view.getByTestId('segmented-control').props.style).flexDirection).toBeUndefined();
  await fireEvent.press(view.getByRole('radio', { name: 'Week' }));
  expect(change).toHaveBeenCalledTimes(1);
});

test('Notice has explicit title/body/action for every tone and icon circles are decorative', async () => {
  const press = jest.fn();
  for (const tone of ['info', 'warning', 'error', 'success'] as const) {
    const view = await render(<Notice tone={tone} title={tone} action={{ label: 'Review', onPress: press }}>Full explanation</Notice>);
    expect(view.getByText(tone)).toBeTruthy();
    expect(view.getByText('Full explanation')).toBeTruthy();
    await fireEvent.press(view.getByRole('button', { name: 'Review' }));
    expect(view.queryByRole('image')).toBeNull();
    await view.unmount();
  }
  expect(press).toHaveBeenCalledTimes(4);
  const tile = await render(<IconTile name="run" size="focus" tone="run" />);
  expect(tile.queryByRole('image')).toBeNull();
  expect(tile.toJSON()).toMatchObject({ props: { pointerEvents: 'none', accessibilityElementsHidden: true,
    style: { width: 64, height: 64, backgroundColor: colors.sport.run.soft } } });
});

test('review host and direct route are unavailable in release', async () => {
  const original = __DEV__;
  try {
    Object.assign(globalThis, { __DEV__: false });
    const gallery = await render(<PrimitiveGallery />);
    expect(gallery.toJSON()).toBeNull();
    const route = await render(<DevPrimitivesRoute />);
    expect(route.getByText('Root redirect')).toBeTruthy();
  } finally { Object.assign(globalThis, { __DEV__: original }); }
});

test('divider and static skeleton are excluded from the accessibility tree', async () => {
  const view = await render(<><Divider /><Skeleton /></>);
  expect(view.getByTestId('week-skeleton', { includeHiddenElements: true }).props).toMatchObject({
    accessible: false, accessibilityElementsHidden: true, importantForAccessibility: 'no-hide-descendants',
  });
  expect(view.queryByTestId('week-skeleton')).toBeNull();
});
