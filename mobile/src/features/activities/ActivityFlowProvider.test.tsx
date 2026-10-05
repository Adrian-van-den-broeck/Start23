import { act, render } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import * as api from '../../api/client';
import type { CompletedActivity } from '../../api/types';
import { workout } from '../planning/planning.test-fixtures';
import { ActivityFlowProvider, useActivityFlow } from './ActivityFlowProvider';
import { activityOnboarding, completeActivity, externalActivity, pendingActivity } from './activities.test-fixtures';

jest.mock('../../api/client', () => ({
  confirmActivityMatch: jest.fn(), createActivity: jest.fn(), getCalendar: jest.fn(), getOnboarding: jest.fn(),
  listActivities: jest.fn(), listPlannedExternalActivities: jest.fn(), submitActivityRpeWithRefresh: jest.fn(),
}));
let flow: ReturnType<typeof useActivityFlow>;
function Probe() { flow = useActivityFlow(); return null; }
function Host({ token = 'token-a', identity = 'athlete-a', entry = true, children }: PropsWithChildren<{
  token?: string; identity?: string; entry?: boolean;
}>) { return <ActivityFlowProvider accessToken={token} athleteIdentity={identity}><Probe />{entry ? children : null}</ActivityFlowProvider>; }
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (value: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { resolve, reject, promise }; }
async function loaded(rows: CompletedActivity[] = []) {
  jest.mocked(api.listActivities).mockResolvedValue(rows);
  const view = await render(<Host />);
  await act(() => flow.ensureActivitiesLoaded());
  return view;
}
beforeEach(() => {
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.mocked(api.listActivities).mockResolvedValue([]);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [], rest_days: [] }));
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.createActivity).mockResolvedValue(pendingActivity);
  jest.mocked(api.submitActivityRpeWithRefresh).mockResolvedValue(completeActivity);
});

test('owner is lazy; concurrent entry reads and rerenders issue one exact four-read load', async () => {
  const view = await render(<Host />); expect(api.listActivities).not.toHaveBeenCalled();
  const rows = deferred<CompletedActivity[]>(); jest.mocked(api.listActivities).mockReturnValue(rows.promise);
  let load!: Promise<void>;
  await act(() => { load = flow.ensureActivitiesLoaded(); void flow.ensureActivitiesLoaded(); });
  await view.rerender(<Host token="rotated-token" />);
  expect(flow.busy).toBe(true); expect(api.listActivities).toHaveBeenCalledTimes(1);
  expect(api.listActivities).toHaveBeenCalledWith('token-a');
  expect(api.getOnboarding).toHaveBeenCalledWith('token-a'); expect(api.listPlannedExternalActivities).toHaveBeenCalledWith('token-a');
  const dates = jest.mocked(api.getCalendar).mock.calls[0];
  const now = new Date(), from = new Date(now), to = new Date(now); from.setDate(from.getDate() - 14); to.setDate(to.getDate() + 14);
  const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  expect(dates).toEqual(['token-a', iso(from), iso(to)]);
  await act(async () => { rows.resolve([completeActivity]); await load; });
  expect(flow.activities).toEqual([completeActivity]); expect(flow.busy).toBe(false);
  await act(() => flow.ensureActivitiesLoaded()); expect(api.listActivities).toHaveBeenCalledTimes(1);
});

test('list preserves server order, canonical/provider objects and existing scheduled/planned filters', async () => {
  const imported = { ...completeActivity, id: 'provider-record', source: 'canonical_summary' } as CompletedActivity;
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: 'from', to_date: 'to', workouts: [workout, { ...workout, id: 'completed', status: 'completed' }], rest_days: [] });
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([externalActivity, { ...externalActivity, id: 'cancelled', status: 'cancelled' }]);
  await loaded([imported, completeActivity, pendingActivity]);
  expect(flow.activities).toEqual([imported, completeActivity, pendingActivity]); expect(flow.activities[0]).toBe(imported);
  expect(flow.workouts).toEqual([workout]); expect(flow.externalActivities).toEqual([externalActivity]); expect(flow.feedbackActivity).toBe(pendingActivity);
});

test('load failure uses existing error and retries only on explicit entry, not rerender', async () => {
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Safe load failure')).mockResolvedValue([]);
  const view = await render(<Host />); await act(() => flow.ensureActivitiesLoaded());
  expect(flow.error).toBe('Safe load failure'); expect(flow.busy).toBe(false);
  await view.rerender(<Host />); expect(api.listActivities).toHaveBeenCalledTimes(1);
  await act(() => flow.ensureActivitiesLoaded()); expect(api.listActivities).toHaveBeenCalledTimes(2);
});

test('timezone validation still follows publishing returned rows and blocks create', async () => {
  jest.mocked(api.getOnboarding).mockResolvedValue({ ...activityOnboarding, profile: null });
  await loaded([pendingActivity]);
  expect(flow.activities).toEqual([pendingActivity]); expect(flow.pendingRpe).toEqual([pendingActivity]);
  expect(flow.error).toBe('Bevestig eerst je tijdzone in de intake voordat je activiteiten registreert.');
  await act(() => flow.save()); expect(api.createActivity).not.toHaveBeenCalled();
});

test('rapid create and rerender during transport yield one create with exact existing payload and one refresh', async () => {
  const view = await loaded(); await act(() => flow.setStartedAt('2026-10-06T12:00:00Z'));
  const create = deferred<CompletedActivity>(); jest.mocked(api.createActivity).mockReturnValue(create.promise);
  let save!: Promise<void>; await act(() => { save = flow.save(); void flow.save(); });
  await view.rerender(<Host />); expect(api.createActivity).toHaveBeenCalledTimes(1); expect(flow.busy).toBe(true);
  expect(api.createActivity).toHaveBeenCalledWith('token-a', expect.stringMatching(/^[0-9a-f-]{36}$/), {
    discipline: 'run', started_at: '2026-10-06T12:00:00Z', timezone: 'Europe/Amsterdam', duration_minutes: '45',
  });
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]);
  await act(async () => { create.resolve(pendingActivity); await save; });
  expect(api.listActivities).toHaveBeenCalledTimes(2); expect(api.getCalendar).toHaveBeenCalledTimes(2);
  expect(flow.feedbackActivity).toBe(pendingActivity); expect(flow.pendingRpe).toEqual([pendingActivity]); expect(flow.busy).toBe(false);
});

test('ambiguous create retains key, form and unresolved attempt across navigation and explicit retry', async () => {
  const view = await loaded(); await act(() => { flow.setDuration('52'); flow.setDistance('10000'); });
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Safe ambiguous outcome'));
  await act(() => flow.save()); expect(flow.error).toBe('Safe ambiguous outcome'); const first = jest.mocked(api.createActivity).mock.calls[0];
  await view.rerender(<Host entry={false} />); await view.rerender(<Host entry />);
  expect(flow.duration).toBe('52'); expect(flow.distance).toBe('10000'); expect(api.listActivities).toHaveBeenCalledTimes(1);
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]); await act(() => flow.save());
  const second = jest.mocked(api.createActivity).mock.calls[1]; expect(second[1]).toBe(first[1]); expect(second[2]).toEqual(first[2]);
});

test('successful POST followed by failed refresh retries only reads, never another POST', async () => {
  await loaded(); jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Safe refresh failure'));
  await act(() => flow.save()); expect(flow.error).toBe('Safe refresh failure');
  jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]); await act(() => flow.save());
  expect(api.createActivity).toHaveBeenCalledTimes(1); expect(api.listActivities).toHaveBeenCalledTimes(3); expect(flow.feedbackActivity?.id).toBe(pendingActivity.id);
});

test('created activity wins over another pending row; one pending source prevents another create', async () => {
  await loaded(); const other = { ...pendingActivity, id: 'other' };
  jest.mocked(api.listActivities).mockResolvedValue([other, pendingActivity]); await act(() => flow.save());
  expect(flow.pendingRpe).toHaveLength(2); expect(flow.feedbackActivity?.id).toBe('activity-a');
  await act(() => flow.save()); expect(api.createActivity).toHaveBeenCalledTimes(1);
  await loaded([other, pendingActivity]); await act(() => flow.save());
  expect(flow.error).toBe('Rond eerst de RPE van de opgeslagen activiteit af.'); expect(api.createActivity).toHaveBeenCalledTimes(1);
});

test('feedback uses exact activity and HR value; double press/rerender saves and refreshes once', async () => {
  const view = await loaded([pendingActivity]); await act(() => flow.setHeartRateByActivity({ 'activity-a': ' 151 ' }));
  const feedback = deferred<CompletedActivity>(); jest.mocked(api.submitActivityRpeWithRefresh).mockReturnValue(feedback.promise);
  let save!: Promise<void>; await act(() => { save = flow.saveRpe('activity-a', 7); void flow.saveRpe('activity-a', 7); });
  await view.rerender(<Host />); expect(flow.feedbackActivity?.id).toBe('activity-a');
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', pendingActivity, 7, 151);
  jest.mocked(api.listActivities).mockResolvedValue([completeActivity]);
  await act(async () => { feedback.resolve(completeActivity); await save; });
  expect(flow.pendingRpe).toEqual([]); expect(flow.heartRateByActivity).toEqual({}); expect(api.listActivities).toHaveBeenCalledTimes(2);
});

test('failed feedback retains pending identity/HR/key; explicit retry succeeds and only then rotates create key', async () => {
  await loaded(); jest.mocked(api.listActivities).mockResolvedValue([pendingActivity]); await act(() => flow.save());
  const firstKey = jest.mocked(api.createActivity).mock.calls[0][1];
  await act(() => flow.setHeartRateByActivity({ 'activity-a': '148' }));
  jest.mocked(api.submitActivityRpeWithRefresh).mockRejectedValueOnce(new Error('Safe feedback failure'));
  await act(() => flow.saveRpe('activity-a', 4)); expect(flow.pendingRpe).toEqual([pendingActivity]); expect(flow.heartRateByActivity).toEqual({ 'activity-a': '148' });
  expect(flow.error).toBe('Safe feedback failure'); expect(api.listActivities).toHaveBeenCalledTimes(2);
  jest.mocked(api.listActivities).mockResolvedValue([completeActivity]); await act(() => flow.saveRpe('activity-a', 4));
  await act(() => flow.save()); expect(api.createActivity).toHaveBeenCalledTimes(2);
  expect(jest.mocked(api.createActivity).mock.calls[1][1]).not.toBe(firstKey);
});

test('helper success then failed feedback refresh retains the existing displayed rows and cleared HR draft', async () => {
  await loaded([pendingActivity]); await act(() => flow.setHeartRateByActivity({ 'activity-a': '148' }));
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Safe feedback refresh failure'));
  await act(() => flow.saveRpe('activity-a', 4));
  expect(flow.pendingRpe).toEqual([pendingActivity]); expect(flow.heartRateByActivity).toEqual({}); expect(flow.error).toBe('Safe feedback refresh failure');
});

test.each(['19', '261', '150.5', 'bad'])('invalid HR %s preserves draft and does not submit/refresh', async value => {
  await loaded([pendingActivity]); await act(() => flow.setHeartRateByActivity({ 'activity-a': value }));
  await act(() => flow.saveRpe('activity-a', 4)); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  expect(api.listActivities).toHaveBeenCalledTimes(1); expect(flow.pendingRpe).toHaveLength(1);
});

test('corrected RPE passes the exact stored RPE snapshot to unchanged client recovery helper', async () => {
  await loaded([completeActivity]); await act(() => flow.saveRpe('activity-a', 6));
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', completeActivity, 6, undefined);
});

test('explicit match preserves endpoint arguments then complete refresh order', async () => {
  await loaded([pendingActivity]); await act(() => flow.confirmMatch(pendingActivity.id, workout.id));
  expect(api.confirmActivityMatch).toHaveBeenCalledWith('token-a', pendingActivity.id, workout.id); expect(api.listActivities).toHaveBeenCalledTimes(2);
});

test('pending reminder reads coalesce and obsolete response cannot restore feedback after authoritative refresh', async () => {
  await loaded(); const old = deferred<CompletedActivity[]>(); jest.mocked(api.listActivities).mockImplementation((_token, pending) => pending ? old.promise : Promise.resolve([completeActivity]));
  let read!: Promise<void>; await act(() => { read = flow.refreshPendingRpe(); void flow.refreshPendingRpe(); });
  await act(() => flow.saveRpe('missing', 4)); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  await act(() => flow.save()); // authoritative create then full refresh supersedes old reminder
  await act(async () => { old.resolve([pendingActivity]); await read; });
  expect(flow.pendingRpe).toEqual([]); expect(api.listActivities).toHaveBeenCalledTimes(3);
});

test('pending read failure is silent as before and rerender performs no automatic retry', async () => {
  const view = await render(<Host />); jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Safe reminder failure'));
  await act(() => flow.refreshPendingRpe()); await view.rerender(<Host />);
  expect(flow.error).toBeNull(); expect(flow.pendingRpe).toEqual([]); expect(api.listActivities).toHaveBeenCalledTimes(1);
});

test('same shell route/token and reminder remount do not duplicate a completed pending read', async () => {
  const view = await render(<Host />);
  await act(() => flow.refreshPendingRpe('/planning')); await view.rerender(<Host />);
  await act(() => flow.refreshPendingRpe('/planning')); expect(api.listActivities).toHaveBeenCalledTimes(1);
  await act(() => flow.refreshPendingRpe('/activities')); expect(api.listActivities).toHaveBeenCalledTimes(2);
  await view.rerender(<Host token="token-b" />); await act(() => flow.refreshPendingRpe('/activities'));
  expect(api.listActivities).toHaveBeenCalledTimes(3); expect(api.listActivities).toHaveBeenLastCalledWith('token-b', true);
});

test('pending reminder joins an active full read instead of duplicating its pending fetch', async () => {
  const view = await render(<Host />); const rows = deferred<CompletedActivity[]>(); jest.mocked(api.listActivities).mockReturnValue(rows.promise);
  let load!: Promise<void>; await act(() => { load = flow.ensureActivitiesLoaded(); void flow.refreshPendingRpe(); });
  await view.rerender(<Host />); expect(api.listActivities).toHaveBeenCalledTimes(1);
  await act(async () => { rows.resolve([pendingActivity]); await load; }); expect(flow.pendingRpe).toEqual([pendingActivity]);
});

test('token rotation retains owner/form/pending and new actions use current token', async () => {
  const view = await loaded([pendingActivity]); const owner = flow.ensureActivitiesLoaded;
  await act(() => flow.setDuration('52')); await view.rerender(<Host token="token-b" />);
  expect(flow.ensureActivitiesLoaded).toBe(owner); expect(flow.duration).toBe('52'); expect(flow.feedbackActivity).toBe(pendingActivity);
  expect(api.listActivities).toHaveBeenCalledTimes(1); await act(() => flow.saveRpe('activity-a', 4));
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-b', pendingActivity, 4, undefined);
});

test('identity replacement clears data/form/attempt; old async create cannot refresh new athlete', async () => {
  const view = await loaded(); const create = deferred<CompletedActivity>(); jest.mocked(api.createActivity).mockReturnValue(create.promise);
  let old!: Promise<void>; await act(() => { flow.setDuration('52'); }); await act(() => { old = flow.save(); });
  await view.rerender(<Host identity="athlete-b" token="token-b" />);
  expect(flow.activities).toEqual([]); expect(flow.pendingRpe).toEqual([]); expect(flow.duration).toBe('45'); expect(flow.athleteTimezone).toBe('');
  await act(async () => { create.resolve(pendingActivity); await old; }); expect(api.listActivities).toHaveBeenCalledTimes(1);
  expect(flow.pendingRpe).toEqual([]); await act(() => flow.ensureActivitiesLoaded()); expect(api.listActivities).toHaveBeenLastCalledWith('token-b');
});

test('sign-out unmount invalidates old actions and late reads without API replay', async () => {
  const view = await render(<Host />); const rows = deferred<CompletedActivity[]>(); jest.mocked(api.listActivities).mockReturnValue(rows.promise);
  let load!: Promise<void>; const old = flow; await act(() => { load = flow.ensureActivitiesLoaded(); }); await view.unmount();
  await act(async () => { rows.resolve([pendingActivity]); await load; await old.save(); await old.saveRpe('activity-a', 4); });
  expect(api.createActivity).not.toHaveBeenCalled(); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled(); expect(api.listActivities).toHaveBeenCalledTimes(1);
});

test('provider refuses nesting before instantiating another controller/read', async () => {
  const error = jest.spyOn(console, 'error').mockImplementation(() => undefined);
  await expect(render(<Host><ActivityFlowProvider accessToken="token-a" athleteIdentity="athlete-a"><Probe /></ActivityFlowProvider></Host>)).rejects.toThrow('ActivityFlowProvider must not be nested');
  expect(api.listActivities).not.toHaveBeenCalled(); error.mockRestore();
});

test.each(['planned', 'external'] as const)('selection %s retains exact identity and existing duration/distance defaults in create payload', async source => {
  await loaded();
  await act(() => { if (source === 'planned') flow.selectWorkout(workout); else flow.selectExternal(externalActivity); });
  expect(flow.discipline).toBe(source === 'planned' ? workout.discipline : externalActivity.discipline);
  await act(() => flow.save());
  const payload = jest.mocked(api.createActivity).mock.calls[0][2];
  expect(payload).toEqual(expect.objectContaining(source === 'planned' ? {
    planned_workout_id: workout.id, duration_minutes: String(Number(workout.duration_minutes)),
  } : { planned_external_activity_id: externalActivity.id, duration_minutes: '60' }));
  expect(payload).not.toHaveProperty(source === 'planned' ? 'planned_external_activity_id' : 'planned_workout_id');
  expect(flow.selectedWorkout).toBeNull(); expect(flow.selectedExternal).toBeNull();
});

test.each([
  { duration: '0', distance: '', startedAt: '2026-10-06T12:00:00Z' },
  { duration: 'bad', distance: '', startedAt: '2026-10-06T12:00:00Z' },
  { duration: '', distance: '5000', startedAt: '2026-10-06T12:00:00Z' },
  { duration: '45', distance: '1.5', startedAt: '2026-10-06T12:00:00Z' },
  { duration: '45', distance: '-1', startedAt: '2026-10-06T12:00:00Z' },
  { duration: '45', distance: '', startedAt: 'invalid' },
])('existing invalid create fields %j do not mutate or refresh', async fields => {
  await loaded(); await act(() => { flow.setDuration(fields.duration); flow.setDistance(fields.distance); flow.setStartedAt(fields.startedAt); });
  await act(() => flow.save()); expect(api.createActivity).not.toHaveBeenCalled(); expect(api.listActivities).toHaveBeenCalledTimes(1); expect(flow.error).not.toBeNull();
});

test('existing swim distance-only path sends null duration without estimation', async () => {
  await loaded(); await act(() => { flow.setDiscipline('swim'); flow.setDuration(''); flow.setDistance('1000'); });
  await act(() => flow.save()); expect(api.createActivity).toHaveBeenCalledWith('token-a', expect.any(String), expect.objectContaining({ discipline: 'swim', duration_minutes: null, distance_meters: 1000 }));
});

test('identity replacement ignores late pending read and late feedback success', async () => {
  const view = await loaded([pendingActivity]); const feedback = deferred<CompletedActivity>(), pending = deferred<CompletedActivity[]>();
  jest.mocked(api.submitActivityRpeWithRefresh).mockReturnValue(feedback.promise); jest.mocked(api.listActivities).mockReturnValue(pending.promise);
  let read!: Promise<void>, save!: Promise<void>; await act(() => { read = flow.refreshPendingRpe(); save = flow.saveRpe('activity-a', 4); });
  await view.rerender(<Host identity="athlete-b" token="token-b" />);
  await act(async () => { pending.resolve([pendingActivity]); feedback.resolve(completeActivity); await Promise.all([read, save]); });
  expect(flow.activities).toEqual([]); expect(flow.pendingRpe).toEqual([]); expect(flow.error).toBeNull(); expect(api.listActivities).toHaveBeenCalledTimes(2);
});
