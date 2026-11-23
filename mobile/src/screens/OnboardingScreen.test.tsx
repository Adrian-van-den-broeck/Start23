import { fireEvent, render as baseRender, waitFor } from '@testing-library/react-native';

import type {
  GoalPlanningOption,
  OnboardingState,
  PrimaryRaceGoal,
  ZoneProfile,
} from '../api/types';
import {
  GoalStep,
  HeartRateMonitorStep,
  HistoryStep,
  ProfileStep,
  ReviewStep,
  TimezoneStep,
} from './OnboardingScreen';
import type { ReactElement } from 'react';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { setRuntimeLanguage } from '../i18n/runtime';

// No stored preference by default, so the app falls back to Dutch. The English
// tests below store 'en' as the athlete's choice.
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(async () => null),
  setItemAsync: jest.fn(async () => undefined),
  WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked',
}));

// Dutch is the default language; every render goes through the provider like the app does.
const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

beforeEach(() => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  setRuntimeLanguage('nl');
});

function state(overrides: Partial<OnboardingState> = {}): OnboardingState {
  return {
    status: 'in_progress',
    current_step: 'profile',
    completed_steps: [],
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
    ...overrides,
  };
}

// The race type is one compact field; its options live in the sheet it opens.
async function chooseRaceType(
  screen: Awaited<ReturnType<typeof render>>,
  label: string,
  field: RegExp = /^Type wedstrijd: /,
) {
  await fireEvent.press(screen.getByRole('button', { name: field }));
  await fireEvent.press(screen.getByRole('radio', { name: label }));
}

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
  {
    goal_kind: 'personal_goal',
    goal_family: 'general_fitness',
    label: 'Algemene fitheid',
    availability: 'coming_later',
    requires_target_date: false,
    cycle_anchor: 'cycle_week_1',
    unavailable_reason: 'deterministic_rules_not_approved',
  },
];

describe('onboarding components', () => {
  test('profile form submits the separated identifying and physiology input', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <ProfileStep onSave={onSave} profile={null} saving={false} />,
    );

    await fireEvent.changeText(screen.getByLabelText('Voornaam (optioneel)'), 'Ada');
    await fireEvent.changeText(
      screen.getByLabelText('Achternaam (optioneel)'),
      'Lovelace',
    );
    await fireEvent.changeText(screen.getByLabelText('Geboortedatum'), '19900520');
    await fireEvent.changeText(screen.getByLabelText('Rusthartslag, bpm'), '52');
    await fireEvent.press(screen.getByRole('button', { name: 'Profiel opslaan' }));

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith({
        first_name: 'Ada',
        last_name: 'Lovelace',
        date_of_birth: '1990-05-20',
        resting_heart_rate_bpm: 52,
      }),
    );
  });

  test('heart-rate access requires an explicit button action', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <HeartRateMonitorStep onSave={onSave} saving={false} />,
    );

    expect(onSave).not.toHaveBeenCalled();
    await fireEvent.press(
      screen.getByRole('button', {
        name: 'Ja, ik kan gemiddelde hartslag meten',
      }),
    );
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  test('device timezone is displayed and accepted explicitly without GPS', async () => {
    const resolvedOptions = jest.spyOn(
      Intl.DateTimeFormat.prototype,
      'resolvedOptions',
    );
    resolvedOptions.mockReturnValue({
      timeZone: 'Europe/Amsterdam',
    } as Intl.ResolvedDateTimeFormatOptions);
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <TimezoneStep onSave={onSave} profile={null} saving={false} />,
    );

    expect(screen.getAllByText('Europe/Amsterdam').length).toBeGreaterThan(0);
    const detected = screen.getByRole('radio', {
      name: 'Gedetecteerd op dit apparaat: Europe/Amsterdam',
    });
    // Detection alone never selects or stores the value.
    expect(detected.props.accessibilityState.checked).toBe(false);
    expect(
      screen.getByRole('button', { name: 'Tijdzone expliciet bevestigen' })
        .props.accessibilityState.disabled,
    ).toBe(true);
    await fireEvent.press(detected);
    await fireEvent.press(
      screen.getByRole('button', { name: 'Tijdzone expliciet bevestigen' }),
    );
    expect(onSave).toHaveBeenCalledWith('Europe/Amsterdam', 'device');
    resolvedOptions.mockRestore();
  });

  test('a common timezone is chosen from one compact list and saved as a manual choice', async () => {
    const resolvedOptions = jest.spyOn(
      Intl.DateTimeFormat.prototype,
      'resolvedOptions',
    );
    resolvedOptions.mockReturnValue({
      timeZone: 'Europe/Amsterdam',
    } as Intl.ResolvedDateTimeFormatOptions);
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <TimezoneStep onSave={onSave} profile={null} saving={false} />,
    );

    // The list stays closed until asked for, so the step is not a wall of rows.
    expect(screen.queryByRole('radio', { name: 'Europe/Brussels' })).toBeNull();
    await fireEvent.press(
      screen.getByRole('button', { name: 'Veelgebruikte tijdzones: Kies een tijdzone' }),
    );
    await fireEvent.press(screen.getByRole('radio', { name: 'Europe/Brussels' }));
    expect(
      screen.getByRole('button', { name: 'Veelgebruikte tijdzones: Europe/Brussels' }),
    ).toBeTruthy();
    await fireEvent.press(
      screen.getByRole('button', { name: 'Tijdzone expliciet bevestigen' }),
    );
    expect(onSave).toHaveBeenCalledWith('Europe/Brussels', 'manual');
    resolvedOptions.mockRestore();
  });

  test('unavailable device timezone requires a manually accepted IANA value', async () => {
    const resolvedOptions = jest.spyOn(
      Intl.DateTimeFormat.prototype,
      'resolvedOptions',
    );
    resolvedOptions.mockReturnValue({
      timeZone: '',
    } as Intl.ResolvedDateTimeFormatOptions);
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <TimezoneStep onSave={onSave} profile={null} saving={false} />,
    );

    expect(
      screen.getByText(/Automatische detectie is niet beschikbaar/),
    ).toBeTruthy();
    await fireEvent.changeText(
      screen.getByLabelText('Andere IANA-tijdzone'),
      'Europe/Brussels',
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Tijdzone expliciet bevestigen' }),
    );
    expect(onSave).toHaveBeenCalledWith('Europe/Brussels', 'manual');
    resolvedOptions.mockRestore();
  });

  test('history submission still requires all three independent baselines', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <HistoryStep onSave={onSave} saving={false} state={state()} />,
    );
    await fireEvent.changeText(
      screen.getByLabelText('Zwemmen, Gemiddelde uren per week, uur/week'), '2');
    await fireEvent.changeText(
      screen.getByLabelText('Fietsen, Gemiddelde uren per week, uur/week'), '4');
    await fireEvent.changeText(
      screen.getByLabelText('Hardlopen, Gemiddelde uren per week, uur/week'), '3');
    await fireEvent.press(
      screen.getByRole('button', { name: 'Trainingshistorie opslaan' }),
    );

    expect(onSave).toHaveBeenCalledWith({ swim: '2', bike: '4', run: '3' });
  });

  test('run goal submission omits inapplicable swim and bike fields', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <GoalStep
        goal={null}
        onSave={onSave}
        options={goalOptions}
        saving={false}
      />,
    );
    await fireEvent.press(
      screen.getByRole('radio', { name: /Wedstrijd of evenement/ }),
    );
    await chooseRaceType(screen, 'Lopen');
    await fireEvent.changeText(screen.getByLabelText('Naam van de race'), '10K');
    await fireEvent.changeText(screen.getByLabelText('Racedatum'), '20990615');
    await fireEvent.changeText(screen.getByLabelText('Afstand, meter'), '10000');
    await fireEvent.press(screen.getByRole('button', { name: 'Totale richttijd: nog niet ingesteld' }));
    await fireEvent.press(screen.getByRole('radio', { name: '1 uur' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));

    expect(onSave).toHaveBeenCalledWith({
      race_type: 'run',
      race_name: '10K',
      race_date: '2099-06-15',
      run_distance_meters: 10000,
      total_target_time_seconds: 3600,
    });
  });

  test('run pace input derives the existing total-time contract without a pace field', async () => {
    const onSave = jest.fn(async () => undefined);
    const screen = await render(
      <GoalStep goal={null} onSave={onSave} options={goalOptions} saving={false} />,
    );
    await fireEvent.press(screen.getByRole('radio', { name: /Wedstrijd of evenement/ }));
    await chooseRaceType(screen, 'Lopen');
    await fireEvent.changeText(screen.getByLabelText('Naam van de race'), '10K');
    await fireEvent.changeText(screen.getByLabelText('Racedatum'), '20990615');
    await fireEvent.changeText(screen.getByLabelText('Afstand, meter'), '10000');
    await fireEvent.press(screen.getByRole('radio', { name: 'Richttempo (min/km)' }));
    await fireEvent.changeText(screen.getByLabelText('Richttempo'), '5:00');
    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));
    expect(onSave).toHaveBeenCalledWith({
      race_type: 'run', race_name: '10K', race_date: '2099-06-15',
      run_distance_meters: 10000, total_target_time_seconds: 3000,
    });
  });

  test('editing a saved goal loads and preserves exact canonical durations', async () => {
    const onSave = jest.fn(async () => undefined);
    const goal: PrimaryRaceGoal = {
      id: 'goal-id',
      race_type: 'triathlon',
      race_name: 'Bewaarde triatlon',
      race_date: '2099-06-15',
      swim_distance_meters: 1500,
      bike_distance_meters: 40000,
      run_distance_meters: 10000,
      total_target_time_seconds: 13_530,
      swim_target_time_seconds: 1803,
      bike_target_time_seconds: 7207,
      run_target_time_seconds: 3601,
      specific_focus: null,
      priority: 'A',
      goal_type: 'race',
      status: 'active',
      revision: 2,
      created_at: '2026-09-01T10:00:00Z',
      updated_at: '2026-09-01T10:00:00Z',
    };
    const screen = await render(
      <GoalStep
        goal={goal}
        onSave={onSave}
        options={goalOptions}
        saving={false}
      />,
    );

    expect(screen.getByLabelText('Totale richttijd: 03:45:30')).toBeTruthy();
    expect(screen.getByLabelText('Richttijd onderdeel: 00:30:03')).toBeTruthy();
    expect(screen.getByLabelText('Richttijd onderdeel: 02:00:07')).toBeTruthy();
    expect(screen.getByLabelText('Richttijd onderdeel: 01:00:01')).toBeTruthy();

    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));

    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        total_target_time_seconds: 13_530,
        swim_target_time_seconds: 1803,
        bike_target_time_seconds: 7207,
        run_target_time_seconds: 3601,
      }),
    );
  });

  test.each([
    ['run', 'Lopen', ['run']],
    ['bike', 'Fietsen', ['bike']],
    ['swim', 'Zwemmen', ['swim']],
    ['duathlon', 'Duatlon', ['bike', 'run']],
    ['triathlon', 'Triatlon', ['swim', 'bike', 'run']],
  ] as const)(
    '%s goal identifies every missing required field and submits once complete',
    async (raceType, raceLabel, disciplines) => {
      const onSave = jest.fn(async () => undefined);
      const screen = await render(
        <GoalStep
          goal={null}
          onSave={onSave}
          options={goalOptions}
          saving={false}
        />,
      );
      await fireEvent.press(
        screen.getByRole('radio', { name: /Wedstrijd of evenement/ }),
      );
      await chooseRaceType(screen, raceLabel);
      await fireEvent.changeText(
        screen.getByLabelText('Naam van de race'),
        'Bewaarde race',
      );

      await fireEvent.press(
        screen.getByRole('button', { name: 'A-doel opslaan' }),
      );

      expect(onSave).not.toHaveBeenCalled();
      expect(screen.getByLabelText('Naam van de race').props.value).toBe(
        'Bewaarde race',
      );
      expect(screen.getByText('Racedatum is verplicht.')).toBeTruthy();
      expect(screen.getByText('Totale richttijd is verplicht.')).toBeTruthy();
      expect(screen.getAllByText('Afstand is verplicht.')).toHaveLength(
        disciplines.length,
      );
      expect(
        screen.getByText(/Vul de gemarkeerde verplichte velden in/),
      ).toBeTruthy();

      await fireEvent.changeText(screen.getByLabelText('Racedatum'), '20990615');
      await fireEvent.press(screen.getByRole('button', { name: 'Totale richttijd: nog niet ingesteld' }));
      await fireEvent.press(screen.getByRole('radio', { name: '3 uur' }));
      await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
      const distanceFields = screen.getAllByLabelText('Afstand, meter');
      for (const field of distanceFields) {
        await fireEvent.changeText(field, '1000');
      }
      await fireEvent.press(
        screen.getByRole('button', { name: 'A-doel opslaan' }),
      );

      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          race_type: raceType,
          race_name: 'Bewaarde race',
          race_date: '2099-06-15',
          total_target_time_seconds: 10800,
          ...Object.fromEntries(
            disciplines.map((discipline) => [
              `${discipline}_distance_meters`,
              1000,
            ]),
          ),
        }),
      );
    },
  );

  test('pending required zone remains a separate approval action', async () => {
    const onApproveZone = jest.fn(async () => undefined);
    const pendingZone = {
      id: 'zone-id',
      discipline: 'run',
      status: 'pending',
      proposal_id: 'proposal-id',
      base_zone_profile_id: null,
      metric_profiles: [],
      metric: { metric_kind: 'run_lthr_bpm', value: '172' },
      zone_model_version: 'phase-13-joren-ruleset-1',
    } as unknown as ZoneProfile;
    const irrelevantActiveZone = {
      ...pendingZone,
      id: 'swim-zone-id',
      discipline: 'swim',
      status: 'active',
      proposal_id: null,
    } as unknown as ZoneProfile;
    const screen = await render(
      <ReviewStep
        onApproveZone={onApproveZone}
        onComplete={jest.fn(async () => undefined)}
        onRejectZone={jest.fn(async () => undefined)}
        saving={false}
        state={state({ zones: [pendingZone, irrelevantActiveZone] })}
      />,
    );

    expect(screen.getByText('0/1 disciplines')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Zones bevestigen' }));
    expect(onApproveZone).toHaveBeenCalledWith('proposal-id', null);
  });
});

describe('onboarding components in English', () => {
  beforeEach(() => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en');
  });

  test('profile form shows its labels, hints and actions in English', async () => {
    const screen = await render(
      <ProfileStep onSave={jest.fn(async () => undefined)} profile={null} saving={false} />,
    );

    expect(await screen.findByText('Your basics')).toBeTruthy();
    expect(screen.getByLabelText('First name (optional)')).toBeTruthy();
    expect(screen.getByLabelText('Last name (optional)')).toBeTruthy();
    expect(screen.getByText('Use YYYY-MM-DD. The dashes appear automatically.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Save profile' })).toBeTruthy();
    expect(screen.queryByText('Jouw basis')).toBeNull();
  });

  test('goal form keeps server option labels but translates its own copy', async () => {
    const screen = await render(
      <GoalStep goal={null} onSave={jest.fn(async () => undefined)} options={goalOptions} saving={false} />,
    );

    expect(await screen.findByText('Choose your training goal')).toBeTruthy();
    // The race option label comes from the server and is shown as delivered.
    await fireEvent.press(screen.getByRole('radio', { name: 'Wedstrijd of evenement' }));
    expect(screen.getByText('Wedstrijd of evenement · Available')).toBeTruthy();
    expect(screen.getByText('Race type')).toBeTruthy();
    await chooseRaceType(screen, 'Triathlon', /^Race type: /);
    expect(screen.getByRole('button', { name: 'Race type: Triathlon' })).toBeTruthy();
    expect(screen.getByLabelText('Specific focus (optional)')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Total target time: not set yet' })).toBeTruthy();

    await fireEvent.press(screen.getByRole('button', { name: 'Save A goal' }));

    expect(screen.getByText('Race name is required.')).toBeTruthy();
    expect(screen.getByText('Total target time is required.')).toBeTruthy();
    expect(
      screen.getByText(/^Fill in the highlighted required fields: race name, race date, swim distance/),
    ).toBeTruthy();
  });

  test('review step summarises progress in English', async () => {
    const screen = await render(
      <ReviewStep
        onApproveZone={jest.fn(async () => undefined)}
        onComplete={jest.fn(async () => undefined)}
        onRejectZone={jest.fn(async () => undefined)}
        saving={false}
        state={state()}
      />,
    );

    expect(await screen.findByText('Ready for your first proposal')).toBeTruthy();
    expect(screen.getByText('A goal')).toBeTruthy();
    expect(screen.getAllByText('Missing')).toHaveLength(2);
    expect(screen.getByText('You stay in control')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Finish onboarding' })).toBeTruthy();
  });
});
