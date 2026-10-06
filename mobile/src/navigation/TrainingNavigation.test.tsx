import { act, fireEvent, render, waitFor, within } from '@testing-library/react-native';
import { ExpoRoot } from 'expo-router/build/ExpoRoot';
import { getMockContext } from 'expo-router/build/testing-library/mock-config';
import { Stack, router, usePathname } from 'expo-router';
import { Animated, Text, View } from 'react-native';
import type { PropsWithChildren } from 'react';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import * as detailBoundary from '../ui/WorkoutDetailBoundary';
import { useActivityFlow } from '../features/activities/ActivityFlowProvider';
import { activityOnboarding, pendingActivity } from '../features/activities/activities.test-fixtures';
import { usePlanningCalendar, usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { activePlan, draft, onboarding, pendingPlan, warning, workout } from '../features/planning/planning.test-fixtures';
import { useOptionalPlanningPresentation } from './PlanningPresentationProvider';
import AuthenticatedLayout from '../../app/(authenticated)/_layout';
import PlanningRoute from '../../app/(authenticated)/(training)/planning';
import CalendarRoute from '../../app/(authenticated)/(training)/calendar';
import ActivitiesRoute from '../../app/(authenticated)/(training)/activities';
import TrainingLayout from '../../app/(authenticated)/(training)/_layout';
import ProfileRoute from '../../app/(authenticated)/profile';
import TestsRoute from '../../app/(authenticated)/tests';
import CalibrationRoute from '../../app/(authenticated)/calibration';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../api/client', () => ({
  listActivities: jest.fn(), listPlannedExternalActivities: jest.fn(), createActivity: jest.fn(), submitActivityRpeWithRefresh: jest.fn(), confirmActivityMatch: jest.fn(), approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(),
  getCalendar: jest.fn(), getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(), getSwipeWeekDraft: jest.fn(),
  getWeeklyPlan: jest.fn(), markGoalAchieved: jest.fn(), movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(),
  rejectPlanProposal: jest.fn(), submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
}));
jest.mock('@gorhom/bottom-sheet', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const RN = jest.requireActual<typeof import('react-native')>('react-native');
  return {
    BottomSheetBackdrop: () => null,
    BottomSheetView: ({ children }: PropsWithChildren) => <RN.View>{children}</RN.View>,
    BottomSheetModal: React.forwardRef((_props: PropsWithChildren, ref) => {
      React.useImperativeHandle(ref, () => ({ present: jest.fn(), dismiss: jest.fn() })); return null;
    })
  };
});
jest.mock('react-native-reanimated-carousel', () => ({ Carousel: () => null }));
const mockAuthListeners = new Set<() => void>();
const mockSignOut = jest.fn(async () => { mockAuth.session = null; mockAuthListeners.forEach((listener) => listener()); });
const mockAuth = {
  configurationError: null, loading: false,
  session: { access_token: 'token-a', user: { id: 'athlete-a' } } as { access_token: string; user: { id: string; }; } | null,
  signOut: mockSignOut
};
jest.mock('../auth/AuthProvider', () => ({
  useAuth: () => {
    const React = jest.requireActual<typeof import('react')>('react');
    const [, update] = React.useReducer((value: number) => value + 1, 0);
    React.useEffect(() => { mockAuthListeners.add(update); return () => { mockAuthListeners.delete(update); }; }, []);
    return mockAuth;
  }
}));
jest.mock('../screens/ProfileScreen', () => {
  const { Pressable, Text } = jest.requireActual('react-native');
  return {
    ProfileScreen: ({ onBack, onSignOut, onOpenTests }: { onBack: () => void; onSignOut: () => void; onOpenTests: () => void; }) => <>
      <Text>Profile task</Text><Pressable accessibilityRole="button" onPress={onBack}><Text>Profile Back</Text></Pressable>
      <Pressable accessibilityRole="button" onPress={onSignOut}><Text>Sign out fixture</Text></Pressable>
      <Pressable accessibilityRole="button" onPress={onOpenTests}><Text>Open tests fixture</Text></Pressable>
    </>
  };
});
jest.mock('../screens/CalibrationScreen', () => {
  const { Pressable, Text } = jest.requireActual('react-native');
  return { CalibrationScreen: ({ onBack }: { onBack: () => void; }) => <Pressable accessibilityRole="button" onPress={onBack}><Text>Tests Back</Text></Pressable> };
});
jest.mock('../screens/ActivityScreen', () => {
  const { Pressable, Text } = jest.requireActual('react-native');
  return {
    ActivityScreen: ({ onBack, onOpenProfile }: { onBack: () => void; onOpenProfile?: () => void; }) => <>
      <Text>Existing V1 Activities</Text><Pressable accessibilityRole="button" onPress={onBack}><Text>Activity Back</Text></Pressable>
      {onOpenProfile ? <Pressable accessibilityRole="button" onPress={onOpenProfile}><Text>Profile</Text></Pressable> : null}
    </>
  };
});

let activityFlow: ReturnType<typeof useActivityFlow>;
let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let navigation: NonNullable<ReturnType<typeof useOptionalPlanningPresentation>>;
function Probe() {
  activityFlow = useActivityFlow();
  const value = useOptionalPlanningPresentation();
  const path = usePathname();
  return <View><Text testID="path">{path}</Text>{value ? <OwnerProbe /> : null}</View>;
}
function OwnerProbe() { flow = usePlanningFlow(); calendar = usePlanningCalendar(); navigation = useOptionalPlanningPresentation()!; return null; }
function AuthenticatedHost() { return <AuthenticatedLayout />; }
// Probe is inside the same retained host as actual routes, through Stack layout.
function Root() { return <LanguageProvider><UiVersionProvider><Stack screenOptions={{ headerShown: false }} /></UiVersionProvider></LanguageProvider>; }
function Group() { return <><Probe /><TrainingLayout /></>; }
function renderRouter(context: Parameters<typeof getMockContext>[0], { initialUrl }: { initialUrl: string; }) {
  process.env.EXPO_ROUTER_IMPORT_MODE = 'sync';
  return render(<ExpoRoot context={getMockContext(context)} location={initialUrl} />);
}
const routes = {
  _layout: Root,
  index: () => <Text>Auth destination</Text>,
  '(authenticated)/_layout': AuthenticatedHost,
  '(authenticated)/(training)/_layout': Group,
  '(authenticated)/(training)/planning': PlanningRoute,
  '(authenticated)/(training)/calendar': CalendarRoute,
  '(authenticated)/(training)/activities': ActivitiesRoute,
  '(authenticated)/profile': ProfileRoute,
  '(authenticated)/tests': TestsRoute,
  '(authenticated)/calibration': CalibrationRoute,
  '(authenticated)/onboarding': () => <Text>Existing onboarding resume</Text>,
};
beforeEach(() => {
  jest.clearAllMocks(); process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  mockAuth.session = { access_token: 'token-a', user: { id: 'athlete-a' } };
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.latest-plan-id' ? activePlan.id : null);
  jest.mocked(api.getOnboarding).mockResolvedValue({ ...onboarding, ...activityOnboarding, current_step: 'completed' });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.listActivities).mockResolvedValue([]);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [workout], rest_days: [] }));
});
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; jest.useRealTimers(); jest.restoreAllMocks(); });

test('Slice 5B real create pending reminder return and feedback retain one owner and exact identity across roots', async () => {
  let activities: typeof pendingActivity[] = [];
  jest.mocked(api.listActivities).mockImplementation(async (_token, pending) => pending ? activities.filter(activity => activity.processing_state === 'awaiting_rpe') : activities);
  jest.mocked(api.createActivity).mockImplementation(async () => { activities = [pendingActivity]; return pendingActivity; });
  jest.mocked(api.submitActivityRpeWithRefresh).mockImplementation(async (_token, activity, rpe) => {
    const updated = { ...activity, rpe, processing_state: 'complete' as const, qualitative_result: 'unplanned' as const };
    activities = [updated]; return updated;
  });
  const view = await renderRouter(routes, { initialUrl: '/planning' }); await view.findByText('Approved');
  const planningOwner = flow.setWeekStart, calendarOwner = calendar.loadCalendarRange, activityOwner = activityFlow.ensureActivitiesLoaded;
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' })); await view.findByText('No activities recorded yet.');
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' }));
  await fireEvent.changeText(view.getByLabelText('Distance (metres, optional)'), '5000');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); await view.findByText('Activity feedback');
  await fireEvent.changeText(view.getByLabelText('Average heart rate (bpm)'), '151');
  const reads = jest.mocked(api.listActivities).mock.calls.filter(call => !call[1]).length;
  for (const destination of ['Week', 'Calendar', 'Activities']) {
    await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: destination }));
    expect(activityFlow.feedbackActivity?.id).toBe(pendingActivity.id);
  }
  expect(view.getByLabelText('Average heart rate (bpm)').props.value).toBe('151');
  await fireEvent.press(view.getByRole('button', { name: 'Back to Activities' }));
  expect(view.getByRole('button', { name: 'Add activity' })).toBeDisabled();
  await fireEvent.press(view.getByRole('tab', { name: 'Week' }));
  const reminder = '1 workout waiting for RPE · open Training & RPE';
  expect(view.getAllByText(reminder)).toHaveLength(1); await fireEvent.press(view.getByText(reminder)); await view.findByText('Activity feedback');
  expect(activityFlow.feedbackActivity?.id).toBe(pendingActivity.id);
  expect(jest.mocked(api.listActivities).mock.calls.filter(call => !call[1])).toHaveLength(reads);
  await fireEvent.press(view.getByRole('radio', { name: 'Save RPE · Focus nodig, praten in zinnen. (RPE 4)' })); await view.findByTestId('v2-activities');
  expect(view.queryByText(reminder)).toBeNull(); expect(api.createActivity).toHaveBeenCalledTimes(1); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', pendingActivity, 4, 151);
  expect(activityFlow.ensureActivitiesLoaded).toBe(activityOwner); expect(flow.setWeekStart).toBe(planningOwner); expect(calendar.loadCalendarRange).toBe(calendarOwner);
});

test('Slice 5B V1 V2 navigator replacement from Activities retains task draft and pending HR without history reread', async () => {
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  const view = await renderRouter(routes, { initialUrl: '/activities' }); await view.findByTestId('activity-pending');
  const owner = activityFlow.ensureActivitiesLoaded;
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' })); await fireEvent.changeText(view.getByLabelText('Average heart rate (bpm)'), '149');
  await act(() => activityFlow.setDistance('6789'));
  const reads = jest.mocked(api.listActivities).mock.calls.filter(call => !call[1]).length;
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' })); await view.findByText('Existing V1 Activities');
  expect(view.getByTestId('path').props.children).toBe('/activities'); expect(activityFlow.ensureActivitiesLoaded).toBe(owner);
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' })); await view.findByText('Activity feedback');
  expect(view.getByLabelText('Average heart rate (bpm)').props.value).toBe('149'); expect(activityFlow.distance).toBe('6789');
  expect(jest.mocked(api.listActivities).mock.calls.filter(call => !call[1])).toHaveLength(reads);
  expect(api.createActivity).not.toHaveBeenCalled(); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
});

test('Slice 5B create in flight locks roots and version, settles without losing ambiguous attempt identity', async () => {
  let reject!: (error: Error) => void;
  jest.mocked(api.createActivity).mockImplementation(() => new Promise((_resolve, no) => { reject = no; }));
  const view = await renderRouter(routes, { initialUrl: '/activities' }); await view.findByText('No activities recorded yet.');
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' }));
  const save = view.getByRole('button', { name: 'Save activity' }); await fireEvent.press(save); await fireEvent.press(save);
  expect(view.queryByTestId('training-root-navigation')).toBeNull(); expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Activities' })).toBeDisabled(); expect(api.createActivity).toHaveBeenCalledTimes(1);
  const key = jest.mocked(api.createActivity).mock.calls[0][1];
  await act(() => reject(new Error('Safe uncertain outcome')));
  expect(view.getByTestId('training-root-navigation')).toBeTruthy();
  for (const destination of ['Week', 'Calendar', 'Activities']) await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: destination }));
  expect(view.getByRole('alert')).toHaveTextContent('Safe uncertain outcome');
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Safe explicit retry failure'));
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); expect(jest.mocked(api.createActivity).mock.calls[1][1]).toBe(key);
});

test('Slice 5B sign out then athlete B has no A history, feedback view, RPE or HR draft', async () => {
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  const view = await renderRouter(routes, { initialUrl: '/activities' }); await view.findByTestId('activity-pending');
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' })); await fireEvent.changeText(view.getByLabelText('Average heart rate (bpm)'), '199');
  await fireEvent.press(view.getByRole('button', { name: 'Back to Activities' })); await fireEvent.press(view.getByRole('button', { name: 'Profile' }));
  await fireEvent.press(view.getByRole('button', { name: 'Sign out fixture' })); await view.findByText('Auth destination');
  jest.mocked(api.listActivities).mockResolvedValue([]);
  await act(() => { mockAuth.session = { access_token: 'token-b', user: { id: 'athlete-b' } }; mockAuthListeners.forEach(listener => listener()); router.replace('/activities'); });
  await view.findByText('No activities recorded yet.'); expect(navigation.activityView).toBe('history'); expect(navigation.activityCorrectionId).toBeNull();
  expect(activityFlow.pendingRpe).toEqual([]); expect(activityFlow.heartRateByActivity).toEqual({}); expect(activityFlow.activities).toEqual([]);
  expect(view.queryByRole('radio')).toBeNull();
});

test('Slice 5B unresolved feedback save locks roots/reminder/version and never writes twice', async () => {
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  let finish!: (activity: typeof pendingActivity) => void;
  jest.mocked(api.submitActivityRpeWithRefresh).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const view = await renderRouter(routes, { initialUrl: '/activities' }); await view.findByTestId('activity-pending');
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' }));
  const choice = view.getByRole('radio', { name: 'Save RPE · Focus nodig, praten in zinnen. (RPE 4)' });
  await fireEvent.press(choice); await fireEvent.press(choice);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('training-root-navigation')).toBeNull(); expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Activities' })).toBeDisabled();
  expect(view.getByRole('button', { name: '1 workout waiting for RPE · open Training & RPE' })).toBeDisabled();
  const updated = { ...pendingActivity, rpe: 4, processing_state: 'complete' as const };
  jest.mocked(api.listActivities).mockImplementation(async (_token, pending) => pending ? [] : [updated]);
  await act(() => finish(updated)); await view.findByTestId('v2-activities');
  expect(view.getByTestId('training-root-navigation')).toBeTruthy(); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
});

test('Slice 5A one Activity owner survives Week Activities Calendar Activities and presentation preference changes', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = activityFlow.ensureActivitiesLoaded;
  await act(() => activityFlow.ensureActivitiesLoaded());
  await act(() => { activityFlow.setDuration('52'); activityFlow.setHeartRateByActivity({ 'activity-a': '148' }); });
  for (const destination of ['Activities', 'Calendar', 'Activities', 'Week']) {
    await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: destination }));
    expect(activityFlow.ensureActivitiesLoaded).toBe(owner); expect(activityFlow.duration).toBe('52');
  }
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  expect(activityFlow.ensureActivitiesLoaded).toBe(owner); expect(activityFlow.duration).toBe('52');
  expect(activityFlow.heartRateByActivity).toEqual({ 'activity-a': '148' });
  expect(jest.mocked(api.listActivities).mock.calls.filter(call => !call[1])).toHaveLength(1);
  expect(api.createActivity).not.toHaveBeenCalled(); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
});

test('Slice 5A token rotation keeps Activity state; identity replacement and sign-out remove it', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  const view = await renderRouter(routes, { initialUrl: '/planning' }); await view.findByText('Approved');
  await act(() => activityFlow.ensureActivitiesLoaded()); await act(() => activityFlow.setDistance('5000'));
  const owner = activityFlow.ensureActivitiesLoaded;
  await act(() => { mockAuth.session = { access_token: 'rotated-token', user: { id: 'athlete-a' } }; mockAuthListeners.forEach(listener => listener()); });
  expect(activityFlow.ensureActivitiesLoaded).toBe(owner); expect(activityFlow.distance).toBe('5000');
  await act(() => { mockAuth.session = { access_token: 'token-b', user: { id: 'athlete-b' } }; mockAuthListeners.forEach(listener => listener()); });
  expect(activityFlow.ensureActivitiesLoaded).not.toBe(owner); expect(activityFlow.distance).toBe(''); expect(activityFlow.activities).toEqual([]);
  const old = activityFlow;
  await act(() => mockSignOut()); await view.findByText('Auth destination');
  await act(() => old.save()); expect(api.createActivity).not.toHaveBeenCalled();
});

test('Slice 5A shared authoritative refresh updates the one shell reminder after feedback', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding); jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  const view = await renderRouter(routes, { initialUrl: '/planning' }); await view.findByText('Approved');
  const label = '1 workout waiting for RPE · open Training & RPE'; await view.findByText(label);
  await act(() => activityFlow.ensureActivitiesLoaded()); expect(view.getAllByText(label)).toHaveLength(1);
  jest.mocked(api.listActivities).mockResolvedValue([]); jest.mocked(api.submitActivityRpeWithRefresh).mockResolvedValue({ ...pendingActivity, rpe: 4, processing_state: 'complete' });
  await act(() => activityFlow.saveRpe(pendingActivity.id, 4));
  expect(view.queryByText(label)).toBeNull(); expect(activityFlow.pendingRpe).toEqual([]);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1); expect(jest.mocked(api.listActivities).mock.calls.filter(call => !call[1])).toHaveLength(2);
});

test('real JS tabs keep one owner, one restore and loaded Calendar context across roots', async () => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = flow.setWeekStart;
  const reader = calendar.loadCalendarRange;
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await view.findByText('Training calendar');
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(1));
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(2));
  await act(() => navigation.calendarNavigation.selectDate('2026-10-07'));
  const anchor = navigation.calendarNavigation.anchor;
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' }));
  await view.findByTestId('v2-activities');
  await fireEvent.press(view.getByRole('tab', { name: 'Week' }));
  await view.findByText('Approved');
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  expect(navigation.calendarNavigation.mode).toBe('month');
  expect(navigation.calendarNavigation.selectedDate).toBe('2026-10-07');
  expect(navigation.calendarNavigation.anchor).toBe(anchor);
  expect(flow.setWeekStart).toBe(owner); expect(calendar.loadCalendarRange).toBe(reader);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1); expect(api.getCalendar).toHaveBeenCalledTimes(3);
  expect(api.getOnboarding).toHaveBeenCalledTimes(2);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled(); expect(api.transitionSwipeWeekDraft).not.toHaveBeenCalled();
});

test.each(['/planning', '/calendar', '/activities'])('incomplete/version-resume gates direct %s without a Planning bootstrap', async (path) => {
  jest.mocked(api.getOnboarding).mockResolvedValue({ ...onboarding, current_step: 'zones', status: 'upgrade_required', upgrade_required: true });
  const view = await renderRouter(routes, { initialUrl: path });
  await view.findByText('Existing onboarding resume');
  expect(api.getWeeklyPlan).not.toHaveBeenCalled(); expect(api.getCalendar).not.toHaveBeenCalled();
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
});

test('failed readiness stays closed and retries without starting an owner', async () => {
  jest.mocked(api.getOnboarding).mockRejectedValueOnce(new Error('safe test failure'));
  const view = await renderRouter(routes, { initialUrl: '/calendar' });
  await view.findByText('Could not check your onboarding');
  expect(api.getWeeklyPlan).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Try again' }));
  await view.findByText('Training calendar');
});

test('unauthenticated direct entry returns Auth with no training reads', async () => {
  mockAuth.session = null;
  const view = await renderRouter(routes, { initialUrl: '/calendar' });
  await view.findByText('Auth destination');
  expect(api.getOnboarding).not.toHaveBeenCalled(); expect(api.getWeeklyPlan).not.toHaveBeenCalled();
});

test.each(['Week', 'Calendar', 'Activities'])('Profile from %s returns to actual origin above tabs', async (origin) => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  if (origin !== 'Week') await fireEvent.press(view.getByRole('tab', { name: origin }));
  const path = origin === 'Week' ? '/planning' : origin === 'Calendar' ? '/calendar' : '/activities';
  await fireEvent.press(view.getByRole('button', { name: 'Profile' }));
  await view.findByText('Profile task');
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Profile Back' }));
  await waitFor(() => expect(view.getByTestId('path').props.children).toBe(path));
  expect(view.getByRole('tab', { name: origin }).props.accessibilityState.selected).toBe(true);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});

test('Calendar detail holds the exact loaded object and returns Month/date/scroll without reads', async () => {
  const detail = jest.spyOn(detailBoundary, 'WorkoutDetailBoundary');
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await act(() => navigation.calendarNavigation.selectDate('2026-10-07'));
  await waitFor(() => expect(calendar.calendarRange?.fromDate).toBe('2026-09-28'));
  await fireEvent.scroll(view.getByTestId('calendar-scroll'), { nativeEvent: { contentOffset: { y: 216 } } });
  await fireEvent.press(await view.findByRole('button', { name: `View workout · ${workout.name}` }));
  expect(detail.mock.calls.at(-1)?.[0].workout).toBe(workout);
  const calls = jest.mocked(api.getCalendar).mock.calls.length;
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Close' }));
  expect(navigation.calendarNavigation.mode).toBe('month');
  expect(navigation.calendarNavigation.selectedDate).toBe('2026-10-07');
  expect(view.getByTestId('calendar-scroll').props.contentOffset.y).toBe(216);
  expect(api.getCalendar).toHaveBeenCalledTimes(calls);
});

test('resumed draft and revisions survive tabs and safe V1/V2 navigator replacement', async () => {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.latest-swipe-draft-id' ? draft.id : null);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(draft);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Choose your workouts');
  const owner = flow.setWeekStart;
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: 'Week' }));
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await view.findByText('Stel je week samen');
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  await view.findByText('Choose your workouts');
  expect(view.getByRole('tab', { name: 'Activities' })).toBeTruthy();
  expect(flow.swipeDraft).toBe(draft); expect(flow.setWeekStart).toBe(owner);
  expect(api.getSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled(); expect(api.transitionSwipeWeekDraft).not.toHaveBeenCalled();
});

test('Slice 4A task transition locks roots and comparison, then re-entry across roots retains the exact returned draft', async () => {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.latest-swipe-draft-id' ? draft.id : null);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(draft);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Choose your workouts');
  const owner = flow.setWeekStart;
  const reader = calendar.loadCalendarRange;
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await view.findByText('Choose your workouts');
  expect(view.queryByTestId('training-root-navigation')).toBeNull();
  let finish!: () => void;
  const updated = { ...draft, revision: 5, passed_count: 1, can_undo: true };
  jest.mocked(api.transitionSwipeWeekDraft).mockImplementation(async () => {
    await new Promise<void>((resolve) => { finish = resolve; }); return updated;
  });
  const pass = view.getByRole('button', { name: `Pass · ${draft.current_candidate!.name}` });
  await fireEvent.press(pass); await fireEvent.press(pass);
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  await act(() => finish());
  await waitFor(() => expect(flow.swipeDraft).toBe(updated));
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: 'Week' }));
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  expect(flow.swipeDraft).toBe(updated);
  expect(flow.setWeekStart).toBe(owner); expect(calendar.loadCalendarRange).toBe(reader);
  expect(api.getSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
});

test('Slice 4A automatic submit restores root tabs directly at pending Week without mounting proposal review', async () => {
  const ready = { ...draft, state: 'placement' as const, current_candidate: null };
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.latest-swipe-draft-id' ? draft.id : null);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(ready);
  const pending = { ...pendingPlan, active_revision: null };
  jest.mocked(api.submitSwipeWeekDraft).mockResolvedValue({ plan: pending, proposal: pending.proposal! });
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Confirm your training dates');
  const owner = flow.setWeekStart;
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await fireEvent.press(view.getByRole('button', { name: 'Continue to placement' }));
  await view.findByText('Place your workouts');
  await fireEvent.press(view.getByRole('button', { name: 'Place automatically and submit proposal' }));
  await view.findByText('Proposal awaiting review');
  expect(view.getByTestId('training-root-navigation')).toBeTruthy();
  expect(navigation.task).toBeNull(); expect(flow.setWeekStart).toBe(owner);
  expect(flow.swipeDraft).toBeNull(); expect(flow.plan).toBe(pending);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.getPendingWorkoutAlternatives).not.toHaveBeenCalled();
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  expect(api.rejectPlanProposal).not.toHaveBeenCalled();
});

test('approved roots replace tab and stack navigators after all destinations have been visited', async () => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = flow.setWeekStart;
  const calendarOwner = calendar.loadCalendarRange;
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await view.findByText('Training calendar');
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(2));
  await act(() => navigation.calendarNavigation.selectDate('2026-10-07'));
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' }));
  await view.findByTestId('v2-activities');
  await fireEvent.press(view.getByRole('tab', { name: 'Week' }));
  for (let attempt = 0; attempt < 2; attempt++) {
    await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
    await view.findByText('Your training week');
    expect(view.queryByTestId('training-root-navigation')).toBeNull();
    await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
    await view.findByText('Approved');
    await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
    await view.findByText('Training calendar');
    expect(navigation.calendarNavigation.mode).toBe('month');
    expect(navigation.calendarNavigation.selectedDate).toBe('2026-10-07');
    await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: 'Week' }));
  }
  expect(flow.setWeekStart).toBe(owner);
  expect(calendar.loadCalendarRange).toBe(calendarOwner);
  expect(flow.plan).toBe(activePlan);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
  expect(api.getCalendar).toHaveBeenCalledTimes(3);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('detail keeps the measured navigation footprint to avoid clamping Calendar scroll', async () => {
  const view = await renderRouter(routes, { initialUrl: '/calendar' });
  await view.findByText('Training calendar');
  await fireEvent(view.getByTestId('training-root-navigation'), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: 393, height: 80 } }
  });
  await act(() => navigation.setDetailWorkout(workout));
  expect(view.queryByTestId('training-root-navigation')).toBeNull();
  const footprint = view.getByTestId('training-detail-footprint', { includeHiddenElements: true });
  expect(footprint.props.children.props.style.height).toBe(80);
  expect(footprint.props.pointerEvents).toBe('none');
  expect(footprint.props.accessibilityElementsHidden).toBe(true);
  await act(() => navigation.setDetailWorkout(null));
  expect(view.getByTestId('training-root-navigation')).toBeTruthy();
});

test('creation task hides root navigation, retains root owner during comparison, then returns settled Week', async () => {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : null);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  expect(navigation.rootVersion).toBe('v2');
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Prepare your training week');
  expect(view.getByRole('tab', { name: 'Week' })).toBeTruthy();
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test.each(['/tests', '/calibration'])('legacy direct %s remains a task with safe Week fallback', async (path) => {
  const view = await renderRouter(routes, { initialUrl: path });
  await view.findByText('Tests Back');
  expect(api.getWeeklyPlan).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Tests Back' }));
  await view.findByText('Approved');
});

test('direct Activities lazily mounts V2 history and root Back settles Week', async () => {
  const view = await renderRouter(routes, { initialUrl: '/activities' });
  await view.findByTestId('v2-activities');
  expect(api.getCalendar).toHaveBeenCalledTimes(1); // Existing Activity owner's calendar-context read.
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Approved');
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Activities' }));
  await act(() => router.back());
  await waitFor(() => expect(view.getByTestId('path').props.children).toBe('/planning'));
});

test('sign-out removes the owner; another athlete gets new empty plan/calendar state', async () => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = flow.setWeekStart;
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await waitFor(() => expect(calendar.calendarWorkouts).toEqual([workout]));
  await fireEvent.press(view.getByRole('button', { name: 'Profile' }));
  await fireEvent.press(view.getByRole('button', { name: 'Sign out fixture' }));
  await view.findByText('Auth destination');
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : null);
  await act(() => { mockAuth.session = { access_token: 'token-b', user: { id: 'athlete-b' } }; mockAuthListeners.forEach((listener) => listener()); router.replace('/planning'); });
  await view.findByText('Prepare your training week');
  expect(flow.setWeekStart).not.toBe(owner); expect(flow.plan).toBeNull(); expect(flow.swipeDraft).toBeNull();
  expect(calendar.calendarWorkouts).toEqual([]); expect(calendar.calendarRange).toBeNull();
});

test('requested V1 keeps the original internal Week/Calendar navigation with no root tabs', async () => {
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Week van 2026-10-05');
  expect(view.queryByRole('tab', { name: 'Activities' })).toBeNull();
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await view.findByText('Training calendar');
  expect(view.getByTestId('path').props.children).toBe('/planning');
});

test('pending RPE has one global reminder and action across root destinations', async () => {
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const label = '1 workout waiting for RPE · open Training & RPE';
  expect(view.getAllByText(label)).toHaveLength(1);
  await fireEvent.press(view.getByText(label));
  await view.findByText('Activity feedback');
  expect(activityFlow.feedbackActivity?.id).toBe(pendingActivity.id);
  expect(view.getAllByText(label)).toHaveLength(1);
});

test('language switching localizes the same three root destinations', async () => {
  const { useLanguage } = jest.requireActual<typeof import('../i18n/LanguageProvider')>('../i18n/LanguageProvider');
  let change!: ReturnType<typeof useLanguage>['setPreference'];
  function LanguageProbe() { change = useLanguage().setPreference; return <Group />; }
  const view = await renderRouter({ ...routes, '(authenticated)/(training)/_layout': LanguageProbe }, { initialUrl: '/planning' });
  await view.findByText('Approved');
  await act(() => change('nl'));
  const bar = within(view.getByTestId('training-root-navigation'));
  expect(bar.getByRole('tab', { name: 'Kalender' })).toBeTruthy();
  expect(bar.getByRole('tab', { name: 'Activiteiten' })).toBeTruthy();
  expect(bar.getByRole('tab', { name: 'Week' }).props.accessibilityState.selected).toBe(true);
});

test.each(['planning write', 'pending move', 'move chooser', 'activity write', 'sheet dismissal'])('%s prevents root navigation and global RPE navigation', async (reason) => {
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  if (reason === 'planning write') jest.mocked(api.createSwipeWeekDraft).mockImplementation(() => new Promise(() => undefined));
  if (reason === 'pending move') jest.mocked(api.validatePlanLayout).mockResolvedValue({ warnings: [warning] } as Awaited<ReturnType<typeof api.validatePlanLayout>>);
  await act(() => {
    if (reason === 'planning write') void flow.generate();
    else if (reason === 'pending move') void flow.requestWorkoutMove(workout, '2026-10-08');
    else if (reason === 'move chooser') navigation.setMoveWorkoutId(workout.id);
    else if (reason === 'activity write') navigation.setActivityBusy(true);
    else navigation.setSheetOpen(true);
  });
  expect(view.queryByTestId('training-root-navigation')).toBeNull();
  await fireEvent.press(view.getByText('1 workout waiting for RPE · open Training & RPE'));
  expect(view.getByTestId('path').props.children).toBe('/planning');
  expect(api.movePlannedWorkout).not.toHaveBeenCalled();
});

test('identity replacement without an intermediate sign-out resets flow and selection', async () => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = flow.setWeekStart;
  await act(() => navigation.calendarNavigation.changeMode('month'));
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : null);
  await act(() => { mockAuth.session = { access_token: 'token-b', user: { id: 'athlete-b' } }; mockAuthListeners.forEach((listener) => listener()); });
  await view.findByText('Prepare your training week');
  expect(flow.setWeekStart).not.toBe(owner); expect(flow.plan).toBeNull();
  expect(navigation.calendarNavigation.mode).toBe('week'); expect(calendar.calendarRange).toBeNull();
});

test('token rotation preserves owner and shared Calendar selection', async () => {
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  const owner = flow.setWeekStart;
  await act(() => navigation.calendarNavigation.changeMode('month'));
  await act(() => { mockAuth.session = { access_token: 'rotated-token', user: { id: 'athlete-a' } }; mockAuthListeners.forEach((listener) => listener()); });
  expect(flow.setWeekStart).toBe(owner); expect(navigation.calendarNavigation.mode).toBe('month');
});

test('returning during the same pending Calendar read does not start another read', async () => {
  let finish!: (value: Awaited<ReturnType<typeof api.getCalendar>>) => void;
  jest.mocked(api.getCalendar).mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Approved');
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: 'Week' }));
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await act(() => finish({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] }));
  await view.findByText(workout.name);
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
});

test('changed approved revision invalidates Calendar; hidden Calendar does not reload until focused', async () => {
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await waitFor(() => expect(flow.activePlan).toBe(activePlan));
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await view.findByText(workout.name);
  await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: 'Week' }));
  const updated = { ...activePlan, revision: 4, active_revision: 4, revision_id: 'revision-4' };
  jest.mocked(api.approvePlanProposal).mockResolvedValue({ state: 'applied', plan_id: updated.id, active_revision: 4 });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(updated);
  await act(async () => { await flow.approve(); });
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
  await waitFor(() => expect(api.getCalendar).toHaveBeenCalledTimes(2));
  expect(flow.plan).toBe(updated);
});

test('V1 swipe animation locks presentation switching before its deferred write', async () => {
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.latest-swipe-draft-id' ? draft.id : null);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(draft);
  const timing = Animated.timing;
  jest.spyOn(Animated, 'timing').mockImplementation((value, config) => {
    if (typeof config.toValue === 'object' && 'x' in config.toValue) return { start: jest.fn(), stop: jest.fn(), reset: jest.fn() };
    return timing(value, config);
  });
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Stel je week samen');
  await fireEvent.press(view.getByRole('button', { name: 'Kiezen' }));
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  expect(navigation.rootVersion).toBe('v1'); expect(navigation.locked).toBe(true);
  expect(api.transitionSwipeWeekDraft).not.toHaveBeenCalled();
});


test('Slice 4B review/editor Back preserve one owner and pending proposal while roots remain usable', async () => {
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: pendingPlan.proposal!.id, workout_id: workout.id, can_remove: false, alternatives: [] });
  const view = await renderRouter(routes, { initialUrl: '/planning' });
  await view.findByText('Review proposal'); const owner = flow.setWeekStart; const reader = calendar.loadCalendarRange;
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  await view.findByText('Review your week proposal'); expect(view.queryByTestId('training-root-navigation')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: /^View alternatives/ }));
  await view.findByText('There are currently no alternatives for this workout.');
  await fireEvent.press(view.getByRole('button', { name: 'Back to proposal' }));
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(flow.plan).toBe(pendingPlan); expect(flow.activePlan).toBe(activePlan);
  for (const root of ['Calendar', 'Activities', 'Week']) await fireEvent.press(within(view.getByTestId('training-root-navigation')).getByRole('tab', { name: root }));
  expect(flow.setWeekStart).toBe(owner); expect(calendar.loadCalendarRange).toBe(reader);
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled(); expect(api.editPendingWorkout).not.toHaveBeenCalled();
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
});
test('Slice 4B editor write locks shell and comparison, then explicit approval restores active Week without another owner', async () => {
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  const candidate = { ...draft.current_candidate!, id: 'returned-alternative' };
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: pendingPlan.proposal!.id, workout_id: workout.id, can_remove: false, alternatives: [candidate] });
  const view = await renderRouter(routes, { initialUrl: '/planning' }); await view.findByText('Review proposal');
  const owner = flow.setWeekStart; const reader = calendar.loadCalendarRange;
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  await fireEvent.press(view.getByRole('button', { name: /^View alternatives/ }));
  await view.findByRole('radio'); await fireEvent.press(view.getByRole('radio'));
  let finish!: () => void;
  const updated = { ...pendingPlan, revision: 4, revision_id: 'revision-4', proposal: { ...pendingPlan.proposal!, id: 'proposal-4' } };
  jest.mocked(api.editPendingWorkout).mockImplementation(async () => { await new Promise<void>(resolve => { finish = resolve; }); return { plan: updated, proposal: updated.proposal }; });
  await fireEvent.press(view.getByRole('button', { name: 'Replace workout in proposal' }));
  expect(view.getByRole('button', { name: 'Back to proposal' })).toBeDisabled(); expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.queryByTestId('training-root-navigation')).toBeNull(); expect(api.approvePlanProposal).not.toHaveBeenCalled();
  await act(() => finish()); await view.findByText('Review your week proposal');
  const approved = { ...activePlan, revision: 4, active_revision: 4, revision_id: 'revision-4' };
  jest.mocked(api.approvePlanProposal).mockResolvedValue({ state: 'applied', plan_id: activePlan.id, active_revision: 4 }); jest.mocked(api.getWeeklyPlan).mockResolvedValue(approved);
  await fireEvent.press(view.getByRole('button', { name: 'Approve week' })); await view.findByText('Approved');
  expect(flow.plan).toBe(approved); expect(flow.activePlan).toBe(approved); expect(navigation.task).toBeNull();
  expect(view.getByTestId('training-root-navigation')).toBeTruthy(); expect(flow.setWeekStart).toBe(owner); expect(calendar.loadCalendarRange).toBe(reader);
  expect(api.approvePlanProposal).toHaveBeenCalledWith('token-a', updated.proposal.id, 2); expect(api.editPendingWorkout).toHaveBeenCalledTimes(1);
});
