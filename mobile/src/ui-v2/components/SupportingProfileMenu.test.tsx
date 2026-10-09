import * as SecureStore from 'expo-secure-store';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { SupportingProfileMenu } from './SupportingProfileMenu';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device-only' }));
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('nl'); });
test('existing destinations and sign-out invoke only supplied callbacks', async () => {
  const profile = jest.fn(); const integrations = jest.fn(); const signOut = jest.fn();
  const view = await render(<LanguageProvider><SupportingProfileMenu onOpenProfile={profile} onOpenIntegrations={integrations} onSignOut={signOut} /></LanguageProvider>);
  await view.findByText('Alles over jouw setup');
  await fireEvent.press(view.getByRole('button', { name: 'Intakeprofiel' })); await fireEvent.press(view.getByRole('button', { name: 'Integraties' }));
  await fireEvent.press(view.getByRole('button', { name: 'Veilig afmelden' }));
  expect(profile).toHaveBeenCalledTimes(1); expect(integrations).toHaveBeenCalledTimes(1); expect(signOut).toHaveBeenCalledTimes(1);
  expect(view.queryByText('Settings')).toBeNull();
});
test('exclusive language preference persists and localizes the same supporting content', async () => {
  const view = await render(<LanguageProvider><SupportingProfileMenu onOpenProfile={jest.fn()} onOpenIntegrations={jest.fn()} onSignOut={jest.fn()} /></LanguageProvider>);
  await view.findByText('Taal'); expect(view.getByRole('radio', { name: 'Nederlands' })).toBeChecked();
  await fireEvent.press(view.getByRole('radio', { name: 'English' })); await view.findByText('Language');
  expect(view.getByRole('radio', { name: 'English' })).toBeChecked(); expect(view.getByRole('radio', { name: 'Nederlands' })).not.toBeChecked();
  await waitFor(() => expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.language-preference', 'en', { keychainAccessible: 'device-only' }));
  await fireEvent.press(view.getByRole('radio', { name: 'Automatic' }));
  await waitFor(() => expect(SecureStore.setItemAsync).toHaveBeenCalledWith('start23.language-preference', 'system', { keychainAccessible: 'device-only' }));
});
