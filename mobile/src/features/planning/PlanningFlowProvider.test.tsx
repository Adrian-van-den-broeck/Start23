import { act, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import type { PropsWithChildren } from 'react';

import * as api from '../../api/client';
import type { CalendarResponse, PendingWorkoutAlternatives } from '../../api/types';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { UiVersionProvider, useUiVersion } from '../../ui/UiVersionProvider';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from './PlanningFlowProvider';
import { activePlan, draft, occurrence, onboarding, pendingPlan, proposal, warning, workout } from './planning.test-fixtures';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device-only' }));
jest.mock('../../api/client', () => ({
  approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(), getCalendar: jest.fn(),
  getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(), getSwipeWeekDraft: jest.fn(), getWeeklyPlan: jest.fn(),
  markGoalAchieved: jest.fn(), movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(), rejectPlanProposal: jest.fn(),
  submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
}));

let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let ui: ReturnType<typeof useUiVersion>;
const owners: ReturnType<typeof usePlanningFlow>[] = [];
function Probe() {
  flow = usePlanningFlow();
  calendar = usePlanningCalendar();
  ui = useUiVersion();
  owners.push(flow);
  return null;
}
function Host({ token = 'token-a', identity = 'athlete-a', children }: PropsWithChildren<{ token?: string; identity?: string; }>) {
  return <LanguageProvider><UiVersionProvider><PlanningFlowProvider accessToken={token} athleteIdentity={identity}>
    {children ?? <><Probe /><Probe /></>}
  </PlanningFlowProvider></UiVersionProvider></LanguageProvider>;
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function resume(kind: 'plan' | 'draft', id: string) {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key === `start23.latest-${kind === 'plan' ? 'plan' : 'swipe-draft'}-id` ? id : null);
}
async function loadedPlan(plan = activePlan) {
  resume('plan', plan.id);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : plan);
  const view = await render(<Host />);
  await waitFor(() => expect(flow.plan).toBe(plan));
  return view;
}
async function loadedDraft(value = draft) {
  resume('draft', value.id);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(value);
  const view = await render(<Host />);
  await waitFor(() => expect(flow.swipeDraft).toBe(value));
  return view;
}
beforeEach(() => {
  jest.clearAllMocks(); owners.length = 0;
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.mocked(SecureStore.getItemAsync).mockReset();
  jest.mocked(SecureStore.setItemAsync).mockReset();
  jest.mocked(SecureStore.deleteItemAsync).mockReset();
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
});

test('initial load has one owner, no plan discovery, no duplicate effects or writes on rerender/UI switch', async () => {
  const view = await render(<Host />);
  await waitFor(() => expect(api.getOnboarding).toHaveBeenCalledTimes(1));
  expect(flow.plan).toBeNull(); expect(flow.swipeDraft).toBeNull();
  expect(flow.selectedDays).toEqual(new Set([0, 2, 5]));
  expect(owners.at(-1)).toBe(owners.at(-2));
  const before = flow;
  await act(() => ui.setRequested('v2'));
  await view.rerender(<Host />);
  expect(flow.setWeekStart).toBe(before.setWeekStart);
  expect(api.getOnboarding).toHaveBeenCalledTimes(1);
  expect(api.getWeeklyPlan).not.toHaveBeenCalled(); expect(api.getSwipeWeekDraft).not.toHaveBeenCalled();
  expect(api.getCalendar).not.toHaveBeenCalled(); expect(api.submitSwipeWeekDraft).not.toHaveBeenCalled();
});

test('same-tick repeated creation is locked before busy renders, including preference changes', async () => {
  const response = deferred<typeof draft>();
  jest.mocked(api.createSwipeWeekDraft).mockReturnValue(response.promise);
  const view = await render(<Host />);
  await waitFor(() => expect(flow.resumeState).toBe('ready'));
  await act(() => { void flow.generate(); void flow.generate(); ui.setRequested('v2'); });
  await view.rerender(<Host />);
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
  await act(() => response.resolve(draft));
  await waitFor(() => expect(flow.swipeDraft).toBe(draft));
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
});

test.each(['accept', 'pass', 'undo', 'reset_passed'] as const)('shared synchronous lock prevents duplicate %s and cross-control writes', async (action) => {
  const initial = { ...draft, can_undo: true, passed_count: 1 };
  const response = deferred<typeof draft>();
  jest.mocked(api.transitionSwipeWeekDraft).mockReturnValue(response.promise);
  await loadedDraft(initial);
  await act(() => { flow.transitionDraft(action); flow.transitionDraft(action); flow.placeDraftWorkout(occurrence.occurrence_id, '2026-10-05'); flow.submitDraft('automatic'); });
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledWith('token-a', initial.id, {
    expected_revision: initial.revision, action,
    ...(action === 'accept' || action === 'pass' ? { candidate_template_id: occurrence.id, candidate_occurrence_id: occurrence.occurrence_id } : {}),
  });
  expect(api.placeSwipeWeekWorkout).not.toHaveBeenCalled();
  expect(api.submitSwipeWeekDraft).not.toHaveBeenCalled();
  await act(() => response.resolve({ ...initial, revision: initial.revision + 1 }));
});

test('same-tick repeated placement writes only the exact occurrence/date/revision once', async () => {
  const response = deferred<typeof draft>();
  jest.mocked(api.placeSwipeWeekWorkout).mockReturnValue(response.promise);
  await loadedDraft({ ...draft, state: 'placement', accepted_workouts: [occurrence] });
  await act(() => { flow.placeDraftWorkout(occurrence.occurrence_id, '2026-10-05'); flow.placeDraftWorkout(occurrence.occurrence_id, '2026-10-07'); });
  expect(api.placeSwipeWeekWorkout).toHaveBeenCalledTimes(1);
  expect(api.placeSwipeWeekWorkout).toHaveBeenCalledWith('token-a', draft.id, occurrence.occurrence_id, draft.revision, '2026-10-05');
  await act(() => response.resolve({ ...draft, revision: 5 }));
});

test.each(['automatic', 'manual'] as const)('same-tick duplicate %s submit is locked through persistence and clears to pending only', async (mode) => {
  const response = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal }>();
  const stored = deferred<void>();
  const deleted = deferred<void>();
  jest.mocked(api.submitSwipeWeekDraft).mockReturnValue(response.promise);
  const initial = { ...draft, state: 'placement' as const, accepted_workouts: [occurrence] };
  await loadedDraft(initial);
  jest.mocked(SecureStore.setItemAsync).mockReturnValue(stored.promise);
  jest.mocked(SecureStore.deleteItemAsync).mockReturnValue(deleted.promise);
  await act(() => { flow.submitDraft(mode); flow.submitDraft(mode); });
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, draft.revision, mode);
  await act(() => response.resolve({ plan: pendingPlan, proposal }));
  expect(flow.swipeDraft).toBe(initial); expect(flow.plan).toBeNull(); expect(flow.busy).toBe(true);
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.latest-plan-id', pendingPlan.id, { keychainAccessible: 'device-only' });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-swipe-draft-id');
  await act(() => stored.resolve());
  expect(flow.swipeDraft).toBe(initial); expect(flow.plan).toBeNull();
  await act(() => { flow.submitDraft(mode); deleted.resolve(); });
  await waitFor(() => expect(flow.swipeDraft).toBeNull());
  expect(flow.plan?.revision_state).toBe('pending_approval'); expect(flow.plan?.proposal?.state).toBe('pending');
  expect(flow.view).toBe('plan'); expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('failed mutation releases the lock but keeps exact draft and uses the safe existing error', async () => {
  await loadedDraft(draft);
  jest.mocked(api.transitionSwipeWeekDraft).mockRejectedValue(new Error('Refresh required'));
  await act(() => { flow.transitionDraft('accept'); flow.transitionDraft('pass'); });
  await waitFor(() => expect(flow.busy).toBe(false));
  expect(flow.swipeDraft).toBe(draft); expect(flow.error).toBe('Refresh required');
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValue({ ...draft, revision: 5 });
  await act(() => flow.transitionDraft('undo'));
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(2);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test('active revision is read once separately from the pending proposal; rerender preserves both', async () => {
  const view = await loadedPlan(pendingPlan);
  expect(flow.plan?.active_revision).toBe(2); expect(flow.plan?.revision).toBe(3);
  expect(flow.plan?.proposal).toBe(proposal); expect(flow.plan?.warnings).toEqual([warning]);
  expect(flow.injuries).toEqual(new Set(['run'])); expect(flow.availableDates).toEqual(activePlan.available_dates);
  await view.rerender(<Host />);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(2); expect(api.getWeeklyPlan).toHaveBeenCalledWith('token-a', 'plan-a', 2);
  expect(flow.activePlan).toBe(activePlan);
});

test('resumed draft takes precedence over remembered plan and preserves exact occurrence/placement/consent', async () => {
  const repeat = { ...occurrence, occurrence_id: 'occurrence-b' };
  const restored = { ...draft, availability_source: 'previous_week' as const, accepted_workouts: [occurrence, repeat], placements: [{ occurrence_id: repeat.occurrence_id, scheduled_date: '2026-10-07' }] };
  await loadedDraft(restored);
  expect(flow.swipeDraft).toBe(restored); expect(flow.view).toBe('deck'); expect(flow.reusePreviousWeek).toBe(true);
  expect(flow.crossTrainingOptIns).toEqual(new Set(['bike'])); expect(flow.selectedDays).toEqual(new Set([0, 2]));
  expect(flow.swipeDraft?.accepted_workouts.map((item) => item.occurrence_id)).toEqual(['occurrence-a', 'occurrence-b']);
  expect(api.getWeeklyPlan).not.toHaveBeenCalled();
});

test('submitted draft restores its plan and clears draft only after saving plan reference', async () => {
  resume('draft', draft.id);
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue({ ...draft, state: 'submitted', plan_id: activePlan.id });
  await render(<Host />);
  await waitFor(() => expect(flow.plan).toBe(activePlan));
  expect(api.getWeeklyPlan).toHaveBeenCalledWith('token-a', activePlan.id);
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.latest-plan-id', activePlan.id, { keychainAccessible: 'device-only' });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-swipe-draft-id');
  expect(flow.swipeDraft).toBeNull(); expect(flow.view).toBe('plan');
});

test('invalid or foreign cached draft is cleared, then invalid or foreign plan is cleared through the existing authenticated reads', async () => {
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async (key) => key.endsWith('draft-id') ? 'foreign-draft' : key.endsWith('plan-id') ? 'foreign-plan' : null);
  jest.mocked(api.getSwipeWeekDraft).mockRejectedValue(new Error('Safe unavailable'));
  jest.mocked(api.getWeeklyPlan).mockRejectedValue(new Error('Safe unavailable'));
  await render(<Host />);
  await waitFor(() => expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-plan-id'));
  expect(jest.mocked(SecureStore.deleteItemAsync).mock.calls).toEqual([['start23.latest-swipe-draft-id'], ['start23.latest-plan-id']]);
  expect(flow.plan).toBeNull(); expect(flow.error).toBeNull();
});

test('create forwards exact dates, injuries, opt-ins and week; persistence precedes switching to the draft', async () => {
  const saved = deferred<void>();
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  jest.mocked(SecureStore.setItemAsync).mockReturnValue(saved.promise);
  await render(<Host />);
  await act(() => { flow.setWeekStart('2026-10-05'); flow.toggleDay(2); flow.toggleDay(6); flow.toggleInjury('run'); flow.toggleCrossTraining('bike'); });
  let operation!: Promise<void>;
  await act(() => { operation = flow.generate(); });
  expect(api.createSwipeWeekDraft).toHaveBeenCalledWith('token-a', { week_start: '2026-10-05', available_dates: ['2026-10-05', '2026-10-10', '2026-10-11'], confirmed_injuries: ['run'], cross_training_opt_ins: ['bike'] });
  expect(flow.busy).toBe(true); expect(flow.swipeDraft).toBeNull();
  await act(async () => { saved.resolve(); await operation; });
  expect(flow.swipeDraft).toBe(draft); expect(flow.view).toBe('deck'); expect(flow.busy).toBe(false);
});

test('active-bound creation supplies active revision; explicit reuse omits dates and injury toggle removes that opt-in', async () => {
  await loadedPlan();
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  await act(() => { flow.setReusePreviousWeek(true); flow.toggleCrossTraining('bike'); flow.toggleInjury('bike'); });
  await act(async () => { await flow.generate(); });
  expect(api.createSwipeWeekDraft).toHaveBeenCalledWith('token-a', { week_start: activePlan.week_start, reuse_previous_week: true, confirmed_injuries: ['run', 'bike'], cross_training_opt_ins: [], plan_id: activePlan.id, expected_base_revision: 2 });
});

test.each(['accept', 'pass', 'undo', 'reset_passed'] as const)('%s uses exact current draft revision and occurrence only when required; rerender never retries', async (action) => {
  const view = await loadedDraft();
  const request = deferred<typeof draft>();
  jest.mocked(api.transitionSwipeWeekDraft).mockReturnValue(request.promise);
  await act(() => flow.transitionDraft(action));
  expect(flow.busy).toBe(true);
  await view.rerender(<Host />);
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, { expected_revision: 4, action, ...(['accept', 'pass'].includes(action) ? { candidate_template_id: occurrence.id, candidate_occurrence_id: occurrence.occurrence_id } : {}) });
  const updated = { ...draft, revision: 5, current_candidate: { ...occurrence, occurrence_id: 'occurrence-b' }, accepted_workouts: [occurrence] };
  await act(async () => request.resolve(updated));
  expect(flow.swipeDraft).toBe(updated); expect(flow.busy).toBe(false);
});

test('repeated template accept and same-date manual placements retain independent occurrence identities and successive revisions', async () => {
  await loadedDraft();
  const second = { ...occurrence, occurrence_id: 'occurrence-b' };
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValueOnce({ ...draft, revision: 5, accepted_workouts: [occurrence], current_candidate: second });
  await act(() => flow.transitionDraft('accept'));
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValueOnce({ ...draft, revision: 6, state: 'placement', accepted_workouts: [occurrence, second], current_candidate: null });
  await act(() => flow.transitionDraft('accept'));
  expect(jest.mocked(api.transitionSwipeWeekDraft).mock.calls[1][2]).toEqual({ expected_revision: 5, action: 'accept', candidate_template_id: second.id, candidate_occurrence_id: second.occurrence_id });
  for (const id of ['occurrence-a', 'occurrence-b']) {
    const previous = flow.swipeDraft!;
    jest.mocked(api.placeSwipeWeekWorkout).mockResolvedValueOnce({ ...previous, revision: previous.revision + 1, placements: [...previous.placements, { occurrence_id: id, scheduled_date: '2026-10-07' }] });
    await act(() => flow.placeDraftWorkout(id, '2026-10-07'));
    expect(api.placeSwipeWeekWorkout).toHaveBeenLastCalledWith('token-a', draft.id, previous.revision === 6 ? 'occurrence-a' : 'occurrence-b', previous.revision, '2026-10-07');
  }
  expect(flow.swipeDraft?.placements).toHaveLength(2);
  await act(() => flow.transitionDraft('accept'));
  expect(api.transitionSwipeWeekDraft).toHaveBeenCalledTimes(2);
});

test.each(['automatic', 'manual'] as const)('%s submit runs once, saves both resume references before clearing draft, and stays pending', async (mode) => {
  const view = await loadedDraft({ ...draft, state: 'placement' });
  const request = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal; }>();
  jest.mocked(api.submitSwipeWeekDraft).mockReturnValue(request.promise);
  await act(() => flow.submitDraft(mode));
  await view.rerender(<Host />);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
  expect(api.submitSwipeWeekDraft).toHaveBeenCalledWith('token-a', draft.id, 4, mode);
  await act(async () => request.resolve({ plan: pendingPlan, proposal }));
  expect(flow.swipeDraft).toBeNull(); expect(flow.plan).toBe(pendingPlan); expect(flow.view).toBe('plan');
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.latest-plan-id', pendingPlan.id, { keychainAccessible: 'device-only' });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-swipe-draft-id');
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test.each(['approve', 'reject'] as const)('%s preserves mutation-then-read order and its precise read revision; rerender does not repeat', async (action) => {
  const view = await loadedPlan(pendingPlan);
  const request = deferred<void>();
  const mutation = action === 'approve' ? api.approvePlanProposal : api.rejectPlanProposal;
  jest.mocked(api.approvePlanProposal).mockImplementation(async () => { await request.promise; return { state: 'applied', plan_id: pendingPlan.id, active_revision: 3 }; });
  jest.mocked(api.rejectPlanProposal).mockImplementation(async () => { await request.promise; return { state: 'rejected', plan_id: pendingPlan.id }; });
  await act(() => flow[action]());
  await view.rerender(<Host />);
  expect(mutation).toHaveBeenCalledTimes(1); expect(api.getWeeklyPlan).toHaveBeenCalledTimes(2);
  if (action === 'approve') expect(mutation).toHaveBeenCalledWith('token-a', proposal.id, 2);
  else expect(mutation).toHaveBeenCalledWith('token-a', proposal.id);
  const result = action === 'approve' ? activePlan : { ...pendingPlan, revision_state: 'rejected' as const };
  jest.mocked(api.getWeeklyPlan).mockResolvedValueOnce(result);
  await act(async () => request.resolve());
  expect(jest.mocked(api.getWeeklyPlan).mock.calls[2]).toEqual(action === 'approve' ? ['token-a', pendingPlan.id] : ['token-a', pendingPlan.id, 3]);
  expect(flow.plan).toBe(result); expect(flow.busy).toBe(false);
});

test('stale approve keeps reviewed proposal/warnings, reports safe error and never refreshes/reapproves implicitly', async () => {
  const view = await loadedPlan(pendingPlan);
  jest.mocked(api.approvePlanProposal).mockRejectedValue(new Error('Je week is gewijzigd.'));
  await act(() => flow.approve()); await view.rerender(<Host />);
  expect(flow.plan).toBe(pendingPlan); expect(flow.error).toBe('Je week is gewijzigd.'); expect(flow.busy).toBe(false);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1); expect(api.getWeeklyPlan).toHaveBeenCalledTimes(2);
});

test('alternatives and edits use options proposal/revision, preserve can_remove, and keep slot loading separate', async () => {
  await loadedPlan(pendingPlan);
  const options: PendingWorkoutAlternatives = { plan_id: pendingPlan.id, revision: 8, proposal_id: 'options-proposal', workout_id: workout.id, can_remove: false, alternatives: [occurrence] };
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(options);
  await act(async () => { await flow.pendingWorkouts.load(workout.id); });
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, 3);
  expect(flow.pendingWorkouts.editors[workout.id].options?.can_remove).toBe(false);
  const request = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal; }>();
  jest.mocked(api.editPendingWorkout).mockReturnValue(request.promise);
  let operation!: Promise<boolean>;
  await act(() => { operation = flow.pendingWorkouts.apply(workout.id, occurrence.id); });
  expect(flow.busy).toBe(false); expect(flow.pendingWorkouts.editors[workout.id].loading).toBe(true);
  expect(api.editPendingWorkout).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, { expected_revision: 8, expected_proposal_id: 'options-proposal', replacement_template_id: occurrence.id });
  const updated = { ...pendingPlan, revision: 9 };
  await act(async () => { request.resolve({ plan: updated, proposal }); await operation; });
  expect(flow.plan).toBe(updated);
  await act(() => flow.pendingWorkouts.release(workout.id));
  expect(flow.pendingWorkouts.editors[workout.id]).toBeUndefined();
});

test('move validates complete layout with active revision, retains warning for cancel/confirm, and commits only server result', async () => {
  const sibling = { ...workout, id: 'workout-b' };
  await loadedPlan({ ...activePlan, workouts: [workout, sibling] });
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: false, warnings: [warning] });
  await act(() => flow.requestWorkoutMove(workout, '2026-10-10'));
  expect(api.validatePlanLayout).toHaveBeenCalledWith('token-a', activePlan.id, 2, [{ workout_id: workout.id, scheduled_date: '2026-10-10' }, { workout_id: sibling.id, scheduled_date: sibling.scheduled_date }]);
  expect(flow.pendingMove?.warnings).toEqual([warning]); expect(api.movePlannedWorkout).not.toHaveBeenCalled();
  await act(() => flow.cancelWorkoutMove()); expect(flow.pendingMove).toBeNull();
  await act(() => flow.requestWorkoutMove(workout, '2026-10-10'));
  const updated = { ...activePlan, revision: 3, active_revision: 3, workouts: [{ ...workout, scheduled_date: '2026-10-10' }] };
  jest.mocked(api.movePlannedWorkout).mockResolvedValue(updated);
  await act(() => flow.confirmWorkoutMove());
  expect(api.movePlannedWorkout).toHaveBeenCalledWith('token-a', workout.id, 2, '2026-10-10');
  expect(flow.plan).toBe(updated); expect(flow.pendingMove).toBeNull();
});

test('warning-free move validates before write; invalid date and server stale/rejection never change placement', async () => {
  await loadedPlan();
  await act(() => flow.requestWorkoutMove(workout, '2026-10-12'));
  expect(api.validatePlanLayout).not.toHaveBeenCalled(); expect(flow.error).toMatch(/geldige datum/);
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: true, warnings: [] });
  jest.mocked(api.movePlannedWorkout).mockRejectedValue(new Error('Safe move rejected'));
  await act(() => flow.requestWorkoutMove(workout, '2026-10-10'));
  expect(jest.mocked(api.validatePlanLayout).mock.invocationCallOrder[0]).toBeLessThan(jest.mocked(api.movePlannedWorkout).mock.invocationCallOrder[0]);
  expect(flow.plan).toBe(activePlan); expect(flow.error).toBe('Safe move rejected'); expect(flow.busy).toBe(false);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});

test('calendar reads remain independent of mutation busy; latest range wins across success, failure and finally', async () => {
  const view = await loadedDraft();
  const swipe = deferred<typeof draft>();
  const old = deferred<CalendarResponse>(); const latest = deferred<CalendarResponse>();
  jest.mocked(api.transitionSwipeWeekDraft).mockReturnValue(swipe.promise);
  jest.mocked(api.getCalendar).mockReturnValueOnce(old.promise).mockReturnValueOnce(latest.promise);
  await act(() => { flow.transitionDraft('pass'); calendar.loadCalendarRange('2026-10-05', '2026-10-12'); });
  expect(flow.busy).toBe(true); expect(calendar.calendarLoading).toBe(true);
  await act(() => calendar.loadCalendarRange('2026-10-12', '2026-10-19'));
  await act(async () => old.reject(new Error('Old range failed')));
  expect(flow.error).toBeNull(); expect(calendar.calendarLoading).toBe(true);
  await act(async () => latest.resolve({ from_date: '2026-10-12', to_date: '2026-10-19', workouts: [workout], rest_days: [{ date: '2026-10-13', reason: 'planned_rest' }] }));
  expect(calendar.calendarWorkouts).toEqual([workout]); expect(calendar.calendarLoading).toBe(false); expect(flow.busy).toBe(true);
  await view.rerender(<Host />);
  expect(jest.mocked(api.getCalendar).mock.calls).toEqual([['token-a', '2026-10-05', '2026-10-12'], ['token-a', '2026-10-12', '2026-10-19']]);
  await act(async () => swipe.resolve(draft)); expect(flow.busy).toBe(false);
});

test('identity change resets flow; token rotation preserves edits and owner identity; unmount/reentry keeps existing persistence semantics', async () => {
  const view = await loadedPlan();
  await act(() => flow.toggleCrossTraining('bike'));
  await view.rerender(<Host token="token-b" />);
  expect(flow.crossTrainingOptIns).toEqual(new Set(['bike'])); expect(flow.plan).toBe(activePlan);
  await waitFor(() => expect(api.getWeeklyPlan).toHaveBeenCalledWith('token-b', activePlan.id));
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  await view.rerender(<Host token="token-c" identity="athlete-b" />);
  expect(flow.plan).toBeNull(); expect(flow.swipeDraft).toBeNull(); expect(flow.crossTrainingOptIns.size).toBe(0);
  await view.unmount();
  // Baseline sign-out does not clear plan/draft storage; server ownership validates on resume.
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
  await loadedPlan(); expect(flow.plan).toBe(activePlan);
});

test('nested providers fail before creating a second owner', async () => {
  const quiet = jest.spyOn(console, 'error').mockImplementation(() => undefined);
  try {
    await expect(render(<Host><PlanningFlowProvider accessToken="token-a"><Probe /></PlanningFlowProvider></Host>)).rejects.toThrow('already has an owner');
    expect(api.getOnboarding).not.toHaveBeenCalled();
  } finally { quiet.mockRestore(); }
});

test('incomplete submit and capacity failure keep original draft, warnings and safe error without recovery/retry', async () => {
  const view = await loadedDraft();
  jest.mocked(api.submitSwipeWeekDraft).mockRejectedValue(new Error('Safe incomplete placement'));
  await act(() => flow.submitDraft('manual'));
  expect(flow.swipeDraft).toBe(draft); expect(flow.error).toBe('Safe incomplete placement');
  expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
  jest.mocked(api.createSwipeWeekDraft).mockRejectedValue(new Error('Safe catalog capacity message'));
  await act(async () => { await flow.generate(); });
  await view.rerender(<Host />);
  expect(flow.error).toBe('Safe catalog capacity message'); expect(flow.swipeDraft?.warnings).toEqual([warning]);
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1); expect(api.submitSwipeWeekDraft).toHaveBeenCalledTimes(1);
});

test('pending editor stale response preserves reviewed options and plan without refetching or losing can_remove', async () => {
  await loadedPlan(pendingPlan);
  const options: PendingWorkoutAlternatives = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: true, alternatives: [occurrence] };
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(options);
  await act(async () => { await flow.pendingWorkouts.load(workout.id); });
  jest.mocked(api.editPendingWorkout).mockRejectedValue(new Error('Safe stale alternatives'));
  await act(async () => { await flow.pendingWorkouts.apply(workout.id, null); });
  expect(api.editPendingWorkout).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, { expected_revision: 3, expected_proposal_id: proposal.id, replacement_template_id: null });
  expect(flow.pendingWorkouts.editors[workout.id]).toEqual({ options, loading: false });
  expect(flow.plan).toBe(pendingPlan); expect(flow.error).toBe('Safe stale alternatives');
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
});

test('rejected confirmed move retains reviewable warning until existing cancel or explicit retry', async () => {
  await loadedPlan();
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: false, warnings: [warning] });
  await act(() => flow.requestWorkoutMove(workout, '2026-10-10'));
  const pending = flow.pendingMove;
  jest.mocked(api.movePlannedWorkout).mockRejectedValue(new Error('Safe stale move'));
  await act(() => flow.confirmWorkoutMove());
  expect(flow.pendingMove).toBe(pending); expect(flow.plan).toBe(activePlan); expect(flow.error).toBe('Safe stale move');
  expect(api.validatePlanLayout).toHaveBeenCalledTimes(1); expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
  await act(() => flow.cancelWorkoutMove()); expect(flow.pendingMove).toBeNull();
});

test('late calendar success cannot replace newer failure or clear its error/loading state', async () => {
  await render(<Host />);
  const old = deferred<CalendarResponse>(); const latest = deferred<CalendarResponse>();
  jest.mocked(api.getCalendar).mockReturnValueOnce(old.promise).mockReturnValueOnce(latest.promise);
  await act(() => { calendar.loadCalendarRange('2026-10-05', '2026-10-12'); calendar.loadCalendarRange('2026-10-12', '2026-10-19'); });
  await act(async () => latest.reject(new Error('Safe latest range error')));
  await act(async () => old.resolve({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [workout], rest_days: [] }));
  expect(calendar.calendarWorkouts).toEqual([]); expect(calendar.calendarLoading).toBe(false);
  expect(flow.error).toBe('Safe latest range error'); expect(flow.busy).toBe(false);
});

test('clear rejected plan keeps original storage key and resets only the plan', async () => {
  await loadedPlan({ ...pendingPlan, revision_state: 'rejected' });
  await act(() => flow.clearPlan());
  expect(flow.plan).toBeNull(); expect(flow.weekStart).toBe('2026-10-05'); expect(flow.injuries).toEqual(new Set(['run']));
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-plan-id');
});

test('released pending editor discards late local options/loading without contaminating its remount', async () => {
  await loadedPlan(pendingPlan);
  const old = deferred<PendingWorkoutAlternatives>();
  const current = deferred<PendingWorkoutAlternatives>();
  jest.mocked(api.getPendingWorkoutAlternatives).mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise);
  let first!: Promise<boolean>; let second!: Promise<boolean>;
  await act(() => { first = flow.pendingWorkouts.load(workout.id); });
  await act(() => flow.pendingWorkouts.release(workout.id));
  await act(() => { second = flow.pendingWorkouts.load(workout.id); });
  const options: PendingWorkoutAlternatives = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: false, alternatives: [] };
  await act(async () => { old.resolve(options); await first; });
  expect(flow.pendingWorkouts.editors[workout.id]).toEqual({ options: null, loading: true });
  await act(async () => { current.resolve(options); await second; });
  expect(flow.pendingWorkouts.editors[workout.id]).toEqual({ options, loading: false });
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(2);
});

test('failed resume exposes uncertainty without changing reference clearing or retrying on rerender', async () => {
  resume('plan', activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockRejectedValue(new Error('Safe transport error'));
  const view = await render(<Host />);
  await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(flow.plan).toBeNull();
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-plan-id');
  await view.rerender(<Host />);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});
test('late active-revision read cannot cross an identity reset', async () => {
  const request = deferred<typeof activePlan>();
  resume('plan', pendingPlan.id);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? request.promise : pendingPlan);
  const view = await render(<Host />);
  await waitFor(() => expect(flow.activeReadState).toBe('loading'));
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  await view.rerender(<Host identity="athlete-b" token="token-b" />);
  await act(async () => request.resolve(activePlan));
  expect(flow.plan).toBeNull(); expect(flow.activePlan).toBeNull();
});


test('Slice 4B alternatives deduplicate same-tick load, rerender and shared decision while unresolved', async () => {
  const view = await loadedPlan(pendingPlan);
  const options: PendingWorkoutAlternatives = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: false, alternatives: [occurrence] };
  const request = deferred<PendingWorkoutAlternatives>(); jest.mocked(api.getPendingWorkoutAlternatives).mockReturnValue(request.promise);
  let first!: Promise<boolean>;
  await act(() => { first = flow.pendingWorkouts.load(workout.id); void flow.pendingWorkouts.load(workout.id); flow.approve(); flow.reject(); });
  await view.rerender(<Host />);
  expect(api.getPendingWorkoutAlternatives).toHaveBeenCalledTimes(1);
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
  await act(async () => { request.resolve(options); await first; });
  expect(flow.pendingWorkouts.editors[workout.id]).toEqual({ options, loading: false });
});
test.each(['replacement', 'removal'] as const)('Slice 4B %s has one shared synchronous lock across duplicate/edit/approve/reject', async action => {
  await loadedPlan(pendingPlan);
  const options: PendingWorkoutAlternatives = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: true, alternatives: [occurrence] };
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(options);
  await act(async () => { await flow.pendingWorkouts.load(workout.id); });
  const request = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal }>(); jest.mocked(api.editPendingWorkout).mockReturnValue(request.promise);
  let operation!: Promise<boolean>;
  const replacement = action === 'removal' ? null : occurrence.id;
  await act(() => { operation = flow.pendingWorkouts.apply(workout.id, replacement); void flow.pendingWorkouts.apply(workout.id, replacement); flow.approve(); flow.reject(); });
  expect(api.editPendingWorkout).toHaveBeenCalledTimes(1); expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
  expect(api.editPendingWorkout).toHaveBeenCalledWith('token-a', pendingPlan.id, workout.id, { expected_revision: 3, expected_proposal_id: proposal.id, replacement_template_id: replacement });
  const result = { ...pendingPlan, revision: 4, proposal: { ...proposal, id: 'new-proposal' } };
  await act(async () => { request.resolve({ plan: result, proposal: result.proposal }); expect(await operation).toBe(true); });
  expect(flow.plan).toBe(result);
});
test.each([false, undefined])('Slice 4B cannot remove with unknown/false capability %s or choose unreturned template', async can_remove => {
  await loadedPlan(pendingPlan);
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: can_remove as boolean, alternatives: [occurrence] });
  await act(async () => { await flow.pendingWorkouts.load(workout.id); await flow.pendingWorkouts.apply(workout.id, null); await flow.pendingWorkouts.apply(workout.id, 'not-returned'); });
  expect(api.editPendingWorkout).not.toHaveBeenCalled();
});
test.each(['approve', 'reject'] as const)('Slice 4B rapid %s and cross-decision writes execute only one exact transaction', async action => {
  await loadedPlan(pendingPlan);
  const gate = deferred<void>();
  jest.mocked(api.approvePlanProposal).mockImplementation(async () => { await gate.promise; return { state: 'applied', plan_id: pendingPlan.id, active_revision: 3 }; });
  jest.mocked(api.rejectPlanProposal).mockImplementation(async () => { await gate.promise; return { state: 'rejected', plan_id: pendingPlan.id }; });
  await act(() => { flow[action](); flow[action](); flow[action === 'approve' ? 'reject' : 'approve'](); });
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(action === 'approve' ? 1 : 0); expect(api.rejectPlanProposal).toHaveBeenCalledTimes(action === 'reject' ? 1 : 0);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  await act(async () => gate.resolve());
});
test.each(['expired', 'superseded', 'rejected', 'active'] as const)('Slice 4B %s snapshot cannot approve/reject even if old proposal ID is present', async revision_state => {
  await loadedPlan({ ...pendingPlan, revision_state });
  await act(() => { flow.approve(); flow.reject(); });
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
});
test('Slice 4B callbacks from an old snapshot cannot act after authoritative replacement', async () => {
  await loadedPlan(pendingPlan); const oldApprove = flow.approve; const oldReject = flow.reject;
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: false, alternatives: [occurrence] });
  await act(async () => { await flow.pendingWorkouts.load(workout.id); });
  const next = { ...pendingPlan, revision: 4, proposal: { ...proposal, id: 'new-proposal' } };
  jest.mocked(api.editPendingWorkout).mockResolvedValue({ plan: next, proposal: next.proposal });
  await act(async () => { await flow.pendingWorkouts.apply(workout.id, occurrence.id); });
  await act(() => { oldApprove(); oldReject(); });
  expect(flow.plan).toBe(next); expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(api.rejectPlanProposal).not.toHaveBeenCalled();
});
test('Slice 4B late options and edit acknowledgments cannot resurrect a cleared/replaced reviewed snapshot', async () => {
  await loadedPlan(pendingPlan);
  const options = { plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: true, alternatives: [occurrence] };
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(options);
  await act(async () => { await flow.pendingWorkouts.load(workout.id); });
  const request = deferred<{ plan: typeof pendingPlan; proposal: typeof proposal }>(); jest.mocked(api.editPendingWorkout).mockReturnValue(request.promise);
  let operation!: Promise<boolean>;
  await act(() => { operation = flow.pendingWorkouts.apply(workout.id, occurrence.id); });
  await act(() => flow.clearPlan());
  await act(async () => { request.resolve({ plan: pendingPlan, proposal }); expect(await operation).toBe(false); });
  expect(flow.plan).toBeNull();
});
