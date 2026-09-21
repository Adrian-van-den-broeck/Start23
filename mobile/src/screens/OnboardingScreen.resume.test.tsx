import { fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  completeOnboarding,
  getGoalPlanningOptions,
  getOnboarding,
} from '../api/client';
import type { OnboardingState } from '../api/types';
import { OnboardingScreen } from './OnboardingScreen';

jest.mock('../api/client', () => ({
  approveZoneProposal: jest.fn(),
  completeOnboarding: jest.fn(),
  getGoalPlanningOptions: jest.fn(),
  getOnboarding: jest.fn(),
  rejectZoneProposal: jest.fn(),
  saveCalculatedZones: jest.fn(),
  saveDisciplineSetup: jest.fn(),
  saveOperationalProfile: jest.fn(),
  savePrimaryGoal: jest.fn(),
  saveProfile: jest.fn(),
  saveTrainingHistory: jest.fn(),
}));

const state: OnboardingState = {
  status: 'upgrade_required',
  current_step: 'timezone',
  completed_steps: ['profile', 'heart_rate_monitor', 'history'],
  current_onboarding_version: 'phase-14-onboarding-v2',
  current_ruleset_version: 'phase-13-joren-ruleset-1',
  completed_onboarding_version: 'phase-13-onboarding-v1',
  completed_ruleset_version: 'phase-13-joren-ruleset-1',
  upgrade_required: true,
  missing_upgrade_steps: ['timezone', 'goal'],
  profile: null,
  training_history: [],
  primary_goal: null,
  required_disciplines: [],
  zones: [],
  discipline_setups: [],
  can_complete: false,
  initial_plan_request_id: 'historical-request',
  onboarding_revision: 7,
};

describe('OnboardingScreen resume behavior', () => {
  test('renders the server-selected upgrade step without restarting history', async () => {
    jest.mocked(getOnboarding).mockResolvedValue(state);
    jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
    const screen = await render(
      <OnboardingScreen
        accessToken="athlete-token"
        onOpenCalibration={jest.fn()}
        onOpenPlanning={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );

    expect(await screen.findByText('Werk je onboarding bij')).toBeTruthy();
    expect(screen.getByText(/Tijdzone, Doel/)).toBeTruthy();
    expect(screen.getByText('Bevestig je tijdzone')).toBeTruthy();
    expect(screen.queryByText('Waar sta je nu?')).toBeNull();
  });

  test('completion navigates directly to planning without the removed interstitial', async () => {
    jest.mocked(getOnboarding).mockResolvedValue({
      ...state,
      status: 'in_progress',
      current_step: 'review',
      completed_steps: [
        'profile',
        'heart_rate_monitor',
        'timezone',
        'history',
        'goal',
        'zones',
      ],
      upgrade_required: false,
      missing_upgrade_steps: [],
      can_complete: true,
      onboarding_revision: 9,
    });
    jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
    jest.mocked(completeOnboarding).mockResolvedValue({
      onboarding: {
        ...state,
        status: 'completed',
        current_step: 'completed',
      },
      initial_plan_request_id: 'request-id',
      initial_plan_request_status: 'pending',
    });
    const onOpenPlanning = jest.fn();
    const screen = await render(
      <OnboardingScreen
        accessToken="athlete-token"
        onOpenCalibration={jest.fn()}
        onOpenPlanning={onOpenPlanning}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );

    await fireEvent.press(
      await screen.findByRole('button', { name: 'Onboarding afronden' }),
    );

    await waitFor(() => {
      expect(completeOnboarding).toHaveBeenCalledWith('athlete-token', 9);
      expect(onOpenPlanning).toHaveBeenCalledTimes(1);
    });
    expect(screen.queryByText('Je basis staat.')).toBeNull();
  });
});
