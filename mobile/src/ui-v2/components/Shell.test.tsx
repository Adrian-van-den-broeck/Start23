import { fireEvent, render } from '@testing-library/react-native';
import * as Native from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppHeader } from './AppHeader';
import { BottomNavigation, NavigationFooter } from './BottomNavigation';
import { ShellInsets, ShellSafeArea } from './ShellInsets';
import { PendingRpeBanner } from './PendingRpeBanner';
import { colors, layout } from '../tokens';

const destinations = [
  { key: 'planning', label: 'Week', icon: 'week' },
  { key: 'calendar', label: 'Calendar', icon: 'calendar' },
  { key: 'activities', label: 'Activities', icon: 'activities' },
] as const;
jest.mock('react-native/Libraries/Utilities/useWindowDimensions', () => ({ __esModule: true, default: jest.fn(() => ({ width: 393, height: 800, fontScale: 1, scale: 1 })) }));
afterEach(() => jest.restoreAllMocks());
test('measured fit switches all labels together, grows and invalidates translated measurements', async () => {
  jest.mocked(Native.useWindowDimensions).mockReturnValue({ width: 412, height: 800, fontScale: 1, scale: 1 });
  const onSelect = jest.fn(); const onHeight = jest.fn();
  const view = await render(<BottomNavigation destinations={destinations} selectedKey="calendar" onSelect={onSelect} onHeight={onHeight} />);
  await fireEvent(view.getByTestId('training-root-navigation'), 'layout', { nativeEvent: { layout: { width: 388, height: 64 } } });
  for (const destination of destinations) {
    await fireEvent(view.getByTestId(`navigation-measure-${destination.key}`, { includeHiddenElements: true }), 'textLayout', { nativeEvent: { lines: [{ width: 52 }] } });
  }
  for (const tab of view.getAllByRole('tab')) expect(Native.StyleSheet.flatten(tab.props.style).flexDirection).toBe('row');
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' })); expect(onSelect).toHaveBeenCalledWith('activities');
  expect(onHeight).toHaveBeenCalledWith(64);
  expect(Native.StyleSheet.flatten(view.getByRole('tab', { name: 'Calendar' }).props.style).backgroundColor).toBe(colors.primary);
  await view.rerender(<BottomNavigation destinations={destinations.map(d => ({ ...d, label: `${d.label} extended source label` }))} selectedKey="calendar" onSelect={onSelect} />);
  for (const tab of view.getAllByRole('tab')) expect(Native.StyleSheet.flatten(tab.props.style).flexDirection).not.toBe('row');
});
test.each([[320, 1], [360, 1], [393, 2]])('narrow/large text %s/%s retains three scalable visible labels', async (width, fontScale) => {
  jest.mocked(Native.useWindowDimensions).mockReturnValue({ width, height: 800, fontScale, scale: 1 });
  const view = await render(<BottomNavigation destinations={destinations} selectedKey="planning" onSelect={jest.fn()} />);
  for (const tab of view.getAllByRole('tab')) {
    expect(Native.StyleSheet.flatten(tab.props.style)).toMatchObject({ minHeight: 56, minWidth: 48 });
    expect(Native.StyleSheet.flatten(tab.props.style).flexDirection).not.toBe('row');
  }
  expect(view.getByRole('tab', { name: 'Week' }).props.accessibilityState.selected).toBe(true);
});
test('header callbacks and disabled state stay literal, landscape stays decorative', async () => {
  const back = jest.fn(); const profile = jest.fn();
  const view = await render(<AppHeader title="Training calendar" onBack={back} backLabel="Return to Week" onProfile={profile} profileLabel="Profile" profileDisabled landscape="treesRiver" />);
  expect(Native.StyleSheet.flatten(view.getByRole('button', { name: 'Profile' }).props.style)).toMatchObject({ minHeight: 48, minWidth: 48 });
  await fireEvent.press(view.getByRole('button', { name: 'Profile' })); expect(profile).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Return to Week' })); expect(back).toHaveBeenCalledTimes(1);
  expect(view.getByTestId('header-landscape', { includeHiddenElements: true }).props.pointerEvents).toBe('none');
});
test('owned safe areas are removed once; independent detail retains modal bottom area', async () => {
  const view = await render(<SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 393, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <ShellInsets top><ShellInsets bottom><ShellSafeArea testID="root" /><ShellSafeArea testID="detail" independent /></ShellInsets></ShellInsets>
    <NavigationFooter bottomInset={24}><Native.Text>Footer</Native.Text></NavigationFooter>
  </SafeAreaProvider>);
  expect(view.getByTestId('root').props.edges).toEqual({ top: 'off', bottom: 'off', left: 'off', right: 'off' });
  expect(view.getByTestId('detail').props.edges.bottom).toBe('additive');
});
test('reminder grows in normal flow, preserves disabled navigation and has no blur', async () => {
  const onPress = jest.fn();
  const view = await render(<PendingRpeBanner label="1 workout waiting for RPE" disabled onPress={onPress} />);
  const target = view.getByRole('button');
  expect(Native.StyleSheet.flatten(target.props.style).minHeight).toBe(layout.touch);
  await fireEvent.press(target); expect(onPress).not.toHaveBeenCalled();
});
