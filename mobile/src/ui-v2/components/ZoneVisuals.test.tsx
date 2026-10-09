import { render } from '@testing-library/react-native';
import type { ZoneMetricKind, ZoneProfileSnapshot } from '../../api/types';
import { ZoneProfileValues } from './ZoneVisuals';

function snapshot(kind: ZoneMetricKind): ZoneProfileSnapshot {
  return {
    id: 'profile-original', discipline: kind.startsWith('run') ? 'run' : kind.startsWith('bike') ? 'bike' : 'swim',
    version: 7, status: 'active', setup_method: 'calculated', source_method: 'original-source', source_quality: 'measured_lab',
    review_status: 'pending_review', reviewer_id: null, reviewed_at: null, effective_from: null,
    zone_model_version: 'original-model', evidence_version: 'original-evidence', created_at: '2026-09-01T12:00:00Z',
    values_hidden: false, metric: { metric_kind: kind, value: '300' },
    metric_profiles: [{ metric_kind: kind, source_value: '300', is_primary: true, boundary_source: 'athlete_entered',
      zone_model_version: 'start23-zone-model-1.0', boundaries: [{ zone_number: 1, lower_value: null, upper_value: '300' }] }],
    boundaries: [{ zone_number: 5, lower_value: '300', upper_value: null }], proposal_id: null, base_zone_profile_id: null,
  };
}

test.each(['active', 'pending', 'superseded'] as const)('values_hidden blocks every numeric subtree for %s, including accessibility', async status => {
  const profile = snapshot('run_lthr_bpm');
  profile.status = status;
  profile.values_hidden = true;
  profile.metric = { metric_kind: 'run_lthr_bpm', value: '991731' };
  profile.metric_profiles[0].source_value = '991732';
  profile.metric_profiles[0].boundaries = [{ zone_number: 4, lower_value: '991733', upper_value: '991734' }];
  profile.boundaries = [{ zone_number: 5, lower_value: '991735', upper_value: '991736' }];
  const screen = await render(<ZoneProfileValues profile={profile} />);
  expect(screen.getByText(/Numerieke waarden blijven verborgen/)).toBeTruthy();
  const rendered = JSON.stringify(screen.toJSON());
  for (const secret of ['991731', '991732', '991733', '991734', '991735', '991736']) expect(rendered).not.toContain(secret);
  expect(rendered).not.toContain('Z4');
  expect(rendered).not.toContain('Z5');
  expect(screen.getByText(/original-source/)).toBeTruthy();
  expect(screen.getByText('Model: original-model')).toBeTruthy();
  expect(screen.getByText('Bewijs: original-evidence')).toBeTruthy();
});

test.each([
  ['run_threshold_pace_seconds_per_km', '5:00 /km'], ['run_lthr_bpm', '300 bpm'],
  ['bike_ftp_watts', '300 watt'], ['bike_threshold_heart_rate_bpm', '300 bpm'],
  ['swim_css_seconds_per_100m', '300 sec/100 m'],
] as const)('preserves original %s units and open bounds', async (kind, value) => {
  const screen = await render(<ZoneProfileValues profile={snapshot(kind)} />);
  expect(screen.getAllByText(value)).toHaveLength(2);
  expect(screen.getByText('open – ' + value)).toBeTruthy();
  expect(screen.getByText('athlete_entered · start23-zone-model-1.0')).toBeTruthy();
});

test('a numeric-free profile never invents a threshold or zone table', async () => {
  const profile = snapshot('swim_css_seconds_per_100m');
  profile.metric = null; profile.metric_profiles = []; profile.boundaries = [];
  const screen = await render(<ZoneProfileValues profile={profile} />);
  expect(screen.queryByText(/300|Z1|Z5/)).toBeNull();
  expect(screen.getByText(/original-source/)).toBeTruthy();
});
