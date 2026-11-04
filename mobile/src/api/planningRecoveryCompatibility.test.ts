import { activePlan } from '../features/planning/planning.test-fixtures';
import { pendingNext } from '../features/planning/planningTask.test-fixtures';
import { pendingActivity } from '../features/activities/activities.test-fixtures';
import { planningRecoveryFailure, recoveryEndpointAbsent } from './planningRecovery';

const path = '/api/v1/weekly-plans/recovery';
const oldSchema = jest.requireActual('../../../docs/releases/evidence/remediation/observed-live-contract.json') as {
  openapi: string; paths: Record<string, unknown>;
  activity_input: { additionalProperties: boolean; properties: Record<string, unknown> };
};
const newSchema = { openapi: '3.1.0', paths: { [path]: { get: {} } } };
function response(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}
function loadClient() {
  jest.resetModules();
  process.env.EXPO_PUBLIC_API_BASE_URL = 'https://api.start23.test';
  const fetchMock = jest.fn(); global.fetch = fetchMock;
  return { client: jest.requireActual('./client') as typeof import('./client'), fetchMock };
}

test.each([
  { active: null, pending: null, draft: null },
  { active: activePlan, pending: pendingNext, draft: null },
])('new backend preserves exact authoritative empty/known recovery without capability requests', async recovery => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(200, recovery));
  await expect(client.discoverPlanning('token-a')).resolves.toEqual(recovery);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toBe(`https://api.start23.test${path}`);
});

test.each([404, 405, 422])('old backend %s plus absent advertised GET is unavailable, never empty', async status => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(status, {})).mockResolvedValueOnce(response(200, oldSchema));
  await expect(client.discoverPlanning('token-a')).rejects.toMatchObject({ name: 'PlanningRecoveryEndpointUnavailableError' });
  expect(fetchMock.mock.calls.map(call => call[0])).toEqual([`https://api.start23.test${path}`, 'https://api.start23.test/openapi.json']);
  expect(fetchMock.mock.calls.every(call => !call[1].method || call[1].method === 'GET')).toBe(true);
});

test.each([newSchema, {}, { openapi: '3.1.0', paths: [] }, { openapi: '3.1.0', paths: { [path]: null } }])('404 with advertised or unverifiable capability remains unknown %j', async schema => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(404, {})).mockResolvedValueOnce(response(200, schema));
  await expect(client.discoverPlanning('token-a')).rejects.toMatchObject({ name: 'ApiRequestError', status: 404 });
});

test('failed capability read retains the original failure rather than claiming endpoint absence', async () => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(422, {})).mockRejectedValueOnce(new TypeError('Offline'));
  await expect(client.discoverPlanning('token-a')).rejects.toMatchObject({ status: 422 });
});

test.each([401, 403, 500, 503])('auth/transient %s is preserved without compatibility fallback', async status => {
  const { client, fetchMock } = loadClient(); fetchMock.mockResolvedValueOnce(response(status, {}));
  await expect(client.discoverPlanning('token-a')).rejects.toMatchObject({ status });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test.each([
  [401, null, 'authentication'], [403, null, 'authorization'], [404, null, 'unknown'],
  [422, null, 'unknown'], [503, null, 'transient'], [null, 'network_unavailable', 'transient'],
  [200, 'response_invalid', 'unknown'], [200, 'response_unreadable', 'unknown'],
] as const)('failure classification preserves %s/%s as %s', (status, code, expected) => {
  expect(planningRecoveryFailure({ status, code })).toBe(expected);
});

test('capability evidence never treats a malformed schema as authoritative absence', () => {
  expect(recoveryEndpointAbsent(oldSchema)).toBe(true);
  for (const value of [null, {}, { openapi: '3.1.0' }, { openapi: '3.1.0', paths: [] }, newSchema]) expect(recoveryEndpointAbsent(value)).toBe(false);
});

test('activity transport matches the exact observed older input schema and keeps retry identity', async () => {
  const { client, fetchMock } = loadClient();
  fetchMock.mockResolvedValueOnce(response(201, pendingActivity));
  await client.createActivity('token-a', 'stable-retry-key', {
    discipline: 'run', started_at: '2026-11-04T10:00:00Z', timezone: 'Europe/Amsterdam',
    duration_minutes: '37', performed_duration_confirmed: true,
  });
  const payload = JSON.parse(fetchMock.mock.calls[0][1].body as string) as Record<string, unknown>;
  expect(oldSchema.activity_input.additionalProperties).toBe(false);
  expect(Object.keys(payload).every(key => key in oldSchema.activity_input.properties)).toBe(true);
  expect(payload).not.toHaveProperty('performed_duration_confirmed');
  expect(fetchMock.mock.calls[0][1].headers['Idempotency-Key']).toBe('stable-retry-key');
});
