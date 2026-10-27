import { act, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { AppState, type AppStateStatus } from 'react-native';

import * as api from '../../api/client';
import type { PlanningRecovery, SwipeWeekDraft, WeeklyPlan } from '../../api/types';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from './PlanningFlowProvider';
import { latestPlanIdKey, latestSwipeDraftIdKey, scopedResumeKey } from './planningResume';
import { activePlan, draft, onboarding, pendingPlan } from './planning.test-fixtures';
import { approvedNext, pendingNext } from './planningTask.test-fixtures';
import { weekHomeViewModel } from '../../ui-v2/utils/weekHomeViewModel';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../../api/client');
let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let storage: Map<string, string>;
let plans: Map<string, WeeklyPlan>;
let drafts: Map<string, SwipeWeekDraft>;
let recoveries: Map<string, PlanningRecovery>;
let onForeground: (state: AppStateStatus) => void;
const key = (owner = 'athlete-a', kind = latestPlanIdKey) => scopedResumeKey(owner, kind);
const bPlan: WeeklyPlan = { ...activePlan, id: 'plan-b', revision_id: 'revision-b' };
const notFound = () => Object.assign(new Error('Planning resource not found'), { status: 404 });
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function Probe() { flow = usePlanningFlow(); calendar = usePlanningCalendar(); return null; }
function Host({ owner = 'athlete-a', token = owner }: { owner?: string; token?: string }) {
  return <LanguageProvider><PlanningFlowProvider athleteIdentity={owner} accessToken={token}><Probe /></PlanningFlowProvider></LanguageProvider>;
}
async function ready() { await waitFor(() => expect(flow.resumeState).toBe('ready')); }
beforeEach(() => {
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  storage = new Map(); plans = new Map([[activePlan.id, activePlan], [bPlan.id, bPlan]]); drafts = new Map([[draft.id, draft]]);
  recoveries = new Map([
    ['athlete-a', { active: null, pending: null, draft: null }],
    ['athlete-b', { active: bPlan, pending: null, draft: null }],
  ]);
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_event, callback) => {
    onForeground = callback; return { remove: jest.fn() };
  });
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async k => storage.get(k) ?? null);
  jest.mocked(SecureStore.setItemAsync).mockImplementation(async (k, value) => { storage.set(k, value); });
  jest.mocked(SecureStore.deleteItemAsync).mockImplementation(async k => { storage.delete(k); });
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.discoverPlanning).mockImplementation(async token => recoveries.get(token)!);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (token, id, revision) => {
    if ((token === 'athlete-b') !== (id === bPlan.id)) throw notFound();
    const value = plans.get(id);
    if (!value) throw notFound();
    return revision === activePlan.revision && id === activePlan.id ? activePlan : value;
  });
  jest.mocked(api.getSwipeWeekDraft).mockImplementation(async (token, id) => {
    if (token !== 'athlete-a' || !drafts.has(id)) throw notFound(); return drafts.get(id)!;
  });
});
afterEach(() => jest.restoreAllMocks());

test('normal local resume and process restart verify the same owner identity', async () => {
  storage.set(key(), activePlan.id);
  const view = await render(<Host />); await ready();
  expect(flow.activePlan).toBe(activePlan); expect(flow.injuries).toEqual(new Set(['run']));
  await view.unmount(); await render(<Host />); await ready();
  expect(flow.plan).toBe(activePlan); expect(storage.get(key())).toBe(activePlan.id);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test.each([
  ['offline', new Error('Offline')], ['timeout', new Error('Timeout')],
  ['500', Object.assign(new Error('Unavailable'), { status: 500 })],
  ['502', Object.assign(new Error('Unavailable'), { status: 502 })],
  ['503', Object.assign(new Error('Unavailable'), { status: 503 })],
  ['auth', Object.assign(new Error('Auth unavailable'), { status: 401 })],
  ['forbidden', Object.assign(new Error('Denied'), { status: 403 })],
  ['malformed', new SyntaxError('Malformed response')],
])('%s read preserves locator, unknown state and explicit retry', async (_name, error) => {
  storage.set(key(), activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockRejectedValueOnce(error);
  await render(<Host />);
  await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(storage.get(key())).toBe(activePlan.id); expect(flow.plan).toBeNull();
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
  const model = weekHomeViewModel({ plan: flow.plan, activePlan: flow.activePlan, draft: flow.swipeDraft, today: '2026-10-05', resumeState: flow.resumeState, activeReadState: flow.activeReadState });
  expect(model.empty).toBeNull(); expect(model.mainAction).toBeNull();
  await act(() => flow.retryResume()); await ready();
  expect(flow.activePlan).toBe(activePlan); expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test('transient draft read retains both locators and last verified plan', async () => {
  storage.set(key(), activePlan.id); storage.set(key('athlete-a', latestSwipeDraftIdKey), draft.id);
  jest.mocked(api.getSwipeWeekDraft).mockRejectedValueOnce(new Error('Offline'));
  await render(<Host />); await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(flow.plan).toBe(activePlan); expect(storage.size).toBe(2);
  await act(() => flow.retryResume()); await ready(); expect(flow.swipeDraft).toBe(draft);
});

test.each(['missing', 'foreign'])('definitive %s locator is removed only from this owner before empty discovery', async kind => {
  storage.set(key(), kind === 'foreign' ? bPlan.id : 'missing'); storage.set(key('athlete-b'), bPlan.id);
  await render(<Host />); await ready();
  expect(flow.plan).toBeNull(); expect(storage.has(key())).toBe(false); expect(storage.get(key('athlete-b'))).toBe(bPlan.id);
  expect(api.discoverPlanning).toHaveBeenCalledWith('athlete-a');
});

test('valid empty discovery permits existing empty state without creating anything', async () => {
  await render(<Host />); await ready(); expect(flow.plan).toBeNull(); expect(flow.swipeDraft).toBeNull();
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled(); expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
});

test.each(['reinstall', 'second device', 'web/no local locator'])('%s discovers the active authoritative plan', async () => {
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  await render(<Host />); await ready();
  expect(flow.plan).toBe(activePlan); expect(storage.get(key())).toBe(activePlan.id);
  expect(api.getWeeklyPlan).not.toHaveBeenCalled(); expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('A/B/A retains independent owner storage and state', async () => {
  storage.set(key(), activePlan.id);
  const view = await render(<Host />); await ready();
  await view.rerender(<Host owner="athlete-b" />); await ready();
  expect(flow.plan).toBe(bPlan); expect(storage.get(key())).toBe(activePlan.id);
  expect(storage.get(key('athlete-b'))).toBe(bPlan.id);
  await view.rerender(<Host />); await ready(); expect(flow.plan).toBe(activePlan);
  expect(storage.get(key('athlete-b'))).toBe(bPlan.id);
});

test.each(['switch', 'logout'])('slow A GET after %s cannot publish or persist', async kind => {
  const response = deferred<WeeklyPlan>(); storage.set(key(), activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockReturnValueOnce(response.promise);
  const view = await render(<Host />);
  await waitFor(() => expect(api.getWeeklyPlan).toHaveBeenCalledTimes(1));
  if (kind === 'switch') await view.rerender(<Host owner="athlete-b" />); else await view.unmount();
  await act(() => response.resolve(activePlan));
  if (kind === 'switch') { await ready(); expect(flow.plan).toBe(bPlan); }
  expect(storage.get(key())).toBe(activePlan.id);
  expect(SecureStore.setItemAsync).not.toHaveBeenCalledWith(key('athlete-b'), activePlan.id, expect.anything());
});

test('already issued native A write finishes only in A namespace after B starts', async () => {
  const writing = deferred<void>();
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  jest.mocked(SecureStore.setItemAsync).mockImplementation(async (k, value) => {
    if (k === key()) await writing.promise;
    storage.set(k, value);
  });
  const view = await render(<Host />);
  await waitFor(() => expect(SecureStore.setItemAsync).toHaveBeenCalledWith(key(), activePlan.id, expect.anything()));
  await view.rerender(<Host owner="athlete-b" />); await ready();
  expect(flow.plan).toBe(bPlan); // A's native write is still unresolved.
  await act(() => writing.resolve());
  expect(flow.plan).toBe(bPlan); expect(storage.get(key())).toBe(activePlan.id); expect(storage.get(key('athlete-b'))).toBe(bPlan.id);
});

test.each(['plan', 'draft'])('verified legacy %s is copied only after owner GET; global key remains untouched', async kind => {
  const legacy = kind === 'plan' ? latestPlanIdKey : latestSwipeDraftIdKey;
  const value = kind === 'plan' ? activePlan.id : draft.id;
  storage.set(legacy, value); await render(<Host />); await ready();
  expect(storage.get(scopedResumeKey('athlete-a', legacy))).toBe(value); expect(storage.get(legacy)).toBe(value);
  if (kind === 'plan') expect(flow.plan).toBe(activePlan); else expect(flow.swipeDraft).toBe(draft);
});

test('foreign legacy locator is never adopted/deleted and authenticated discovery recovers A', async () => {
  storage.set(latestPlanIdKey, bPlan.id);
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  await render(<Host />); await ready();
  expect(flow.plan).toBe(activePlan); expect(storage.get(latestPlanIdKey)).toBe(bPlan.id); expect(storage.get(key())).toBe(activePlan.id);
});

test('unverifiable legacy read preserves global locator and remains recoverable', async () => {
  storage.set(latestPlanIdKey, activePlan.id); jest.mocked(api.getWeeklyPlan).mockRejectedValueOnce(new Error('Offline'));
  jest.mocked(api.discoverPlanning).mockRejectedValueOnce(new Error('Offline'));
  await render(<Host />); await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(storage.get(latestPlanIdKey)).toBe(activePlan.id); expect(storage.has(key())).toBe(false); expect(flow.plan).toBeNull();
});

test('active plus next-week pending stays separate, reviews exact proposal through A4, never auto-approves', async () => {
  recoveries.set('athlete-a', { active: activePlan, pending: pendingNext, draft: null });
  await render(<Host />); await ready();
  expect(flow.plan).toBe(activePlan); expect(flow.taskHandoff?.reviewed).toBe(pendingNext);
  expect(storage.get(key())).toBe(activePlan.id); expect(api.approvePlanProposal).not.toHaveBeenCalled();
  await act(() => flow.openRecoveredReview()); expect(flow.plan).toBe(pendingNext);
  await act(() => flow.closeRecoveredReview()); expect(flow.plan).toBe(activePlan);
  jest.mocked(api.approvePlanProposal).mockResolvedValue({ state: 'applied', plan_id: approvedNext.id, active_revision: approvedNext.revision });
  plans.set(approvedNext.id, approvedNext);
  await act(() => flow.openRecoveredReview()); await act(() => flow.approve());
  await waitFor(() => expect(flow.taskHandoff?.phase).toBe('complete'));
  expect(flow.activePlan).toBe(approvedNext); expect(storage.get(key())).toBe(approvedNext.id);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
});

test('discovered open draft restores exact revision and occurrences', async () => {
  recoveries.set('athlete-a', { active: null, pending: null, draft: { ...draft, state: 'collecting' } });
  await render(<Host />); await ready(); expect(flow.swipeDraft).toBe(draft); expect(flow.view).toBe('deck');
  expect(storage.get(key('athlete-a', latestSwipeDraftIdKey))).toBe(draft.id);
});

test('old draft cannot displace a newer approved plan', async () => {
  storage.set(key('athlete-a', latestSwipeDraftIdKey), draft.id);
  recoveries.set('athlete-a', { active: approvedNext, pending: null, draft: null });
  await render(<Host />); await ready(); expect(flow.plan).toBe(approvedNext); expect(flow.swipeDraft).toBeNull();
  expect(storage.has(key('athlete-a', latestSwipeDraftIdKey))).toBe(false);
});

test('remote approval supersedes stale local pending and invalidates Calendar', async () => {
  storage.set(key(), pendingPlan.id); plans.set(pendingPlan.id, pendingPlan);
  recoveries.set('athlete-a', { active: null, pending: pendingPlan, draft: null });
  await render(<Host />); await ready(); expect(flow.plan).toBe(pendingPlan);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-10-05', to_date: '2026-10-12', workouts: [], rest_days: [] });
  await act(() => calendar.loadCalendarRange('2026-10-05', '2026-10-12'));
  expect(calendar.calendarRange).not.toBeNull();
  const remote: WeeklyPlan = { ...pendingPlan, revision_state: 'active', state: 'active', active_revision: pendingPlan.revision, proposal: { ...pendingPlan.proposal!, state: 'applied' } };
  plans.set(remote.id, remote); recoveries.set('athlete-a', { active: remote, pending: null, draft: null });
  await act(() => onForeground('active')); await ready(); expect(flow.plan).toBe(remote); expect(flow.activePlan).toBe(remote);
  const before = jest.mocked(api.getCalendar).mock.calls.length;
  await act(() => calendar.ensureCalendarRange('2026-10-05', '2026-10-12'));
  expect(api.getCalendar).toHaveBeenCalledTimes(before + 1);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('two concurrent retry intents cause one resume, and a draft revision race preserves its locator', async () => {
  const response = deferred<PlanningRecovery>();
  recoveries.set('athlete-a', { active: null, pending: null, draft: { ...draft, state: 'collecting' } });
  await render(<Host />); await ready();
  jest.mocked(api.discoverPlanning).mockReturnValueOnce(response.promise);
  await act(() => { flow.retryResume(); flow.retryResume(); });
  await waitFor(() => expect(api.discoverPlanning).toHaveBeenCalledTimes(2));
  drafts.set(draft.id, { ...draft, revision: draft.revision + 1 });
  await act(() => response.resolve({ active: null, pending: null, draft: { ...draft, state: 'collecting' } }));
  await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(storage.get(key('athlete-a', latestSwipeDraftIdKey))).toBe(draft.id);
  expect(api.createSwipeWeekDraft).not.toHaveBeenCalled();
});

test('discovery failure retains verified state, exact locator and permits retry', async () => {
  storage.set(key(), activePlan.id); jest.mocked(api.discoverPlanning).mockRejectedValueOnce(new Error('503'));
  await render(<Host />); await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(flow.plan).toBe(activePlan); expect(storage.get(key())).toBe(activePlan.id);
  await act(() => flow.retryResume()); await ready(); expect(flow.plan).toBe(activePlan);
});


test.each(['creation', 'submission'])('late %s result after owner replacement cannot write B storage', async kind => {
  const response = deferred<SwipeWeekDraft>();
  storage.set(key('athlete-a', latestSwipeDraftIdKey), draft.id);
  const view = await render(<Host />); await ready();
  if (kind === 'creation') {
    jest.mocked(api.createSwipeWeekDraft).mockReturnValueOnce(response.promise);
    await act(() => { void flow.generate(); });
  } else {
    jest.mocked(api.submitSwipeWeekDraft).mockImplementationOnce(async () => {
      await response.promise; return { plan: pendingPlan, proposal: pendingPlan.proposal! };
    });
    await act(() => flow.submitDraft('automatic'));
  }
  await view.rerender(<Host owner="athlete-b" />); await ready();
  await act(() => response.resolve(draft));
  expect(flow.plan).toBe(bPlan); expect(flow.swipeDraft).toBeNull();
  expect(storage.get(key('athlete-b'))).toBe(bPlan.id);
  expect(storage.get(key('athlete-a', latestSwipeDraftIdKey))).toBe(draft.id);
  expect(storage.has(key('athlete-b', latestSwipeDraftIdKey))).toBe(false);
});

test('malformed successful local plan read cannot publish partial state or clear identity', async () => {
  storage.set(key(), activePlan.id);
  jest.mocked(api.getWeeklyPlan).mockResolvedValueOnce({ id: activePlan.id } as WeeklyPlan);
  await render(<Host />); await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(flow.plan).toBeNull(); expect(storage.get(key())).toBe(activePlan.id);
});


test('unverifiable global hint falls back to authenticated discovery without adoption', async () => {
  storage.set(latestPlanIdKey, bPlan.id);
  jest.mocked(api.getWeeklyPlan).mockRejectedValueOnce(Object.assign(new Error('Unavailable'), { status: 503 }));
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  await render(<Host />); await ready();
  expect(flow.plan).toBe(activePlan); expect(storage.get(key())).toBe(activePlan.id);
  expect(storage.get(latestPlanIdKey)).toBe(bPlan.id);
});


test('unmounted pending editor cannot publish options or invoke its continuation', async () => {
  plans.set(pendingPlan.id, pendingPlan); storage.set(key(), pendingPlan.id);
  const view = await render(<Host />); await ready();
  const response = deferred<Awaited<ReturnType<typeof api.getPendingWorkoutAlternatives>>>();
  const loaded = jest.fn();
  jest.mocked(api.getPendingWorkoutAlternatives).mockReturnValueOnce(response.promise);
  let completion!: Promise<boolean>;
  await act(() => { completion = flow.pendingWorkouts.load(pendingPlan.workouts[0].id, loaded); });
  await view.unmount();
  await act(async () => {
    response.resolve({ plan_id: pendingPlan.id, revision: pendingPlan.revision, proposal_id: pendingPlan.proposal!.id, workout_id: pendingPlan.workouts[0].id, can_remove: false, alternatives: [] });
    expect(await completion).toBe(false);
  });
  expect(loaded).not.toHaveBeenCalled();
});


test('SecureStore read failure still permits authoritative server discovery', async () => {
  jest.mocked(SecureStore.getItemAsync).mockRejectedValue(new Error('Storage unavailable'));
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  await render(<Host />); await ready(); expect(flow.activePlan).toBe(activePlan);
});

test('verified local approved week selection survives a discovery default for an earlier week', async () => {
  storage.set(key(), approvedNext.id); plans.set(approvedNext.id, approvedNext);
  recoveries.set('athlete-a', { active: activePlan, pending: null, draft: null });
  await render(<Host />); await ready(); expect(flow.plan).toBe(approvedNext);
  expect(storage.get(key())).toBe(approvedNext.id);
});


test('successful draft read survives a transient discovery failure', async () => {
  storage.set(key('athlete-a', latestSwipeDraftIdKey), draft.id);
  jest.mocked(api.discoverPlanning).mockRejectedValueOnce(new Error('503'));
  await render(<Host />); await waitFor(() => expect(flow.resumeState).toBe('failed'));
  expect(flow.swipeDraft).toBe(draft); expect(storage.get(key('athlete-a', latestSwipeDraftIdKey))).toBe(draft.id);
});

test('successful draft creation remains recoverable when its locator write fails', async () => {
  await render(<Host />); await ready();
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(draft);
  jest.mocked(SecureStore.setItemAsync).mockRejectedValueOnce(new Error('Storage unavailable'));
  await act(() => flow.generate());
  expect(flow.swipeDraft).toBe(draft); expect(flow.resumeState).toBe('failed'); expect(flow.view).toBe('deck');
  expect(api.createSwipeWeekDraft).toHaveBeenCalledTimes(1);
});
