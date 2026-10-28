import { act, render } from '@testing-library/react-native';
import { AppState, type AppStateStatus } from 'react-native';
import { AuthApiError, AuthRetryableFetchError, AuthUnknownError, type AuthChangeEvent, type Session } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import { AuthProvider, AUTH_REFRESH_DEADLINE_MS, useAuth } from './AuthProvider';
import { getSupabaseClient } from '../lib/supabase';

jest.mock('../lib/supabase', () => ({ getSupabaseClient: jest.fn(), supabaseConfigurationError: null }));
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device' }));
let latest: ReturnType<typeof useAuth>;
let event: (event: AuthChangeEvent, session: Session | null) => void;
let foreground: (state: AppStateStatus) => void;
const refreshSession = jest.fn();
const signOut = jest.fn();
function Probe() { latest = useAuth(); return null; }
function session(owner = 'A', refresh = 'rotated-A'): Session {
  return { access_token: `access-${owner}`, refresh_token: refresh, expires_at: Date.now() / 1000 + 3600, expires_in: 3600, token_type: 'bearer', user: { id: owner } } as Session;
}
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(r => { resolve = r; }); return { promise, resolve }; }
const success = (s = session()) => ({ data: { session: s, user: s.user }, error: null });
const failure = (error: Error) => ({ data: { session: null, user: null }, error });
async function mount() { return render(<AuthProvider><Probe /></AuthProvider>); }
async function flush() { await act(async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); }); }
beforeEach(() => {
  jest.useFakeTimers(); jest.clearAllMocks();
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue('original-A');
  jest.mocked(SecureStore.setItemAsync).mockResolvedValue();
  jest.mocked(SecureStore.deleteItemAsync).mockResolvedValue();
  refreshSession.mockResolvedValue(success()); signOut.mockResolvedValue({ error: null });
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_name, handler) => { foreground = handler; return { remove: jest.fn() }; });
  jest.mocked(getSupabaseClient).mockReturnValue({ auth: { refreshSession, signOut, startAutoRefresh: jest.fn(), stopAutoRefresh: jest.fn(), onAuthStateChange: (cb: typeof event) => { event = cb; return { data: { subscription: { unsubscribe: jest.fn() } } }; } } } as unknown as ReturnType<typeof getSupabaseClient>);
});
afterEach(() => { jest.restoreAllMocks(); jest.useRealTimers(); });

test('online startup persists rotation and publishes a valid access token', async () => {
  await mount(); await flush();
  expect(latest.session?.user.id).toBe('A'); expect(latest.loading).toBe(false);
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.refresh-token', 'rotated-A', expect.anything());
});
test('offline bootstrap preserves token, reports recovery and online retry succeeds', async () => {
  refreshSession.mockResolvedValueOnce(failure(new AuthRetryableFetchError('offline', 0)));
  await mount(); await flush();
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
  expect(latest).toMatchObject({ session: null, loading: false, recovery: 'network' });
  await act(async () => { await latest.retry(); });
  expect(refreshSession.mock.calls.map(c => c[0])).toEqual([{ refresh_token: 'original-A' }, { refresh_token: 'original-A' }]);
  expect(latest.session?.user.id).toBe('A');
});
test.each([
  [new AuthRetryableFetchError('outage', 503), 'provider'],
  [new AuthApiError('rate limited', 429, 'over_request_rate_limit'), 'provider'],
  [new AuthApiError('timeout', 408, 'request_timeout'), 'timeout'],
  [new AuthUnknownError('decode', new SyntaxError('broken')), 'unavailable'],
  [new AuthApiError('unexpected 400', 400, 'validation_failed'), 'unavailable'],
])('temporary or unclassified failure preserves credentials (%s)', async (error, recovery) => {
  refreshSession.mockResolvedValue(failure(error)); await mount(); await flush();
  expect(latest.recovery).toBe(recovery); expect(latest.loading).toBe(false);
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});
test.each(['refresh_token_not_found', 'refresh_token_already_used', 'session_expired'])('verified invalid credential %s is cleared and never retried', async code => {
  refreshSession.mockResolvedValue(failure(new AuthApiError('invalid', 400, code)));
  await mount(); await flush(); await act(async () => { await latest.retry(); });
  expect(latest.session).toBeNull(); expect(latest.recovery).toBeNull();
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(1); expect(refreshSession).toHaveBeenCalledTimes(1);
});
test('SecureStore read failure is explicit, preserves storage, and is retryable', async () => {
  jest.mocked(SecureStore.getItemAsync).mockRejectedValueOnce(new Error('keychain locked'));
  await mount(); await flush(); expect(latest.recovery).toBe('storage_read'); expect(refreshSession).not.toHaveBeenCalled();
  await act(async () => { await latest.retry(); }); expect(latest.session?.user.id).toBe('A');
});
test('failed secure write retries the rotated in-memory token, never the older disk token', async () => {
  jest.mocked(SecureStore.setItemAsync).mockRejectedValueOnce(new Error('keychain locked'));
  await mount(); await flush(); expect(latest.recovery).toBe('storage_write');
  await act(async () => { await latest.retry(); });
  expect(refreshSession.mock.calls[1][0]).toEqual({ refresh_token: 'rotated-A' });
  expect(latest.recovery).toBeNull(); expect(latest.session?.user.id).toBe('A');
});
test('overlapping retry and background/foreground coalesce; late rotation cannot overwrite newer event', async () => {
  const pending = deferred<ReturnType<typeof success>>(); refreshSession.mockReturnValue(pending.promise);
  await mount(); await flush();
  await act(async () => { void latest.retry(); foreground('background'); foreground('active'); });
  expect(refreshSession).toHaveBeenCalledTimes(1);
  await act(async () => { event('TOKEN_REFRESHED', session('A', 'newer')); event('TOKEN_REFRESHED', session('A', 'older')); pending.resolve(success(session('A', 'older'))); }); await flush();
  expect(latest.session?.refresh_token).toBe('newer');
  expect(jest.mocked(SecureStore.setItemAsync).mock.calls.map(c => c[1])).toEqual(['newer']);
});
test('logout during refresh prevents late token/session resurrection', async () => {
  const pending = deferred<ReturnType<typeof success>>(); refreshSession.mockReturnValue(pending.promise);
  await mount(); await flush(); await act(async () => { await latest.signOut(); });
  await act(async () => { event('TOKEN_REFRESHED', session()); pending.resolve(success()); }); await flush();
  expect(latest.session).toBeNull(); expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(1);
});
test('B sign-in isolates a late A refresh, error, and initial empty SDK event', async () => {
  const pending = deferred<ReturnType<typeof success>>(); refreshSession.mockReturnValue(pending.promise);
  await mount(); await flush();
  await act(async () => { event('SIGNED_IN', session('B', 'refresh-B')); event('INITIAL_SESSION', null); event('TOKEN_REFRESHED', session()); pending.resolve(success()); }); await flush();
  expect(latest.session?.user.id).toBe('B');
  expect(jest.mocked(SecureStore.setItemAsync).mock.calls.map(c => c[1])).toEqual(['refresh-B']);
});
test('deadline settles bootstrap, preserves token, and discards result after unmount', async () => {
  const pending = deferred<ReturnType<typeof success>>(); refreshSession.mockReturnValue(pending.promise);
  const view = await mount(); await flush();
  await act(async () => { await jest.advanceTimersByTimeAsync(AUTH_REFRESH_DEADLINE_MS); });
  expect(latest).toMatchObject({ session: null, recovery: 'timeout', loading: false });
  await view.unmount(); pending.resolve(success()); await flush();
  expect(SecureStore.setItemAsync).not.toHaveBeenCalled(); expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});
test('restart after recoverable failure reads the preserved original credential', async () => {
  refreshSession.mockResolvedValueOnce(failure(new AuthRetryableFetchError('offline', 0)));
  const first = await mount(); await flush(); await first.unmount();
  await mount(); await flush(); expect(latest.session?.user.id).toBe('A');
  expect(refreshSession.mock.calls.map(c => c[0])).toEqual([{ refresh_token: 'original-A' }, { refresh_token: 'original-A' }]);
});
test('serialized keychain writes finish on B even when an A write is already in progress', async () => {
  const pending = deferred<void>(); jest.mocked(SecureStore.setItemAsync).mockReturnValueOnce(pending.promise);
  await mount(); await flush();
  await act(async () => { event('SIGNED_IN', session('B', 'refresh-B')); });
  expect(SecureStore.setItemAsync).toHaveBeenCalledTimes(1);
  await act(async () => { pending.resolve(); }); await flush();
  expect(jest.mocked(SecureStore.setItemAsync).mock.calls.map(c => c[1])).toEqual(['rotated-A', 'refresh-B']);
  expect(latest.session?.user.id).toBe('B');
});
test('logout keeps the sign-in gate busy until the bounded SDK cleanup settles', async () => {
  await mount(); await flush();
  const pending = deferred<{ error: null }>(); signOut.mockReturnValue(pending.promise);
  await act(async () => { void latest.signOut(); }); await flush();
  expect(latest.session).toBeNull(); expect(latest.loading).toBe(true);
  await act(async () => { await jest.advanceTimersByTimeAsync(60_000); });
  expect(latest.loading).toBe(false); expect(latest.session).toBeNull();
  await act(async () => { pending.resolve({ error: null }); event('SIGNED_OUT', null); });
  expect(latest.session).toBeNull();
});
