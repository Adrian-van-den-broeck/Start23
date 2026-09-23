import { render } from '@testing-library/react-native';

import { getOnboarding, saveProfile } from '../api/client';
import type { OnboardingState } from '../api/types';
import { ProfileScreen } from './ProfileScreen';

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

    const screen = await render(
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
    expect(saveProfile).not.toHaveBeenCalled();
  });
});
