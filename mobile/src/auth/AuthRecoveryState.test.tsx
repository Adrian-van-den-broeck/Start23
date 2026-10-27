import { fireEvent, render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useAuth } from './AuthProvider';
import { AuthRecoveryState } from './AuthRecoveryState';

jest.mock('./AuthProvider', () => ({ useAuth: jest.fn() }));
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn() }));
const retry = jest.fn();
test.each([
  ['nl', 'Opnieuw proberen', 'Je sessie herstellen'],
  ['en', 'Retry', 'Restore your session'],
])('recoverable auth uses existing NL/EN notice and retry (%s)', async (language, label, title) => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  jest.mocked(useAuth).mockReturnValue({ recovery: 'network', loading: false, retry } as unknown as ReturnType<typeof useAuth>);
  const view = await render(<LanguageProvider><AuthRecoveryState /></LanguageProvider>);
  await view.findByText(title);
  await fireEvent.press(view.getByRole('button', { name: label }));
  expect(retry).toHaveBeenCalled();
});
