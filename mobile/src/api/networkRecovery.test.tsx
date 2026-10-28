import { act, render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import * as api from './client';
import type { CompletedActivity } from './types';
import { ActivityFlowProvider, useActivityFlow } from '../features/activities/ActivityFlowProvider';
import { usePlanningController } from '../features/planning/usePlanningController';
import { activePlan, onboarding } from '../features/planning/planning.test-fixtures';
import { approvedNext, pendingNext } from '../features/planning/planningTask.test-fixtures';
import { activityOnboarding, pendingActivity } from '../features/activities/activities.test-fixtures';
import { cancelApiRequests } from '../lib/apiCancellation';

jest.mock('./client', () => { process.env.EXPO_PUBLIC_API_BASE_URL = 'https://api.start23.test'; return jest.requireActual('./client'); });
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
let activity: ReturnType<typeof useActivityFlow>;
let planning: ReturnType<typeof usePlanningController>;
let stored: Map<string, string>;
let rows: CompletedActivity[];
let handler: (path: string, init: RequestInit) => Promise<Response>;
let fetchMock: jest.MockedFunction<typeof fetch>;
function ActivityProbe() { activity = useActivityFlow(); return null; }
function ActivityHost({ identity = 'A' }: { identity?: string }) { return <ActivityFlowProvider athleteIdentity={identity} accessToken={identity}><ActivityProbe /></ActivityFlowProvider>; }
function PlanProbe() { planning = usePlanningController('A', 'A', onboarding); return null; }
function response(body: unknown, status = 200): Response { return { ok: status >= 200 && status < 300, status, json: async () => body } as Response; }
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(r => { resolve = r; }); return { promise, resolve }; }
async function flush() { await act(async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); }); }
async function advance(ms = api.API_DEADLINE_MS) { await act(async () => { await jest.advanceTimersByTimeAsync(ms); }); await flush(); }
const writes = () => fetchMock.mock.calls.filter(c => ['POST', 'PUT', 'PATCH'].includes(c[1]?.method ?? 'GET'));
beforeEach(() => {
  jest.useFakeTimers({ now: new Date('2026-10-06T12:00:00Z') });
  jest.clearAllMocks(); rows = []; stored = new Map([['start23.A.latest-plan-id', activePlan.id]]);
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async key => stored.get(key) ?? null);
  jest.mocked(SecureStore.setItemAsync).mockImplementation(async (key, value) => { stored.set(key, value); });
  jest.mocked(SecureStore.deleteItemAsync).mockImplementation(async key => { stored.delete(key); });
  handler = async path => {
    if (path.endsWith('/onboarding')) return response(activityOnboarding);
    if (path.includes('/calendar?')) return response({ workouts: [], rest_days: [] });
    if (path.endsWith('/planned-external-activities')) return response([]);
    if (path.includes('/weekly-plans/recovery')) return response({ active: null, pending: null, draft: null });
    if (path.includes('/weekly-plans/plan-a')) return response(activePlan);
    if (path.endsWith(`/activities/${pendingActivity.id}`)) return response(rows.find(r => r.id === pendingActivity.id) ?? pendingActivity);
    if (path.endsWith('/activities') || path.endsWith('/activities/pending-rpe')) return response(rows);
    throw new Error('Unhandled synthetic route');
  };
  fetchMock = jest.fn((url, init) => handler(String(url), init ?? {})); global.fetch = fetchMock;
});
afterEach(() => { jest.useRealTimers(); });

test('activity POST timeout releases busy, retains form, lock, immutable payload and logical key on explicit retry', async () => {
  const view = await render(<ActivityHost />);
  await act(() => activity.ensureActivitiesLoaded());
  await act(() => { activity.setDuration('52'); });
  const original = handler; let created = false;
  handler = async (path, init) => {
    if (init.method === 'POST' && path.endsWith('/activities')) {
      if (!created) { created = true; rows = [pendingActivity]; return new Promise(() => {}); }
      return response(rows[0]); // same server-side idempotent logical create
    }
    return original(path, init);
  };
  await act(async () => { void activity.save(); void activity.save(); }); await flush();
  expect(writes()).toHaveLength(1); await advance();
  expect(activity.busy).toBe(false); expect(activity.duration).toBe('52'); expect(activity.error).toBeTruthy();
  await act(() => { activity.setDuration('60'); });
  await act(() => activity.refreshActivities()); // A7 refresh cannot erase unresolved create
  await act(() => activity.save());
  expect(writes()).toHaveLength(2);
  expect(writes()[1][1]?.body).toBe(writes()[0][1]?.body);
  expect(writes()[1][1]?.headers).toEqual(writes()[0][1]?.headers);
  expect(rows).toHaveLength(1); await view.unmount();
});
test('timeout of authoritative activity refresh preserves A7 pending entity and form', async () => {
  rows = [pendingActivity]; await render(<ActivityHost />); await act(() => activity.ensureActivitiesLoaded());
  await act(() => { activity.setHeartRateByActivity({ [pendingActivity.id]: '151' }); });
  const original = handler; handler = (path, init) => path.endsWith('/activities') ? new Promise(() => {}) : original(path, init);
  await act(async () => { void activity.refreshActivities(); }); await advance();
  expect(activity.refreshing).toBe(false); expect(activity.activities).toEqual(rows);
  expect(activity.pendingRpe).toEqual(rows); expect(activity.heartRateByActivity[pendingActivity.id]).toBe('151');
});
test('A6 hung resume preserves saved locator and cannot become an empty plan; retry recovers', async () => {
  const original = handler; handler = (path, init) => path.includes('/weekly-plans/plan-a') ? new Promise(() => {}) : original(path, init);
  await render(<PlanProbe />); await flush(); await advance();
  expect(planning.resumeState).toBe('failed'); expect(stored.get('start23.A.latest-plan-id')).toBe(activePlan.id);
  handler = original; await act(() => planning.retryResume()); await flush();
  expect(planning.resumeState).toBe('ready'); expect(planning.plan?.id).toBe(activePlan.id); expect(writes()).toHaveLength(0);
});
test('A4 approval timeout holds the exact proposal; explicit recovery reads committed revision without another POST', async () => {
  await render(<PlanProbe />); await flush();
  await act(() => planning.receiveTaskPlan('check-in:original', pendingNext));
  const original = handler; let committed = false;
  handler = (path, init) => {
    if (path.endsWith('/next-proposal/approve')) { committed = true; return new Promise(() => {}); }
    if (path.endsWith('/next-plan?revision=1')) return Promise.resolve(response(committed ? approvedNext : pendingNext));
    return original(path, init);
  };
  await act(async () => { void planning.approveTaskPlan('check-in:original', pendingNext).catch(() => false); }); await advance();
  expect(planning.busy).toBe(false); expect(planning.taskHandoff?.phase).toBe('verify');
  expect(planning.plan?.id).toBe(activePlan.id);
  await act(() => planning.approveTaskPlan('check-in:original', pendingNext));
  expect(planning.activePlan?.id).toBe(approvedNext.id); expect(writes()).toHaveLength(1);
});
test('account switch during POST cannot publish late A into B; abort does not assert server rollback', async () => {
  const pending = deferred<Response>(); const original = handler;
  handler = (path, init) => init.method === 'POST' ? pending.promise : original(path, init);
  const view = await render(<ActivityHost />); await act(() => activity.ensureActivitiesLoaded());
  await act(async () => { void activity.save(); }); await flush();
  await view.rerender(<ActivityHost identity="B" />); cancelApiRequests('A'); await flush();
  rows = [pendingActivity]; pending.resolve(response(pendingActivity)); await flush();
  expect(activity.activities).toEqual([]); expect(activity.pendingRpe).toEqual([]); expect(activity.busy).toBe(false); expect(writes()).toHaveLength(1);
});
test('navigation/unmount while GET pending cannot publish its late result', async () => {
  const pending = deferred<Response>(); const original = handler;
  handler = (path, init) => path.endsWith('/activities') ? pending.promise : original(path, init);
  const view = await render(<ActivityHost />);
  await act(async () => { void activity.ensureActivitiesLoaded(); });
  await view.unmount(); pending.resolve(response([pendingActivity])); await flush();
  expect(activity.activities).toEqual([]); expect(writes()).toHaveLength(0);
});
