import { act, render } from '@testing-library/react-native';
import { getGoalPlanningOptions, getOnboarding, getPhysiologyProfile } from '../api/client';
import type { OnboardingState } from '../api/types';
import { OnboardingScreen } from './OnboardingScreen';

jest.mock('../api/client', () => ({ getGoalPlanningOptions: jest.fn(), getOnboarding: jest.fn(), getPhysiologyProfile: jest.fn() }));
const completed = { current_step: 'completed' } as OnboardingState;
function pending<T>() { let resolve!: (value: T) => void; let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
beforeEach(() => jest.resetAllMocks());

test('completed intake opens training before unrelated form reads finish or fail', async () => {
  const goals = pending<[]>(), physiology = pending<null>();
  jest.mocked(getOnboarding).mockResolvedValue(completed);
  jest.mocked(getGoalPlanningOptions).mockReturnValue(goals.promise);
  jest.mocked(getPhysiologyProfile).mockReturnValue(physiology.promise);
  const onOpenPlanning = jest.fn();
  const view = await render(<OnboardingScreen accessToken="a" onOpenPlanning={onOpenPlanning} onOpenCalibration={jest.fn()} onSignOut={jest.fn()} />);
  expect(onOpenPlanning).toHaveBeenCalledTimes(1);
  await view.unmount();
  await act(async () => { goals.reject(new Error('Synthetic unavailable auxiliary read')); physiology.resolve(null); });
  expect(onOpenPlanning).toHaveBeenCalledTimes(1);
});

test('callback identity changes do not restart intake; pending read uses current navigation', async () => {
  const read = pending<OnboardingState>();
  jest.mocked(getOnboarding).mockReturnValue(read.promise);
  jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
  jest.mocked(getPhysiologyProfile).mockResolvedValue(null);
  const old = jest.fn(), current = jest.fn();
  const props = { accessToken: 'a', onOpenCalibration: jest.fn(), onSignOut: jest.fn() };
  const view = await render(<OnboardingScreen {...props} onOpenPlanning={old} />);
  await view.rerender(<OnboardingScreen {...props} onOpenPlanning={current} />);
  expect(getOnboarding).toHaveBeenCalledTimes(1);
  await act(async () => { read.resolve(completed); });
  expect(old).not.toHaveBeenCalled(); expect(current).toHaveBeenCalledTimes(1);
});

test('account change and navigation away suppress late intake navigation', async () => {
  const a = pending<OnboardingState>(), b = pending<OnboardingState>();
  jest.mocked(getOnboarding).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
  jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
  jest.mocked(getPhysiologyProfile).mockResolvedValue(null);
  const open = jest.fn(); const props = { onOpenPlanning: open, onOpenCalibration: jest.fn(), onSignOut: jest.fn() };
  const view = await render(<OnboardingScreen {...props} accessToken="a" />);
  await view.rerender(<OnboardingScreen {...props} accessToken="b" />);
  await act(async () => { a.resolve(completed); });
  expect(open).not.toHaveBeenCalled();
  await view.unmount();
  await act(async () => { b.resolve(completed); });
  expect(open).not.toHaveBeenCalled();
});
