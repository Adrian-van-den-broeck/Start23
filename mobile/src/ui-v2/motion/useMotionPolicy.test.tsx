import { act, render } from '@testing-library/react-native';
import { AccessibilityInfo, Text } from 'react-native';
import * as Reanimated from 'react-native-reanimated';
import { ContentTransition } from './ContentTransition';
import { useMotionPolicy } from './useMotionPolicy';

function Probe() {
  const { reducedMotion } = useMotionPolicy();
  return <Text>{String(reducedMotion)}</Text>;
}

test('system preference updates live, cleans up, and late startup response cannot overwrite an event', async () => {
  let finish!: (value: boolean) => void;
  let listener!: (value: boolean) => void;
  const remove = jest.fn();
  const read = jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockReturnValue(new Promise((done) => { finish = done; }));
  const subscribe = jest.spyOn(AccessibilityInfo, 'addEventListener').mockImplementation((_event, handler) => {
    listener = handler as unknown as (value: boolean) => void; return { remove } as unknown as ReturnType<typeof AccessibilityInfo.addEventListener>;
  });
  const view = await render(<Probe />);
  await act(async () => { listener(false); finish(true); });
  expect(view.getByText('false')).toBeTruthy();
  await act(async () => { listener(true); });
  expect(view.getByText('true')).toBeTruthy();
  await view.unmount();
  expect(remove).toHaveBeenCalled();
  read.mockRestore(); subscribe.mockRestore();
});


test('content uses only the approved 140ms ease-out fade and cancels for reduced motion', async () => {
  const reduced = jest.spyOn(Reanimated, 'useReducedMotion').mockReturnValue(false);
  const read = jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
  const subscribe = jest.spyOn(AccessibilityInfo, 'addEventListener').mockReturnValue({ remove: jest.fn() } as unknown as ReturnType<typeof AccessibilityInfo.addEventListener>);
  const timing = jest.spyOn(Reanimated, 'withTiming');
  const cancellation = jest.spyOn(Reanimated, 'cancelAnimation');
  timing.mockClear(); cancellation.mockClear();
  const view = await render(<ContentTransition><Text>Source content</Text></ContentTransition>);
  expect(timing).toHaveBeenCalledWith(1, { duration: 140, easing: expect.any(Function) });
  await view.unmount();
  expect(cancellation).toHaveBeenCalled();
  timing.mockClear(); reduced.mockReturnValue(true); read.mockResolvedValue(true);
  const reducedView = await render(<ContentTransition><Text>Reduced content</Text></ContentTransition>);
  expect(timing).not.toHaveBeenCalled();
  await reducedView.unmount();
  reduced.mockRestore(); read.mockRestore(); timing.mockRestore(); cancellation.mockRestore(); subscribe.mockRestore();
});
