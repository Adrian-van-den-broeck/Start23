import type { ReactElement } from 'react';
import { fireEvent, render as renderUi, waitFor, within } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';

import {
  approveZoneProposal,
  confirmCalibrationThreshold,
  createActivity,
  evaluateCalibration,
  getCalibrationStatus,
  getOnboarding,
  listCalibrationProtocols,
  rejectCalibrationThreshold,
  saveCalibrationObservation,
  submitActivityRpe,
} from '../api/client';
import type {
  CalibrationEvaluation,
  CalibrationProtocol,
  CompletedActivity,
  DisciplineSetup,
  OnboardingState,
} from '../api/types';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { CalibrationScreen } from './CalibrationScreen';

// Dutch is the default language; the English test opts in through the stored preference.
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(async () => null),
  setItemAsync: jest.fn(async () => undefined),
  WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked',
}));

function render(ui: ReactElement) {
  return renderUi(ui, { wrapper: LanguageProvider });
}

jest.mock('../api/client', () => ({
  approveZoneProposal: jest.fn(),
  confirmCalibrationThreshold: jest.fn(),
  createActivity: jest.fn(),
  evaluateCalibration: jest.fn(),
  getCalibrationStatus: jest.fn(),
  getOnboarding: jest.fn(),
  listCalibrationProtocols: jest.fn(),
  rejectCalibrationThreshold: jest.fn(),
  saveCalibrationObservation: jest.fn(),
  submitActivityRpe: jest.fn(),
}));

const setup: DisciplineSetup = {
  discipline: 'run',
  setup_route: 'calibration_week',
  guidance_mode: 'heart_rate',
  setup_status: 'calibration_pending',
  protocol_id: 'start23_week1_run_calibration_v1',
  pool_length_meters: null,
  threshold_status: 'unknown',
  zone_status: 'pending_protocol',
  source: 'week1_calibration',
  validation_status: 'not_assessed',
  confidence: 'not_assessed',
  known_thresholds: [],
  known_zone_profiles: [],
  revision: 1,
  created_at: '2026-09-21T10:00:00Z',
  updated_at: '2026-09-21T10:00:00Z',
};

const protocol: CalibrationProtocol = {
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
  segments: [
    {
      order: 1,
      segment_id: 'warmup',
      purpose: 'warmup',
      duration_seconds: 600,
      distance_meters: null,
      target_rpe_min: 2,
      target_rpe_max: 3,
      rpe_zone_number: 1,
      rpe_display_label: 'Zone 1 · RPE 2-3',
      rpe_training_type: 'Herstel',
      rpe_description: 'Heel ontspannen; moeiteloos praten en zingen.',
      optional: false,
    },
    {
      order: 2,
      segment_id: 'comfortable_20min',
      purpose: 'calibration_observation',
      duration_seconds: 1200,
      distance_meters: null,
      target_rpe_min: 4,
      target_rpe_max: 4,
      rpe_zone_number: 2,
      rpe_display_label: 'Zone 2 · RPE 4',
      rpe_training_type: 'Duur',
      rpe_description: 'Comfortabel tempo; vlot babbelen in hele zinnen.',
      optional: false,
    },
    {
      order: 3,
      segment_id: 'cooldown',
      purpose: 'cooldown',
      duration_seconds: 600,
      distance_meters: null,
      target_rpe_min: 1,
      target_rpe_max: 2,
      rpe_zone_number: 1,
      rpe_display_label: 'Zone 1 · RPE 1-2',
      rpe_training_type: 'Herstel',
      rpe_description: 'Rustig uitlopen.',
      optional: false,
    },
  ],
};

const onboarding = {
  status: 'in_progress',
  current_step: 'zones',
  completed_steps: ['profile', 'heart_rate_monitor', 'timezone'],
  current_onboarding_version: 'phase-14-onboarding-v2',
  current_ruleset_version: 'phase-13-joren-ruleset-1',
  completed_onboarding_version: null,
  completed_ruleset_version: null,
  upgrade_required: false,
  missing_upgrade_steps: [],
  profile: {
    timezone: 'Europe/Amsterdam',
    timezone_confirmed_at: '2026-09-21T10:00:00Z',
  },
  training_history: [],
  primary_goal: null,
  required_disciplines: ['run'],
  zones: [],
  discipline_setups: [setup],
  can_complete: false,
  initial_plan_request_id: null,
  onboarding_revision: 2,
} as unknown as OnboardingState;

const evaluation: CalibrationEvaluation = {
  id: 'evaluation-id',
  activity_id: 'activity-id',
  protocol_id: protocol.protocol_id,
  discipline: 'run',
  ruleset_version: 'phase-13-joren-ruleset-1',
  status: 'threshold_estimated',
  threshold_status: 'threshold_estimated',
  zone_status: 'pending_athlete_confirmation',
  confidence: 'medium',
  reason_codes: ['zone_profile_pending_athlete_confirmation'],
  thresholds: [{ metric_kind: 'run_lthr_bpm', value: '165' }],
  zone_model_version: 'phase-13-joren-ruleset-1',
  zone_profiles: [],
  requires_athlete_confirmation: true,
  review_status: 'pending_athlete_confirmation',
  fingerprint: 'fingerprint',
  created_at: '2026-09-21T10:30:00Z',
};

function arrange() {
  jest.mocked(getCalibrationStatus).mockResolvedValue({
    setups: [setup],
    evaluations: [],
    threshold_decisions: [],
  });
  jest.mocked(getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(listCalibrationProtocols).mockResolvedValue([protocol]);
  jest.mocked(createActivity).mockResolvedValue({
    id: 'activity-id',
  } as CompletedActivity);
  jest.mocked(submitActivityRpe).mockResolvedValue({
    id: 'activity-id',
  } as CompletedActivity);
  jest.mocked(saveCalibrationObservation).mockImplementation(async (_, input) => ({
    ...input,
    id: 'observation-id',
    fingerprint: 'observation-fingerprint',
    created_at: '2026-09-21T10:30:00Z',
  }));
  jest.mocked(evaluateCalibration).mockResolvedValue(evaluation);
}

describe('CalibrationScreen Phase 15 flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    arrange();
  });

  test('opens directly on the actionable flow with the prominent pain warning and no timezone notice', async () => {
    const screen = await render(
      <CalibrationScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );

    expect(await screen.findByRole('alert', { name: 'Stop als je pijn voelt' })).toBeTruthy();
    expect(screen.queryByText('Stop if you feel pain')).toBeNull();
    expect(screen.getByLabelText('Totale duur: 00:40:00')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /feedback invullen/i })).toBeNull();
    expect(screen.queryByText(/Tijdzone uit je bevestigde profiel/i)).toBeNull();
  });

  // Owner decision: the internal protocol provenance line is for staging candidates only.
  test('protocol provenance stays out of regular builds and shows in a staging candidate', async () => {
    const keys = ['EXPO_PUBLIC_VERIFICATION_BUILD', 'EXPO_PUBLIC_API_BASE_URL', 'EXPO_PUBLIC_SUPABASE_URL'] as const;
    const saved = keys.map((key) => process.env[key]);
    const provenance = 'Protocol: start23_week1_run_calibration_v1 · v1 · approved_active';
    try {
      const regular = await render(<CalibrationScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} />);
      await regular.findByRole('alert', { name: 'Stop als je pijn voelt' });
      expect(regular.queryByText(provenance)).toBeNull();
      expect(regular.getByText('Beoordeeld v1')).toBeTruthy();
      await regular.unmount();
      process.env.EXPO_PUBLIC_VERIFICATION_BUILD = '1';
      process.env.EXPO_PUBLIC_API_BASE_URL = 'https://r6-api-r6-staging.up.railway.app';
      process.env.EXPO_PUBLIC_SUPABASE_URL = 'https://isfumhgqphieoayqahjv.supabase.co';
      const staging = await render(<CalibrationScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} />);
      expect(await staging.findByText(provenance)).toBeTruthy();
    } finally {
      keys.forEach((key, index) => { if (saved[index] === undefined) delete process.env[key]; else process.env[key] = saved[index]; });
    }
  });

  test.each([
    ['swim', 'start23_swim_css_400_200_v1', 'field_test'],
    ['run', 'start23_week1_run_calibration_v1', 'submaximal_calibration'],
    ['bike', 'start23_week1_bike_calibration_v1', 'submaximal_calibration'],
    ['swim', 'start23_week1_swim_calibration_v1', 'submaximal_calibration'],
  ] as const)(
    'shows the pain warning before executable %s protocol %s',
    async (discipline, protocolId, protocolType) => {
      const selectedSetup: DisciplineSetup = {
        ...setup,
        discipline,
        setup_route:
          protocolType === 'field_test' ? 'field_test' : 'calibration_week',
        setup_status:
          protocolType === 'field_test' ? 'test_pending' : 'calibration_pending',
        protocol_id: protocolId,
        source:
          protocolType === 'field_test' ? 'field_test' : 'week1_calibration',
      };
      const selectedProtocol: CalibrationProtocol = {
        ...protocol,
        protocol_id: protocolId,
        discipline,
        protocol_type: protocolType,
        required_observation_type:
          discipline === 'swim'
            ? 'elapsed_time_distance_and_rpe'
            : 'average_heart_rate_and_rpe',
        segments: protocol.segments,
      };
      jest.mocked(getCalibrationStatus).mockResolvedValue({
        setups: [selectedSetup],
        evaluations: [],
        threshold_decisions: [],
      });
      jest.mocked(listCalibrationProtocols).mockResolvedValue([selectedProtocol]);

      const screen = await render(
        <CalibrationScreen
          accessToken="athlete-token"
          onBack={jest.fn()}
          onSignOut={jest.fn(async () => undefined)}
        />,
      );

      expect(
        await screen.findByRole('alert', { name: 'Stop als je pijn voelt' }),
      ).toBeTruthy();
    },
  );

  test('submits exact average HR and canonical RPE while zones remain pending', async () => {
    const screen = await render(
      <CalibrationScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    await screen.findByText('Objectief + jouw gevoel');

    // RPE is a compact field; the scale opens in a sheet and closes on choice.
    await fireEvent.press(screen.getByRole('button', { name: 'Hoe voelde de volledige sessie?: Kies je RPE' }));
    await fireEvent.press(
      within(screen.getByLabelText('Hoe voelde de volledige sessie?')).getByRole('radio', {
        name: 'Zwaar, net niet in het rood. (RPE 6)',
      }),
    );
    expect(screen.getByRole('button', {
      name: 'Hoe voelde de volledige sessie?: Zwaar, net niet in het rood. (RPE 6)',
    })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Hoe voelde dit blok?: Kies je RPE' }));
    await fireEvent.press(
      within(screen.getByLabelText('Hoe voelde dit blok?')).getByRole('radio', {
        name: 'Focus nodig, praten in zinnen. (RPE 4)',
      }),
    );
    await fireEvent.changeText(
      screen.getByLabelText('Gemiddelde hartslag'),
      '148',
    );
    await fireEvent.press(
      screen.getByRole('button', {
        name: 'Opslaan en resultaat berekenen',
      }),
    );

    await waitFor(() => {
      expect(submitActivityRpe).toHaveBeenCalledWith(
        'athlete-token',
        'activity-id',
        6,
        148,
      );
      expect(saveCalibrationObservation).toHaveBeenCalledWith(
        'athlete-token',
        expect.objectContaining({
          activity_id: 'activity-id',
          average_heart_rate_bpm: '148',
          reported_block_rpe: 4,
          target_rpe: 4,
        }),
      );
    });
    expect(await screen.findByText('Drempel geschat')).toBeTruthy();
    // Confidence, zone state and versions are written out, never shown as API codes.
    expect(screen.getByText('Vertrouwen: gemiddeld')).toBeTruthy();
    expect(screen.getByText('Zones: wachten op jouw bevestiging')).toBeTruthy();
    expect(screen.getByText(/^Regels: /)).toBeTruthy();
    expect(JSON.stringify(screen.toJSON())).not.toMatch(/pending_athlete_confirmation|Vertrouwen: medium|joren|model_derived|start23-zone-model/);
    expect(screen.getByText(/afzonderlijk, nog niet actief zonevoorstel/)).toBeTruthy();
    expect(approveZoneProposal).not.toHaveBeenCalled();

    jest.mocked(confirmCalibrationThreshold).mockResolvedValue({
      evaluation_id: 'evaluation-id',
      state: 'accepted',
      zone_profile_id: 'pending-zone-id',
      zone_proposal_id: 'zone-proposal-id',
      base_zone_profile_id: null,
      decided_at: '2026-09-21T10:40:00Z',
      zone_proposal_state: 'pending',
    });
    await fireEvent.press(
      screen.getByRole('button', { name: 'Drempel bevestigen' }),
    );
    expect(await screen.findByRole('button', { name: 'Zones bevestigen' })).toBeTruthy();
    expect(approveZoneProposal).not.toHaveBeenCalled();
  });

  test('shows the below-140 warning before threshold approval', async () => {
    const lowEvaluation: CalibrationEvaluation = {
      ...evaluation,
      reason_codes: [
        'calculated_threshold_unusually_low',
        'zone_profile_pending_athlete_confirmation',
      ],
      thresholds: [{ metric_kind: 'run_lthr_bpm', value: '119' }],
    };
    jest.mocked(getCalibrationStatus).mockResolvedValue({
      setups: [setup],
      evaluations: [lowEvaluation],
      threshold_decisions: [],
    });
    const screen = await render(
      <CalibrationScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    await fireEvent.press(await screen.findByRole('button', { name: /Bekijk/ }));
    expect(screen.getByText(/berekende drempel lijkt ongewoon laag/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Drempel bevestigen' })).toBeTruthy();
  });

  test('a new Tests navigation session does not retain a stale protocol selection', async () => {
    const bikeSetup: DisciplineSetup = {
      ...setup,
      discipline: 'bike',
      protocol_id: 'start23_week1_bike_calibration_v1',
    };
    const bikeProtocol: CalibrationProtocol = {
      ...protocol,
      discipline: 'bike',
      protocol_id: 'start23_week1_bike_calibration_v1',
    };
    jest.mocked(getCalibrationStatus).mockResolvedValue({
      setups: [setup, bikeSetup],
      evaluations: [],
      threshold_decisions: [],
    });
    jest.mocked(listCalibrationProtocols).mockImplementation(
      async (_token, discipline) =>
        discipline === 'run' ? [protocol] : [bikeProtocol],
    );

    const first = await render(
      <CalibrationScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    const bikeChoice = await first.findByRole('radio', { name: 'Fietsen' });
    await fireEvent.press(bikeChoice);
    expect(bikeChoice.props.accessibilityState.checked).toBe(true);
    await first.unmount();

    const second = await render(
      <CalibrationScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
      />,
    );
    const runChoice = await second.findByRole('radio', { name: 'Hardlopen' });

    expect(runChoice.props.accessibilityState.checked).toBe(true);
  });
});


describe('Batch 11 calibration lifecycle separation', () => {
  beforeEach(() => { jest.clearAllMocks(); arrange(); });
  const props = { accessToken: 'athlete-token', onBack: jest.fn(), onSignOut: jest.fn(async () => undefined) };
  test('unavailable executable protocols stay empty, with no invented observation or completion', async () => {
    jest.mocked(listCalibrationProtocols).mockResolvedValue([]);
    const screen = await render(<CalibrationScreen {...props} />);
    expect(await screen.findByText('Geen protocol gekozen')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Opslaan en resultaat berekenen' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Zones bevestigen' })).toBeNull();
    expect(createActivity).not.toHaveBeenCalled();
    expect(evaluateCalibration).not.toHaveBeenCalled();
  });
  test('historical incomplete observation keeps its reason and cannot confirm a threshold', async () => {
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [setup], evaluations: [{
      ...evaluation, status: 'insufficient_data', threshold_status: 'unknown', zone_status: 'pending_protocol',
      requires_athlete_confirmation: false, thresholds: [], reason_codes: ['interrupted'],
    }], threshold_decisions: [] });
    const screen = await render(<CalibrationScreen {...props} />);
    await fireEvent.press(await screen.findByRole('button', { name: /Bekijk/ }));
    expect(screen.getByText('Meer of betere gegevens nodig')).toBeTruthy();
    expect(screen.getByText(/Een verplicht blok is onderbroken/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Drempel bevestigen' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Zones bevestigen' })).toBeNull();
    expect(approveZoneProposal).not.toHaveBeenCalled();
  });
  test('threshold rejection is its own request and never activates zones', async () => {
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [setup], evaluations: [evaluation], threshold_decisions: [] });
    jest.mocked(rejectCalibrationThreshold).mockResolvedValue({ evaluation_id: evaluation.id, state: 'rejected',
      zone_profile_id: null, zone_proposal_id: null, base_zone_profile_id: null,
      decided_at: '2026-09-21T10:40:00Z', zone_proposal_state: null });
    const screen = await render(<CalibrationScreen {...props} />);
    await fireEvent.press(await screen.findByRole('button', { name: /Bekijk/ }));
    await fireEvent.press(screen.getByRole('button', { name: 'Drempel afwijzen' }));
    await waitFor(() => expect(rejectCalibrationThreshold).toHaveBeenCalledWith('athlete-token', evaluation.id));
    expect(screen.getByText(/Je hebt de drempel afgewezen/)).toBeTruthy();
    expect(confirmCalibrationThreshold).not.toHaveBeenCalled();
    expect(approveZoneProposal).not.toHaveBeenCalled();
  });
  test('zone activation requires a separate explicit request with the original base profile', async () => {
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [setup], evaluations: [evaluation], threshold_decisions: [] });
    jest.mocked(confirmCalibrationThreshold).mockResolvedValue({ evaluation_id: evaluation.id, state: 'accepted',
      zone_profile_id: 'pending-zone-id', zone_proposal_id: 'zone-proposal-id', base_zone_profile_id: 'active-zone-id',
      decided_at: '2026-09-21T10:40:00Z', zone_proposal_state: 'pending' });
    jest.mocked(approveZoneProposal).mockResolvedValue({} as never);
    const screen = await render(<CalibrationScreen {...props} />);
    await fireEvent.press(await screen.findByRole('button', { name: /Bekijk/ }));
    expect(screen.queryByRole('button', { name: 'Zones bevestigen' })).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Drempel bevestigen' }));
    await screen.findByRole('button', { name: 'Zones bevestigen' });
    expect(approveZoneProposal).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByRole('button', { name: 'Zones bevestigen' }));
    await waitFor(() => expect(approveZoneProposal).toHaveBeenCalledWith('athlete-token', 'zone-proposal-id', 'active-zone-id'));
  });
});

// Read-only CalibrationService.protocols projections, retained with Batch 11 provenance.
const currentProtocols = require('../../../docs/ui/evidence/final-visual-batch-11/current-protocol-projections.json') as Record<'run' | 'bike' | 'swim', CalibrationProtocol[]>;
describe('Batch 11 current source-backed protocol forms', () => {
  beforeEach(() => { jest.clearAllMocks(); arrange(); });
  test.each(['run', 'bike'] as const)('%s keeps its approved optional observation excluded until explicitly included', async (discipline) => {
    const current = currentProtocols[discipline].find(item => item.protocol_type === 'submaximal_calibration')!;
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [{ ...setup, discipline, protocol_id: current.protocol_id }], evaluations: [], threshold_decisions: [] });
    jest.mocked(listCalibrationProtocols).mockResolvedValue([current]);
    const screen = await render(<CalibrationScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} />);
    const optional = await screen.findByRole('checkbox', { name: 'Optioneel blok uitgevoerd' });
    expect(optional.props.accessibilityState.checked).toBe(false);
    expect(screen.getAllByLabelText('Gemiddelde hartslag')).toHaveLength(1);
    await fireEvent.press(optional);
    expect(optional.props.accessibilityState.checked).toBe(true);
    expect(screen.getAllByLabelText('Gemiddelde hartslag')).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: 'Hoe voelde dit blok?: Kies je RPE' })).toHaveLength(2);
    expect(createActivity).not.toHaveBeenCalled();
    expect(evaluateCalibration).not.toHaveBeenCalled();
  });
  test('current swim calibration retains both measured repetition blocks and the pool confirmation', async () => {
    const current = currentProtocols.swim.find(item => item.protocol_type === 'submaximal_calibration')!;
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [{ ...setup, discipline: 'swim', protocol_id: current.protocol_id, guidance_mode: 'pace', pool_length_meters: 25 }], evaluations: [], threshold_decisions: [] });
    jest.mocked(listCalibrationProtocols).mockResolvedValue([current]);
    const screen = await render(<CalibrationScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} />);
    const pool = await screen.findByRole('checkbox', { name: '25 m-bad, vrije slag en zonder paddles/vliezen/pull buoy' });
    expect(pool.props.accessibilityState.checked).toBe(false);
    expect(screen.getAllByRole('button', { name: 'Gemeten totale tijd van dit blok: nog niet ingesteld' })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: 'Herhaling 4: nog niet ingesteld' })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: 'Rust 4: 0:00' })).toHaveLength(2);
    // Each repetition time is picked on its own wheel; the others keep their values.
    await fireEvent.press(screen.getAllByRole('button', { name: 'Herhaling 2: nog niet ingesteld' })[0]!);
    await fireEvent.press(screen.getByRole('radio', { name: '3 min' }));
    await fireEvent.press(screen.getByRole('radio', { name: '30 sec' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    expect(screen.getByRole('button', { name: 'Herhaling 2: 3:30' })).toBeTruthy();
    expect(screen.getAllByRole('button', { name: 'Herhaling 1: nog niet ingesteld' })).toHaveLength(2);
    expect(screen.getByText('Beoordeeld v' + current.version)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Drempel bevestigen' })).toBeNull();
    expect(createActivity).not.toHaveBeenCalled();
    expect(evaluateCalibration).not.toHaveBeenCalled();
  });
});

describe('CalibrationScreen in English', () => {
  const props = { accessToken: 'athlete-token', onBack: jest.fn(), onSignOut: jest.fn(async () => undefined) };
  beforeEach(() => {
    jest.clearAllMocks();
    arrange();
    jest.mocked(SecureStore.getItemAsync).mockResolvedValueOnce('en');
  });

  test('shows the feedback form, pain warning and RPE scale in English', async () => {
    const screen = await render(<CalibrationScreen {...props} />);
    expect(await screen.findByRole('alert', { name: 'Stop if you feel pain' })).toBeTruthy();
    expect(screen.queryByText('Stop als je pijn voelt')).toBeNull();
    expect(screen.getByRole('radio', { name: 'Running' })).toBeTruthy();
    expect(screen.getByText('Week 1 run calibration')).toBeTruthy();
    expect(screen.getByText('Submaximal')).toBeTruthy();
    expect(screen.getByText('Reviewed v1')).toBeTruthy();
    expect(screen.getByText('Guided by heart rate. Follow the blocks below and fill in your feedback right away.')).toBeTruthy();
    expect(screen.getByText('Objective + how it felt')).toBeTruthy();
    expect(screen.getByLabelText('Total duration: 00:40:00')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'How did the whole session feel?: Choose your RPE' }));
    expect(within(screen.getByLabelText('How did the whole session feel?')).getByRole('radio', {
      name: 'Hard, not quite in the red. (RPE 6)',
    })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Close' }));
    expect(screen.getByRole('button', { name: 'How did this block feel?: Choose your RPE' })).toBeTruthy();
    expect(screen.getByLabelText('Average heart rate')).toBeTruthy();
    expect(screen.queryByText('Objectief + jouw gevoel')).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Save and calculate result' }));
    expect(await screen.findByText('Session RPE must be a whole number from 1 to 10.')).toBeTruthy();
    expect(createActivity).not.toHaveBeenCalled();
  });

  test('shows a prior result and threshold decision in English', async () => {
    jest.mocked(getCalibrationStatus).mockResolvedValue({ setups: [setup], evaluations: [evaluation], threshold_decisions: [] });
    const screen = await render(<CalibrationScreen {...props} />);
    expect(await screen.findByText('1 earlier evaluation for this protocol.')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: /^View / }));
    expect(screen.getByText('Result')).toBeTruthy();
    expect(screen.getByText('Threshold estimated')).toBeTruthy();
    expect(screen.getByText('Confidence: medium')).toBeTruthy();
    expect(screen.getByText('Run LTHR (bpm)')).toBeTruthy();
    expect(screen.getByText(/The threshold and calculated zones are waiting for your separate confirmations/)).toBeTruthy();
    expect(screen.getByText(/Wombo creates a separate zone proposal that is not active yet/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Confirm threshold' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reject threshold' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Drempel bevestigen' })).toBeNull();
    expect(approveZoneProposal).not.toHaveBeenCalled();
  });
});
