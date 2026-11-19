import { fireEvent, render } from '@testing-library/react-native';
import * as Haptics from 'expo-haptics';
import { Dimensions, Text } from 'react-native';
import { State, type PanGesture } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { PlacementRail } from './PlacementRail';

jest.mock('./presentation', () => ({ studioPresentation: true }));
jest.mock('expo-haptics', () => ({ selectionAsync: jest.fn(async () => {}) }));

const originalWindow = Dimensions.get('window');
beforeEach(() => Dimensions.set({ window: { width: 412, height: 892, fontScale: 1, scale: 1 } }));
afterEach(() => Dimensions.set({ window: originalWindow }));

test('only a valid release requests placement and only its acknowledged date gives feedback', async () => {
  const dates = ['2026-10-05', '2026-10-07'];
  const select = jest.fn();
  const rail = (selected?: string) => <LanguageProvider>
    <PlacementRail dates={dates} selected={selected} disabled={false} label="Workout" onSelect={select}>
      <Text>Dates</Text>
    </PlacementRail>
  </LanguageProvider>;
  const screen = await render(rail(dates[0]));
  await fireEvent(screen.getByTestId('placement-rail'), 'layout', { nativeEvent: { layout: { width: 200 } } });
  await screen.findByTestId('placement-touch-grip');
  const release = (x: number, state: State) => fireGestureHandler<PanGesture>(getByGestureTestId('placement-grip'), [
    { state: State.BEGAN }, { state: State.ACTIVE, x, y: 80, translationX: 0 }, { state, x, y: 80 },
  ]);
  release(160, State.CANCELLED);
  release(240, State.END);
  release(40, State.END);
  expect(select).not.toHaveBeenCalled();
  release(160, State.END);
  expect(select.mock.calls).toEqual([[dates[1]]]);
  expect(Haptics.selectionAsync).not.toHaveBeenCalled();
  await screen.rerender(rail(dates[1]));
  expect(Haptics.selectionAsync).toHaveBeenCalledTimes(1);
});
