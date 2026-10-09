import { fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  approveZoneProposal,
  rejectZoneProposal,
  getOnboarding,
  getZoneProfileState,
  scheduleFieldTest,
} from '../api/client';
import type { DisciplineSetup, OnboardingState, ZoneProfileSnapshot, ZoneProfileState } from '../api/types';
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


const sourceProfile: ZoneProfileSnapshot = {
  id: 'active-v1', discipline: 'run', version: 1, setup_method: 'manual', status: 'active',
  source_method: 'original-source', source_quality: 'measured_lab', review_status: 'confirmed_by_athlete',
  reviewer_id: null, reviewed_at: null, effective_from: null, zone_model_version: 'original-model', evidence_version: 'original-evidence',
  created_at: '2026-09-01T12:00:00Z', values_hidden: false, metric: { metric_kind: 'run_lthr_bpm', value: '172' },
  metric_profiles: [], boundaries: [{ zone_number: 5, lower_value: '177', upper_value: null }], proposal_id: null, base_zone_profile_id: null,
};
function pendingState(hidden = false): ZoneProfileState {
  return { disciplines: [{ discipline: 'run', setup: null, numeric_zone_visibility: 'proposal_confirmation_pending',
    active_profile: { ...sourceProfile, values_hidden: hidden },
    pending_profile: { ...sourceProfile, id: 'pending-v2', version: 2, status: 'pending', proposal_id: 'zone-proposal', base_zone_profile_id: 'active-v1', values_hidden: hidden },
    prior_profiles: [{ ...sourceProfile, id: 'historical-v0', version: 0, status: 'superseded', values_hidden: hidden }],
    test_assignments: [], available_test_scheduling_modes: [] }] };
}
describe('Batch 11 Zones versions and decisions', () => {
  beforeEach(() => { jest.clearAllMocks(); jest.mocked(getOnboarding).mockResolvedValue({} as OnboardingState); });
  const props = { accessToken: 'athlete-token', onBack: jest.fn(), onSignOut: jest.fn(async () => undefined), planContext: null };
  test.each(['approve', 'reject'] as const)('keeps active, pending and superseded sources separate during explicit %s', async decision => {
    jest.mocked(getZoneProfileState).mockResolvedValue(pendingState());
    jest.mocked(approveZoneProposal).mockResolvedValue({} as never);
    jest.mocked(rejectZoneProposal).mockResolvedValue({} as never);
    const screen = await render(<ZoneProfileScreen {...props} />);
    await screen.findByText('Nieuw voorstel');
    expect(screen.getByText('Actief profiel')).toBeTruthy();
    expect(screen.getByText('Versie 0 · superseded')).toBeTruthy();
    expect(screen.getAllByText('172 bpm')).toHaveLength(3);
    expect(screen.getAllByText('177 bpm – open')).toHaveLength(3);
    expect(screen.getAllByText('Model: original-model')).toHaveLength(3);
    expect(approveZoneProposal).not.toHaveBeenCalled(); expect(rejectZoneProposal).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByRole('button', { name: decision === 'approve' ? 'Zones goedkeuren' : 'Afwijzen' }));
    await waitFor(() => {
      if (decision === 'approve') expect(approveZoneProposal).toHaveBeenCalledWith('athlete-token', 'zone-proposal', 'active-v1');
      else expect(rejectZoneProposal).toHaveBeenCalledWith('athlete-token', 'zone-proposal');
    });
    expect(screen.getByText('Actief profiel')).toBeTruthy();
  });
  test('hidden values remain absent from the complete overview, including pending/history and accessibility', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(pendingState(true));
    const screen = await render(<ZoneProfileScreen {...props} />);
    await screen.findByText('Nieuw voorstel');
    const publicTree = JSON.stringify(screen.toJSON());
    expect(publicTree).not.toContain('172'); expect(publicTree).not.toContain('177');
    expect(screen.getAllByText(/Numerieke waarden blijven verborgen/)).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Zones goedkeuren' })).toBeTruthy();
    expect(screen.getByText('Versie 0 · superseded')).toBeTruthy();
  });
});
