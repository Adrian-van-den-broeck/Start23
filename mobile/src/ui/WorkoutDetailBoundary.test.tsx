import { act, fireEvent, render } from '@testing-library/react-native';
import { Pressable, Text } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import * as legacy from '../components/WorkoutDetail';
import { LanguageProvider } from '../i18n/LanguageProvider';
import * as modern from '../ui-v2/screens/WorkoutDetailScreen';
import { sourceWorkout } from '../ui-v2/utils/workout.test-fixtures';
import { UiVersionProvider, useUiVersion } from './UiVersionProvider';
import { UiVersionControl } from './UiVersionControl';
import { WorkoutDetailBoundary } from './WorkoutDetailBoundary';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
jest.mock('../api/client', () => ({ getCalendar: jest.fn(), movePlannedWorkout: jest.fn() }));

const originalDev = __DEV__;
const originalFlag = process.env.EXPO_PUBLIC_UI_VERSION;
beforeEach(() => {
  Object.defineProperty(globalThis, '__DEV__', { value: true, configurable: true });
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en');
  jest.clearAllMocks();
});
afterEach(() => {
  Object.defineProperty(globalThis, '__DEV__', { value: originalDev, configurable: true });
  if (originalFlag === undefined) delete process.env.EXPO_PUBLIC_UI_VERSION;
  else process.env.EXPO_PUBLIC_UI_VERSION = originalFlag;
  jest.restoreAllMocks();
});

test('one stable Modal, exact same snapshot/close callback, no I/O, and scroll survive V1 → V2 → V1', async () => {
  const v1 = jest.spyOn(legacy, 'WorkoutDetail');
  const v2 = jest.spyOn(modern, 'WorkoutDetailScreen');
  const fetchSpy = jest.spyOn(globalThis, 'fetch');
  const close = jest.fn();
  const view = await render(<LanguageProvider><UiVersionProvider>
    <WorkoutDetailBoundary workout={sourceWorkout} onClose={close} />
  </UiVersionProvider></LanguageProvider>);
  expect(v1.mock.calls.at(-1)?.[0]).toEqual({ workout: sourceWorkout, onClose: close });
  expect(v1.mock.calls.at(-1)?.[0].workout).toBe(sourceWorkout);
  expect(v2).not.toHaveBeenCalled();
  const modal = view.getByTestId('workout-detail-modal');
  const control = view.getByRole('button', { name: 'UI V2' });
  await fireEvent.scroll(view.getByTestId('workout-detail-scroll'), { nativeEvent: { contentOffset: { x: 0, y: 245 } } });
  jest.clearAllMocks();
  await fireEvent.press(control);
  expect(v1).not.toHaveBeenCalled();
  expect(v2.mock.calls.at(-1)?.[0].workout).toBe(sourceWorkout);
  expect(v2.mock.calls.at(-1)?.[0].onClose).toBe(close);
  expect(view.getByTestId('workout-detail-modal')).toBe(modal);
  expect(view.getByTestId('workout-detail-scroll').props.contentOffset.y).toBe(245);
  expect(view.getAllByTestId('workout-detail-scroll')).toHaveLength(1);
  expect(view.getByRole('button', { name: 'UI V2' }).props.accessibilityState.selected).toBe(true);
  await fireEvent.press(view.getByRole('button', { name: 'Close' }));
  expect(close).toHaveBeenCalledTimes(1);
  jest.clearAllMocks();
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  expect(v2).not.toHaveBeenCalled();
  expect(v1.mock.calls.at(-1)?.[0].workout).toBe(sourceWorkout);
  expect(view.getByTestId('workout-detail-scroll').props.contentOffset.y).toBe(245);
  // V1's shorter content may clamp to zero. Returning to V2 retains its own offset.
  await fireEvent.scroll(view.getByTestId('workout-detail-scroll'), { nativeEvent: { contentOffset: { y: 0 } } });
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  expect(view.getByTestId('workout-detail-scroll').props.contentOffset.y).toBe(245);
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await fireEvent.press(view.getByRole('button', { name: 'Sluiten' }));
  await fireEvent(view.getByTestId('workout-detail-modal'), 'requestClose');
  expect(close).toHaveBeenCalledTimes(2);
  expect(fetchSpy).not.toHaveBeenCalled();
  expect(SecureStore.getItemAsync).not.toHaveBeenCalled();
  expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
});

function ProgrammaticPreference() {
  const { requested, setRequested, effectiveVersion } = useUiVersion();
  return <><Text>{`${requested}/${effectiveVersion('workoutDetail')}`}</Text>
    <Pressable accessibilityRole="button" accessibilityLabel="request V2" onPress={() => setRequested('v2')}>
      <Text>Request</Text></Pressable><UiVersionControl /></>;
}

test('non-development env and programmatic requests force V1 and hide control', async () => {
  Object.defineProperty(globalThis, '__DEV__', { value: false, configurable: true });
  process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  const view = await render(<LanguageProvider><UiVersionProvider><ProgrammaticPreference />
    <WorkoutDetailBoundary workout={sourceWorkout} onClose={jest.fn()} />
  </UiVersionProvider></LanguageProvider>);
  expect(view.getByText('v1/v1')).toBeTruthy();
  await act(async () => { await fireEvent.press(view.getByRole('button', { name: 'request V2' })); });
  expect(view.getByText('v1/v1')).toBeTruthy();
  expect(view.queryByRole('button', { name: 'UI V2' })).toBeNull();
  expect(view.queryByText('Session sequence')).toBeNull();
});

test('null and new selected snapshots reset only detail offset', async () => {
  const close = jest.fn();
  const tree = (workout: typeof sourceWorkout | null) => <LanguageProvider><UiVersionProvider>
    <WorkoutDetailBoundary workout={workout} onClose={close} />
  </UiVersionProvider></LanguageProvider>;
  const view = await render(tree(sourceWorkout));
  await fireEvent.scroll(view.getByTestId('workout-detail-scroll'), { nativeEvent: { contentOffset: { y: 245 } } });
  await view.rerender(tree(null));
  expect(view.queryByRole('button', { name: 'UI V2' })).toBeNull();
  await view.rerender(tree({ ...sourceWorkout, id: 'new-snapshot' }));
  expect(view.getByTestId('workout-detail-scroll').props.contentOffset.y).toBe(0);
});
