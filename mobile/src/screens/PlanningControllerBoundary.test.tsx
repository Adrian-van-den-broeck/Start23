import { fireEvent, render, waitFor } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { activePlan, draft, occurrence, onboarding, pendingPlan, proposal, workout } from '../features/planning/planning.test-fixtures';
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
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  process.env.EXPO_PUBLIC_UI_VERSION = 'v1';
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
});
function resume(kind: 'plan' | 'draft') {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) =>
    key === (kind === 'plan' ? 'start23.latest-plan-id' : 'start23.latest-swipe-draft-id') ? (kind === 'plan' ? pendingPlan.id : draft.id) : null);
}

test('V1 create action uses shared owner and preserves confirmation controls', async () => {
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  const view = await render(presentation());
  await fireEvent.changeText(view.getByLabelText('Week start op maandag'), '2026-10-05');
  await fireEvent.press(view.getByRole('checkbox', { name: 'Lopen' }));
  await fireEvent.press(view.getAllByRole('checkbox', { name: 'Fietsen' })[1]);
  await fireEvent.press(view.getByRole('button', { name: 'Maak weekvoorstel' }));
  await waitFor(() => expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1));
  expect(api.createSwipeWeekDraft).toHaveBeenCalledWith('token-a', {
    week_start: '2026-10-05', available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
    confirmed_injuries: ['run'], cross_training_opt_ins: ['bike'],
  });
  await view.findByText('Stel je week samen');
  await view.rerender(presentation());
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
});

test('V1 undo and reset passed call the owner without duplicate transitions', async () => {
  resume('draft');
  const restored = { ...draft, can_undo: true, passed_count: 1 };
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(restored);
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValueOnce({ ...restored, revision: 5 }).mockResolvedValueOnce({ ...restored, revision: 6 });
  const view = await render(presentation());
  await view.findByText('Stel je week samen');
  await fireEvent.press(view.getByRole('button', { name: 'Ongedaan maken' }));
  await waitFor(() => expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1));
  await fireEvent.press(view.getByRole('button', { name: 'Opnieuw bekijken' }));
  expect(jest.mocked(api.transitionSwipeWeekDraft).mock.calls.map((call) => call[2])).toEqual([{ expected_revision: 4, action: 'undo' }, { expected_revision: 5, action: 'reset_passed' }]);
});

test('V1 manual completion and request busy disable submit; rerender never resubmits', async () => {
  resume('draft');
  const placed = { ...draft, state: 'placement' as const, current_candidate: null, accepted_workouts: [occurrence], placements: [] };
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(placed);
  jest.mocked(api.placeSwipeWeekWorkout).mockResolvedValue({ ...placed, revision: 5, placements: [{ occurrence_id: occurrence.occurrence_id, scheduled_date: '2026-10-07' }] });
  let resolve!: (value: { plan: typeof pendingPlan; proposal: typeof proposal }) => void;
  jest.mocked(api.submitSwipeWeekDraft).mockReturnValue(new Promise((yes) => { resolve = yes; }));
  const view = await render(presentation());
  await view.findByText('Controleer handmatige planning');
  expect(view.getByRole('button', { name: 'Controleer handmatige planning' })).toBeDisabled();
  await fireEvent.press(view.getAllByRole('radio')[2]);
  expect(api.placeSwipeWeekWorkout).toHaveBeenCalledWith('token-a', draft.id, occurrence.occurrence_id, 4, '2026-10-07');
  await fireEvent.press(view.getByRole('button', { name: 'Controleer handmatige planning' }));
  expect(view.getByRole('button', { name: 'Verspreid over beschikbare dagen' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Verspreid over beschikbare dagen' }));
  await view.rerender(presentation());
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, 5, 'manual');
  resolve({ plan: pendingPlan, proposal });
  await view.findByText('Week van 2026-10-05');
});

test.each(['approve', 'reject'] as const)('V1 %s and pending editor read once per slot/revision; rerender and UI toggle never repeat', async (action) => {
  resume('plan');
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, alternatives: [], can_remove: true });
  let finish!: () => void;
  const gate = new Promise<void>((yes) => { finish = yes; });
  jest.mocked(api.approvePlanProposal).mockImplementation(async () => { await gate; return { state: 'applied', plan_id: pendingPlan.id, active_revision: 3 }; });
  jest.mocked(api.rejectPlanProposal).mockImplementation(async () => { await gate; return { state: 'rejected', plan_id: pendingPlan.id }; });
  const view = await render(presentation());
  await view.findByText('Week van 2026-10-05');
  await waitFor(() => expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1));
  await view.rerender(presentation());
  // Slice 2b now implements Week; V1 mutation regression stays on V1.
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
  // The baseline carries can_remove but exposes no remove button.
  expect(view.queryByRole('button', { name: /Verwijder/ })).toBeNull();
  const button = view.getByRole('button', { name: action === 'approve' ? 'Week goedkeuren' : 'Afwijzen' });
  await fireEvent.press(button);
  expect(button).toBeDisabled();
  await fireEvent.press(button);
  await view.rerender(presentation());
  const mutation = action === 'approve' ? api.approvePlanProposal : api.rejectPlanProposal;
  expect(mutation).toHaveBeenCalledTimes(1);
  finish();
  await waitFor(() => expect(api.getWeeklyPlan).toHaveBeenCalledTimes(3));
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
});

afterEach(() => { delete process.env.EXPO_PUBLIC_UI_VERSION; });
