import * as SecureStore from 'expo-secure-store';
import type { ReactElement } from 'react';
import { render } from '@testing-library/react-native';

import { getOnboarding, saveProfile } from '../api/client';
import type { OnboardingState } from '../api/types';
import { ProfileScreen } from './ProfileScreen';
import { LanguageProvider } from '../i18n/LanguageProvider';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => null), setItemAsync: jest.fn(async () => undefined), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked' }));
const renderWithLanguage = (ui: ReactElement) => render(<LanguageProvider>{ui}</LanguageProvider>);

jest.mock('../api/client', () => ({
  getOnboarding: jest.fn(),
  saveProfile: jest.fn(),
}));

describe('ProfileScreen navigation regression', () => {
  test('renders a completed athlete profile without reopening onboarding', async () => {
    jest.mocked(getOnboarding).mockResolvedValue({
      current_step: 'completed',
      profile: {
        athlete_id: 'opaque-athlete-id',
        first_name: 'Ada',
        last_name: 'Lovelace',
        date_of_birth: '1990-05-20',
        resting_heart_rate_bpm: 52,
        timezone: 'Europe/Amsterdam',
        timezone_source: 'device',
        timezone_confirmed_at: '2026-09-01T00:00:00Z',
        heart_rate_monitor_confirmed_at: '2026-09-01T00:00:00Z',
        onboarding_status: 'completed',
        revision: 4,
        identifying_revision: 2,
        physiology_revision: 2,
        created_at: '2026-09-01T00:00:00Z',
        updated_at: '2026-09-23T08:00:00Z',
      },
    } as OnboardingState);

    const screen = await renderWithLanguage(
      <ProfileScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onOpenPioneerAccess={jest.fn()}
        onOpenTests={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );

    expect(await screen.findByDisplayValue('Ada')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Testen en kalibratie/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Pioneer toegang/ })).toBeTruthy();
    expect(screen.queryByText(/Stap \d van/)).toBeNull();
    expect(saveProfile).not.toHaveBeenCalled();
  });

  test('English preference translates the profile destinations', async () => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValueOnce('en');
    jest.mocked(getOnboarding).mockRejectedValue('offline');
    const screen = await renderWithLanguage(
      <ProfileScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onOpenPioneerAccess={jest.fn()}
        onOpenTests={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    expect(await screen.findByText('My profile')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Tests and calibration/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Pioneer access/ })).toBeTruthy();
    expect(screen.getByText('Open the current protocols you can carry out.')).toBeTruthy();
    expect(screen.getByText('Redeem your personal beta code.')).toBeTruthy();
    expect(screen.queryByText('Testen en kalibratie')).toBeNull();
  });
});
