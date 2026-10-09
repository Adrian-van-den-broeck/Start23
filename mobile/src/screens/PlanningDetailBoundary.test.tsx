import { fireEvent, render, waitFor, within } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import type { OnboardingState, WeeklyPlan } from '../api/types';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import * as boundary from '../ui/WorkoutDetailBoundary';
import { sourceWorkout } from '../ui-v2/utils/workout.test-fixtures';
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

const workout = { ...sourceWorkout, discipline: 'run' as const, scheduled_date: '2026-09-23', status: 'scheduled' as const };
const plan: WeeklyPlan = {
  id: 'plan', week_start: '2026-09-21', timezone: 'Europe/Amsterdam', state: 'active', active_revision: 2,
  revision_id: 'revision', revision: 2, revision_state: 'active', phase: 'base', target_basis: 'prior_planned_hold',
  taper_period: null, total_duration_minutes: '30.5', low_intensity_percent: '100', high_intensity_percent: '0',
  display_low_intensity_percent: 100, display_high_intensity_percent: 0, low_intensity_minutes: '30.5',
  high_intensity_minutes: '0', confirmed_injuries: [], low_only_disciplines: [], available_dates: ['2026-09-23'],
  availability_source: 'explicit', workouts: [workout], rest_days: [], warnings: [], proposal: null,
};

beforeEach(() => {
  jest.clearAllMocks();
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => {
    if (key === 'start23.latest-plan-id') return 'plan';
    if (key === 'start23.language-preference') return 'en';
    return null;
  });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(plan);
  jest.mocked(api.getOnboarding).mockResolvedValue({ primary_goal: null } as OnboardingState);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-09-21', to_date: '2026-09-28', workouts: [workout], rest_days: [] });
});
afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; jest.restoreAllMocks(); });

test.each(['Week', 'Calendar'])('%s opens exact owned snapshot; comparison and dismissal retain origin without I/O', async (origin) => {
  const spy = jest.spyOn(boundary, 'WorkoutDetailBoundary');
  const view = await render(<SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}><LanguageProvider><UiVersionProvider><PlanningScreen accessToken="fixture-token"
    onSignOut={jest.fn(async () => undefined)} onBackToOnboarding={jest.fn()} onOpenActivities={jest.fn()}
    onOpenCheckIn={jest.fn()} onOpenIntegrations={jest.fn()} onOpenProfile={jest.fn()} onOpenZoneProfile={jest.fn()} />
  </UiVersionProvider></LanguageProvider></SafeAreaProvider>);
  await view.findByText('Week van 2026-09-21');
  if (origin === 'Calendar') {
    await fireEvent.press(view.getByRole('tab', { name: 'Calendar' }));
    await view.findByText('Training calendar');
    await waitFor(() => expect(api.getCalendar).toHaveBeenCalled());
    await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
    await fireEvent.press(view.getByLabelText(/View.*23/));
  }
  await fireEvent.press(view.getByRole('button', { name: workout.name }));
  expect(spy.mock.calls.at(-1)?.[0].workout).toBe(workout);
  const modal = view.getByTestId('workout-detail-modal');
  jest.clearAllMocks();
  await fireEvent.press(within(modal).getByRole('button', { name: 'UI V2' }));
  expect(spy.mock.calls.at(-1)?.[0].workout).toBe(workout);
  expect(view.getByTestId('workout-detail-modal')).toBe(modal);
  await fireEvent.press(within(modal).getByRole('button', { name: 'Close' }));
  expect(view.queryByTestId('workout-detail-modal')).toBeNull();
  expect(view.getByRole('tab', { name: origin }).props.accessibilityState.selected).toBe(true);
  if (origin === 'Calendar') {
    expect(view.getByRole('tab', { name: 'Month' }).props.accessibilityState.selected).toBe(true);
    expect(view.getByLabelText(/View.*23/).props.accessibilityState.selected).toBe(true);
  }
  for (const method of Object.values(api).filter(jest.isMockFunction)) expect(method).not.toHaveBeenCalled();
  expect(SecureStore.getItemAsync).not.toHaveBeenCalled();
  expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});
