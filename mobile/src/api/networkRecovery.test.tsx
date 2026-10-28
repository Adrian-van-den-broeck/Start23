import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityBoundary } from '../ui/ActivityBoundary';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { uncertainWriteMessage } from '../i18n/recoveryMessages';
import { PlanningFlowProvider, usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { savedCheckIn } from '../features/checkins/checkIn.test-fixtures';
import { CheckInScreen } from '../screens/CheckInScreen';
import { act, fireEvent, render } from '@testing-library/react-native';
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
function unreadable(): Response { return { ok: true, status: 200, json: async () => { throw new SyntaxError('truncated'); } } as unknown as Response; }
const completed = (rpe = 4): CompletedActivity => ({ ...pendingActivity, processing_state: 'complete', qualitative_result: 'unplanned', rpe, rpe_submitted_at: '2026-10-06T11:00:00Z', metrics: { average_heart_rate_bpm: 151, max_heart_rate_bpm: null, normalized_power_watts: null, average_speed_kmh: null, max_speed_kmh: null, average_pace_seconds_per_km: null, zone_minutes: null, low_intensity_minutes: null, high_intensity_minutes: null } });

test('malformed committed RPE recovers in the real Activity owner without a duplicate choice/PUT', async () => {
  rows = [pendingActivity]; await render(<ActivityHost />); await act(() => activity.ensureActivitiesLoaded());
  await act(() => activity.setHeartRateByActivity({ [pendingActivity.id]: '151' }));
  const original = handler;
  handler = (path, init) => { if (init.method === 'PUT') { rows = [completed()]; return Promise.resolve(unreadable()); } return original(path, init); };
  await act(() => activity.saveRpe(pendingActivity.id, 4));
  expect(activity.activities[0]).toEqual(completed()); expect(activity.pendingRpe).toEqual([]);
  expect(activity.busy).toBe(false); expect(writes()).toHaveLength(1);
});
test('RPE explicit retry first verifies original identity and preserves RPE/HR/precondition through input edits and refresh', async () => {
  rows = [pendingActivity]; await render(<ActivityHost />); await act(() => activity.ensureActivitiesLoaded());
  await act(() => activity.setHeartRateByActivity({ [pendingActivity.id]: '151' }));
  const original = handler; let count = 0;
  handler = (path, init) => {
    if (init.method === 'PUT') {
      if (++count === 1) return new Promise(() => {});
      rows = [completed()]; return Promise.resolve(response(rows[0]));
    }
    return original(path, init);
  };
  await act(async () => { void activity.saveRpe(pendingActivity.id, 4); void activity.saveRpe(pendingActivity.id, 7); });
  await advance(); expect(activity.busy).toBe(false); expect(writes()).toHaveLength(1);
  await act(() => activity.setHeartRateByActivity({ [pendingActivity.id]: '160' }));
  await act(() => activity.refreshActivities());
  await act(() => activity.saveRpe(pendingActivity.id, 7));
  expect(writes()).toHaveLength(2); expect(writes()[1][1]?.body).toBe(writes()[0][1]?.body);
  expect(JSON.parse(String(writes()[1][1]?.body))).toEqual({ rpe: 4, average_heart_rate_bpm: 151 });
  expect(activity.activities[0]).toEqual(completed()); expect(activity.pendingRpe).toEqual([]);
});
test('malformed activity create retains one immutable logical attempt for explicit idempotent replay', async () => {
  await render(<ActivityHost />); await act(() => activity.ensureActivitiesLoaded());
  const original = handler; let count = 0;
  handler = (path, init) => {
    if (init.method === 'POST' && path.endsWith('/activities')) { rows = [pendingActivity]; return Promise.resolve(++count === 1 ? unreadable() : response(rows[0])); }
    return original(path, init);
  };
  await act(() => activity.save()); expect(activity.busy).toBe(false); expect(activity.error).toBe(uncertainWriteMessage);
  await act(() => activity.setDuration('99')); await act(() => activity.save());
  expect(writes()).toHaveLength(2); expect(writes()[1][1]?.body).toBe(writes()[0][1]?.body);
  expect(writes()[1][1]?.headers).toEqual(writes()[0][1]?.headers); expect(rows).toHaveLength(1);
});
test('ordinary plan approval with unreadable receipt uses A4 verify/read instead of another POST', async () => {
  const pending = { ...activePlan, revision: 3, revision_id: 'revision-3', revision_state: 'pending_approval' as const, proposal: { ...pendingNext.proposal!, id: 'proposal-a', base_plan_revision: 2, target_plan_revision_id: 'revision-3' } };
  const applied = { ...pending, revision_state: 'active' as const, active_revision: 3, proposal: { ...pending.proposal, state: 'applied' as const } };
  const original = handler; let committed = false;
  handler = (path, init) => {
    if (path.endsWith('/proposal-a/approve')) { committed = true; return Promise.resolve(unreadable()); }
    if (path.endsWith('/weekly-plans/plan-a') || path.endsWith('/weekly-plans/plan-a?revision=3')) return Promise.resolve(response(committed ? applied : pending));
    return original(path, init);
  };
  await render(<PlanProbe />); await flush(); await act(() => planning.approve()); await flush();
  expect(planning.busy).toBe(false); expect(planning.taskHandoff?.phase).toBe('verify'); expect(writes()).toHaveLength(1);
  await act(() => planning.approve()); await flush();
  expect(planning.plan?.revision_state).toBe('active'); expect(planning.plan?.revision).toBe(3); expect(writes()).toHaveLength(1);
});
test('movement timeout preserves original expected revision and read-checks renewed occurrence IDs before any explicit retry', async () => {
  const updated = { ...activePlan, revision: 3, active_revision: 3, revision_id: 'revision-3', workouts: [{ ...activePlan.workouts[0], id: 'renewed-workout', scheduled_date: '2026-10-08' }] };
  const original = handler; let committed = false;
  handler = (path, init) => {
    if (path.endsWith('/validate')) return Promise.resolve(response({ valid_for_generated_schedule: true, warnings: [] }));
    if (init.method === 'PATCH') { committed = true; return new Promise(() => {}); }
    if (path.endsWith('/weekly-plans/plan-a')) return Promise.resolve(response(committed ? updated : activePlan));
    return original(path, init);
  };
  await render(<PlanProbe />); await flush();
  await act(() => planning.requestWorkoutMove(activePlan.workouts[0], '2026-10-08')); await advance();
  expect(planning.busy).toBe(false); expect(planning.plan?.revision).toBe(2);
  await act(() => planning.requestWorkoutMove(activePlan.workouts[0], '2026-10-09')); await flush();
  expect(planning.plan?.revision).toBe(3); expect(planning.plan?.workouts[0].id).toBe('renewed-workout');
  const patches = fetchMock.mock.calls.filter(c => c[1]?.method === 'PATCH');
  expect(patches).toHaveLength(1); expect(JSON.parse(String(patches[0][1]?.body))).toEqual({ expected_revision: 2, scheduled_date: '2026-10-08' });
});
function SharedPlanProbe() { planning = usePlanningFlow(); return null; }
function CheckInHost({ visible = true }: { visible?: boolean }) {
  return <LanguageProvider><PlanningFlowProvider accessToken="A" athleteIdentity="A" initialOnboarding={onboarding}>
    <SharedPlanProbe />{visible ? <CheckInScreen athleteIdentity="A" accessToken="A" onBack={() => {}} onSignOut={async () => {}} /> : null}
  </PlanningFlowProvider></LanguageProvider>;
}
test.each(['retry', 'restart'] as const)('A5 proposal identity survives hung committed generation and %s in actual CheckIn UI', async recovery => {
  const confirmed = { ...savedCheckIn, week_start: pendingNext.week_start, context: { ...savedCheckIn.context!, state: 'confirmed', confirmed_at: '2026-10-06T12:00:00Z' } };
  const original = handler; let proposals = 0; let calls = 0;
  handler = (path, init) => {
    if (path.endsWith('/checkins')) return Promise.resolve(response(calls ? { ...confirmed, status: 'completed', plan_proposal_id: pendingNext.proposal!.id } : confirmed));
    if (path.endsWith('/injury-restrictions')) return Promise.resolve(response([]));
    if (path.endsWith(`/checkins/${confirmed.id}/plan-proposals`)) {
      if (++calls === 1) { proposals++; return new Promise(() => {}); }
      return Promise.resolve(response({ plan: pendingNext, proposal: pendingNext.proposal }));
    }
    return original(path, init);
  };
  const view = await render(<CheckInHost />); await flush();
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' })); await flush();
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' })); await advance(api.PLANNING_DEADLINE_MS);
  expect(planning.activePlan?.id).toBe(activePlan.id); expect(planning.taskHandoff).toBeNull();
  expect(view.getByRole('button', { name: 'Maak planvoorstel' })).toBeEnabled();
  if (recovery === 'restart') {
    await view.rerender(<CheckInHost visible={false} />); await view.rerender(<CheckInHost />);
    await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  } else await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await flush(); expect(planning.taskHandoff?.reviewed.id).toBe(pendingNext.id);
  expect(planning.taskHandoff?.reviewed.revision_id).toBe(pendingNext.revision_id);
  expect(planning.activePlan?.id).toBe(activePlan.id); expect(proposals).toBe(1);
  expect(fetchMock.mock.calls.filter(c => String(c[0]).endsWith('/plan-proposals')).map(c => c[0])).toEqual([
    `https://api.start23.test/api/v1/checkins/${confirmed.id}/plan-proposals`, `https://api.start23.test/api/v1/checkins/${confirmed.id}/plan-proposals`,
  ]);
});
function ActivityUiHost() {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><ActivityFlowProvider athleteIdentity="A" accessToken="A"><ActivityProbe />
      <ActivityBoundary version="v2" view="entry" correctionId={null} onCorrection={() => {}} onVersion={() => {}} switchLocked={false}
        onView={() => {}} onBack={() => {}} onSignOut={async () => {}} />
    </ActivityFlowProvider></UiVersionProvider></LanguageProvider>
  </SafeAreaProvider>;
}
test.each([
  ['nl', 'Activiteit opslaan', 'Werkelijke duur (minuten)', 'De uitkomst van het opslaan is nog onbekend.'],
  ['en', 'Save activity', 'Actual duration (minutes)', 'The save outcome is still unknown.'],
])('actual V2 entry keeps fields, settles busy and shows localized recovery on timeout (%s)', async (language, saveLabel, durationLabel, message) => {
  stored.set('start23.language-preference', language);
  const original = handler;
  handler = (path, init) => init.method === 'POST' && path.endsWith('/activities') ? new Promise(() => {}) : original(path, init);
  const view = await render(<ActivityUiHost />); await flush();
  await fireEvent.changeText(view.getByLabelText(durationLabel), '53');
  await fireEvent.press(view.getByRole('button', { name: saveLabel }));
  await advance();
  expect(view.getByLabelText(durationLabel).props.value).toBe('53');
  expect(view.getByRole('button', { name: saveLabel })).toBeEnabled();
  expect(view.getByText(new RegExp(message.replace('.', '\\.')))).toBeTruthy();
  expect(writes()).toHaveLength(1);
});
test('unknown check-in start retains its original week locator even if the entry field is edited before retry', async () => {
  const original = handler; let count = 0;
  const open = { ...savedCheckIn, context: null, context_revision: 0 };
  handler = (path, init) => {
    if (path.endsWith('/checkins')) return ++count === 1 ? new Promise(() => {}) : Promise.resolve(response(open));
    if (path.endsWith('/injury-restrictions')) return Promise.resolve(response([]));
    return original(path, init);
  };
  const view = await render(<CheckInHost />); await flush();
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' })); await advance();
  await fireEvent.changeText(view.getByLabelText('Week start op maandag'), '2026-11-02');
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' })); await flush();
  const starts = fetchMock.mock.calls.filter(c => String(c[0]).endsWith('/checkins'));
  expect(starts).toHaveLength(2); expect(starts[1][1]?.body).toBe(starts[0][1]?.body);
  expect(view.getByText('Week van ' + open.week_start)).toBeTruthy();
});
