import 'react-native-url-polyfill/auto';

import {
  createClient,
  processLock,
  type SupabaseClient,
} from '@supabase/supabase-js';

import type { TranslationKey } from '../i18n/dictionaries';
import { translate } from '../i18n/runtime';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabasePublishableKey =
  process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

// A translation key, so the message follows the language active when it is shown.
export const supabaseConfigurationError: TranslationKey | null =
  !supabaseUrl || !supabasePublishableKey
    ? 'errors.supabaseConfigMissing'
    : null;

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (supabaseConfigurationError || !supabaseUrl || !supabasePublishableKey) {
    throw new Error(translate(supabaseConfigurationError ?? 'errors.supabaseNotConfigured'));
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
