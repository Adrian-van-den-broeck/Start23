import * as SecureStore from 'expo-secure-store';
import type { ReactElement } from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react-native';

import { getPioneerRedemption, redeemPioneerAccess } from '../api/client';
import { PioneerAccessScreen } from './PioneerAccessScreen';
import { LanguageProvider } from '../i18n/LanguageProvider';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => null), setItemAsync: jest.fn(async () => undefined), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked' }));
const renderWithLanguage = (ui: ReactElement) => render(<LanguageProvider>{ui}</LanguageProvider>);

jest.mock('../api/client', () => ({
  getPioneerRedemption: jest.fn(),
  redeemPioneerAccess: jest.fn(),
}));

describe('PioneerAccessScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(getPioneerRedemption).mockResolvedValue(null);
  });

  test('redeems a valid normalized code with one idempotency key', async () => {
    jest.mocked(redeemPioneerAccess).mockResolvedValue({
      program: 'pioneer',
      status: 'active',
      redeemed_at: '2026-09-23T08:00:00Z',
    });
    const screen = await renderWithLanguage(
      <PioneerAccessScreen accessToken="athlete-token" onBack={jest.fn()} />,
    );
    await screen.findByLabelText('Pioneer access-code');

    await fireEvent.changeText(
      screen.getByLabelText('Pioneer access-code'),
      'valid-code',
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Code inwisselen' }),
    );

    await waitFor(() =>
      expect(redeemPioneerAccess).toHaveBeenCalledWith(
        'athlete-token',
        expect.any(String),
        'VALID-CODE',
      ),
    );
    expect(await screen.findByText('Pioneer toegang actief')).toBeTruthy();
  });

  test('surfaces a deterministic rejected-code error', async () => {
    jest.mocked(redeemPioneerAccess).mockRejectedValue(
      new Error('The Pioneer access code has expired.'),
    );
    const screen = await renderWithLanguage(
      <PioneerAccessScreen accessToken="athlete-token" onBack={jest.fn()} />,
    );
    await screen.findByLabelText('Pioneer access-code');

    await fireEvent.changeText(
      screen.getByLabelText('Pioneer access-code'),
      'EXPIRED1',
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Code inwisselen' }),
    );

    expect(
      await screen.findByRole('alert', {
        name: 'The Pioneer access code has expired.',
      }),
    ).toBeTruthy();
  });

  test('English preference translates the redemption copy and confirmation', async () => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValueOnce('en');
    jest.mocked(redeemPioneerAccess).mockResolvedValue({ program: 'pioneer', status: 'active', redeemed_at: '2026-09-23T08:00:00Z' });
    const screen = await renderWithLanguage(<PioneerAccessScreen accessToken="athlete-token" onBack={jest.fn()} />);
    await screen.findByLabelText('Pioneer access code');
    expect(screen.getByText('Access with your code')).toBeTruthy();
    expect(screen.getByText(/Your code is not stored in the app/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Profile' })).toBeTruthy();
    await fireEvent.changeText(screen.getByLabelText('Pioneer access code'), 'valid-code');
    await fireEvent.press(screen.getByRole('button', { name: 'Redeem code' }));
    expect(await screen.findByText('Pioneer access active')).toBeTruthy();
    expect(screen.getByText(/^Redeemed on /)).toBeTruthy();
  });
});
