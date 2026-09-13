import { fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  getZoneSetupOptions,
  listCalibrationProtocols,
} from '../api/client';
import type { OnboardingState } from '../api/types';
import { ZoneSetupStep } from './ZoneSetupStep';

jest.mock('../api/client', () => ({
  getZoneSetupOptions: jest.fn(),
  listCalibrationProtocols: jest.fn(),
}));

const getOptions = jest.mocked(getZoneSetupOptions);
const getProtocols = jest.mocked(listCalibrationProtocols);

const state: OnboardingState = {
  status: 'in_progress',
  current_step: 'zones',
  completed_steps: ['profile', 'heart_rate_monitor', 'timezone', 'history', 'goal'],
  current_onboarding_version: 'phase-14-onboarding-v2',
  current_ruleset_version: 'phase-13-joren-ruleset-1',
  completed_onboarding_version: null,
  completed_ruleset_version: null,
  upgrade_required: false,
  missing_upgrade_steps: [],
  profile: null,
  training_history: [],
  primary_goal: null,
  required_disciplines: ['run'],
  zones: [],
  discipline_setups: [],
  can_complete: false,
  initial_plan_request_id: null,
  onboarding_revision: 0,
};

describe('ZoneSetupStep', () => {
  beforeEach(() => {
    getOptions.mockResolvedValue([
      {
        setup_route: 'known_values',
        label: 'Bekende waarden',
        creates_threshold: false,
        creates_zones: true,
        requires_athlete_confirmation: true,
        activation_behavior: 'calculated_result_stays_pending',
      },
      {
        setup_route: 'calibration_week',
        label: 'Rustig kalibreren',
        creates_threshold: true,
        creates_zones: true,
        requires_athlete_confirmation: true,
        activation_behavior: 'calculated_result_stays_pending',
      },
    ]);
    getProtocols.mockResolvedValue([
      {
        protocol_id: 'start23_week1_run_calibration_v1',
        discipline: 'run',
        protocol_type: 'submaximal_calibration',
        version: 1,
        review_status: 'approved_active',
        result_status_on_success: 'threshold_estimated',
        guidance_modes: ['heart_rate'],
        required_observation_type: 'average_heart_rate_and_rpe',
        calculated_result: 'threshold_and_zone_profiles',
        pending_zone_lifecycle: 'confirmation_creates_pending_proposal',
        segments: [],
      },
    ]);
  });

  test('renders only current run routes and submits pending calibration intent', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <ZoneSetupStep
        accessToken="athlete-token"
        onSave={onSave}
        saving={false}
        state={state}
      />,
    );

    await screen.findByText('Rustig kalibreren');
    expect(screen.queryByText('Maximale veldtest')).toBeNull();
    expect(getOptions).toHaveBeenCalledWith('athlete-token', 'run');
    expect(getProtocols).toHaveBeenCalledWith('athlete-token', 'run');

    await fireEvent.press(
      screen.getByRole('radio', { name: /Rustig kalibreren/ }),
    );
    expect(
      screen.getByText(/berekent deterministisch een drempel en vijf zones/),
    ).toBeTruthy();
    await fireEvent.press(
      screen.getByRole('button', { name: 'Week-1-kalibratie kiezen' }),
    );

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith('run', {
        setup_route: 'calibration_week',
        guidance_mode: 'heart_rate',
      }),
    );
  });
});
