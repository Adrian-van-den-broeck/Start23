import { fireEvent, render } from '@testing-library/react-native';
import type { PropsWithChildren } from 'react';
import * as SecureStore from 'expo-secure-store';
import { listActivities } from '../api/client';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import AuthenticatedLayout from '../../app/(authenticated)/_layout';

const mockPush = jest.fn();
jest.mock('expo-router', () => ({ usePathname: () => '/planning', useRouter: () => ({ push: mockPush }), Stack: () => null, Redirect: () => null }));
jest.mock('../api/client', () => ({ listActivities: jest.fn() }));
jest.mock('./TrainingFlowHost', () => ({ TrainingFlowHost: ({ children }: PropsWithChildren) => children }));
jest.mock('../auth/AuthProvider', () => {
  const auth = { configurationError: null, loading: false, session: { access_token: 'verified-test-token', user: { id: 'fixture-athlete' } } };
  return { useAuth: () => auth };
});
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
jest.mock('expo-blur', () => {
  const { View } = jest.requireActual('react-native');
  return { BlurView: View };
});
jest.mock('react-native-safe-area-context', () => {
  const { View } = jest.requireActual('react-native');
  return { SafeAreaView: ({ children, ...props }: PropsWithChildren<{ edges: string[]; }>) => <View testID="reminder-safe-area" {...props}>{children}</View> };
});
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });

// Match the actual root UI provider; default V1 still exercises the legacy reminder.
test.each([1, 2])('shell-owned reminder keeps exact count %s and destination, below a top safe area', async (count) => {
  jest.mocked(listActivities).mockResolvedValue(Array.from({ length: count }, () => ({})) as Awaited<ReturnType<typeof listActivities>>);
  const view = await render(<LanguageProvider><UiVersionProvider><AuthenticatedLayout /></UiVersionProvider></LanguageProvider>);
  const text = `${count} workout${count === 1 ? '' : 's'} waiting for RPE · open Training & RPE`;
  await view.findByText(text);
  expect(view.getByTestId('reminder-safe-area').props.edges).toEqual(['top']);
  expect(listActivities).toHaveBeenCalledTimes(1);
  expect(listActivities).toHaveBeenCalledWith('verified-test-token', true);
  await fireEvent.press(view.getByRole('button'));
  expect(mockPush).toHaveBeenCalledWith('/activities');
  await view.rerender(<LanguageProvider><UiVersionProvider><AuthenticatedLayout /></UiVersionProvider></LanguageProvider>);
  expect(listActivities).toHaveBeenCalledTimes(1);
});

test('no reminder reserves no shell inset or additional container', async () => {
  jest.mocked(listActivities).mockResolvedValue([]);
  const view = await render(<LanguageProvider><UiVersionProvider><AuthenticatedLayout /></UiVersionProvider></LanguageProvider>);
  expect(view.queryByTestId('reminder-safe-area')).toBeNull();
});
