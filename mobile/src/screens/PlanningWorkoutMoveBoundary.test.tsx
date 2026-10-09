import { act, fireEvent, render, within } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider, useUiVersion } from '../ui/UiVersionProvider';
import { activePlan, onboarding, pendingPlan, proposal, workout, warning } from '../features/planning/planning.test-fixtures';
import { usePlanningFlow, usePlanningCalendar } from '../features/planning/PlanningFlowProvider';
import { PlanningFlowProvider } from '../features/planning/PlanningFlowProvider';
import { PlanningPresentationProvider } from '../navigation/PlanningPresentationProvider';
import { PlanningBoundary } from './PlanningScreen';

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


let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let ui: ReturnType<typeof useUiVersion>;
function Probe() { flow = usePlanningFlow(); calendar = usePlanningCalendar(); ui = useUiVersion(); return null; }
function presentation(destination: 'calendar' | 'week' = 'calendar') {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><PlanningFlowProvider accessToken="token-a" athleteIdentity="athlete-a"><PlanningPresentationProvider><Probe /><PlanningBoundary destination={destination}
      onSignOut={jest.fn(async () => undefined)} onBackToOnboarding={jest.fn()} onOpenActivities={jest.fn()}
      onOpenCheckIn={jest.fn()} onOpenIntegrations={jest.fn()} onOpenProfile={jest.fn()} onOpenZoneProfile={jest.fn()} /></PlanningPresentationProvider></PlanningFlowProvider>
    </UiVersionProvider></LanguageProvider>
  </SafeAreaProvider>;
}

beforeEach(() => {
  // The fixture Wednesday must not become "Today" when the real date changes.
  // Freeze Date while retaining real timers for asynchronous rendering.
  jest.useFakeTimers({
    now: new Date('2026-10-06T12:00:00Z'),
    doNotFake: ['hrtime', 'nextTick', 'performance', 'queueMicrotask',
      'requestAnimationFrame', 'cancelAnimationFrame', 'requestIdleCallback',
      'cancelIdleCallback', 'setImmediate', 'clearImmediate', 'setInterval',
      'clearInterval', 'setTimeout', 'clearTimeout'],
  });
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : null);
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] });
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, alternatives: [], can_remove: false });
});
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; jest.restoreAllMocks(); jest.useRealTimers(); });
function restore(kind: 'plan') {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) =>
    key === 'start23.language-preference' ? 'en' :
      key === (kind === 'plan' ? 'start23.latest-plan-id' : 'start23.latest-swipe-draft-id') ? activePlan.id : null);
}


async function enterCalendar(value = activePlan, rows = value.workouts) {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(value);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: value.week_start, to_date: '2026-10-12', workouts: rows, rest_days: value.rest_days });
  const view = await render(presentation('week')); await view.findByTestId('week-header-title'); await view.rerender(presentation()); await view.findByRole('button', { name: `Move ${workout.name}` }); return view;
}
async function openMove(view: Awaited<ReturnType<typeof enterCalendar>>) {
  await fireEvent.press(view.getByRole('button', { name: `Move ${workout.name}` }));
  await view.findByRole('header', { name: 'Move workout' });
}
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(yes => { resolve = yes; }); return { promise, resolve }; }
async function choose(view: Awaited<ReturnType<typeof enterCalendar>>) {
  await fireEvent.press(view.getByRole('radio', { name: 'Saturday, 10 October 2026' }));
}

test('Calendar move entry names full active occurrence; chooser has seven full dates, current/checked date and explicit no-op guard', async () => {
  const view = await enterCalendar(); await openMove(view);
  expect(view.getByText(`Current date: Wednesday, 7 October 2026`)).toBeTruthy();
  expect(view.getAllByRole('radio')).toHaveLength(7);
  expect(view.getByRole('radio', { name: /^Wednesday, 7 October 2026/ })).toBeChecked();
  expect(view.getByRole('button', { name: 'Review move' })).toBeDisabled();
  await choose(view); expect(view.getByRole('radio', { name: 'Saturday, 10 October 2026' })).toBeChecked();
  expect(view.getByText('New date: Saturday, 10 October 2026')).toBeTruthy();
  expect(api.validatePlanLayout).not.toHaveBeenCalled(); expect(api.movePlannedWorkout).not.toHaveBeenCalled();
  const serialized = JSON.stringify(view.toJSON()); expect(serialized).not.toMatch(/private_planned_load|private_realized_load|selector_diagnostics|\btss\b/i);
});

test('chooser Cancel returns same Calendar and does not validate, mutate, change range or occurrence', async () => {
  const view = await enterCalendar(); const range = calendar.calendarRange; await openMove(view); await choose(view);
  await fireEvent.press(view.getAllByRole('button', { name: 'Cancel' })[0]);
  expect(view.queryByRole('header', { name: 'Move workout' })).toBeNull(); expect(flow.plan).toBe(activePlan);
  expect(calendar.calendarRange).toBe(range); expect(api.validatePlanLayout).not.toHaveBeenCalled(); expect(api.movePlannedWorkout).not.toHaveBeenCalled();
});

test.each(['cancel', 'back'] as const)('warning %s clears reviewed intent without PATCH, preserves origin and reenables comparison', async dismissal => {
  const view = await enterCalendar(); await openMove(view); await choose(view);
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: false, warnings: [warning, { ...warning, code: 'exact-public-copy', message: 'Supplied second warning' }] });
  await fireEvent.press(view.getByRole('button', { name: 'Review move' }));
  await view.findByRole('header', { name: 'Review this move' });
  expect(view.getByText('Supplied second warning')).toBeTruthy(); expect(view.getByText('Weekcombinatie vraagt aandacht')).toBeTruthy();
  expect(within(view.getByTestId('workout-move-modal')).getByRole('button', { name: 'UI V1' })).toBeDisabled(); expect(api.movePlannedWorkout).not.toHaveBeenCalled();
  if (dismissal === 'cancel') await fireEvent.press(view.getAllByRole('button', { name: 'Cancel' })[1]);
  else await fireEvent(view.getByTestId('workout-move-modal'), 'requestClose');
  expect(flow.pendingMove).toBeNull(); expect(flow.plan).toBe(activePlan); expect(api.movePlannedWorkout).not.toHaveBeenCalled();
  expect(view.getByRole('button', { name: 'UI V1' })).toBeEnabled();
});

test.each([false, true])('authoritative %s warning path moves exact occurrence once, updates Calendar/Week/detail without duplicate reads', async warned => {
  const sibling = { ...workout, id: 'repeat-template-sibling', name: 'Same template other occurrence' };
  const previous = { ...activePlan, workouts: [workout, sibling] }; const view = await enterCalendar(previous);
  await openMove(view); await choose(view);
  const validation = deferred<{ valid_for_generated_schedule: boolean; warnings: typeof warning[] }>();
  jest.mocked(api.validatePlanLayout).mockReturnValue(validation.promise);
  const control = view.getByRole('button', { name: 'Review move' });
  await act(async () => { await fireEvent.press(control); await fireEvent.press(control); });
  expect(view.getByRole('button', { name: 'Review move' })).toBeDisabled();
  expect(api.validatePlanLayout).toHaveBeenCalledTimes(1);
  const patch = deferred<typeof previous>(); jest.mocked(api.movePlannedWorkout).mockReturnValue(patch.promise);
  await act(() => validation.resolve({ valid_for_generated_schedule: !warned, warnings: warned ? [warning] : [] }));
  if (warned) {
    expect(api.movePlannedWorkout).not.toHaveBeenCalled();
    await view.rerender(presentation()); await act(() => ui.setRequested('v1'));
    await view.findByRole('header', { name: 'Review this move' });
    const confirm = view.getByRole('button', { name: 'Move anyway' });
    await act(async () => { await fireEvent.press(confirm); await fireEvent.press(confirm); });
  }
  expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
  expect(api.movePlannedWorkout).toHaveBeenCalledWith('token-a', workout.id, 2, '2026-10-10');
  const updated = { ...previous, revision: 6, active_revision: 6, workouts: [{ ...workout, scheduled_date: '2026-10-10' }, sibling], rest_days: [{ date: '2026-10-10', reason: 'planned_rest' as const }] };
  await act(() => patch.resolve(updated)); await view.findByTestId('calendar-workout-workout-a');
  expect(flow.plan).toBe(updated); expect(flow.activePlan).toBe(updated); expect(flow.pendingMove).toBeNull();
  expect(calendar.calendarWorkouts).toEqual(updated.workouts); expect(calendar.calendarRestDays).toEqual(updated.rest_days);
  expect(api.getCalendar).toHaveBeenCalledTimes(1); expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
  await act(() => ui.setRequested('v2'));
  await fireEvent.press(view.getByRole('button', { name: new RegExp(`^View workout.*${workout.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }));
  await view.findByRole('header', { name: 'Workout' });
  await fireEvent.press(view.getByRole('button', { name: 'Close' }));
  expect(flow.plan).toBe(updated); expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await view.rerender(presentation('week')); await view.findByTestId('week-header-title');
  expect(view.getByText('Wednesday 7 October')).toBeTruthy(); expect(flow.activePlan?.workouts[0].scheduled_date).toBe('2026-10-10'); expect(flow.activePlan?.workouts[1]).toBe(sibling);
  expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
});

test.each(['Safe stale PATCH', 'Safe rejected move', 'Safe network failure'])('failed warned move %s retains exact review and unchanged authoritative plan', async message => {
  const view = await enterCalendar(); await openMove(view); await choose(view);
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: false, warnings: [warning] });
  await fireEvent.press(view.getByRole('button', { name: 'Review move' }));
  jest.mocked(api.movePlannedWorkout).mockRejectedValue(new Error(message));
  await fireEvent.press(view.getByRole('button', { name: 'Move anyway' })); await within(view.getByTestId('workout-move-modal')).findByText(message);
  expect(flow.plan).toBe(activePlan); expect(calendar.calendarWorkouts).toEqual([workout]);
  expect(flow.pendingMove?.scheduledDate).toBe('2026-10-10'); expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
  await view.rerender(presentation()); expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
});

test('nonactive, cancelled, completed, historical and stale Calendar rows have no move entry', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(pendingPlan);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: activePlan.week_start, to_date: '2026-10-12', workouts: [workout], rest_days: [] });
  const view = await render(presentation()); await view.findByTestId('calendar-workout-workout-a');
  expect(view.queryByRole('button', { name: `Move ${workout.name}` })).toBeNull(); await view.unmount();
  const rows = [{ ...workout, status: 'cancelled' as const }, { ...workout, id: 'completed', status: 'completed' as const }, { ...workout, id: 'historical' }];
  jest.mocked(api.getWeeklyPlan).mockResolvedValue({ ...activePlan, workouts: rows.slice(0, 2) });
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: activePlan.week_start, to_date: '2026-10-12', workouts: rows, rest_days: [] });
  const other = await render(presentation()); await other.findByTestId('calendar-workout-historical');
  expect(other.queryAllByRole('button', { name: /^Move / })).toHaveLength(0);
});
