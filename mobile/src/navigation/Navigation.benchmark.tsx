import { Profiler } from 'react';
import { writeFileSync } from 'fs';
import { OnboardingScreen } from '../screens/OnboardingScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import { ExpoRoot } from 'expo-router/build/ExpoRoot';
import { getMockContext } from 'expo-router/build/testing-library/mock-config';
import { Stack, usePathname } from 'expo-router';
import { Text, View } from 'react-native';
import type { PropsWithChildren } from 'react';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { activityOnboarding } from '../features/activities/activities.test-fixtures';
import { usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { activePlan, onboarding, workout } from '../features/planning/planning.test-fixtures';
import { useOptionalPlanningPresentation } from './PlanningPresentationProvider';
import AuthenticatedLayout from '../../app/(authenticated)/_layout';
import PlanningRoute from '../../app/(authenticated)/(training)/planning';
import CalendarRoute from '../../app/(authenticated)/(training)/calendar';
import ActivitiesRoute from '../../app/(authenticated)/(training)/activities';
import TrainingLayout from '../../app/(authenticated)/(training)/_layout';
import ProfileRoute from '../../app/(authenticated)/profile';
import TestsRoute from '../../app/(authenticated)/tests';
import CalibrationRoute from '../../app/(authenticated)/calibration';
import CheckInRoute from '../../app/(authenticated)/check-in';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../api/client', () => ({
  getGoalPlanningOptions: jest.fn(), getPhysiologyProfile: jest.fn(),
  listActivities: jest.fn(), listPlannedExternalActivities: jest.fn(), createActivity: jest.fn(), submitActivityRpeWithRefresh: jest.fn(), confirmActivityMatch: jest.fn(), approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(),
  getCalendar: jest.fn(), getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(), getSwipeWeekDraft: jest.fn(),
  discoverPlanning: jest.fn(), getWeeklyPlan: jest.fn(), markGoalAchieved: jest.fn(), movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(),
  rejectPlanProposal: jest.fn(), submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
  startWeeklyCheckIn: jest.fn(), getInjuryRestrictions: jest.fn(), createCheckInPlanProposal: jest.fn(),
}));
jest.mock('@gorhom/bottom-sheet', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const RN = jest.requireActual<typeof import('react-native')>('react-native');
  return {
    BottomSheetBackdrop: () => null,
    BottomSheetView: ({ children }: PropsWithChildren) => <RN.View>{children}</RN.View>,
    BottomSheetScrollView: ({ children }: PropsWithChildren) => <RN.ScrollView>{children}</RN.ScrollView>,
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
let flow: ReturnType<typeof usePlanningFlow>;
function Probe() {
  const value = useOptionalPlanningPresentation();
  const path = usePathname();
  return <View><Text testID="path">{path}</Text>{value ? <OwnerProbe /> : null}</View>;
}
function OwnerProbe() { flow = usePlanningFlow(); return null; }
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
  '(authenticated)/check-in': CheckInRoute,
  '(authenticated)/onboarding': () => <Text>Existing onboarding resume</Text>,
};
beforeEach(() => {
  jest.clearAllMocks(); process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  mockAuth.session = { access_token: 'token-a', user: { id: 'athlete-a' } };
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === 'start23.language-preference' ? 'en' : key === 'start23.athlete-a.latest-plan-id' ? activePlan.id : null);
  jest.mocked(SecureStore.setItemAsync).mockResolvedValue(undefined);
  jest.mocked(SecureStore.deleteItemAsync).mockResolvedValue(undefined);
  jest.mocked(api.getOnboarding).mockResolvedValue({ ...onboarding, ...activityOnboarding, current_step: 'completed' });
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: null, pending: null, draft: null });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.listActivities).mockResolvedValue([]);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [workout], rest_days: [] }));
});
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; jest.useRealTimers(); jest.restoreAllMocks(); });


const fixture = { ...onboarding, ...activityOnboarding, status: 'completed', current_step: 'completed',
  completed_steps: [], discipline_setups: [], training_history: [], zones: [], required_disciplines: ['run'],
  profile: { ...activityOnboarding.profile!, first_name: 'Synthetic', last_name: 'Benchmark', date_of_birth: '1990-05-20',
    resting_heart_rate_bpm: 52, revision: 4, identifying_revision: 2, physiology_revision: 2 },
};
const pause = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
test('representative V1 actual screens and retained navigation benchmark', async () => {
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  const output: Record<string, unknown>[] = [];
  jest.mocked(api.getOnboarding).mockImplementation(async () => { await pause(40); return fixture as typeof onboarding; });
  jest.mocked(api.getGoalPlanningOptions).mockImplementation(async () => { await pause(240); return []; });
  jest.mocked(api.getPhysiologyProfile).mockImplementation(async () => { await pause(240); return null; });
  jest.mocked(api.getWeeklyPlan).mockImplementation(async () => { await pause(40); return activePlan; });
  jest.mocked(api.discoverPlanning).mockImplementation(async () => { await pause(40); return { active: null, pending: null, draft: null }; });
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => { await pause(40); return { from_date: from, to_date: to, workouts: [workout], rest_days: [] }; });
  const counts = () => Object.fromEntries(Object.entries(api).filter(([,value]) => jest.isMockFunction(value)).map(([key,value]) => [key, (value as jest.Mock).mock.calls.length]));
  for (let run = 0; run < 5; run++) {
    const before = counts(); let duration = 0, renders = 0;
    const profiler: React.ProfilerOnRenderCallback = (_id, _phase, actual) => { duration += actual; renders++; };
    let start = performance.now(); const planning = jest.fn();
    const intake = await render(<Profiler id="intake" onRender={profiler}><OnboardingScreen accessToken="token-a" onOpenPlanning={planning} onOpenCalibration={jest.fn()} onSignOut={mockSignOut} /></Profiler>);
    await waitFor(() => expect(planning).toHaveBeenCalled(), { interval: 5 });
    output.push({ operation: 'completed-onboarding-to-training-callback', run, milliseconds: performance.now()-start, renderMilliseconds: duration, commits: renders, callsBefore: before, callsAfter: counts() });
    await intake.unmount();
    for (const visit of ['cold', 'warm']) {
      const calls = counts(); duration = 0; renders = 0; start = performance.now();
      const profile = await render(<Profiler id="profile" onRender={profiler}><ProfileScreen accessToken="token-a" onBack={jest.fn()} onOpenTests={jest.fn()} onOpenPioneerAccess={jest.fn()} onSignOut={mockSignOut}/></Profiler>);
      await waitFor(() => expect(profile.queryByDisplayValue('Synthetic')).not.toBeNull(), { interval: 5 });
      output.push({ operation: 'profile-'+visit, run, milliseconds: performance.now()-start, renderMilliseconds: duration, commits: renders, callsBefore: calls, callsAfter: counts() });
      await profile.unmount();
    }
    start = performance.now(); const calls = counts();
    const nav = await renderRouter(routes, { initialUrl: '/planning' });
    await waitFor(() => expect(nav.queryAllByText(workout.name).length).toBeGreaterThan(0), { interval: 5 });
    output.push({ operation: 'week-cold', run, milliseconds: performance.now()-start, callsBefore: calls, callsAfter: counts() });
    const owner = flow.setWeekStart;
    for (const [operation, tab] of [['calendar-cold','Calendar'],['week-warm','Week'],['calendar-warm','Calendar']]) {
      start = performance.now(); const prior = counts();
      await fireEvent.press(nav.getAllByRole('tab', { name: tab })[0]);
      await waitFor(() => expect(nav.queryAllByText(workout.name).length).toBeGreaterThan(0), { interval: 5 });
      expect(flow.setWeekStart).toBe(owner);
      output.push({ operation, run, milliseconds: performance.now()-start, callsBefore: prior, callsAfter: counts() });
    }
    await nav.unmount();
  }
  writeFileSync(process.env.A9_BENCH_OUTPUT!, JSON.stringify({ environment: 'Jest React development renderer, real screens/controllers, mocked API 40ms and auxiliary intake reads 240ms; native animations mocked; not device latency', measurements: output }, null, 2));
}, 60000);
