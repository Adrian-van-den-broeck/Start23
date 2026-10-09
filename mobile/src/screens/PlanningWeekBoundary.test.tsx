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
    BottomSheetScrollView: ({ children }: PropsWithChildren) => <RN.ScrollView>{children}</RN.ScrollView>,
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
test('V2 no plan opens provisional availability without a draft/create/read, and returns to Week', async () => {
  const view = await render(presentation());
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
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
  await view.findByText('Choose your workouts');
  await fireEvent.press(view.getByRole('button', { name: `Pass · ${occurrence.name}` }));
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
  await view.findByText('Review your week proposal');
  await waitFor(() => expect(view.getByRole('button', { name: 'Back to Week' })).toBeEnabled());
  await fireEvent.press(view.getByRole('button', { name: 'Approve week' }));
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Approve week' }));
  await view.rerender(presentation());
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  expect(api.approvePlanProposal).toHaveBeenCalledWith('token-a', proposal.id, 2);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue({ ...activePlan, revision: 3, active_revision: 3 });
  await act(async () => finish());
  await view.findByText('Approved');
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(3);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
});
test('Calendar entry has one range effect and detail comparison retains V2 Week origin and scroll', async () => {
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

test('goal entry preserves the existing V1 explicit achievement confirmation surface without writing', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.getOnboarding).mockResolvedValue({
    ...onboarding, primary_goal: {
      id: 'goal-a', race_type: 'run', race_name: 'Known race', race_date: '2027-04-11',
      swim_distance_meters: null, bike_distance_meters: null, run_distance_meters: 10000,
      total_target_time_seconds: 3600, swim_target_time_seconds: null, bike_target_time_seconds: null,
      run_target_time_seconds: null, specific_focus: null, priority: 'A', goal_type: 'race',
      status: 'active', revision: 1, created_at: '2026-10-05T00:00:00Z', updated_at: '2026-10-05T00:00:00Z',
    }
  });
  const view = await render(presentation());
  await fireEvent.press(await view.findByRole('button', { name: 'Goal · Known race' }));
  await view.findByRole('button', { name: 'Markeer “Known race” als behaald' });
  expect(api.markGoalAchieved).not.toHaveBeenCalled();
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});

test.each(['week', 'month'] as const)('Calendar %s detail and V1/V2 return retain range/date/scroll/origin with no reads or mutations', async (mode) => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  const loaded = { ...workout, id: 'calendar-occurrence', name: 'Exact loaded Calendar occurrence' };
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from_date, to_date) => ({ from_date, to_date, workouts: [loaded], rest_days: [] }));
  const detail = jest.spyOn(detailBoundary, 'WorkoutDetailBoundary');
  const view = await render(presentation()); await view.findByText('Approved');
  await fireEvent.scroll(view.getByTestId('week-home-scroll'), { nativeEvent: { contentOffset: { x: 0, y: 88 } } });
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  await view.findByText(loaded.name);
  if (mode === 'month') {
    await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
    await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(2));
    await fireEvent.press(view.getByTestId('calendar-date-2026-10-07'));
  }
  const calls = mode === 'month' ? 2 : 1;
  await view.findByRole('button', { name: 'View workout · ' + loaded.name });
  await fireEvent.scroll(view.getByTestId('calendar-scroll'), { nativeEvent: { contentOffset: { x: 0, y: 133 } } });
  await fireEvent.press(view.getByRole('button', { name: 'View workout · ' + loaded.name }));
  expect(detail.mock.calls.at(-1)?.[0].workout).toBe(loaded);
  const modal = view.getByTestId('workout-detail-modal');
  await fireEvent.press(within(modal).getByRole('button', { name: 'UI V1' }));
  await fireEvent.press(within(modal).getByRole('button', { name: 'UI V2' }));
  await fireEvent(modal, 'requestClose');
  expect(view.getByTestId('calendar-scroll').props.contentOffset.y).toBe(133);
  expect(view.getByRole('tab', { name: mode === 'month' ? 'Month' : 'Week' }).props.accessibilityState.selected).toBe(true);
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await view.findByText('Training calendar'); expect(view.queryByTestId('calendar-scroll')).toBeNull();
  if (mode === 'month') expect(view.getByLabelText('View 7 October 2026').props.accessibilityState.selected).toBe(true);
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  expect(view.getByTestId('calendar-scroll').props.contentOffset.y).toBe(133);
  if (mode === 'month') expect(view.getByTestId('calendar-date-2026-10-07').props.accessibilityState.selected).toBe(true);
  await view.rerender(presentation()); expect(api.getCalendar).toHaveBeenCalledTimes(calls);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1); expect(api.getOnboarding).toHaveBeenCalledTimes(1);
  expect(api.movePlannedWorkout).not.toHaveBeenCalled(); expect(api.validatePlanLayout).not.toHaveBeenCalled(); expect(api.approvePlanProposal).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(view.getByTestId('week-home-scroll').props.contentOffset.y).toBe(88);
});

test('rapid Calendar Week/Month requests use one reader; stale month completion cannot replace the latest week', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  let finishMonth!: (value: Awaited<ReturnType<typeof api.getCalendar>>) => void;
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from_date, to_date) => from_date === '2026-09-28'
    ? new Promise((yes) => { finishMonth = yes; }) : { from_date, to_date, workouts: [workout], rest_days: [] });
  const view = await render(presentation()); await view.findByText('Approved');
  await fireEvent.press(view.getByRole('button', { name: 'View week' })); await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Week' })); await view.findByText(workout.name);
  await act(() => finishMonth({ from_date: '2026-09-28', to_date: '2026-11-02', workouts: [{ ...workout, name: 'Stale Month row' }], rest_days: [] }));
  expect(view.queryByText('Stale Month row')).toBeNull(); expect(view.getByTestId('calendar-week-agenda')).toBeTruthy();
  expect(view.queryByTestId('calendar-month-grid')).toBeNull(); expect(view.queryByTestId('calendar-month-day-list')).toBeNull();
  expect(jest.mocked(api.getCalendar).mock.calls).toEqual([
    ['token-a', '2026-10-05', '2026-10-12'], ['token-a', '2026-09-28', '2026-11-02'], ['token-a', '2026-10-05', '2026-10-12'],
  ]);
});

test('Month selection opens its exact Week; previous/next/Today retain date-only ranges', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from_date, to_date) => ({ from_date, to_date, workouts: [], rest_days: [] }));
  const view = await render(presentation()); await view.findByText('Approved');
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await fireEvent.press(view.getByRole('button', { name: 'Next month' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenLastCalledWith('token-a', '2026-10-26', '2026-12-07'));
  await fireEvent.press(view.getByRole('button', { name: 'Previous month' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenLastCalledWith('token-a', '2026-09-28', '2026-11-02'));
  await fireEvent.press(view.getByTestId('calendar-date-2026-11-01'));
  await fireEvent.press(view.getByRole('button', { name: 'View this date’s week' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenLastCalledWith('token-a', '2026-10-26', '2026-11-02'));
  await fireEvent.press(view.getByRole('button', { name: 'Today' }));
  const now = new Date(); const day = now.getDay() || 7; now.setDate(now.getDate() - day + 1);
  const start = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-');
  expect(jest.mocked(api.getCalendar).mock.calls.at(-1)?.[1]).toBe(start);
});


test('Calendar entered from V1 retains the V1 origin across safe Calendar V2 comparison, without another read', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  const view = await render(presentation());
  await view.findByText('Week van 2026-10-05');
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(1));
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  await view.findByTestId('calendar-scroll');
  expect(view.queryByTestId('week-home-scroll')).toBeNull();
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Week van 2026-10-05');
  expect(view.queryByTestId('calendar-scroll')).toBeNull();
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});
