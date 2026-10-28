import * as api from './client';
import { activateApiToken, retireApiToken, cancelApiRequests } from '../lib/apiCancellation';
import { pendingActivity } from '../features/activities/activities.test-fixtures';

jest.mock('./client', () => {
  process.env.EXPO_PUBLIC_API_BASE_URL = 'https://api.start23.test';
  return jest.requireActual('./client');
});
function response(body: unknown, status = 200): Response { return { ok: status >= 200 && status < 300, status, json: async () => body } as Response; }
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(r => { resolve = r; }); return { promise, resolve }; }
let fetchMock: jest.MockedFunction<typeof fetch>;
beforeEach(() => { jest.useFakeTimers(); fetchMock = jest.fn(); global.fetch = fetchMock; });
afterEach(() => { jest.useRealTimers(); });

test('hung GET settles, aborts best effort, cleans timers and ignores completion after deadline', async () => {
  const late = deferred<Response>(); fetchMock.mockReturnValue(late.promise);
  const result = api.getActivity('A', pendingActivity.id).catch(e => e);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  expect(await result).toMatchObject({ code: 'request_timeout', method: 'GET', outcome: 'rejected', retryable: true });
  expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true);
  late.resolve(response(pendingActivity)); await Promise.resolve();
  expect(jest.getTimerCount()).toBe(0); expect(fetchMock).toHaveBeenCalledTimes(1);
});
test.each([
  ['activity POST', () => api.createActivity('A', 'original-key', { discipline: 'run', started_at: pendingActivity.started_at, timezone: pendingActivity.timezone, duration_minutes: '45' }), api.API_DEADLINE_MS, 'POST'],
  ['RPE PUT', () => api.submitActivityRpe('A', pendingActivity.id, 4, 151), api.API_DEADLINE_MS, 'PUT'],
  ['check-in proposal', () => api.createCheckInPlanProposal('A', 'original-check-in'), api.PLANNING_DEADLINE_MS, 'POST'],
  ['plan approval', () => api.approvePlanProposal('A', 'original-proposal', 2), api.API_DEADLINE_MS, 'POST'],
  ['workout movement', () => api.movePlannedWorkout('A', 'original-workout', 2, '2026-10-08'), api.API_DEADLINE_MS, 'PATCH'],
])('hung %s has unknown commit status and never repeats automatically', async (_name, operation, deadline, method) => {
  fetchMock.mockReturnValue(new Promise(() => {}));
  const result = operation().catch(e => e);
  await jest.advanceTimersByTimeAsync(deadline);
  expect(await result).toMatchObject({ code: 'request_timeout', outcome: 'unknown', method });
  expect(fetchMock).toHaveBeenCalledTimes(1); expect(jest.getTimerCount()).toBe(0);
});
test('deadline includes never-settling successful response body', async () => {
  fetchMock.mockResolvedValue({ ok: true, status: 200, json: () => new Promise(() => {}) } as unknown as Response);
  const result = api.submitActivityRpe('A', pendingActivity.id, 4).catch(e => e);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  expect(await result).toMatchObject({ code: 'request_timeout', status: 200, outcome: 'unknown' });
});
test('overlapping reads settle independently; cancelling A cannot cancel B', async () => {
  fetchMock.mockReturnValue(new Promise(() => {}));
  const a = api.getActivity('A', 'activity-a').catch(e => e);
  const b = api.getActivity('B', 'activity-b').catch(e => e);
  cancelApiRequests('A'); await Promise.resolve();
  expect(await a).toMatchObject({ code: 'request_cancelled', retryable: false });
  expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true);
  expect(fetchMock.mock.calls[1][1]?.signal?.aborted).toBe(false);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  expect(await b).toMatchObject({ code: 'request_timeout' }); expect(jest.getTimerCount()).toBe(0);
});
test('caller cancellation before dispatch is definitely unsent; after dispatch remains ambiguous', async () => {
  const caller = new AbortController(); caller.abort();
  await expect(api.request('A', '/api/v1/activities', { method: 'POST', signal: caller.signal })).rejects.toMatchObject({ code: 'request_cancelled', outcome: 'rejected' });
  expect(fetchMock).not.toHaveBeenCalled();
  fetchMock.mockReturnValue(new Promise(() => {}));
  const result = api.createActivity('A', 'key', { discipline: 'run', started_at: pendingActivity.started_at, timezone: pendingActivity.timezone, duration_minutes: '45' }).catch(e => e);
  cancelApiRequests('A');
  expect(await result).toMatchObject({ code: 'request_cancelled', outcome: 'unknown' });
  expect(jest.getTimerCount()).toBe(0);
});
test('late server commit after client cancellation is not fabricated as success or retried', async () => {
  const pending = deferred<Response>(); fetchMock.mockReturnValue(pending.promise);
  const result = api.submitActivityRpe('A', pendingActivity.id, 4).catch(e => e);
  cancelApiRequests('A'); const error = await result;
  pending.resolve(response({ ...pendingActivity, rpe: 4, processing_state: 'complete' }));
  await Promise.resolve(); expect(error.outcome).toBe('unknown'); expect(fetchMock).toHaveBeenCalledTimes(1);
});
test('definitive rejection remains distinguishable from uncertain server error', async () => {
  fetchMock.mockResolvedValueOnce(response({ error: { code: 'activity_correction_stale' } }, 409)).mockResolvedValueOnce(response({}, 503));
  await expect(api.submitActivityRpe('A', pendingActivity.id, 4)).rejects.toMatchObject({ outcome: 'rejected', status: 409 });
  await expect(api.submitActivityRpe('A', pendingActivity.id, 4)).rejects.toMatchObject({ outcome: 'unknown', status: 503 });
  expect(jest.getTimerCount()).toBe(0);
});
test('retiring an auth token also stops an onboarding GET retry sleeping between attempts', async () => {
  activateApiToken('retired-owner');
  fetchMock.mockRejectedValue(new TypeError('offline'));
  const result = api.getOnboarding('retired-owner').catch(e => e);
  await jest.advanceTimersByTimeAsync(1);
  retireApiToken('retired-owner', Date.now() + 60_000);
  await jest.advanceTimersByTimeAsync(400);
  expect(await result).toMatchObject({ code: 'request_cancelled', retryable: false });
  expect(fetchMock).toHaveBeenCalledTimes(1); expect(jest.getTimerCount()).toBe(0);
  activateApiToken('retired-owner');
});
test('WOMBO-012 never-settling fetch must settle within five simulated minutes', async () => {
  fetchMock.mockReturnValue(new Promise(() => {}));
  let settled = false;
  void api.getActivity('A', pendingActivity.id).then(() => { settled = true; }, () => { settled = true; });
  await jest.advanceTimersByTimeAsync(300_000);
  expect(settled).toBe(true);
});
test.each([200, 404])('late HTTP %s after a suspended JS clock deadline cannot win ahead of the delayed timer', async status => {
  const pending = deferred<Response>(); fetchMock.mockReturnValue(pending.promise);
  const result = api.getActivity('A', pendingActivity.id).catch(e => e);
  jest.setSystemTime(Date.now() + api.API_DEADLINE_MS + 1);
  pending.resolve(response(status === 200 ? pendingActivity : {}, status));
  expect(await result).toMatchObject({ code: 'request_timeout', status: null });
  expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true); expect(jest.getTimerCount()).toBe(0);
});
