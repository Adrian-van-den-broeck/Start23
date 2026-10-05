import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { activePlan, draft, occurrence, onboarding, pendingPlan, proposal, workout } from '../features/planning/planning.test-fixtures';
import { usePlanningFlow } from '../features/planning/PlanningFlowProvider';
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
    BottomSheetModal: React.forwardRef((_props: PropsWithChildren, ref) => {
      React.useImperativeHandle(ref, () => ({ present: jest.fn(), dismiss: jest.fn() }));
      return null;
    }),
  };
});
jest.mock('react-native-reanimated-carousel', () => ({ Carousel: () => null }));


let flow: ReturnType<typeof usePlanningFlow>;
function Probe() { flow = usePlanningFlow(); return null; }
function presentation() {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><PlanningFlowProvider accessToken="token-a" athleteIdentity="athlete-a"><PlanningPresentationProvider><Probe /><PlanningBoundary
      onSignOut={jest.fn(async () => undefined)} onBackToOnboarding={jest.fn()} onOpenActivities={jest.fn()}
      onOpenCheckIn={jest.fn()} onOpenIntegrations={jest.fn()} onOpenProfile={jest.fn()} onOpenZoneProfile={jest.fn()} /></PlanningPresentationProvider></PlanningFlowProvider>
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

async function enterDraft(value = draft) {
  restore('draft'); jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(value);
  const view = await render(presentation());
  await view.findAllByText('Workout selection in progress');
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await view.findByText('Choose your workouts');
  return view;
}

test('availability uses exact defaults, explicit dates, injuries and cross-training create payload', async () => {
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  const view = await render(presentation());
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
  expect(flow.selectedDays).toEqual(new Set([0, 2, 5]));
  await fireEvent.changeText(view.getByLabelText('Week starts on Monday'), '2026-10-05');
  await fireEvent.press(view.getByRole('checkbox', { name: 'Confirmed injury · Running' }));
  await fireEvent.press(view.getByRole('checkbox', { name: 'Optional alternative training · Cycling' }));
  await fireEvent.press(view.getByRole('button', { name: 'Start choosing workouts' }));
  await view.findByText('Choose your workouts');
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.createSwipeWeekDraft).toHaveBeenCalledWith('token-a', {
    week_start: '2026-10-05', available_dates: ['2026-10-05', '2026-10-07', '2026-10-10'],
    confirmed_injuries: ['run'], cross_training_opt_ins: ['bike'],
  });
  expect(flow.swipeDraft).toBe(draft);
});

test('reuse forwards only reuse_previous_week and retains active-plan binding', async () => {
  restore('plan'); jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  const view = await render(presentation());
  await view.findByText('Approved');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
  await fireEvent.press(view.getByRole('checkbox', { name: 'Use the same available days as last week' }));
  await fireEvent.press(view.getByRole('button', { name: 'Start choosing workouts' }));
  await view.findByText('Choose your workouts');
  expect(api.createSwipeWeekDraft).toHaveBeenCalledWith('token-a', {
    week_start: activePlan.week_start, reuse_previous_week: true, confirmed_injuries: ['run'], cross_training_opt_ins: [],
    plan_id: activePlan.id, expected_base_revision: activePlan.active_revision,
  });
});

test('empty availability cannot create; invalid week error remains availability without recreation', async () => {
  const view = await render(presentation());
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
  await act(() => { flow.toggleDay(0); flow.toggleDay(2); flow.toggleDay(5); });
  expect(view.getByRole('button', { name: 'Start choosing workouts' })).toBeDisabled();
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('checkbox', { name: /Monday ·/ }));
  await fireEvent.changeText(view.getByLabelText('Week starts on Monday'), '2026-10-06');
  jest.mocked(api.createSwipeWeekDraft).mockRejectedValue(new Error('Check your week start'));
  await fireEvent.press(view.getByRole('button', { name: 'Start choosing workouts' }));
  await view.findByText('Check your week start');
  expect(flow.swipeDraft).toBeNull();
  await view.rerender(presentation());
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(jest.mocked(api.createSwipeWeekDraft).mock.calls[0][1].week_start).toBe('2026-10-06');
});

test('rapid create remains locked across rerender, Back and version switch until draft storage settles', async () => {
  let finish!: () => void;
  jest.mocked(api.createSwipeWeekDraft).mockImplementation(async () => {
    await new Promise<void>((resolve) => { finish = resolve; }); return draft;
  });
  const view = await render(presentation());
  await view.findByText('Prepare your training week');
  await fireEvent.press(view.getByRole('button', { name: 'Prepare week' }));
  await view.findByText('When can you train?');
  const create = view.getByRole('button', { name: 'Start choosing workouts' });
  await fireEvent.press(create); await fireEvent.press(create);
  await view.rerender(presentation());
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
  await act(() => finish());
  await view.findByText('Choose your workouts');
});

test('leave, re-enter, cold restore and V1/V2 comparison retain exact draft/revision and candidate', async () => {
  const view = await enterDraft();
  const same = flow.swipeDraft;
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  expect(flow.swipeDraft).toBe(same);
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' }));
  await view.findByText('Stel je week samen');
  expect(view.queryByText('Choose your workouts')).toBeNull();
  expect(flow.swipeDraft).toBe(same);
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' }));
  await view.findByText('Choose your workouts');
  expect(view.queryByText('Stel je week samen')).toBeNull();
  expect(flow.swipeDraft?.revision).toBe(draft.revision);
  await view.unmount();
  const cold = await render(presentation());
  await cold.findAllByText('Workout selection in progress');
  await fireEvent.press(cold.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await cold.findByText('Choose your workouts');
  expect(flow.swipeDraft).toBe(draft);
  expect(api.getSwipeWeekDraft).toHaveBeenCalledTimes(2);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.transitionSwipeWeekDraft).not.toHaveBeenCalled();
});

test.each(['accept', 'pass', 'undo', 'reset_passed'] as const)('V2 %s preserves exact revision/identity and double press cannot duplicate', async (action) => {
  const initial = { ...draft, can_undo: true, passed_count: 1 };
  const view = await enterDraft(initial);
  let finish!: () => void;
  jest.mocked(api.transitionSwipeWeekDraft).mockImplementation(async () => {
    await new Promise<void>((resolve) => { finish = resolve; }); return { ...initial, revision: 5 };
  });
  const labels = { accept: `Choose · ${occurrence.name}`, pass: `Pass · ${occurrence.name}`, undo: 'Undo', reset_passed: 'Reset passed workouts' };
  const button = view.getByRole('button', { name: labels[action] });
  await fireEvent.press(button); await fireEvent.press(button);
  await view.rerender(presentation());
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, {
    expected_revision: draft.revision, action,
    ...(action === 'accept' || action === 'pass' ? { candidate_template_id: occurrence.id, candidate_occurrence_id: occurrence.occurrence_id } : {}),
  });
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  await act(() => finish());
  await waitFor(() => expect(flow.swipeDraft?.revision).toBe(5));
});

test.each(['Refresh required', 'Draft unavailable', 'Network unavailable'])('safe failure %s retains exact draft with no create or retry effect', async (message) => {
  const view = await enterDraft();
  jest.mocked(api.transitionSwipeWeekDraft).mockRejectedValue(new Error(message));
  await fireEvent.press(view.getByRole('button', { name: `Choose · ${occurrence.name}` }));
  await view.findByText(message);
  expect(flow.swipeDraft).toBe(draft);
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  expect(flow.swipeDraft).toBe(draft);
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test.each(['automatic', 'manual'] as const)('selection to %s placement to pending Week uses exact occurrences/revision/mode', async (mode) => {
  const repeat = { ...occurrence, occurrence_id: 'repeat' };
  const ready = {
    ...draft, state: 'placement' as const, accepted_workouts: [occurrence, repeat], current_candidate: null,
    available_dates: ['2026-10-05'], placements: []
  };
  restore('draft'); jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(ready);
  const view = await render(presentation());
  await view.findAllByText('Dates still to confirm');
  await fireEvent.press(view.getAllByRole('button', { name: 'Continue choosing' })[0]);
  await view.findByText('Choose your workouts');
  await fireEvent.press(view.getByRole('button', { name: 'Continue to placement' }));
  await view.findByText('Place your workouts');
  if (mode === 'manual') {
    await fireEvent.press(view.getByRole('radio', { name: 'Choose dates manually' }));
    jest.mocked(api.placeSwipeWeekWorkout).mockResolvedValueOnce({
      ...ready, revision: 5,
      placements: [{ occurrence_id: occurrence.occurrence_id, scheduled_date: '2026-10-05' }]
    }).mockResolvedValueOnce({
      ...ready, revision: 6,
      placements: ready.accepted_workouts.map((workout) => ({ occurrence_id: workout.occurrence_id, scheduled_date: '2026-10-05' }))
    });
    const dates = () => [1, 2].map((number) => view.getByRole('radio', { name: `Choice ${number} · ${occurrence.name} · Monday, 5 October 2026` }));
    await fireEvent.press(dates()[0]);
    await waitFor(() => expect(flow.swipeDraft?.revision).toBe(5));
    await fireEvent.press(dates()[1]);
    await waitFor(() => expect(flow.swipeDraft?.revision).toBe(6));
    expect(api.placeSwipeWeekWorkout).toHaveBeenNthCalledWith(1, 'token-a', draft.id, occurrence.occurrence_id, 4, '2026-10-05');
    expect(api.placeSwipeWeekWorkout).toHaveBeenNthCalledWith(2, 'token-a', draft.id, 'repeat', 5, '2026-10-05');
  }
  const pending = { ...pendingPlan, active_revision: null };
  let finish!: () => void;
  jest.mocked(api.submitSwipeWeekDraft).mockImplementation(async () => {
    await new Promise<void>((resolve) => { finish = resolve; }); return { plan: pending, proposal };
  });
  const label = mode === 'manual' ? 'Submit manual placement as proposal' : 'Place automatically and submit proposal';
  const submit = view.getByRole('button', { name: label });
  await fireEvent.press(submit); await fireEvent.press(submit);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, mode === 'manual' ? 6 : 4, mode);
  await act(() => finish());
  await view.findAllByText('Proposal awaiting review');
  expect(view.queryByText('Place your workouts')).toBeNull();
  expect(flow.swipeDraft).toBeNull(); expect(flow.plan).toBe(pending);
  expect(flow.plan?.proposal?.state).toBe('pending');
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  expect(api.getPendingWorkoutAlternatives).not.toHaveBeenCalled();
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.latest-plan-id', pending.id, expect.any(Object));
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-swipe-draft-id');
});
