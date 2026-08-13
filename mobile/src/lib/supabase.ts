import 'react-native-url-polyfill/auto';

import {
  createClient,
  processLock,
  type SupabaseClient,
} from '@supabase/supabase-js';

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
    auth: {
      autoRefreshToken: true,
      persistSession: false,
      detectSessionInUrl: false,
      lock: processLock,
    },
  });
  return client;
}
