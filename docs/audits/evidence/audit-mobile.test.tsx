// Audit-only characterization tests: assertions describe defects, not acceptance.
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import * as api from '../../../mobile/src/api/client';
import { LanguageProvider } from '../../../mobile/src/i18n/LanguageProvider';
import { PlanningFlowProvider, usePlanningFlow } from '../../../mobile/src/features/planning/PlanningFlowProvider';
import { ActivityFlowProvider, useActivityFlow } from '../../../mobile/src/features/activities/ActivityFlowProvider';
import { activePlan, draft, onboarding, pendingPlan } from '../../../mobile/src/features/planning/planning.test-fixtures';
import { CheckInScreen } from '../../../mobile/src/screens/CheckInScreen';
import checkinFixtures from '../../ui/evidence/final-visual-batch-12/public-fixtures.json';
import type { WeeklyCheckIn } from '../../../mobile/src/api/types';
import { activityOnboarding, pendingActivity } from '../../../mobile/src/features/activities/activities.test-fixtures';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device-only' }));
jest.mock('../../../mobile/src/api/client', () => ({
  approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(), getCalendar: jest.fn(),
  getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(), getSwipeWeekDraft: jest.fn(), getWeeklyPlan: jest.fn(),
  markGoalAchieved: jest.fn(), movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(), rejectPlanProposal: jest.fn(),
  submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
  startWeeklyCheckIn: jest.fn(), saveWeeklyCheckInContext: jest.fn(), confirmWeeklyCheckInContext: jest.fn(), createCheckInPlanProposal: jest.fn(), extractWeeklyCheckInContextCandidate: jest.fn(),
  confirmActivityMatch: jest.fn(), createActivity: jest.fn(), listActivities: jest.fn(), listPlannedExternalActivities: jest.fn(), submitActivityRpeWithRefresh: jest.fn(),
}));

let planFlow: ReturnType<typeof usePlanningFlow>;
let activityFlow: ReturnType<typeof useActivityFlow>;
function PlanProbe() { planFlow = usePlanningFlow(); return null; }
function ActivityProbe() { activityFlow = useActivityFlow(); return null; }
function PlanHost({ identity = 'athlete-a', token = 'token-a' }: { identity?: string; token?: string }) {
  return <LanguageProvider><PlanningFlowProvider athleteIdentity={identity} accessToken={token}><PlanProbe /></PlanningFlowProvider></LanguageProvider>;
}
function ActivityHost() { return <ActivityFlowProvider athleteIdentity="athlete-a" accessToken="token-a"><ActivityProbe /></ActivityFlowProvider>; }
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(yes => { resolve = yes; }); return { resolve, promise }; }
let storage: Map<string, string>;
beforeEach(() => {
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  storage = new Map();
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async key => storage.get(key) ?? null);
  jest.mocked(SecureStore.setItemAsync).mockImplementation(async (key, value) => { storage.set(key, value); });
  jest.mocked(SecureStore.deleteItemAsync).mockImplementation(async key => { storage.delete(key); });
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-10-01', to_date: '2026-11-01', workouts: [], rest_days: [] });
  jest.mocked(api.listActivities).mockResolvedValue([]);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
});

test('AUD-001: a transient resume failure deletes the sole saved plan locator', async () => {
  storage.set('start23.latest-plan-id', activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockRejectedValue(Object.assign(new Error('Offline'), { status: null }));
  const view = await render(<PlanHost />);
  await waitFor(() => expect(planFlow.resumeState).toBe('failed'));
  expect(storage.has('start23.latest-plan-id')).toBe(false);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  await view.rerender(<PlanHost token="refreshed-token" />);
  await waitFor(() => expect(planFlow.resumeState).toBe('ready'));
  expect(planFlow.plan).toBeNull();
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1);
});

test('AUD-002: switching accounts destroys the previous accounts unscoped locator', async () => {
  storage.set('start23.latest-plan-id', activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async token => {
    if (token === 'token-a') return activePlan;
    throw Object.assign(new Error('Not found'), { status: 404 });
  });
  const view = await render(<PlanHost />);
  await waitFor(() => expect(planFlow.plan).toBe(activePlan));
  await view.rerender(<PlanHost identity="athlete-b" token="token-b" />);
  await waitFor(() => expect(planFlow.resumeState).toBe('ready'));
  expect(storage.has('start23.latest-plan-id')).toBe(false);
  await view.rerender(<PlanHost identity="athlete-a" token="token-a" />);
  await waitFor(() => expect(planFlow.resumeState).toBe('ready'));
  expect(planFlow.plan).toBeNull();
});

test('AUD-003: completion of an old accounts generate writes the global locator after switch', async () => {
  const response = deferred<typeof draft>();
  jest.mocked(api.createSwipeWeekDraft).mockReturnValue(response.promise);
  const view = await render(<PlanHost />);
  await waitFor(() => expect(planFlow.resumeState).toBe('ready'));
  let write!: Promise<void>;
  await act(() => { write = planFlow.generate(); });
  await view.rerender(<PlanHost identity="athlete-b" token="token-b" />);
  await waitFor(() => expect(planFlow.resumeState).toBe('ready'));
  await act(async () => { response.resolve(draft); await write; });
  expect(storage.get('start23.latest-swipe-draft-id')).toBe(draft.id);
  expect(planFlow.swipeDraft).toBeNull();
});

test('AUD-004: a pending reminder from another device cannot be completed from cached history', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  await render(<ActivityHost />);
  await act(() => activityFlow.ensureActivitiesLoaded());
  expect(activityFlow.activities).toEqual([]);
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  await act(() => activityFlow.refreshPendingRpe('/activities'));
  expect(activityFlow.feedbackActivity?.id).toBe(pendingActivity.id);
  await act(() => activityFlow.saveRpe(pendingActivity.id, 4));
  expect(activityFlow.error).toBe('De activiteit is niet meer beschikbaar.');
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  await act(() => activityFlow.ensureActivitiesLoaded());
  expect(activityFlow.activities).toEqual([]);
});

test('AUD-005: an initial history read remains cached after subsequent Activities entries', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  await render(<ActivityHost />);
  await act(() => activityFlow.ensureActivitiesLoaded());
  const firstCalls = jest.mocked(api.getCalendar).mock.calls.length;
  await act(() => activityFlow.ensureActivitiesLoaded());
  expect(api.getCalendar).toHaveBeenCalledTimes(firstCalls);
});

test('AUD-006 CONTROL: committed approval recovers through the backends idempotent retry contract', async () => {
  storage.set('start23.latest-plan-id', pendingPlan.id);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, _id, revision) => revision === 2 ? activePlan : pendingPlan);
  await render(<PlanHost />);
  await waitFor(() => expect(planFlow.plan).toBe(pendingPlan));
  jest.mocked(api.getWeeklyPlan).mockRejectedValue(new Error('Offline after approval'));
  jest.mocked(api.approvePlanProposal).mockResolvedValue(undefined as never);
  await act(() => planFlow.approve());
  await waitFor(() => expect(planFlow.error).toBe('Offline after approval'));
  const readCount = jest.mocked(api.getWeeklyPlan).mock.calls.length;
  jest.mocked(api.approvePlanProposal).mockResolvedValue(undefined as never);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue({ ...activePlan, revision: 3, active_revision: 3 });
  await act(() => planFlow.approve());
  await waitFor(() => expect(planFlow.plan?.revision_state).toBe('active'));
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(readCount + 1);
});

test('AUD-007: reopening saved restricted context displays and resaves an unrestricted answer', async () => {
  const saved = checkinFixtures.saved as WeeklyCheckIn;
  const restricted = { ...saved, context: { ...saved.context!, restrictions: [{
    discipline: 'run' as const, status: 'self_reported_blocked' as const,
    source: 'athlete' as const, athlete_plan_choice: 'keep_blocked' as const,
  }], alarm_symptoms_acknowledged: true } };
  jest.mocked(api.startWeeklyCheckIn).mockResolvedValue(restricted);
  jest.mocked(api.saveWeeklyCheckInContext).mockResolvedValue(restricted);
  const view = await render(<CheckInScreen accessToken="token-a" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} />);
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Week van ' + saved.week_start);
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).toBeChecked();
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  expect(api.saveWeeklyCheckInContext).toHaveBeenCalledWith('token-a', saved.id, expect.objectContaining({
    restrictions: expect.arrayContaining([expect.objectContaining({ discipline: 'run', status: 'none', athlete_plan_choice: 'resume_unrestricted' })]),
    alarm_symptoms_acknowledged: false,
  }));
});

test('AUD-008: check-in approval neither updates the retained planning owner nor its saved locator', async () => {
  storage.set('start23.latest-plan-id', activePlan.id);
  const nextPlan = { ...pendingPlan, id: 'next-week-plan', week_start: '2026-10-12' };
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(activePlan);
  jest.mocked(api.startWeeklyCheckIn).mockResolvedValue(checkinFixtures.confirmed as WeeklyCheckIn);
  jest.mocked(api.createCheckInPlanProposal).mockResolvedValue({ plan: nextPlan, proposal: nextPlan.proposal! });
  jest.mocked(api.approvePlanProposal).mockResolvedValue(undefined as never);
  const back = jest.fn();
  const view = await render(<LanguageProvider><PlanningFlowProvider athleteIdentity="athlete-a" accessToken="token-a">
    <PlanProbe /><CheckInScreen accessToken="token-a" onBack={back} onSignOut={jest.fn(async () => undefined)} />
  </PlanningFlowProvider></LanguageProvider>);
  await waitFor(() => expect(planFlow.plan).toBe(activePlan));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByRole('button', { name: 'Maak planvoorstel' });
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await view.findByRole('button', { name: 'Voorstel goedkeuren' });
  const reads = jest.mocked(api.getWeeklyPlan).mock.calls.length;
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await waitFor(() => expect(back).toHaveBeenCalledTimes(1));
  expect(planFlow.plan).toBe(activePlan);
  expect(storage.get('start23.latest-plan-id')).toBe(activePlan.id);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(reads);
});
