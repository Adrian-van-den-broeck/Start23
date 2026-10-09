import { act, fireEvent, render } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import * as api from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { activePlan, onboarding, pendingPlan, proposal, workout, occurrence } from '../features/planning/planning.test-fixtures';
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
    BottomSheetScrollView: ({ children }: PropsWithChildren) => <RN.ScrollView>{children}</RN.ScrollView>,
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
function restore(kind: 'plan') {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) =>
    key === 'start23.language-preference' ? 'en' :
      key === (kind === 'plan' ? 'start23.latest-plan-id' : 'start23.latest-swipe-draft-id') ? activePlan.id : null);
}

async function enterReview(value = pendingPlan, activeValue = activePlan) {
  restore('plan');
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activeValue : value);
  const view = await render(presentation());
  await view.findByText('Review proposal');
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  await view.findByText('Review your week proposal');
  return view;
}
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (value: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
const options = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, alternatives: [{ ...occurrence, id: 'alternative-b', name: 'Supplied alternative' }], can_remove: false };
async function editor(view: Awaited<ReturnType<typeof enterReview>>) {
  await fireEvent.press(view.getByRole('button', { name: /^View alternatives/ }));
  await view.findByText('Alternatives for this workout');
}

test('review and Back preserve pending snapshot, all occurrences/warnings and active schedule without fetching editors or deciding', async () => {
  const repeat = { ...workout, id: 'second', scheduled_date: '2026-10-10' };
  const value = { ...pendingPlan, workouts: [workout, repeat] };
  const view = await enterReview(value);
  expect(view.getAllByRole('button', { name: /^View alternatives/ })).toHaveLength(2);
  expect(view.getByText('Your approved plan remains active until you approve this proposal.')).toBeTruthy();
  expect(view.getByText('Weekcombinatie vraagt aandacht')).toBeTruthy();
  expect(api.getPendingWorkoutAlternatives).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(flow.plan).toBe(value); expect(flow.activePlan).toBe(activePlan);
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  expect(flow.plan).toBe(value); expect(api.getPendingWorkoutAlternatives).not.toHaveBeenCalled();
});
test('alternatives load only on open with exact revision; rerender/rapid opening does not duplicate; Back retains proposal', async () => {
  const view = await enterReview();
  const request = deferred<typeof options>(); jest.mocked(api.getPendingWorkoutAlternatives).mockReturnValue(request.promise);
  await editor(view);
  await view.rerender(presentation());
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, 3);
  expect(view.getByRole('button', { name: 'Back to proposal' })).toBeDisabled();
  await act(async () => request.resolve(options));
  await fireEvent.press(view.getByRole('button', { name: 'Back to proposal' }));
  expect(flow.plan).toBe(pendingPlan); expect(view.getByText('Review your week proposal')).toBeTruthy();
  expect(api.editPendingWorkout).not.toHaveBeenCalled(); expect(api.approvePlanProposal).not.toHaveBeenCalled();
});
test('replacement awaits acknowledgment, retains exact returned options transaction and returns to updated pending review', async () => {
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(options);
  const view = await enterReview(); await editor(view);
  await fireEvent.press(view.getByRole('radio', { name: /Select alternative/ }));
  const request = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal }>();
  jest.mocked(api.editPendingWorkout).mockReturnValue(request.promise);
  await fireEvent.press(view.getByRole('button', { name: 'Replace workout in proposal' }));
  expect(flow.plan).toBe(pendingPlan);
  expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(api.editPendingWorkout).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, { expected_revision: 3, expected_proposal_id: proposal.id, replacement_template_id: 'alternative-b' });
  const nextProposal = { ...proposal, id: 'proposal-b' }; const updated = { ...pendingPlan, revision: 4, revision_id: 'revision-4', proposal: nextProposal, workouts: [{ ...workout, name: 'Returned replacement' }] };
  await act(async () => request.resolve({ plan: updated, proposal: nextProposal }));
  expect(flow.plan).toBe(updated); await view.findByText('Returned replacement');
  expect(view.queryByText('Alternatives for this workout')).toBeNull();
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
});
test('server-enabled removal requires a separate confirmation and uses null replacement only in pending context', async () => {
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ ...options, can_remove: true });
  const view = await enterReview(); await editor(view);
  await fireEvent.press(view.getByRole('button', { name: 'Remove workout from proposal' }));
  expect(api.editPendingWorkout).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Keep workout' }));
  expect(api.editPendingWorkout).not.toHaveBeenCalled();
  const updated = { ...pendingPlan, revision: 4, workouts: [], proposal: { ...proposal, id: 'removed-proposal' } };
  jest.mocked(api.editPendingWorkout).mockResolvedValue({ plan: updated, proposal: updated.proposal });
  await fireEvent.press(view.getByRole('button', { name: 'Remove workout from proposal' }));
  await fireEvent.press(view.getByRole('button', { name: 'Confirm removal from proposal' }));
  await view.findByText('This proposal contains no workouts.');
  expect(api.editPendingWorkout).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, { expected_revision: 3, expected_proposal_id: proposal.id, replacement_template_id: null });
  expect(flow.activePlan).toBe(activePlan); expect(api.approvePlanProposal).not.toHaveBeenCalled();
});
test.each([false, undefined])('remove capability %s never exposes a functional removal control', async capability => {
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ ...options, can_remove: capability as boolean });
  const view = await enterReview(); await editor(view);
  expect(view.queryByRole('button', { name: 'Remove workout from proposal' })).toBeNull();
});
test('empty alternatives and safe error remain reviewable; explicit retry does not approve or recreate', async () => {
  jest.mocked(api.getPendingWorkoutAlternatives).mockRejectedValueOnce(new Error('Safe options unavailable')).mockResolvedValueOnce({ ...options, alternatives: [] });
  const view = await enterReview(); await editor(view);
  await view.findByText('Safe options unavailable');
  await fireEvent.press(view.getByRole('button', { name: 'Reload alternatives' }));
  await view.findByText('There are currently no alternatives for this workout.');
  expect(view.getByRole('button', { name: 'Replace workout in proposal' })).toBeDisabled();
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(2); expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});
test.each(['approve', 'reject'] as const)('%s is explicit once with exact ID and preserved follow-up read; returns to authoritative Week', async action => {
  const view = await enterReview();
  const request = deferred<void>();
  if (action === 'approve') jest.mocked(api.approvePlanProposal).mockImplementation(async () => { await request.promise; return { state: 'applied', plan_id: pendingPlan.id, active_revision: 3 }; });
  else jest.mocked(api.rejectPlanProposal).mockImplementation(async () => { await request.promise; return { state: 'rejected', plan_id: pendingPlan.id }; });
  const result = action === 'approve' ? { ...activePlan, revision: 3, active_revision: 3, revision_id: 'revision-3' } : { ...pendingPlan, revision_state: 'rejected' as const, proposal: { ...proposal, state: 'rejected' as const } };
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(result);
  const name = action === 'approve' ? 'Approve week' : 'Reject proposal';
  await act(() => { fireEvent(view.getByRole('button', { name }), 'press'); fireEvent(view.getByRole('button', { name }), 'press'); });
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  const mutation = action === 'approve' ? api.approvePlanProposal : api.rejectPlanProposal;
  expect(mutation).toHaveBeenCalledTimes(1);
  expect(mutation).toHaveBeenCalledWith(...(action === 'approve' ? ['token-a', proposal.id, 2] : ['token-a', proposal.id]));
  await act(async () => request.resolve());
  expect(jest.mocked(api.getWeeklyPlan).mock.calls.at(-1)).toEqual(action === 'approve' ? ['token-a', pendingPlan.id] : ['token-a', pendingPlan.id, 3]);
  await view.findByTestId('week-header-title'); expect(view.queryByText('Review your week proposal')).toBeNull();
  expect(flow.activePlan).toBe(action === 'approve' ? result : activePlan);
});
test('stale decision keeps the same reviewed warning/snapshot and never silently reads, retries or transfers intent', async () => {
  const view = await enterReview(); const before = jest.mocked(api.getWeeklyPlan).mock.calls.length;
  jest.mocked(api.approvePlanProposal).mockRejectedValue(new Error('Safe stale proposal'));
  await fireEvent.press(view.getByRole('button', { name: 'Approve week' }));
  await view.findByText('Safe stale proposal');
  expect(flow.plan).toBe(pendingPlan); expect(api.getWeeklyPlan).toHaveBeenCalledTimes(before);
  await view.rerender(presentation()); expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' })); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
});


test.each(['approve', 'reject'] as const)('distinct active and pending schedules stay separate before and after explicit %s', async action => {
  const approved = { ...activePlan, workouts: [{ ...workout, id: 'active-only', name: 'Approved source workout' }] };
  const proposed = { ...workout, id: 'pending-only', name: 'Proposed source workout', scheduled_date: '2026-10-10' };
  const pending = { ...pendingPlan, workouts: [proposed] };
  const view = await enterReview(pending, approved);
  expect(view.getByText('Proposed source workout')).toBeTruthy();
  expect(view.queryByText('Approved source workout')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  await view.findByText('Approved source workout');
  expect(view.queryByText('Proposed source workout')).toBeNull();
  expect(flow.activePlan).toBe(approved);
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  const result = action === 'approve'
    ? { ...approved, revision: 3, active_revision: 3, revision_id: 'revision-3', workouts: [proposed] }
    : { ...pending, revision_state: 'rejected' as const, proposal: { ...proposal, state: 'rejected' as const } };
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(result);
  jest.mocked(api.approvePlanProposal).mockResolvedValue({ state: 'applied', plan_id: pending.id, active_revision: 3 });
  jest.mocked(api.rejectPlanProposal).mockResolvedValue({ state: 'rejected', plan_id: pending.id });
  await fireEvent.press(view.getByRole('button', { name: action === 'approve' ? 'Approve week' : 'Reject proposal' }));
  await view.findByTestId('week-header-title');
  expect(view.getByText(action === 'approve' ? 'Proposed source workout' : 'Approved source workout')).toBeTruthy();
  expect(view.queryByText(action === 'approve' ? 'Approved source workout' : 'Proposed source workout')).toBeNull();
  expect(flow.activePlan).toBe(action === 'approve' ? result : approved);
  expect(flow.activePlan?.workouts).toHaveLength(1);
});
