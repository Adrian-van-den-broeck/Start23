import type { Session } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import {
  createContext,
  type PropsWithChildren,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { AppState, Platform } from 'react-native';

import {
  getSupabaseClient,
  supabaseConfigurationError,
} from '../lib/supabase';

const refreshTokenKey = 'start23.refresh-token';

type AuthContextValue = {
  session: Session | null;
  loading: boolean;
  configurationError: string | null;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function readRefreshToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    return null;
  }
  return SecureStore.getItemAsync(refreshTokenKey);
}

async function writeRefreshToken(refreshToken: string | null): Promise<void> {
  if (Platform.OS === 'web') {
    return;
  }
  if (refreshToken === null) {
    await SecureStore.deleteItemAsync(refreshTokenKey);
    return;
  }
  await SecureStore.setItemAsync(refreshTokenKey, refreshToken, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (supabaseConfigurationError) {
      setLoading(false);
      return;
    }

    const supabase = getSupabaseClient();
    let mounted = true;
    const bootstrap = async () => {
      try {
        const refreshToken = await readRefreshToken();
        if (refreshToken) {
          const { data, error } = await supabase.auth.refreshSession({
            refresh_token: refreshToken,
          });
          if (error) {
            await writeRefreshToken(null);
          } else if (mounted) {
            setSession(data.session);
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void bootstrap();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (mounted) {
        setSession(nextSession);
      }
      void writeRefreshToken(nextSession?.refresh_token ?? null).catch(() => {
        // The in-memory session remains usable; the next launch will require login.
      });
    });
    const appStateSubscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        supabase.auth.startAutoRefresh();
      } else {
        supabase.auth.stopAutoRefresh();
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
      appStateSubscription.remove();
      supabase.auth.stopAutoRefresh();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      configurationError: supabaseConfigurationError,
      signOut: async () => {
        if (supabaseConfigurationError) {
          return;
        }
        const supabase = getSupabaseClient();
        const { error } = await supabase.auth.signOut({ scope: 'local' });
        if (error) {
          throw error;
        }
        await writeRefreshToken(null);
        setSession(null);
      },
    }),
    [loading, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return value;
}
