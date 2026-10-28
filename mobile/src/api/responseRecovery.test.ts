import * as api from './client';
import type { CompletedActivity } from './types';
import { pendingActivity } from '../features/activities/activities.test-fixtures';
import { savedCheckIn } from '../features/checkins/checkIn.test-fixtures';
import { pendingNext } from '../features/planning/planningTask.test-fixtures';

jest.mock('./client', () => { process.env.EXPO_PUBLIC_API_BASE_URL = 'https://api.start23.test'; return jest.requireActual('./client'); });
let fetchMock: jest.MockedFunction<typeof fetch>;
function response(body: unknown, status = 200): Response { return { ok: status >= 200 && status < 300, status, json: async () => body } as Response; }
function broken(): Response { return { ok: true, status: 200, json: async () => { throw new SyntaxError('raw health data and token must never be public'); } } as unknown as Response; }
function completed(rpe = 4): CompletedActivity { return { ...pendingActivity, rpe, processing_state: 'complete', qualitative_result: 'unplanned', rpe_submitted_at: '2026-10-06T11:00:00Z', metrics: { average_heart_rate_bpm: 151, max_heart_rate_bpm: null, normalized_power_watts: null, average_speed_kmh: null, max_speed_kmh: null, average_pace_seconds_per_km: null, zone_minutes: null, low_intensity_minutes: null, high_intensity_minutes: null } }; }
beforeEach(() => { jest.useFakeTimers(); fetchMock = jest.fn(); global.fetch = fetchMock; });
afterEach(() => jest.useRealTimers());

test('WOMBO-013 malformed JSON after committed RPE performs exact read-back without repeating PUT', async () => {
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response(completed()));
  await expect(api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151)).resolves.toEqual(completed());
  expect(fetchMock.mock.calls.map(c => c[1]?.method ?? 'GET')).toEqual(['PUT', 'GET']);
  expect(fetchMock.mock.calls[1][0]).toBe(`https://api.start23.test/api/v1/activities/${pendingActivity.id}`);
});
test.each([null, {}, [], { ...pendingActivity, processing_state: 'complete' }, { ...completed(), id: 'foreign' }, { ...completed(), metrics: { average_heart_rate_bpm: '151' } }])('invalid RPE response is ambiguous and verifies authoritative matching state (%#)', async body => {
  fetchMock.mockResolvedValueOnce(response(body)).mockResolvedValueOnce(response(completed()));
  await expect(api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151)).resolves.toEqual(completed());
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
test('unreadable RPE then failed verification preserves write HTTP context and unknown outcome', async () => {
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response({}, 404));
  const error: unknown = await api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151).catch(e => e);
  expect(error).toMatchObject({ name: 'ApiRequestError', status: 200, method: 'PUT', code: 'response_unreadable', outcome: 'unknown', retryable: true });
  expect(String(error)).not.toContain('raw health data'); expect(fetchMock).toHaveBeenCalledTimes(2);
});
test('read-back of old state does not automatically repeat an uncertain RPE write', async () => {
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response(pendingActivity));
  await expect(api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151)).rejects.toMatchObject({ outcome: 'unknown', status: 200 });
  expect(fetchMock.mock.calls.map(c => c[1]?.method ?? 'GET')).toEqual(['PUT', 'GET']);
});
test('hung RPE after server commit resolves from authoritative GET; timeout before commit stays unknown', async () => {
  fetchMock.mockReturnValueOnce(new Promise(() => {})).mockResolvedValueOnce(response(completed()));
  const committed = api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  await expect(committed).resolves.toEqual(completed());
  fetchMock.mockReturnValueOnce(new Promise(() => {})).mockResolvedValueOnce(response(pendingActivity));
  const notYetCommitted = api.submitActivityRpeWithRefresh('A', pendingActivity, 4, 151).catch(e => e);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  expect(await notYetCommitted).toMatchObject({ outcome: 'unknown', code: 'request_timeout' });
  expect(fetchMock.mock.calls.map(c => c[1]?.method ?? 'GET')).toEqual(['PUT', 'GET', 'PUT', 'GET']);
});
test('malformed successful create preserves ambiguity and leaves replay to explicit original-key action', async () => {
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response(pendingActivity));
  const input = { discipline: 'run' as const, started_at: pendingActivity.started_at, timezone: pendingActivity.timezone, duration_minutes: '45' };
  await expect(api.createActivity('A', 'original-key', input)).rejects.toMatchObject({ outcome: 'unknown', status: 200, method: 'POST', code: 'response_unreadable' });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await expect(api.createActivity('A', 'original-key', input)).resolves.toEqual(pendingActivity);
  expect(fetchMock.mock.calls[1][1]?.headers).toEqual(fetchMock.mock.calls[0][1]?.headers);
  expect(fetchMock.mock.calls[1][1]?.body).toBe(fetchMock.mock.calls[0][1]?.body);
});
test.each([null, {}, { ...pendingActivity, id: 'wrong' }, { ...completed(), rpe: '4' }])('invalid read DTO fails closed without a fabricated activity (%#)', async body => {
  fetchMock.mockResolvedValueOnce(response(body));
  await expect(api.getActivity('A', pendingActivity.id)).rejects.toMatchObject({ code: 'response_invalid', status: 200, outcome: 'rejected', retryable: true });
});
test('malformed read is recoverable with no raw parser error', async () => {
  fetchMock.mockResolvedValueOnce(broken());
  await expect(api.getActivity('A', pendingActivity.id)).rejects.toMatchObject({ name: 'ApiRequestError', code: 'response_unreadable', outcome: 'rejected' });
});
test.each([null, [], { error: null }, { error: { code: ['raw data'], details: { violations: 'broken' } } }])('untrusted error envelope cannot escape as TypeError or raw data (%#)', async body => {
  fetchMock.mockResolvedValueOnce(response(body, 422));
  await expect(api.submitActivityRpe('A', pendingActivity.id, 4)).rejects.toMatchObject({ name: 'ApiRequestError', status: 422, code: null, outcome: 'rejected' });
});
test('invalid plan attachment/approval/recovery projections are never adopted', async () => {
  fetchMock.mockResolvedValueOnce(response({ plan: pendingNext, proposal: { ...pendingNext.proposal, target_plan_revision_id: 'wrong' } }))
    .mockResolvedValueOnce(response({ state: 'applied', plan_id: null, active_revision: '1' }))
    .mockResolvedValueOnce(response({ active: {}, pending: null, draft: null }));
  await expect(api.createCheckInPlanProposal('A', 'check-in-a')).rejects.toMatchObject({ code: 'response_invalid', outcome: 'unknown' });
  await expect(api.approvePlanProposal('A', 'proposal-a', 0)).rejects.toMatchObject({ code: 'response_invalid', outcome: 'unknown' });
  await expect(api.discoverPlanning('A')).rejects.toMatchObject({ code: 'response_invalid', outcome: 'rejected' });
});
test('check-in confirmation with malformed success reads exact original revision/fingerprint, never POSTs twice', async () => {
  const confirmed = { ...savedCheckIn, context: { ...savedCheckIn.context!, state: 'confirmed', confirmed_at: '2026-10-26T12:00:00Z' } };
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response(confirmed));
  await expect(api.confirmWeeklyCheckInContext('A', savedCheckIn.id, 4, savedCheckIn.context!.fingerprint)).resolves.toEqual(confirmed);
  expect(fetchMock.mock.calls.map(c => c[1]?.method ?? 'GET')).toEqual(['POST', 'GET']);
});
test('check-in confirmation cannot infer success from another fingerprint', async () => {
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response({ ...savedCheckIn, context: { ...savedCheckIn.context!, state: 'confirmed', fingerprint: 'other' } }));
  await expect(api.confirmWeeklyCheckInContext('A', savedCheckIn.id, 4, savedCheckIn.context!.fingerprint)).rejects.toMatchObject({ outcome: 'unknown', status: 200 });
});
test('check-in context timeout after commit returns only an exact authoritative answer/revision match', async () => {
  const { blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged } = savedCheckIn.context!;
  const input = { expected_revision: savedCheckIn.context_revision - 1, blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged };
  fetchMock.mockReturnValueOnce(new Promise(() => {})).mockResolvedValueOnce(response(savedCheckIn));
  const result = api.saveWeeklyCheckInContext('A', savedCheckIn.id, input);
  await jest.advanceTimersByTimeAsync(api.API_DEADLINE_MS);
  await expect(result).resolves.toEqual(savedCheckIn);
  expect(fetchMock.mock.calls.map(c => c[1]?.method ?? 'GET')).toEqual(['PUT', 'GET']);
});
test('check-in context with changed professional advice cannot be acknowledged as the original uncertain save', async () => {
  const { blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged } = savedCheckIn.context!;
  const input = { expected_revision: savedCheckIn.context_revision - 1, blocked_dates, fatigue_level, missed_workout_reasons, recurring_activities_confirmed, external_activities, restrictions, alarm_symptoms_acknowledged };
  fetchMock.mockResolvedValueOnce(broken()).mockResolvedValueOnce(response({ ...savedCheckIn, context: { ...savedCheckIn.context!, restrictions: [] } }));
  await expect(api.saveWeeklyCheckInContext('A', savedCheckIn.id, input)).rejects.toMatchObject({ code: 'response_unreadable', outcome: 'unknown' });
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
test('HTTP 408 write response remains ambiguous, never a proof of server rollback', async () => {
  fetchMock.mockResolvedValue(response({}, 408));
  await expect(api.submitActivityRpe('A', pendingActivity.id, 4)).rejects.toMatchObject({ status: 408, outcome: 'unknown', retryable: true });
});
