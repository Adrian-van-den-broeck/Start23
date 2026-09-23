import { fireEvent, render, waitFor, within } from '@testing-library/react-native';

import {
  approveZoneProposal,
  confirmCalibrationThreshold,
  createActivity,
  evaluateCalibration,
  getCalibrationStatus,
  getOnboarding,
  listCalibrationProtocols,
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
import { CalibrationScreen } from './CalibrationScreen';

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

    expect(await screen.findByRole('alert', { name: 'Stop if you feel pain' })).toBeTruthy();
    expect(screen.getByLabelText('Totale duur')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /feedback invullen/i })).toBeNull();
    expect(screen.queryByText(/Tijdzone uit je bevestigde profiel/i)).toBeNull();
  });

  test.each([
    ['run', 'start23_run_threshold_30min_v1', 'field_test'],
    ['bike', 'start23_bike_ftp_30min_v1', 'field_test'],
    ['bike', 'start23_bike_fthr_20min_v1', 'field_test'],
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
        await screen.findByRole('alert', { name: 'Stop if you feel pain' }),
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

    await fireEvent.press(
      within(screen.getByLabelText('Hoe voelde de volledige sessie?')).getByRole('radio', {
        name: 'Zwaar, net niet in het rood. (RPE 6)',
      }),
    );
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
        name: 'Opslaan en deterministisch evalueren',
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
});
