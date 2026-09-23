import { act, fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  completeOnboarding,
  getGoalPlanningOptions,
  getOnboarding,
  getPhysiologyProfile,
  getZoneSetupOptions,
  listCalibrationProtocols,
  saveDisciplineSetup,
} from '../api/client';
import type { Discipline, OnboardingState } from '../api/types';
import { OnboardingScreen } from './OnboardingScreen';

jest.mock('../api/client', () => ({
  approveZoneProposal: jest.fn(),
  completeOnboarding: jest.fn(),
  getGoalPlanningOptions: jest.fn(),
  getOnboarding: jest.fn(),
  getPhysiologyProfile: jest.fn(),
  getZoneSetupOptions: jest.fn(),
  listCalibrationProtocols: jest.fn(),
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
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(getPhysiologyProfile).mockResolvedValue(null);
    jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
    jest.mocked(getZoneSetupOptions).mockResolvedValue([
      {
        setup_route: 'calibration_week',
        label: 'Rustig kalibreren',
        creates_threshold: true,
        creates_zones: true,
        requires_athlete_confirmation: true,
        activation_behavior: 'calculated_result_stays_pending',
      },
    ]);
    jest
      .mocked(listCalibrationProtocols)
      .mockImplementation(async (_token, discipline) => [
        {
          protocol_id: `start23_week1_${discipline}_calibration_v1`,
          discipline,
          protocol_type: 'submaximal_calibration',
          version: 1,
          review_status: 'approved_active',
          result_status_on_success: 'threshold_estimated',
          guidance_modes: [discipline === 'swim' ? 'pace' : 'heart_rate'],
          required_observation_type:
            discipline === 'swim'
              ? 'elapsed_time_distance_and_rpe'
              : 'average_heart_rate_and_rpe',
          calculated_result: 'threshold_and_zone_profiles',
          pending_zone_lifecycle: 'confirmation_creates_pending_proposal',
          segments: [],
        },
      ]);
    jest.mocked(saveDisciplineSetup).mockResolvedValue(undefined as never);
  });

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

  test('a new athlete resumes directly after saving physiology', async () => {
    jest.mocked(getOnboarding).mockResolvedValue({
      ...state,
      status: 'in_progress',
      current_step: 'profile',
      completed_steps: [],
      upgrade_required: false,
      missing_upgrade_steps: [],
      onboarding_revision: 1,
    });
    jest.mocked(getGoalPlanningOptions).mockResolvedValue([]);
    jest.mocked(getPhysiologyProfile).mockResolvedValue({
      athlete_id: '00000000-0000-0000-0000-000000000001',
      date_of_birth: '1990-05-20',
      resting_heart_rate_bpm: 52,
      revision: 1,
      created_at: '2026-09-22T08:00:00Z',
      updated_at: '2026-09-22T08:00:00Z',
    });
    const screen = await render(
      <OnboardingScreen
        accessToken="athlete-token"
        onOpenCalibration={jest.fn()}
        onOpenPlanning={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );

    expect(await screen.findByText('Heb je toegang tot een hartslagmeter?')).toBeTruthy();
    expect(screen.queryByText('Jouw basis')).toBeNull();
  });

  test.each([
    ['marathon run', ['run']],
    ['bike race', ['bike']],
    ['duathlon', ['bike', 'run']],
  ] as const)(
    '%s calibration persists once and opens the actionable test flow',
    async (_label, requiredDisciplines) => {
      const zoneState = {
        ...state,
        status: 'in_progress',
        current_step: 'zones',
        completed_steps: [
          'profile',
          'heart_rate_monitor',
          'timezone',
          'history',
          'goal',
        ],
        upgrade_required: false,
        missing_upgrade_steps: [],
        required_disciplines: [...requiredDisciplines],
        discipline_setups: [],
      } as OnboardingState;
      jest.mocked(getOnboarding).mockResolvedValue(zoneState);
      const onOpenCalibration = jest.fn();
      const screen = await render(
        <OnboardingScreen
          accessToken="athlete-token"
          onOpenCalibration={onOpenCalibration}
          onOpenPlanning={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );

      await fireEvent.press(
        await screen.findByRole('radio', { name: /Rustig kalibreren/ }),
      );
      await fireEvent.press(
        screen.getByRole('button', { name: 'Week-1-kalibratie kiezen' }),
      );

      const discipline = requiredDisciplines[0] as Discipline;
      await waitFor(() => {
        expect(saveDisciplineSetup).toHaveBeenCalledWith(
          'athlete-token',
          discipline,
          {
            setup_route: 'calibration_week',
            guidance_mode: discipline === 'swim' ? 'pace' : 'heart_rate',
          },
        );
        expect(onOpenCalibration).toHaveBeenCalledTimes(1);
      });
      await screen.findByRole('button', {
        name: 'Week-1-kalibratie kiezen',
      });
      expect(getOnboarding).toHaveBeenCalledTimes(1);
    },
  );

  test('refocus reloads server state after returning from calibration', async () => {
    const beforeCalibration = {
      ...state,
      status: 'in_progress',
      current_step: 'zones',
      completed_steps: ['profile', 'heart_rate_monitor', 'timezone', 'history', 'goal'],
      upgrade_required: false,
      missing_upgrade_steps: [],
      required_disciplines: ['run'],
    } as OnboardingState;
    jest.mocked(getOnboarding).mockResolvedValue(beforeCalibration);
    const screen = await render(
      <OnboardingScreen
        accessToken="athlete-token"
        active
        onOpenCalibration={jest.fn()}
        onOpenPlanning={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    await screen.findByText('Rustig kalibreren');

    await act(async () => {
      screen.rerender(
        <OnboardingScreen
          accessToken="athlete-token"
          active={false}
          onOpenCalibration={jest.fn()}
          onOpenPlanning={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );
    });
    jest.mocked(getOnboarding).mockResolvedValue({
      ...beforeCalibration,
      zones: [
        {
          id: 'pending-run-zone',
          discipline: 'run',
          status: 'pending',
          proposal_id: 'pending-run-proposal',
          base_zone_profile_id: null,
          metric_profiles: [],
          metric: { metric_kind: 'run_lthr_bpm', value: '171' },
          zone_model_version: 'phase-13-joren-ruleset-1',
        },
      ],
    } as unknown as OnboardingState);
    await act(async () => {
      screen.rerender(
        <OnboardingScreen
          accessToken="athlete-token"
          active
          onOpenCalibration={jest.fn()}
          onOpenPlanning={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );
    });

    expect(
      await screen.findByText('Zonevoorstel run wacht op bevestiging'),
    ).toBeTruthy();
    await screen.findByText('Rustig kalibreren');
    expect(getOnboarding).toHaveBeenCalledTimes(2);
  });

  test('duathlon resume advances past the persisted bike setup instead of looping', async () => {
    const beforeBikeCalibration = {
      ...state,
      status: 'in_progress',
      current_step: 'zones',
      completed_steps: ['profile', 'heart_rate_monitor', 'timezone', 'history', 'goal'],
      upgrade_required: false,
      missing_upgrade_steps: [],
      required_disciplines: ['bike', 'run'],
      discipline_setups: [],
    } as OnboardingState;
    jest.mocked(getOnboarding).mockResolvedValue(beforeBikeCalibration);
    const screen = await render(
      <OnboardingScreen
        accessToken="athlete-token"
        active
        onOpenCalibration={jest.fn()}
        onOpenPlanning={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    expect(await screen.findByText('Instellen voor fietsen')).toBeTruthy();

    await act(async () => {
      screen.rerender(
        <OnboardingScreen
          accessToken="athlete-token"
          active={false}
          onOpenCalibration={jest.fn()}
          onOpenPlanning={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );
    });
    jest.mocked(getOnboarding).mockResolvedValue({
      ...beforeBikeCalibration,
      discipline_setups: [
        {
          discipline: 'bike',
          setup_route: 'calibration_week',
          guidance_mode: 'heart_rate',
          setup_status: 'calibration_pending',
          protocol_id: 'start23_week1_bike_calibration_v1',
          pool_length_meters: null,
          threshold_status: 'unknown',
          zone_status: 'pending_protocol',
          source: 'week1_calibration',
          validation_status: 'not_assessed',
          confidence: 'not_assessed',
          known_thresholds: [],
          known_zone_profiles: [],
          revision: 1,
          created_at: '2026-09-23T08:00:00Z',
          updated_at: '2026-09-23T08:00:00Z',
        },
      ],
    });
    await act(async () => {
      screen.rerender(
        <OnboardingScreen
          accessToken="athlete-token"
          active
          onOpenCalibration={jest.fn()}
          onOpenPlanning={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );
    });

    expect(await screen.findByText('Instellen voor hardlopen')).toBeTruthy();
    expect(screen.queryByText('Instellen voor fietsen')).toBeNull();
  });
});
