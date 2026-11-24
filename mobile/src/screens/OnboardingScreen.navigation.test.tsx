import { act, fireEvent, render as baseRender, waitFor } from '@testing-library/react-native';
import type { ReactElement } from 'react';
import { BackHandler } from 'react-native';

import {
  getGoalPlanningOptions,
  getOnboarding,
  getPhysiologyProfile,
  getZoneSetupOptions,
  listCalibrationProtocols,
  saveOperationalProfile,
  savePrimaryGoal,
  saveProfile,
  saveTrainingHistory,
} from '../api/client';
import type {
  AthleteProfile,
  GoalPlanningOption,
  OnboardingState,
  PrimaryRaceGoal,
} from '../api/types';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { OnboardingScreen } from './OnboardingScreen';

// Dutch is the default language; every render goes through the provider like the app does.
const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

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

const profile: AthleteProfile = {
  athlete_id: '00000000-0000-0000-0000-000000000001',
  first_name: null,
  last_name: null,
  date_of_birth: '1990-05-20',
  resting_heart_rate_bpm: 52,
  timezone: 'Europe/Brussels',
  timezone_source: 'manual',
  timezone_confirmed_at: '2026-11-01T08:00:00Z',
  heart_rate_monitor_confirmed_at: '2026-11-01T08:00:00Z',
  onboarding_status: 'in_progress',
  revision: 3,
  identifying_revision: 1,
  physiology_revision: 1,
  created_at: '2026-11-01T08:00:00Z',
  updated_at: '2026-11-01T08:00:00Z',
};

const triathlonGoal: PrimaryRaceGoal = {
  id: 'goal-1',
  race_type: 'triathlon',
  race_name: 'Amsterdam Olympic Triathlon',
  race_date: '2099-06-15',
  swim_distance_meters: 1500,
  bike_distance_meters: 40000,
  run_distance_meters: 10000,
  total_target_time_seconds: 9000,
  swim_target_time_seconds: null,
  bike_target_time_seconds: null,
  run_target_time_seconds: null,
  specific_focus: null,
  priority: 'A',
  goal_type: 'race',
  status: 'active',
  revision: 1,
  created_at: '2026-11-01T08:00:00Z',
  updated_at: '2026-11-01T08:00:00Z',
};

const history = (['swim', 'bike', 'run'] as const).map((discipline) => ({
  discipline,
  previous_month_weekly_minutes: '120',
  updated_at: '2026-11-01T08:00:00Z',
})) as unknown as OnboardingState['training_history'];

const goalOptions: GoalPlanningOption[] = [
  {
    goal_kind: 'race_event',
    goal_family: 'race_event',
    label: 'Wedstrijd of evenement',
    availability: 'available',
    requires_target_date: true,
    cycle_anchor: 'race_date',
    unavailable_reason: null,
  },
];

const zonesState: OnboardingState = {
  status: 'in_progress',
  current_step: 'zones',
  completed_steps: ['profile', 'heart_rate_monitor', 'timezone', 'history', 'goal'],
  current_onboarding_version: 'phase-14-onboarding-v2',
  current_ruleset_version: 'phase-13-joren-ruleset-1',
  completed_onboarding_version: null,
  completed_ruleset_version: null,
  upgrade_required: false,
  missing_upgrade_steps: [],
  profile,
  training_history: history,
  primary_goal: triathlonGoal,
  required_disciplines: ['swim', 'bike', 'run'],
  zones: [],
  discipline_setups: [],
  can_complete: false,
  initial_plan_request_id: null,
  onboarding_revision: 4,
};

const reviewState: OnboardingState = {
  ...zonesState,
  current_step: 'review',
  completed_steps: [
    'profile',
    'heart_rate_monitor',
    'timezone',
    'history',
    'goal',
    'zones',
  ],
  can_complete: true,
};

function renderScreen() {
  return render(
    <OnboardingScreen
      accessToken="athlete-token"
      onOpenCalibration={jest.fn()}
      onOpenPlanning={jest.fn()}
      onSignOut={jest.fn(async () => undefined)}
    />,
  );
}

type Screen = Awaited<ReturnType<typeof renderScreen>>;

const previous = (screen: Screen) => screen.getByRole('button', { name: 'Vorige stap' });
const next = (screen: Screen) => screen.getByRole('button', { name: 'Volgende stap' });

describe('OnboardingScreen back navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(getPhysiologyProfile).mockResolvedValue(null);
    jest.mocked(getGoalPlanningOptions).mockResolvedValue(goalOptions);
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
    jest.mocked(listCalibrationProtocols).mockResolvedValue([]);
    jest.mocked(saveOperationalProfile).mockResolvedValue(undefined as never);
    jest.mocked(savePrimaryGoal).mockResolvedValue(undefined as never);
    jest.mocked(saveProfile).mockResolvedValue(undefined as never);
    jest.mocked(saveTrainingHistory).mockResolvedValue(undefined as never);
  });

  test('changing triathlon to a run race from the zone step updates the goal', async () => {
    const runGoal: PrimaryRaceGoal = {
      ...triathlonGoal,
      race_type: 'run',
      swim_distance_meters: null,
      bike_distance_meters: null,
      revision: 2,
    };
    jest
      .mocked(getOnboarding)
      .mockResolvedValueOnce(zonesState)
      .mockResolvedValue({
        ...zonesState,
        primary_goal: runGoal,
        required_disciplines: ['run'],
      });
    const screen = await renderScreen();

    expect(await screen.findByText('Instellen voor zwemmen')).toBeTruthy();
    await fireEvent.press(previous(screen));

    expect(await screen.findByText('Kies je trainingsdoel')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Type wedstrijd: Triatlon' }));
    await fireEvent.press(screen.getByRole('radio', { name: 'Lopen' }));
    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));

    await waitFor(() => {
      expect(savePrimaryGoal).toHaveBeenCalledWith(
        'athlete-token',
        expect.objectContaining({
          race_type: 'run',
          run_distance_meters: 10000,
          total_target_time_seconds: 9000,
        }),
        'goal-1',
      );
    });
    const [, savedInput] = jest.mocked(savePrimaryGoal).mock.calls[0];
    expect(savedInput).not.toHaveProperty('swim_distance_meters');
    expect(savedInput).not.toHaveProperty('bike_distance_meters');
    expect(await screen.findByText('Instellen voor hardlopen')).toBeTruthy();
  });

  test('every step can go back to the start and forward again without saving', async () => {
    jest.mocked(getOnboarding).mockResolvedValue(reviewState);
    const screen = await renderScreen();

    expect(await screen.findByText('Klaar voor je eerste voorstel')).toBeTruthy();
    // The server's own step is the furthest the view can go.
    expect(screen.queryByRole('button', { name: 'Volgende stap' })).toBeNull();

    const expectedTitles = [
      ['Instellen voor zwemmen', /Stap 6 van 7\. Zones/],
      ['Kies je trainingsdoel', /Stap 5 van 7\. Doel/],
      ['Waar sta je nu?', /Stap 4 van 7\. Historie/],
      ['Bevestig je tijdzone', /Stap 3 van 7\. Tijdzone/],
      ['Heb je toegang tot een hartslagmeter?', /Stap 2 van 7\. Hartslag/],
      ['Jouw basis', /Stap 1 van 7\. Profiel/],
    ] as const;
    for (const [title, progress] of expectedTitles) {
      await fireEvent.press(previous(screen));
      expect(await screen.findByText(title)).toBeTruthy();
      expect(screen.getByLabelText(progress)).toBeTruthy();
    }
    expect(screen.queryByRole('button', { name: 'Vorige stap' })).toBeNull();

    expect(next(screen).props.accessibilityHint).toBe('Ga zonder opslaan naar Hartslag.');
    await fireEvent.press(next(screen));
    expect(
      await screen.findByText('Heb je toegang tot een hartslagmeter?'),
    ).toBeTruthy();
    expect(previous(screen).props.accessibilityHint).toBe('Ga terug naar Profiel.');
    expect(saveProfile).not.toHaveBeenCalled();
    expect(saveOperationalProfile).not.toHaveBeenCalled();
    expect(getOnboarding).toHaveBeenCalledTimes(1);
  });

  test('saving a revisited step continues to the next step, not the furthest one', async () => {
    jest.mocked(getOnboarding).mockResolvedValue({
      ...zonesState,
      current_step: 'goal',
      completed_steps: ['profile', 'heart_rate_monitor', 'timezone', 'history'],
    });
    const screen = await renderScreen();

    expect(await screen.findByText('Kies je trainingsdoel')).toBeTruthy();
    await fireEvent.press(previous(screen));
    await screen.findByText('Waar sta je nu?');
    await fireEvent.press(previous(screen));
    expect(await screen.findByText('Bevestig je tijdzone')).toBeTruthy();

    await fireEvent.press(
      screen.getByRole('button', { name: 'Tijdzone bevestigen' }),
    );

    await waitFor(() => {
      expect(saveOperationalProfile).toHaveBeenCalledWith('athlete-token', {
        timezone: 'Europe/Brussels',
        timezone_source: 'manual',
        timezone_confirmed: true,
      });
    });
    expect(await screen.findByText('Waar sta je nu?')).toBeTruthy();
    await fireEvent.press(next(screen));
    expect(await screen.findByText('Kies je trainingsdoel')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Volgende stap' })).toBeNull();
  });

  test('the view follows the server when it moves back behind the viewed step', async () => {
    jest
      .mocked(getOnboarding)
      .mockResolvedValueOnce(reviewState)
      // After the save the server asks for the timezone again.
      .mockResolvedValue({
        ...zonesState,
        current_step: 'timezone',
        completed_steps: ['profile', 'heart_rate_monitor'],
      });
    const screen = await renderScreen();

    await screen.findByText('Klaar voor je eerste voorstel');
    await fireEvent.press(previous(screen));
    await screen.findByText('Instellen voor zwemmen');
    await fireEvent.press(previous(screen));
    await screen.findByText('Kies je trainingsdoel');
    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));

    expect(await screen.findByText('Bevestig je tijdzone')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Volgende stap' })).toBeNull();
    expect(screen.getByLabelText(/Stap 3 van 7\. Tijdzone/)).toBeTruthy();
  });

  test('Android hardware back goes to the previous step and is left alone on the first step', async () => {
    const remove = jest.fn();
    let pressBack: Parameters<typeof BackHandler.addEventListener>[1] | undefined;
    const addEventListener = jest
      .spyOn(BackHandler, 'addEventListener')
      .mockImplementation((_event, handler) => {
        pressBack = handler;
        return { remove };
      });
    jest.mocked(getOnboarding).mockResolvedValue({
      ...zonesState,
      current_step: 'heart_rate_monitor',
      completed_steps: ['profile'],
    });
    const screen = await renderScreen();
    await screen.findByText('Heb je toegang tot een hartslagmeter?');

    expect(addEventListener).toHaveBeenLastCalledWith('hardwareBackPress', expect.any(Function));
    let handled: boolean | null | undefined;
    await act(async () => {
      // The screen's handler does not read the event.
      handled = pressBack?.(undefined as never);
    });

    expect(handled).toBe(true);
    expect(await screen.findByText('Jouw basis')).toBeTruthy();
    // Nothing earlier exists, so the system keeps its default back behaviour.
    expect(remove).toHaveBeenCalled();
    expect(addEventListener.mock.calls.length).toBe(remove.mock.calls.length);
    addEventListener.mockRestore();
  });

  test('goal options are only fetched once the goal step is shown', async () => {
    jest.mocked(getOnboarding).mockResolvedValue(zonesState);
    const screen = await renderScreen();

    await screen.findByText('Instellen voor zwemmen');
    // Startup stays lean: the zone step does not need them.
    expect(getGoalPlanningOptions).not.toHaveBeenCalled();

    await fireEvent.press(previous(screen));

    expect(
      await screen.findByRole('radio', { name: 'Wedstrijd of evenement' }),
    ).toBeTruthy();
    expect(
      screen.getByRole('radio', { name: 'Wedstrijd of evenement' }).props
        .accessibilityState.disabled,
    ).toBe(false);
    expect(getGoalPlanningOptions).toHaveBeenCalledTimes(1);
    expect(getGoalPlanningOptions).toHaveBeenCalledWith('athlete-token');

    // Leaving and returning reuses what was fetched.
    await fireEvent.press(next(screen));
    await screen.findByText('Instellen voor zwemmen');
    await fireEvent.press(previous(screen));
    await screen.findByText('Kies je trainingsdoel');
    expect(getGoalPlanningOptions).toHaveBeenCalledTimes(1);
  });

  test('the revisited goal step waits for its options and offers a retry when they fail', async () => {
    let rejectOptions: (reason: Error) => void = () => undefined;
    jest
      .mocked(getGoalPlanningOptions)
      .mockReturnValueOnce(
        new Promise<GoalPlanningOption[]>((_resolve, reject) => {
          rejectOptions = reject;
        }),
      )
      .mockResolvedValue(goalOptions);
    jest.mocked(getOnboarding).mockResolvedValue(zonesState);
    const screen = await renderScreen();

    await screen.findByText('Instellen voor zwemmen');
    await fireEvent.press(previous(screen));

    // No goal form with empty options while the request is open.
    expect(await screen.findByLabelText('Laden…')).toBeTruthy();
    expect(screen.queryByText('Kies je trainingsdoel')).toBeNull();
    expect(screen.getByLabelText(/Stap 5 van 7\. Doel/)).toBeTruthy();

    await act(async () => {
      rejectOptions(new Error('Doelkeuzes zijn tijdelijk niet beschikbaar.'));
    });

    expect(
      await screen.findByText('Doelkeuzes zijn tijdelijk niet beschikbaar.'),
    ).toBeTruthy();
    expect(screen.queryByText('Kies je trainingsdoel')).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Opnieuw proberen' }));

    expect(await screen.findByText('Kies je trainingsdoel')).toBeTruthy();
    expect(getGoalPlanningOptions).toHaveBeenCalledTimes(2);
    expect(screen.queryByText('Doelkeuzes zijn tijdelijk niet beschikbaar.')).toBeNull();
  });
});
