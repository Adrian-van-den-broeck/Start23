import 'react-native-url-polyfill/auto';

import {
  createClient,
  processLock,
  type SupabaseClient,
} from '@supabase/supabase-js';
import { withDeadline } from './deadline';

export const AUTH_FETCH_DEADLINE_MS = 15_000;

// Buffer inside the deadline so a stalled response body also settles. This is
// the existing client's transport, not a second auth/session owner.
export const authFetch: typeof fetch = (input, init) => withDeadline(async signal => {
  const response = await fetch(input, { ...init, signal });
  const body = await response.text();
  return new Response(response.status === 204 ? null : body, {
    status: response.status, statusText: response.statusText, headers: response.headers,
  });
}, AUTH_FETCH_DEADLINE_MS, init?.signal);

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabasePublishableKey =
  process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const supabaseConfigurationError =
  !supabaseUrl || !supabasePublishableKey
    ? 'Configureer EXPO_PUBLIC_SUPABASE_URL en de publishable key.'
    : null;

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (supabaseConfigurationError || !supabaseUrl || !supabasePublishableKey) {
    throw new Error(supabaseConfigurationError ?? 'Supabase is niet ingesteld.');
  }
  client ??= createClient(supabaseUrl, supabasePublishableKey, {
    global: { fetch: authFetch },
    auth: {
      // AuthProvider schedules/coalesces refresh and reports recoverable errors.
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false,
      lock: processLock,
    },
  });
  return client;
}
