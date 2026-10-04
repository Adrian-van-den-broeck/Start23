import { act, within, fireEvent, render, waitFor } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { activePlan, draft, occurrence, onboarding, pendingPlan, proposal, workout } from '../features/planning/planning.test-fixtures';
import * as detailBoundary from '../ui/WorkoutDetailBoundary';
import { PlanningScreen } from './PlanningScreen';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../api/client', () => ({
  approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(),
  getCalendar: jest.fn(), getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(),
  getSwipeWeekDraft: jest.fn(), getWeeklyPlan: jest.fn(), markGoalAchieved: jest.fn(),
  movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(), rejectPlanProposal: jest.fn(),
  submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
}));
jest.mock('@gorhom/bottom-sheet', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const RN = jest.requireActual<typeof import('react-native')>('react-native');
  return {
    BottomSheetBackdrop: () => null,
    BottomSheetView: ({ children }: PropsWithChildren) => <RN.View>{children}</RN.View>,
    BottomSheetModal: React.forwardRef((_props: PropsWithChildren, ref) => {
      React.useImperativeHandle(ref, () => ({ present: jest.fn(), dismiss: jest.fn() }));
      return null;
    }),
  };
});
jest.mock('react-native-reanimated-carousel', () => ({ Carousel: () => null }));


function presentation() {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><PlanningScreen accessToken="token-a" athleteIdentity="athlete-a"
      onSignOut={jest.fn(async () => undefined)} onBackToOnboarding={jest.fn()} onOpenActivities={jest.fn()}
      onOpenCheckIn={jest.fn()} onOpenIntegrations={jest.fn()} onOpenProfile={jest.fn()} onOpenZoneProfile={jest.fn()} />
    </UiVersionProvider></LanguageProvider>
  </SafeAreaProvider>;
}

beforeEach(() => {
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : null);
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] });
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, alternatives: [], can_remove: false });
});
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; jest.restoreAllMocks(); });
function restore(kind: 'plan' | 'draft') {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) =>
    key === 'start23.language-preference' ? 'en' :
    key === (kind === 'plan' ? 'start23.latest-plan-id' : 'start23.latest-swipe-draft-id') ? (kind === 'plan' ? activePlan.id : draft.id) : null);
}
test('V2 no plan opens V1 preparation without a draft/create/read, and returns to Week', async () => {
  const view = await render(presentation());
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('Wanneer kun je trainen?');
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.getWeeklyPlan).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Prepare your training week');
  expect(api.getOnboarding).toHaveBeenCalledTimes(1);
});
test('root V1/V2 changes keep one bootstrap and never mount both roots or mutate', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  const view = await render(presentation());
  await view.findByText('Approved');
  expect(view.queryByRole('tab', { name: 'Calendar' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await view.findByText('Week van 2026-10-05');
  expect(view.queryByTestId('week-home-scroll')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  await view.findByText('Approved');
  await view.rerender(presentation());
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
  expect(api.getOnboarding).toHaveBeenCalledTimes(1);
  expect(api.getCalendar).not.toHaveBeenCalled();
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.submitSwipeWeekDraft).not.toHaveBeenCalled();
});
test('resumed draft entry uses its exact candidate and revision, with no second restore/create/transition', async () => {
  restore('draft'); jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(draft);
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValue({ ...draft, revision: 5, can_undo: true });
  const view = await render(presentation());
  await view.findAllByText('Workout selection in progress');
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await view.findByText('Stel je week samen');
  await fireEvent.press(view.getByRole('button', { name: 'Overslaan' }));
  await waitFor(() => expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1));
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, { expected_revision: draft.revision, action: 'pass', candidate_template_id: occurrence.id, candidate_occurrence_id: occurrence.occurrence_id });
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  expect(api.getSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
});
test('active plus pending reads each snapshot once and review approves exact proposal; switch is locked until settled', async () => {
  restore('plan');
  let finish!: () => void;
  jest.mocked(api.approvePlanProposal).mockImplementation(async () => {
    await new Promise<void>((yes) => { finish = yes; });
    return { state: 'applied', plan_id: activePlan.id, active_revision: 3 };
  });
  const view = await render(presentation());
  await view.findByText('Approved · new proposal awaiting review');
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(2);
  expect(api.getPendingWorkoutAlternatives).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(2);
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  await view.findByText('Week van 2026-10-05');
  await waitFor(() => expect(view.getByRole('button', { name: 'Back to Week' })).toBeEnabled());
  await fireEvent.press(view.getByRole('button', { name: 'Week goedkeuren' }));
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Week goedkeuren' }));
  await view.rerender(presentation());
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  expect(api.approvePlanProposal).toHaveBeenCalledWith('token-a', proposal.id, 2);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue({ ...activePlan, revision: 3, active_revision: 3 });
  await act(async () => finish());
  await waitFor(() => expect(view.getByRole('button', { name: 'Back to Week' })).toBeEnabled());
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Approved');
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(3);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
});
test('V1 Calendar entry has one range effect and detail comparison retains V2 Week origin and scroll', async () => {
  restore('plan');
  const today = new Date().toLocaleDateString('en-CA', { timeZone: activePlan.timezone });
  const real = { ...workout, scheduled_date: today };
  jest.mocked(api.getWeeklyPlan).mockResolvedValue({ ...activePlan, workouts: [real] });
  const spy = jest.spyOn(detailBoundary, 'WorkoutDetailBoundary');
  const view = await render(presentation());
  await view.findByText('Approved');
  await fireEvent.scroll(view.getByTestId('week-home-scroll'), { nativeEvent: { contentOffset: { y: 123, x: 0 } } });
  await fireEvent.press(view.getByRole('button', { name: 'View workout · ' + real.name }));
  expect(spy.mock.calls.at(-1)?.[0].workout).toBe(real);
  const modal = view.getByTestId('workout-detail-modal');
  await fireEvent.press(within(modal).getByRole('button', { name: 'UI V1' }));
  await fireEvent.press(within(modal).getByRole('button', { name: 'UI V2' }));
  await fireEvent.press(within(modal).getByRole('button', { name: 'Close' }));
  expect(view.getByTestId('week-home-scroll').props.contentOffset.y).toBe(123);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  await view.findByText('Training calendar');
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(1));
  await view.rerender(presentation());
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(view.getByTestId('week-home-scroll').props.contentOffset.y).toBe(123);
});
