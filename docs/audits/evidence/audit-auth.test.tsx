import { act, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { AuthProvider, useAuth } from '../../../mobile/src/auth/AuthProvider';
import { getSupabaseClient } from '../../../mobile/src/lib/supabase';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device-only' }));
jest.mock('../../../mobile/src/lib/supabase', () => ({ getSupabaseClient: jest.fn(), supabaseConfigurationError: null }));
let auth: ReturnType<typeof useAuth>;
function Probe() { auth = useAuth(); return null; }

test('AUD-009: a transient offline refresh error deletes the durable refresh token', async () => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue('synthetic-refresh-token');
  jest.mocked(getSupabaseClient).mockReturnValue({ auth: {
    refreshSession: jest.fn(async () => ({ data: { session: null }, error: { name: 'AuthRetryableFetchError', status: 0 } })),
    onAuthStateChange: jest.fn(() => ({ data: { subscription: { unsubscribe: jest.fn() } } })),
    startAutoRefresh: jest.fn(), stopAutoRefresh: jest.fn(),
  } } as never);
  await act(async () => { await render(<AuthProvider><Probe /></AuthProvider>); });
  await waitFor(() => expect(auth.loading).toBe(false));
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.refresh-token');
  expect(auth.session).toBeNull();
});
