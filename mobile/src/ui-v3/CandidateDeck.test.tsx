import { act, fireEvent, render, within } from '@testing-library/react-native';
import type { ReactNode } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { State, type PanGesture } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import { draft, occurrence } from '../features/planning/planning.test-fixtures';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { SelectionScreen } from '../ui-v2/screens/PlanningCreationScreens';
import { planningCreationViewModel } from '../ui-v2/utils/planningCreationViewModel';

jest.mock('./presentation', () => ({ studioPresentation: true }));
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en') }));

const task = { busy: false, error: null, onBack: jest.fn(), controls: null };
function host(children: ReactNode) {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider>{children}</LanguageProvider></SafeAreaProvider>;
}
async function screen(props: { busy?: boolean; onTransition?: jest.Mock } = {}) {
  const onTransition = props.onTransition ?? jest.fn(async () => undefined);
  const view = await render(host(<SelectionScreen {...task} busy={props.busy ?? false}
    model={planningCreationViewModel(draft)} onTransition={onTransition} onContinue={jest.fn()} />));
  await view.findByText('Choose your workouts');
  return { view, onTransition };
}
function swipe(translationX: number, velocityX = 0) {
  fireGestureHandler<PanGesture>(getByGestureTestId('candidate-deck-swipe'), [
    { state: State.BEGAN }, { state: State.ACTIVE, translationX: translationX / 2 },
    { state: State.END, translationX, translationY: 4, velocityX },
  ]);
}
beforeEach(() => jest.clearAllMocks());

test('the whole candidate card is the swipe surface, with its facts on the card', async () => {
  const { view } = await screen();
  const candidate = within(view.getByTestId('selection-candidate'));
  const surface = within(candidate.getByTestId('workout-swipe-surface'));
  expect(surface.getByRole('header', { name: occurrence.name })).toBeTruthy();
  expect(surface.getByTestId(`selection-occurrence-${occurrence.occurrence_id}`)).toBeTruthy();
});

test.each([
  [120, 0, 'accept'],
  [-120, 0, 'pass'],
  [40, 900, 'accept'],
  [-40, -900, 'pass'],
] as const)('a deliberate swipe of %s px at %s px/s decides %s once', async (x, velocity, expected) => {
  const { onTransition } = await screen();
  await act(async () => { swipe(x, velocity); });
  expect(onTransition).toHaveBeenCalledTimes(1);
  expect(onTransition).toHaveBeenCalledWith(expected);
});

test.each([[50, 0], [40, -900]] as const)('a short or contradicting swipe of %s px at %s px/s decides nothing', async (x, velocity) => {
  const { onTransition } = await screen();
  await act(async () => { swipe(x, velocity); });
  expect(onTransition).not.toHaveBeenCalled();
});

test('buttons follow the card: choose and pass reach the same transition', async () => {
  const { view, onTransition } = await screen();
  await act(async () => { await fireEvent.press(view.getByRole('button', { name: `Choose · ${occurrence.name}` })); });
  expect(onTransition).toHaveBeenLastCalledWith('accept');
  await act(async () => { await fireEvent.press(view.getByRole('button', { name: `Pass · ${occurrence.name}` })); });
  expect(onTransition).toHaveBeenLastCalledWith('pass');
});

test('a busy screen ignores swipes and disables both decisions', async () => {
  const { view, onTransition } = await screen({ busy: true });
  await act(async () => { swipe(140); });
  expect(onTransition).not.toHaveBeenCalled();
  expect(view.getByRole('button', { name: `Choose · ${occurrence.name}` })).toBeDisabled();
  expect(view.getByRole('button', { name: `Pass · ${occurrence.name}` })).toBeDisabled();
});
