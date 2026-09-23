import { fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  getOnboarding,
  getZoneProfileState,
  scheduleFieldTest,
} from '../api/client';
import type { DisciplineSetup, OnboardingState, ZoneProfileState } from '../api/types';
import { ZoneProfileScreen } from './ZoneProfileScreen';

jest.mock('../api/client', () => ({
  approvePlanProposal: jest.fn(),
  approveTestAssignment: jest.fn(),
  approveZoneProposal: jest.fn(),
  getOnboarding: jest.fn(),
  getZoneProfileState: jest.fn(),
  rejectPlanProposal: jest.fn(),
  rejectTestAssignment: jest.fn(),
  rejectZoneProposal: jest.fn(),
  saveCalculatedZones: jest.fn(),
  saveDisciplineSetup: jest.fn(),
  scheduleFieldTest: jest.fn(),
}));

const swimSetup: DisciplineSetup = {
  discipline: 'swim',
  setup_route: 'field_test',
  guidance_mode: 'pace',
  setup_status: 'test_pending',
  protocol_id: 'start23_swim_css_400_200_v1',
  pool_length_meters: 25,
  threshold_status: 'unknown',
  zone_status: 'pending_protocol',
  source: 'field_test',
  validation_status: 'not_assessed',
  confidence: 'not_assessed',
  known_thresholds: [],
  known_zone_profiles: [],
  revision: 1,
  created_at: '2026-09-23T08:00:00Z',
  updated_at: '2026-09-23T08:00:00Z',
};

function profile(modes: ZoneProfileState['disciplines'][number]['available_test_scheduling_modes']): ZoneProfileState {
  return {
    disciplines: [
      {
        discipline: 'swim',
        setup: swimSetup,
        numeric_zone_visibility: 'rpe_guided',
        active_profile: null,
        pending_profile: null,
        prior_profiles: [],
        test_assignments: [],
        available_test_scheduling_modes: modes,
      },
    ],
  };
}

describe('field-test scheduling regression', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(getOnboarding).mockResolvedValue({} as OnboardingState);
    jest.mocked(scheduleFieldTest).mockResolvedValue({} as never);
  });

  test('current server-advertised swim protocol schedules through the API', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(profile(['standalone']));
    const screen = await render(
      <ZoneProfileScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
        planContext={null}
      />,
    );

    await fireEvent.changeText(
      await screen.findByLabelText('Lokale testdatum'),
      '2099-08-29',
    );
    await fireEvent.press(screen.getByRole('button', { name: 'Maak voorstel' }));

    await waitFor(() =>
      expect(scheduleFieldTest).toHaveBeenCalledWith('athlete-token', {
        discipline: 'swim',
        protocol_id: 'start23_swim_css_400_200_v1',
        scheduling_mode: 'standalone',
        scheduled_date: '2099-08-29',
      }),
    );
  });

  test('historical setup cannot leak a scheduling action into a new session', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(profile([]));
    const screen = await render(
      <ZoneProfileScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
        planContext={null}
      />,
    );

    await screen.findByText('Zwemmen');
    expect(screen.queryByText('Veldtest plannen')).toBeNull();
    expect(scheduleFieldTest).not.toHaveBeenCalled();
  });
});
