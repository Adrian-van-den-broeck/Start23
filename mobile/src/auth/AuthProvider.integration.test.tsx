import { act, render } from '@testing-library/react-native';
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import { AuthProvider, useAuth } from './AuthProvider';
import { authFetch, AUTH_FETCH_DEADLINE_MS, getSupabaseClient } from '../lib/supabase';

jest.mock('../lib/supabase', () => {
  process.env.EXPO_PUBLIC_SUPABASE_URL = 'https://auth.start23.test';
  process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = 'test-publishable-key';
  return { ...jest.requireActual('../lib/supabase'), getSupabaseClient: jest.fn() };
});
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device' }));
let latest: ReturnType<typeof useAuth>;
let fetchMock: jest.MockedFunction<typeof fetch>;
let client: ReturnType<typeof createClient>;
function Probe() { latest = useAuth(); return null; }
async function flush() { await act(async () => { for (let i = 0; i < 60; i++) await Promise.resolve(); }); }
function sessionResponse() { return new Response(JSON.stringify({ access_token: 'access-A', refresh_token: 'rotated-A', expires_in: 3600, token_type: 'bearer', user: { id: 'A' } }), { status: 200, headers: { 'Content-Type': 'application/json' } }); }
beforeEach(() => {
  jest.useFakeTimers(); jest.clearAllMocks();
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue('original-A');
  jest.mocked(SecureStore.setItemAsync).mockResolvedValue(); jest.mocked(SecureStore.deleteItemAsync).mockResolvedValue();
  fetchMock = jest.fn(); global.fetch = fetchMock;
  client = createClient('https://auth.start23.test', 'test-publishable-key', { global: { fetch: authFetch }, auth: { autoRefreshToken: false, persistSession: false, detectSessionInUrl: false } });
  jest.mocked(getSupabaseClient).mockReturnValue(client);
});
afterEach(() => { client.auth.stopAutoRefresh(); jest.useRealTimers(); });

test('actual pinned Supabase refresh retries offline transport, preserves disk token and recovers after SDK cooldown', async () => {
  fetchMock.mockRejectedValue(new TypeError('Network request failed'));
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  await act(async () => { await jest.advanceTimersByTimeAsync(31_000); }); await flush();
  expect(latest).toMatchObject({ loading: false, session: null, recovery: 'network' });
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
  fetchMock.mockResolvedValue(sessionResponse());
  // auth-js 2.110.8 caches same-token failures for 60 seconds. Preserve that
  // provider protection rather than mutating its private cooldown state.
  await act(async () => { await jest.advanceTimersByTimeAsync(60_000); });
  await act(async () => { await latest.retry(); }); await flush();
  expect(latest.session?.user.id).toBe('A'); expect(latest.session?.refresh_token).toBe('rotated-A');
  expect(SecureStore.setItemAsync).toHaveBeenLastCalledWith('start23.refresh-token', 'rotated-A', expect.anything());
});
test('hung native Auth fetch aborts and actual SDK returns a classified timeout without clearing refresh credentials', async () => {
  fetchMock.mockReturnValue(new Promise(() => {}));
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  await act(async () => { await jest.advanceTimersByTimeAsync(44_000); }); await flush();
  expect(latest).toMatchObject({ loading: false, session: null, recovery: 'timeout' });
  expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true);
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});
test('actual SDK invalid grant event cannot turn a revoked token into a recoverable network error', async () => {
  fetchMock.mockResolvedValue(new Response(JSON.stringify({ code: 'refresh_token_not_found', msg: 'Revoked' }), { status: 400, headers: { 'X-Supabase-Api-Version': '2024-01-01' } }));
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  expect(latest).toMatchObject({ loading: false, session: null, recovery: null });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(1);
});
test('auth deadline covers a stalled body, and late body completion cannot escape timeout', async () => {
  fetchMock.mockResolvedValue({ status: 200, text: () => new Promise(() => {}) } as unknown as Response);
  const result = authFetch('https://auth.start23.test/token').catch(e => e);
  await jest.advanceTimersByTimeAsync(AUTH_FETCH_DEADLINE_MS);
  expect(await result).toMatchObject({ name: 'DeadlineError' }); expect(jest.getTimerCount()).toBe(0);
});
test('actual SDK late bootstrap A refresh cannot replace B sign-in or its durable rotated token', async () => {
  let resolveA!: (response: Response) => void;
  const a = new Promise<Response>(resolve => { resolveA = resolve; });
  fetchMock.mockImplementation(async (input) => {
    if (String(input).includes('grant_type=password')) return new Response(JSON.stringify({ access_token: 'access-B', refresh_token: 'refresh-B', expires_in: 3600, token_type: 'bearer', user: { id: 'B' } }), { status: 200 });
    return a;
  });
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  await act(async () => { await client.auth.signInWithPassword({ email: 'b@example.test', password: 'synthetic-test-password' }); }); await flush();
  expect(latest.session?.user.id).toBe('B');
  await act(async () => { resolveA(sessionResponse()); }); await flush();
  expect(latest.session?.user.id).toBe('B'); expect(latest.session?.refresh_token).toBe('refresh-B');
  expect(jest.mocked(SecureStore.setItemAsync).mock.calls.map(c => c[1])).toEqual(['refresh-B']);
});
test.each(['{}', '{"access_token":'])('malformed successful Auth refresh remains recoverable and never looks like revoked credentials (%s)', async body => {
  fetchMock.mockImplementation(async () => new Response(body, { status: 200 }));
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  await act(async () => { await jest.advanceTimersByTimeAsync(31_000); }); await flush();
  expect(latest).toMatchObject({ loading: false, session: null, recovery: 'unavailable' });
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});
test('explicit session_not_found from actual Auth API is definitive despite SDK class normalization', async () => {
  fetchMock.mockResolvedValue(new Response(JSON.stringify({ code: 'session_not_found', msg: 'Revoked session' }), { status: 400, headers: { 'X-Supabase-Api-Version': '2024-01-01' } }));
  await render(<AuthProvider><Probe /></AuthProvider>); await flush();
  expect(latest).toMatchObject({ loading: false, session: null, recovery: null });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(1);
});
