import type * as Client from './client';

function deferred<T>() { let resolve!: (value: T) => void;
  const promise = new Promise<T>(yes => { resolve = yes; }); return { promise, resolve }; }
const response = (body: unknown) => ({ ok: true, status: 200, json: async () => body }) as Response;
let client: typeof Client;
let fetchMock: jest.Mock;
const originalFetch = global.fetch;
beforeEach(() => {
  jest.resetModules(); process.env.EXPO_PUBLIC_API_BASE_URL = 'https://synthetic.local';
  client = require('./client'); fetchMock = jest.fn(); global.fetch = fetchMock;
});
afterEach(() => { global.fetch = originalFetch; jest.useRealTimers(); });

test('only overlapping identical owner reads share the actual transport; settled reads stay fresh', async () => {
  const read = deferred<Response>(); fetchMock.mockReturnValueOnce(read.promise);
  const a = client.getOnboarding('a'), b = client.getOnboarding('a');
  expect(fetchMock).toHaveBeenCalledTimes(1);
  read.resolve(response({ current_step: 'completed', onboarding_revision: 1 }));
  expect(await a).toEqual(await b);
  fetchMock.mockResolvedValueOnce(response({ onboarding_revision: 2 }));
  expect((await client.getOnboarding('a')).onboarding_revision).toBe(2);
  expect(fetchMock).toHaveBeenCalledTimes(2);
  const signal = fetchMock.mock.calls[1][1].signal as AbortSignal;
  const { cancelApiRequests } = require('../lib/apiCancellation') as typeof import('../lib/apiCancellation');
  cancelApiRequests('a'); expect(signal.aborted).toBe(false);
});

test('different verified token lifetimes never share an onboarding response', async () => {
  const a = deferred<Response>(), b = deferred<Response>();
  fetchMock.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
  const readA = client.getOnboarding('a'), readB = client.getOnboarding('b');
  expect(fetchMock).toHaveBeenCalledTimes(2);
  b.resolve(response({ initial_plan_request_id: 'b-request' }));
  expect((await readB).initial_plan_request_id).toBe('b-request');
  a.resolve(response({ initial_plan_request_id: 'a-request' }));
  expect((await readA).initial_plan_request_id).toBe('a-request');
});

test('write start and settlement fence old and mid-write reads from authoritative refresh', async () => {
  const before = deferred<Response>(), write = deferred<Response>(), during = deferred<Response>(), after = deferred<Response>();
  fetchMock.mockReturnValueOnce(before.promise).mockReturnValueOnce(write.promise)
    .mockReturnValueOnce(during.promise).mockReturnValueOnce(after.promise);
  const oldRead = client.getOnboarding('a');
  const saving = client.saveOperationalProfile('a', { heart_rate_monitor_confirmed: true });
  const midRead = client.getOnboarding('a');
  before.resolve(response({ onboarding_revision: 1 })); await oldRead;
  // Late cleanup from the pre-write request cannot erase the newer flight.
  const joined = client.getOnboarding('a'); expect(fetchMock).toHaveBeenCalledTimes(3);
  write.resolve(response({})); await saving;
  const current = client.getOnboarding('a'); expect(fetchMock).toHaveBeenCalledTimes(4);
  during.resolve(response({ onboarding_revision: 1 }));
  after.resolve(response({ onboarding_revision: 2 }));
  expect(await midRead).toEqual(await joined);
  expect((await current).onboarding_revision).toBe(2);
  expect(fetchMock.mock.calls.filter(([, init]) => init.method === 'PATCH')).toHaveLength(1);
});

test('retiring an owner cancels a shared read once and never retries its token', async () => {
  const pending = deferred<Response>(); fetchMock.mockReturnValueOnce(pending.promise);
  const a = client.getOnboarding('a').catch(error => error), b = client.getOnboarding('a').catch(error => error);
  const { retireApiToken } = require('../lib/apiCancellation') as typeof import('../lib/apiCancellation');
  retireApiToken('a', Date.now() + 60_000);
  expect(await a).toMatchObject({ code: 'request_cancelled' });
  expect(await b).toMatchObject({ code: 'request_cancelled' });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  pending.resolve(response({ initial_plan_request_id: 'old-a' }));
  fetchMock.mockResolvedValueOnce(response({ initial_plan_request_id: 'b' }));
  expect((await client.getOnboarding('b')).initial_plan_request_id).toBe('b');
});

test('a hung shared read settles through the A8 deadlines and existing read retries', async () => {
  jest.useFakeTimers();
  const late: ReturnType<typeof deferred<Response>>[] = [];
  fetchMock.mockImplementation(() => { const read = deferred<Response>(); late.push(read); return read.promise; });
  const a = client.getOnboarding('a').catch(error => error), b = client.getOnboarding('a').catch(error => error);
  await jest.advanceTimersByTimeAsync(140_000);
  expect(await a).toMatchObject({ code: 'request_timeout', outcome: 'rejected' });
  expect(await b).toMatchObject({ code: 'request_timeout', outcome: 'rejected' });
  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(fetchMock.mock.calls.every(([, init]) => init.signal.aborted)).toBe(true);
  expect(jest.getTimerCount()).toBe(0);
  for (const read of late) read.resolve(response({ initial_plan_request_id: 'late' }));
  fetchMock.mockResolvedValueOnce(response({ initial_plan_request_id: 'current' }));
  expect((await client.getOnboarding('a')).initial_plan_request_id).toBe('current');
});
