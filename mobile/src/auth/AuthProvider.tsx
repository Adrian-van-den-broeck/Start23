import { isAuthApiError, isAuthRetryableFetchError, isAuthSessionMissingError, type Session } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import {
  createContext, type PropsWithChildren, useContext, useEffect, useMemo, useRef, useState,
} from 'react';
import { AppState, Platform } from 'react-native';

import { getSupabaseClient, supabaseConfigurationError } from '../lib/supabase';
import { DeadlineError, withDeadline } from '../lib/deadline';
import { cancelApiRequests } from '../lib/apiCancellation';

const refreshTokenKey = 'start23.refresh-token';
export const AUTH_REFRESH_DEADLINE_MS = 45_000;
export type AuthRecovery = 'network' | 'timeout' | 'provider' | 'storage_read' | 'storage_write' | 'unavailable';

export function classifyRefreshError(error: unknown): AuthRecovery | 'invalid' {
  if (isAuthSessionMissingError(error)) return 'invalid';
  if (isAuthApiError(error) && [
    'refresh_token_not_found', 'refresh_token_already_used', 'session_not_found',
    'session_expired', 'user_not_found', 'user_banned',
  ].includes(error.code ?? '')) return 'invalid';
  if (error instanceof DeadlineError || (isAuthApiError(error) && error.code === 'request_timeout')) return 'timeout';
  if (isAuthRetryableFetchError(error)) return error.status && error.status >= 500 ? 'provider' : 'network';
  if (isAuthApiError(error) && (error.status === 429 || error.status >= 500)) return 'provider';
  // Unknown/client errors are not proof that a persisted credential is revoked.
  return 'unavailable';
}

type AuthContextValue = {
  session: Session | null;
  loading: boolean;
  recovery: AuthRecovery | null;
  retry: () => Promise<void>;
  configurationError: string | null;
  signOut: () => Promise<void>;
};
const AuthContext = createContext<AuthContextValue | null>(null);

async function readRefreshToken(): Promise<string | null> {
  return Platform.OS === 'web' ? null : SecureStore.getItemAsync(refreshTokenKey);
}
async function writeRefreshToken(token: string | null): Promise<void> {
  if (Platform.OS === 'web') return;
  if (token === null) await SecureStore.deleteItemAsync(refreshTokenKey);
  else await SecureStore.setItemAsync(refreshTokenKey, token, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}
function usable(session: Session | null): session is Session {
  return !!session?.access_token && !!session.expires_at && session.expires_at * 1000 > Date.now();
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [recovery, setRecovery] = useState<AuthRecovery | null>(null);
  const actions = useRef({ retry: async () => {}, signOut: async () => {} });

  useEffect(() => {
    if (supabaseConfigurationError) { setLoading(false); return; }
    const auth = getSupabaseClient().auth;
    let alive = true;
    let epoch = 0;
    let token: string | null | undefined;
    let current: Session | null = null;
    let flight: { epoch: number; token: string | null | undefined; promise: Promise<void> } | null = null;
    let writes = Promise.resolve();
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;
    let expiryTimer: ReturnType<typeof setTimeout> | undefined;
    let foreground = AppState.currentState === 'active' || AppState.currentState === null;
    let storageFailed = false;
    const accessTokens = new Set<string>();
    const retireRequests = () => { accessTokens.forEach(cancelApiRequests); accessTokens.clear(); };
    const persist = (value: string | null, version: number) => {
      const result = writes.then(async () => {
        if (!alive || epoch !== version || token !== value) return;
        await writeRefreshToken(value);
      });
      writes = result.catch(() => {});
      return result;
    };
    const report = (value: AuthRecovery) => {
      if (!alive) return;
      setRecovery(value);
      if (!usable(current)) setSession(null);
    };
    const save = (value: string | null, version: number) => persist(value, version).then(() => {
      if (alive && version === epoch) storageFailed = false;
    }).catch(() => {
      if (alive && version === epoch) { storageFailed = true; report('storage_write'); }
    });
    const schedule = () => {
      clearTimeout(refreshTimer);
      clearTimeout(expiryTimer);
      if (!alive || !current) return;
      const remaining = (current.expires_at ?? 0) * 1000 - Date.now();
      expiryTimer = setTimeout(() => {
        if (alive && !usable(current)) { retireRequests(); setSession(null); report('timeout'); }
      }, Math.max(0, remaining));
      if (foreground) refreshTimer = setTimeout(() => { void refresh(); }, Math.max(1_000, remaining - 60_000));
    };
    const accept = (next: Session, version: number) => {
      if (!alive || version !== epoch) return;
      if (current && current.user.id !== next.user.id) retireRequests();
      current = next;
      accessTokens.add(next.access_token);
      token = next.refresh_token;
      setSession(usable(next) ? next : null);
      setRecovery(null);
      void save(token, version);
      schedule();
    };
    const refresh = (): Promise<void> => {
      if (!alive) return Promise.resolve();
      if (flight?.epoch === epoch) return flight.promise;
      const version = epoch;
      const attempt = { epoch: version, token, promise: Promise.resolve() };
      flight = attempt;
      setLoading(!usable(current));
      setRecovery(null);
      attempt.promise = (async () => {
        if (storageFailed && token !== undefined) {
          await save(token, version);
          if (storageFailed || !alive || version !== epoch) return;
        }
        if (token === undefined) {
          try {
            const stored = await readRefreshToken();
            if (!alive || version !== epoch) return;
            token = stored;
            attempt.token = stored;
          } catch { if (alive && version === epoch) report('storage_read'); return; }
        }
        if (!token) return;
        try {
          const result = await withDeadline(() => auth.refreshSession({ refresh_token: token! }), AUTH_REFRESH_DEADLINE_MS);
          if (!alive || version !== epoch) return;
          if (result.error) throw result.error;
          // TOKEN_REFRESHED normally publishes first. Do not rewrite a newer rotation.
          if (result.data.session && token === attempt.token) accept(result.data.session, version);
          else if (!result.data.session && token === attempt.token) report('unavailable');
        } catch (error) {
          if (!alive || version !== epoch || token !== attempt.token) return;
          const kind = classifyRefreshError(error);
          if (kind === 'invalid') {
            ++epoch;
            retireRequests();
            token = null;
            current = null;
            setSession(null);
            setRecovery(null);
            clearTimeout(refreshTimer);
            clearTimeout(expiryTimer);
            await save(null, epoch);
          } else report(kind);
        }
      })().finally(() => {
        if (flight === attempt) flight = null;
        if (alive && version === epoch) setLoading(false);
        else if (alive && !current) setLoading(false);
      });
      return attempt.promise;
    };
    const { data: { subscription } } = auth.onAuthStateChange((event, next) => {
      if (!alive) return;
      if (event === 'INITIAL_SESSION') return; // persistSession:false starts empty.
      if (event === 'TOKEN_REFRESHED' && next) {
        // Only our current refresh may rotate credentials. Late A cannot publish
        // after logout, B sign-in, or a newer rotation.
        if (flight?.epoch === epoch && flight.token === token && (!current || current.user.id === next.user.id)) accept(next, epoch);
      } else if ((event === 'SIGNED_IN' || event === 'USER_UPDATED') && next) {
        ++epoch;
        accept(next, epoch);
        setLoading(false);
      }
      // SDK SIGNED_OUT during refresh may reflect an unclassified provider error.
      // Only explicit logout or a verified invalid refresh clears our credential.
    });
    actions.current = {
      retry: refresh,
      signOut: async () => {
        ++epoch; // invalidate before awaiting the SDK or secure storage.
        retireRequests();
        const version = epoch;
        token = null;
        current = null;
        setSession(null);
        setLoading(false);
        setRecovery(null);
        clearTimeout(refreshTimer);
        clearTimeout(expiryTimer);
        await save(null, version);
        // SDK may be waiting on its refresh lock. UI/credential clearing is local
        // and immediate; its late event cannot republish the retired owner.
        try { await withDeadline(() => auth.signOut({ scope: 'local' }), AUTH_REFRESH_DEADLINE_MS); }
        catch { /* Local credentials are already cleared; no global revocation. */ }
      },
    };
    void refresh();
    const appState = AppState.addEventListener('change', state => {
      foreground = state === 'active';
      clearTimeout(refreshTimer);
      if (foreground && token) void refresh();
    });
    return () => {
      alive = false;
      retireRequests();
      ++epoch;
      clearTimeout(refreshTimer);
      clearTimeout(expiryTimer);
      subscription.unsubscribe();
      appState.remove();
    };
  }, []);
  const value = useMemo<AuthContextValue>(() => ({
    session, loading, recovery, configurationError: supabaseConfigurationError,
    retry: () => actions.current.retry(), signOut: () => actions.current.signOut(),
  }), [session, loading, recovery]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
