import { fireEvent, render, waitFor } from '@testing-library/react-native';

import type {
  GoalPlanningOption,
  OnboardingState,
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
    await fireEvent.changeText(screen.getByLabelText('Rusthartslag'), '52');
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
    await fireEvent.press(
      screen.getByRole('button', { name: /Gedetecteerd op dit apparaat/ }),
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Tijdzone expliciet bevestigen' }),
    );
    expect(onSave).toHaveBeenCalledWith('Europe/Amsterdam', 'device');
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
    const inputs = screen.getAllByLabelText('Gemiddelde uren per week');
    await fireEvent.changeText(inputs[0], '2');
    await fireEvent.changeText(inputs[1], '4');
    await fireEvent.changeText(inputs[2], '3');
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
    await fireEvent.press(screen.getByRole('radio', { name: 'Lopen' }));
    await fireEvent.changeText(screen.getByLabelText('Naam van de race'), '10K');
    await fireEvent.changeText(screen.getByLabelText('Racedatum'), '20990615');
    await fireEvent.changeText(screen.getByLabelText('Afstand'), '10000');
    await fireEvent.changeText(screen.getByLabelText('Totale richttijd'), '1:00:00');
    await fireEvent.press(screen.getByRole('button', { name: 'A-doel opslaan' }));

    expect(onSave).toHaveBeenCalledWith({
      race_type: 'run',
      race_name: '10K',
      race_date: '2099-06-15',
      run_distance_meters: 10000,
      total_target_time_seconds: 3600,
    });
  });

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
