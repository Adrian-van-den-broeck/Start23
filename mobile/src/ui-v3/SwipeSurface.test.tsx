import { render } from '@testing-library/react-native';
import { View } from 'react-native';
import { State, type PanGesture } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import { SwipeSurface } from './SwipeSurface';

jest.mock('./presentation', () => ({ studioPresentation: true }));

test.each([
  [90, 3, State.END, false, 1],
  [-90, 1, State.END, false, -1],
  [40, 2, State.END, false, null],
  [80, 120, State.END, false, null],
  [120, 0, State.CANCELLED, false, null],
  [120, 0, State.END, true, null],
] as const)('swipe %s/%s, terminal state %s and disabled=%s', async (x, y, state, disabled, expected) => {
  const select = jest.fn();
  await render(<SwipeSurface disabled={disabled} onSwipe={select}><View /></SwipeSurface>);
  fireGestureHandler<PanGesture>(getByGestureTestId('horizontal-presentation-swipe'), [
    { state: State.BEGAN }, { state: State.ACTIVE }, { state, translationX: x, translationY: y },
  ]);
  if (expected === null) expect(select).not.toHaveBeenCalled();
  else {
    expect(select).toHaveBeenCalledTimes(1);
    expect(select).toHaveBeenCalledWith(expected);
  }
});
