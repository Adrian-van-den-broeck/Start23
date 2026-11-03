import { act, render, waitFor } from '@testing-library/react-native';
import { useEffect } from 'react';
import * as api from '../../api/client';
import type { CompletedActivity } from '../../api/types';
import { workout } from '../planning/planning.test-fixtures';
import { ActivityFlowProvider, useActivityFlow } from './ActivityFlowProvider';
import { activityOnboarding, completeActivity, pendingActivity } from './activities.test-fixtures';

jest.mock('../../api/client');
let flow: ReturnType<typeof useActivityFlow>;
let server: CompletedActivity[];
const remote: CompletedActivity = { ...pendingActivity, id: 'remote-activity', updated_at: '2026-10-06T12:00:00Z' };
function Probe() { flow = useActivityFlow(); return null; }
function Entry() {
  const owner = useActivityFlow();
  useEffect(() => { void owner.ensureActivitiesLoaded(); }, [owner.ensureActivitiesLoaded]);
  return null;
}
function Host({ entry = true, identity = 'athlete-a', token = 'token-a' }: { entry?: boolean; identity?: string; token?: string }) {
  return <ActivityFlowProvider athleteIdentity={identity} accessToken={token}><Probe />{entry ? <Entry /> : null}</ActivityFlowProvider>;
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
beforeEach(() => {
  jest.useFakeTimers({ now: new Date('2026-10-06T12:00:00Z'), doNotFake: [
    'hrtime', 'nextTick', 'performance', 'queueMicrotask', 'requestAnimationFrame', 'cancelAnimationFrame',
    'requestIdleCallback', 'cancelIdleCallback', 'setImmediate', 'clearImmediate', 'setInterval', 'clearInterval', 'setTimeout', 'clearTimeout',
  ] });
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  server = [];
  jest.mocked(api.listActivities).mockImplementation(async (_token, pending) => pending ? server.filter(row => row.processing_state === 'awaiting_rpe') : [...server]);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [workout], rest_days: [] }));
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.getActivity).mockImplementation(async (_token, id) => {
    const row = server.find(value => value.id === id);
    if (!row) throw Object.assign(new Error('Activity not found'), { status: 404 });
    return row;
  });
  jest.mocked(api.submitActivityRpeWithRefresh).mockImplementation(async (_token, activity, rpe) => {
    const stored = { ...activity, ...completeActivity, id: activity.id, rpe, updated_at: '2026-10-06T13:00:00Z' };
    server = server.map(row => row.id === activity.id ? stored : row);
    return stored;
  });
});

afterEach(() => jest.useRealTimers());

test('WOMBO-010 A: a remote pending reminder absent from first history can submit its exact RPE identity', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  expect(flow.activities).toEqual([]);
  server = [remote];
  await act(() => flow.refreshPendingRpe());
  expect(flow.feedbackActivity).toBe(remote);
  await act(() => flow.saveRpe(remote.id, 4));
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', remote, 4, undefined);
  expect(flow.pendingRpe).toEqual([]);
  expect(flow.activities[0]).toMatchObject({ id: remote.id, rpe: 4, processing_state: 'complete' });
});

test('WOMBO-010 B: reentry refreshes remote history and planned choices after an earlier successful load', async () => {
  const view = await render(<Host />);
  await act(() => flow.setDuration('45'));
  expect(flow.activities).toEqual([]); expect(flow.workouts).toEqual([workout]);
  await view.rerender(<Host entry={false} />);
  server = [remote];
  const next = { ...workout, id: 'new-approved-occurrence', name: 'New approved workout' };
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [next], rest_days: [] }));
  await view.rerender(<Host />);
  expect(flow.activities).toEqual([remote]); expect(flow.workouts).toEqual([next]);
  expect(api.listActivities).toHaveBeenCalledTimes(2);
  expect(api.createActivity).not.toHaveBeenCalled();
});

test('first load, unchanged reentry and rerender have bounded distinct behavior', async () => {
  const view = await render(<Host />);
  await act(() => flow.setDuration('45'));
  expect(api.listActivities).toHaveBeenCalledTimes(1);
  await view.rerender(<Host />); expect(api.listActivities).toHaveBeenCalledTimes(1);
  await view.rerender(<Host entry={false} />); await view.rerender(<Host />);
  expect(api.listActivities).toHaveBeenCalledTimes(2); expect(flow.activities).toEqual([]);
});

test('unknown activity resolves by exact owner GET without downloading history', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45')); server = [remote];
  await act(() => flow.saveRpe(remote.id, 4));
  expect(api.getActivity).toHaveBeenCalledWith('token-a', remote.id);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', remote, 4, undefined);
  // One initial and one post-write load; no full load used for resolution.
  expect(api.listActivities).toHaveBeenCalledTimes(2);
});

test('stale deleted reminder reports absence, removes only that identity and performs no RPE write', async () => {
  server = [remote]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  await act(() => flow.setHeartRateByActivity({ [remote.id]: '151' }));
  server = [];
  await act(() => flow.refreshActivities()); // An absent list row alone is not deletion proof.
  expect(flow.pendingRpe[0].id).toBe(remote.id);
  await act(() => flow.saveRpe(remote.id, 4));
  expect(api.getActivity).toHaveBeenCalledWith('token-a', remote.id);
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  expect(flow.pendingRpe).toEqual([]); expect(flow.error).toBe('Activity not found');
  expect(flow.heartRateByActivity[remote.id]).toBe('151');
});

test('a remotely completed stale reminder cannot turn its RPE choice into a correction', async () => {
  server = [remote]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Offline'));
  await act(() => flow.refreshActivities());
  const completed = { ...remote, ...completeActivity, id: remote.id };
  server = [completed];
  await act(() => flow.saveRpe(remote.id, 4));
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  expect(flow.activities[0]).toBe(completed); expect(flow.pendingRpe).toEqual([]);
  expect(flow.error).toMatch(/intussen verwerkt/);
});

test.each(['foreign', 'malformed', 'offline'])('unverified %s activity resolution cannot write RPE', async reason => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  if (reason === 'offline') jest.mocked(api.getActivity).mockRejectedValueOnce(new Error('Offline'));
  else jest.mocked(api.getActivity).mockResolvedValueOnce(reason === 'foreign' ? { ...remote, id: 'different-id' } : { id: remote.id } as CompletedActivity);
  await act(() => flow.saveRpe(remote.id, 4));
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled(); expect(flow.error).not.toBeNull();
});

test('failed refresh preserves history, planned choices, measurements and local input', async () => {
  server = [remote]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  await act(() => { flow.setDuration('58'); flow.setDistance('8000'); flow.setStartedAt('2026-10-06T09:00:00Z'); flow.setHeartRateByActivity({ [remote.id]: '150' }); flow.selectWorkout(workout); });
  const previous = flow;
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Offline'));
  await act(() => flow.refreshActivities());
  expect(flow.activities).toEqual(previous.activities); expect(flow.workouts).toEqual(previous.workouts);
  expect(flow.duration).toBe(previous.duration); expect(flow.distance).toBe(previous.distance);
  expect(flow.startedAt).toBe(previous.startedAt); expect(flow.selectedWorkout).toBe(workout);
  expect(flow.heartRateByActivity).toEqual(previous.heartRateByActivity);
  expect(flow.feedbackActivity?.id).toBe(remote.id); expect(flow.refreshing).toBe(false);
});

test.each(['success', 'error'])('newer forced history wins over late old %s', async outcome => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  const old = deferred<CompletedActivity[]>(), current = deferred<CompletedActivity[]>();
  jest.mocked(api.listActivities).mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise);
  let first!: Promise<void>, second!: Promise<void>;
  await act(() => { first = flow.refreshActivities(); });
  await act(() => { second = flow.refreshActivities(true); });
  await act(async () => { current.resolve([remote]); await second; });
  await act(async () => { if (outcome === 'success') old.resolve([]); else old.reject(new Error('Obsolete failure')); await first; });
  expect(flow.activities).toEqual([remote]); expect(flow.error).toBeNull(); expect(flow.refreshing).toBe(false);
});

test('duplicate refresh and repeated focus events coalesce without requests on render', async () => {
  const view = await render(<Host entry={false} />);
  const response = deferred<CompletedActivity[]>(); jest.mocked(api.listActivities).mockReturnValueOnce(response.promise);
  await act(() => { flow.setActivitiesFocused(true); flow.setActivitiesFocused(true); void flow.refreshActivities(); });
  await view.rerender(<Host entry={false} />);
  expect(api.listActivities).toHaveBeenCalledTimes(1);
  await act(() => response.resolve([])); await waitFor(() => expect(flow.refreshing).toBe(false));
  await act(() => flow.setActivitiesFocused(true)); expect(api.listActivities).toHaveBeenCalledTimes(1);
  await act(() => flow.setActivitiesFocused(false)); server = [remote];
  await act(() => flow.setActivitiesFocused(true)); expect(flow.activities).toEqual([remote]);
  expect(api.listActivities).toHaveBeenCalledTimes(2);
});

test('older reminder cannot overwrite a newer full-history completion', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  const reminder = deferred<CompletedActivity[]>();
  jest.mocked(api.listActivities).mockImplementationOnce(() => reminder.promise);
  let pending!: Promise<void>;
  await act(() => { pending = flow.refreshPendingRpe(); });
  server = [completeActivity]; await act(() => flow.refreshActivities());
  await act(async () => { reminder.resolve([pendingActivity]); await pending; });
  expect(flow.activities).toEqual([completeActivity]); expect(flow.pendingRpe).toEqual([]);
});

test.each(['switch', 'logout'])('late history after %s cannot publish into another owner', async action => {
  const response = deferred<CompletedActivity[]>();
  jest.mocked(api.listActivities).mockReturnValueOnce(response.promise);
  const view = await render(<Host />);
  await act(() => flow.setDuration('45'));
  if (action === 'switch') await view.rerender(<Host identity="athlete-b" token="token-b" />); else await view.unmount();
  await act(() => response.resolve([remote]));
  if (action === 'switch') { expect(flow.activities).toEqual([]); expect(flow.pendingRpe).toEqual([]); }
  expect(api.createActivity).not.toHaveBeenCalled();
});

test.each(['switch', 'logout'])('late targeted RPE resolution after %s cannot issue its PUT', async action => {
  const response = deferred<CompletedActivity>();
  const view = await render(<Host entry={false} />);
  jest.mocked(api.getActivity).mockReturnValueOnce(response.promise);
  let mutation!: Promise<boolean>; await act(() => { mutation = flow.saveRpe(remote.id, 4); });
  if (action === 'switch') await view.rerender(<Host entry={false} identity="athlete-b" token="token-b" />); else await view.unmount();
  await act(async () => { response.resolve(remote); await mutation; });
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  if (action === 'switch') expect(flow.activities).toEqual([]);
});

test('an unresolved logical POST survives refresh with the same key and payload', async () => {
  const view = await render(<Host />);
  await act(() => flow.setDuration('45'));
  await act(() => { flow.setDuration('52'); flow.setDistance('6000'); });
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Unknown commit'));
  await act(() => flow.save()); const original = jest.mocked(api.createActivity).mock.calls[0];
  await act(() => flow.refreshActivities());
  await view.rerender(<Host entry={false} />); await view.rerender(<Host />);
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [pendingActivity]; return pendingActivity; });
  await act(() => flow.save());
  expect(jest.mocked(api.createActivity).mock.calls[1]).toEqual(original);
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
});

test('read refresh while a POST is pending cannot unlock it or create another logical attempt', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45')); const response = deferred<CompletedActivity>();
  jest.mocked(api.createActivity).mockReturnValueOnce(response.promise);
  let mutation!: Promise<void>; await act(() => { mutation = flow.save(); });
  await act(() => flow.refreshActivities()); expect(flow.busy).toBe(true);
  await act(() => flow.save()); expect(api.createActivity).toHaveBeenCalledTimes(1);
  await act(async () => { server = [pendingActivity]; response.resolve(pendingActivity); await mutation; });
  expect(flow.feedbackActivity?.id).toBe(pendingActivity.id);
});

test('refresh preserves a chosen feedback identity and HR while new reminders arrive', async () => {
  server = [remote]; const view = await render(<Host />);
  await act(() => flow.setDuration('45'));
  await act(() => flow.setHeartRateByActivity({ [remote.id]: '153' }));
  server = [{ ...pendingActivity, id: 'another-remote' }, remote];
  await act(() => flow.refreshActivities());
  await view.rerender(<Host entry={false} />); await view.rerender(<Host />);
  expect(flow.feedbackActivity?.id).toBe(remote.id); expect(flow.heartRateByActivity[remote.id]).toBe('153');
});

test('correction resolves stale identity without silently changing its reviewed expected RPE', async () => {
  server = [completeActivity]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Offline'));
  await act(() => flow.refreshActivities());
  server = [{ ...completeActivity, rpe: 5, updated_at: '2026-10-06T13:00:00Z' }];
  await act(() => flow.saveRpe(completeActivity.id, 4));
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  expect(flow.activities[0].rpe).toBe(5); expect(flow.error).toMatch(/intussen gewijzigd/);
});

test('correction and post-write refresh preserve UUID, expected RPE and do not duplicate mutations', async () => {
  server = [completeActivity]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  const result = deferred<CompletedActivity>(); jest.mocked(api.submitActivityRpeWithRefresh).mockReturnValueOnce(result.promise);
  let first!: Promise<boolean>;
  await act(() => { first = flow.saveRpe(completeActivity.id, 4); void flow.saveRpe(completeActivity.id, 4); });
  await act(() => flow.refreshActivities());
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', completeActivity, 4, undefined);
  const updated = { ...completeActivity, rpe: 4 };
  await act(async () => { server = [updated]; result.resolve(updated); await first; });
  expect(flow.activities[0]).toEqual(updated);
});

test('repeated templates on the same date remain independent planned-workout choices', async () => {
  const second = { ...workout, id: 'second-occurrence' };
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: [workout, second], rest_days: [] }));
  await render(<Host />);
  await act(() => flow.setDuration('45')); await act(() => flow.selectWorkout(second));
  await act(() => flow.refreshActivities()); expect(flow.workouts).toEqual([workout, second]);
  expect(flow.selectedWorkout).toBe(second);
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [pendingActivity]; return pendingActivity; });
  await act(() => flow.setDuration('45'));
  await act(() => flow.save());
  expect(api.createActivity).toHaveBeenCalledWith('token-a', expect.any(String), expect.objectContaining({ planned_workout_id: second.id }));
});


test('pending-only refresh cannot erase an in-flight feedback choice or its HR draft', async () => {
  server = [remote]; await render(<Host />);
  await act(() => flow.setDuration('45'));
  await act(() => flow.setHeartRateByActivity({ [remote.id]: '155' }));
  const response = deferred<CompletedActivity>();
  jest.mocked(api.submitActivityRpeWithRefresh).mockReturnValueOnce(response.promise);
  let mutation!: Promise<boolean>; await act(() => { mutation = flow.saveRpe(remote.id, 4); });
  server = []; await act(() => flow.refreshPendingRpe());
  expect(flow.feedbackActivity?.id).toBe(remote.id); expect(flow.heartRateByActivity[remote.id]).toBe('155');
  expect(flow.busy).toBe(true);
  const updated = { ...remote, ...completeActivity, id: remote.id };
  await act(async () => { server = [updated]; response.resolve(updated); await mutation; });
  expect(flow.pendingRpe).toEqual([]); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
});


test('refresh cannot rewrite the payload of an unresolved create when server timezone changes', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Unknown commit'));
  await act(() => flow.save()); const original = jest.mocked(api.createActivity).mock.calls[0];
  jest.mocked(api.getOnboarding).mockResolvedValue({ ...activityOnboarding, profile: { ...activityOnboarding.profile!, timezone: 'America/Los_Angeles' } });
  await act(() => flow.refreshActivities());
  expect(flow.error).toBe('Unknown commit');
  expect(flow.athleteTimezone).toBe('America/Los_Angeles');
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [pendingActivity]; return pendingActivity; });
  await act(() => flow.save());
  expect(jest.mocked(api.createActivity).mock.calls[1]).toEqual(original);
});

test('completed idempotent create replay reconciles the exact attempt and only then rotates its key', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Unknown commit'));
  await act(() => flow.save()); const key = jest.mocked(api.createActivity).mock.calls[0][1];
  server = [completeActivity]; await act(() => flow.refreshActivities());
  jest.mocked(api.createActivity).mockResolvedValueOnce(completeActivity);
  jest.mocked(api.listActivities).mockRejectedValueOnce(new Error('Confirmed replay refresh failed'));
  await act(() => flow.save());
  expect(flow.error).toBe('Confirmed replay refresh failed');
  await act(() => flow.refreshActivities());
  expect(flow.error).toBeNull();
  expect(jest.mocked(api.createActivity).mock.calls[1][1]).toBe(key);
  expect(flow.pendingRpe).toEqual([]);
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [remote]; return remote; });
  await act(() => flow.save());
  expect(jest.mocked(api.createActivity).mock.calls[2][1]).not.toBe(key);
});

test('definitively deleted locally created activity can be replaced only by a new explicit create', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [pendingActivity]; return pendingActivity; });
  await act(() => flow.save()); const key = jest.mocked(api.createActivity).mock.calls[0][1];
  server = []; await act(() => flow.refreshActivities());
  await act(() => flow.saveRpe(pendingActivity.id, 4));
  expect(flow.pendingRpe).toEqual([]); expect(api.createActivity).toHaveBeenCalledTimes(1);
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [remote]; return remote; });
  await act(() => flow.save());
  expect(api.createActivity).toHaveBeenCalledTimes(2);
  expect(jest.mocked(api.createActivity).mock.calls[1][1]).not.toBe(key);
});


test('authoritative remote feedback completion releases a known local create without an extra POST', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45'));
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [pendingActivity]; return pendingActivity; });
  await act(() => flow.save()); const firstKey = jest.mocked(api.createActivity).mock.calls[0][1];
  server = [completeActivity]; await act(() => flow.refreshActivities());
  expect(flow.pendingRpe).toEqual([]); expect(api.createActivity).toHaveBeenCalledTimes(1);
  jest.mocked(api.createActivity).mockImplementationOnce(async () => { server = [remote]; return remote; });
  await act(() => flow.save());
  expect(jest.mocked(api.createActivity).mock.calls[1][1]).not.toBe(firstKey);
});


test('rapid choices while exact activity GET is unresolved resolve and mutate once', async () => {
  await render(<Host />);
  await act(() => flow.setDuration('45')); server = [remote];
  const response = deferred<CompletedActivity>(); jest.mocked(api.getActivity).mockReturnValueOnce(response.promise);
  let first!: Promise<boolean>;
  await act(() => { first = flow.saveRpe(remote.id, 4); void flow.saveRpe(remote.id, 4); });
  expect(api.getActivity).toHaveBeenCalledTimes(1); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  await act(async () => { response.resolve(remote); await first; });
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
});

