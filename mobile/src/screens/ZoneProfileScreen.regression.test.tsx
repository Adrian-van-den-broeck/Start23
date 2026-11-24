import * as SecureStore from 'expo-secure-store';
import type { ReactElement } from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react-native';

import {
  approveZoneProposal,
  rejectZoneProposal,
  getOnboarding,
  getZoneProfileState,
  scheduleFieldTest,
} from '../api/client';
import type { DisciplineSetup, OnboardingState, TestAssignment, ZoneProfileSnapshot, ZoneProfileState } from '../api/types';
import { ZoneProfileScreen } from './ZoneProfileScreen';
import { LanguageProvider } from '../i18n/LanguageProvider';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => null), setItemAsync: jest.fn(async () => undefined), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked' }));
const renderWithLanguage = (ui: ReactElement) => render(<LanguageProvider>{ui}</LanguageProvider>);

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

  test('setup route is named instead of printed as its API code', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(profile(['standalone']));
    const screen = await renderWithLanguage(
      <ZoneProfileScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} planContext={null} />,
    );
    expect(await screen.findByText('Route: Veldtest')).toBeTruthy();
    expect(screen.queryByText(/field_test/)).toBeNull();
  });

  test('current server-advertised swim protocol schedules through the API', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(profile(['standalone']));
    const screen = await renderWithLanguage(
      <ZoneProfileScreen
        accessToken="athlete-token"
        onBack={jest.fn()}
        onSignOut={jest.fn(async () => undefined)}
        planContext={null}
      />,
    );

    // The date is picked, not typed: the wheel opens on the earliest date the backend accepts (today).
    const now = new Date();
    const today = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-');
    await fireEvent.press(await screen.findByRole('button', { name: 'Lokale testdatum: nog niet ingesteld' }));
    expect(screen.queryByRole('radio', { name: String(now.getFullYear() - 1) })).toBeNull();
    expect(screen.getByRole('radio', { name: String(now.getFullYear() + 1) })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    expect(screen.queryByLabelText('Lokale testdatum')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Maak voorstel' }));

    await waitFor(() =>
      expect(scheduleFieldTest).toHaveBeenCalledWith('athlete-token', {
        discipline: 'swim',
        protocol_id: 'start23_swim_css_400_200_v1',
        scheduling_mode: 'standalone',
        scheduled_date: today,
      }),
    );
  });

  test('a planned test shows its date, protocol and state in words', async () => {
    const assignment: TestAssignment = {
      id: 'assignment-1', discipline: 'swim', protocol_id: 'start23_swim_css_400_200_v1', scheduling_mode: 'standalone',
      scheduled_date: '2026-11-30', state: 'pending_approval', plan_id: null, target_plan_revision_id: null, plan_proposal_id: null,
      revision: 1, proposal_id: 'proposal-1', proposal_state: 'pending', created_at: '2026-11-24T08:00:00Z',
      updated_at: '2026-11-24T08:00:00Z', decided_at: null,
    };
    const state = profile([]);
    state.disciplines[0]!.test_assignments = [assignment, { ...assignment, id: 'assignment-2', protocol_id: 'future_protocol_v9', state: 'cancelled' }];
    jest.mocked(getZoneProfileState).mockResolvedValue(state);
    const screen = await renderWithLanguage(
      <ZoneProfileScreen accessToken="athlete-token" onBack={jest.fn()} onSignOut={jest.fn(async () => undefined)} planContext={null} />,
    );
    expect(await screen.findByText('CSS 400/200 m-test · Wacht op jouw bevestiging')).toBeTruthy();
    expect(screen.getByText('Testprotocol · Geannuleerd')).toBeTruthy();
    expect(screen.getAllByText('ma 30 november 2026 · losse test')).toHaveLength(2);
    expect(JSON.stringify(screen.toJSON())).not.toMatch(/2026-11-30|pending_approval|start23_swim|future_protocol|cancelled/);
  });

  test('historical setup cannot leak a scheduling action into a new session', async () => {
    jest.mocked(getZoneProfileState).mockResolvedValue(profile([]));
    const screen = await renderWithLanguage(
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
  source_method: 'field_test', source_quality: 'measured_lab', review_status: 'confirmed_by_athlete',
  reviewer_id: null, reviewed_at: null, effective_from: null, zone_model_version: 'start23-zone-model-1.0', evidence_version: 'voorstel-start23-zone-1-5-rekenmodel-v1.0',
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
    const screen = await renderWithLanguage(<ZoneProfileScreen {...props} />);
    await screen.findByText('Nieuw voorstel');
    expect(screen.getByText('Actief profiel')).toBeTruthy();
    expect(screen.getByText('Versie 0 · vervangen')).toBeTruthy();
    expect(screen.getAllByText('172 bpm')).toHaveLength(3);
    expect(screen.getAllByText('177 bpm – open')).toHaveLength(3);
    expect(screen.getAllByText('Model: Zonemodel 1.0')).toHaveLength(3);
    expect(screen.getAllByText('Veldtest · Labmeting · Door jou bevestigd')).toHaveLength(3);
    expect(JSON.stringify(screen.toJSON())).not.toMatch(/field_test|measured_lab|confirmed_by_athlete|start23-zone|superseded/);
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
    const screen = await renderWithLanguage(<ZoneProfileScreen {...props} />);
    await screen.findByText('Nieuw voorstel');
    const publicTree = JSON.stringify(screen.toJSON());
    expect(publicTree).not.toContain('172'); expect(publicTree).not.toContain('177');
    expect(screen.getAllByText(/Numerieke waarden blijven verborgen/)).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Zones goedkeuren' })).toBeTruthy();
    expect(screen.getByText('Versie 0 · vervangen')).toBeTruthy();
  });
});

describe('English zone profile', () => {
  beforeEach(() => { jest.clearAllMocks(); jest.mocked(getOnboarding).mockResolvedValue({} as OnboardingState); });
  const props = { accessToken: 'athlete-token', onBack: jest.fn(), onSignOut: jest.fn(async () => undefined), planContext: null };
  test('setup, scheduling and validation copy follow the English preference', async () => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValueOnce('en');
    jest.mocked(getZoneProfileState).mockResolvedValue(profile(['standalone']));
    const screen = await renderWithLanguage(<ZoneProfileScreen {...props} />);
    expect(await screen.findByText('Route: Field test')).toBeTruthy();
    expect(screen.getByText('Swimming')).toBeTruthy();
    expect(screen.getByText('RPE-guided')).toBeTruthy();
    expect(screen.getByText('Personal profile')).toBeTruthy();
    expect(screen.getByText('My disciplines')).toBeTruthy();
    expect(screen.getByText('Plan linked')).toBeTruthy();
    expect(screen.getByText('Schedule field test')).toBeTruthy();
    expect(screen.getByText(/The CSS test stays standalone/)).toBeTruthy();
    expect(screen.getByRole('radio', { name: 'Standalone test' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Change values or route' })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Create proposal' }));
    expect(await screen.findByText('Choose a test date first.')).toBeTruthy();
    expect(scheduleFieldTest).not.toHaveBeenCalled();
    expect(screen.queryByText('Veldtest plannen')).toBeNull();
  });
  test('active, pending and prior versions are labelled in English', async () => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValueOnce('en');
    jest.mocked(getZoneProfileState).mockResolvedValue(pendingState());
    const screen = await renderWithLanguage(<ZoneProfileScreen {...props} />);
    await screen.findByText('New proposal');
    expect(screen.getByText('Active profile')).toBeTruthy();
    expect(screen.getByText('Previous values')).toBeTruthy();
    expect(screen.getByText('Version 0 · replaced')).toBeTruthy();
    expect(screen.getByText('Zone proposal awaiting confirmation')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Approve zones' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reject' })).toBeTruthy();
  });
});
