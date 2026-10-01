import { fireEvent, render } from '@testing-library/react-native';

import type { PlannedWorkout } from '../api/types';
import { WorkoutDetail } from './WorkoutDetail';

const swim: PlannedWorkout = {
  id: 'swim-1', template_id: 'template-1', template_key: 'swim-distance',
  template_version: 1, discipline: 'swim', name: 'Techniekzwemmen',
  description: 'Afstandsgestuurde techniektraining.', duration_minutes: null,
  distance_meters: 1200, intensity_bucket: 'low', expected_rpe_min: 2,
  expected_rpe_max: 3, scheduled_date: '2026-09-21', source: 'auto_planned',
  status: 'scheduled', warnings: [], rpe_zones: [], segments: [{
    sequence: 1, name: 'Techniek', instructions: 'Zwem gecontroleerd met plank.',
    duration_minutes: null, distance_meters: 400, zone_target: 1,
    protocol_target: null, rpe_target: null, expected_rpe: 2,
    is_swim_technique: true,
  }],
};

test('detail shows catalog instructions and retains swim distance without inventing duration', async () => {
  const onClose = jest.fn();
  const screen = await render(<WorkoutDetail workout={swim} onClose={onClose} />);
  expect(screen.getByText('Afstandsgestuurde techniektraining.')).toBeTruthy();
  expect(screen.getByText('Zwem gecontroleerd met plank.')).toBeTruthy();
  expect(screen.getByText(/1200 m · afstandgestuurd/)).toBeTruthy();
  expect(screen.queryByText('0 min')).toBeNull();
  await fireEvent.press(screen.getByRole('button', { name: 'Sluiten' }));
  expect(onClose).toHaveBeenCalledTimes(1);
});
