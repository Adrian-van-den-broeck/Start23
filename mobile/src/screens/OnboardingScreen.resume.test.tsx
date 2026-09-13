import { render } from '@testing-library/react-native';

import { getGoalPlanningOptions, getOnboarding } from '../api/client';
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
});
