import { fireEvent, render } from '@testing-library/react-native';

import type { PlannedWorkout } from '../api/types';
import { LanguageProvider } from '../i18n/LanguageProvider';
import {
  isDateInWeek,
  resolveWeekDragDate,
  WeekSchedule,
} from './WeekSchedule';

const workout: PlannedWorkout = {
  id: 'workout-1',
  template_id: 'template-1',
  template_key: 'easy-run',
  template_version: 1,
  discipline: 'run',
  name: 'Rustige duurloop',
  description: 'Rustig lopen.',
  duration_minutes: '45',
  distance_meters: null,
  intensity_bucket: 'low',
  expected_rpe_min: 2,
  expected_rpe_max: 3,
  segments: [],
  rpe_zones: [],
  scheduled_date: '2026-09-21',
  source: 'auto_planned',
  status: 'scheduled',
  warnings: [],
};

describe('WeekSchedule', () => {
  test('same-week drag resolution changes only the date and clamps to Sunday', () => {
    expect(resolveWeekDragDate('2026-09-21', '2026-09-21', 116 * 2)).toBe(
      '2026-09-23',
    );
    expect(resolveWeekDragDate('2026-09-21', '2026-09-21', 116 * 20)).toBe(
      '2026-09-27',
    );
  });

  test('cross-week dates are rejected', () => {
    expect(isDateInWeek('2026-09-27', '2026-09-21')).toBe(true);
    expect(isDateInWeek('2026-09-28', '2026-09-21')).toBe(false);
    expect(() =>
      resolveWeekDragDate('2026-09-21', '2026-09-28', -116),
    ).toThrow('outside the active week');
  });

  test('accessible non-drag date selection requests the same server move', async () => {
    const onMove = jest.fn();
    const screen = await render(
      <LanguageProvider>
        <WeekSchedule
          busy={false}
          onMove={onMove}
          weekStart="2026-09-21"
          workouts={[workout]}
        />
      </LanguageProvider>,
    );

    await fireEvent.press(
      screen.getByRole('button', { name: 'Andere datum kiezen' }),
    );
    await fireEvent.press(
      screen.getByRole('button', {
        name: /Verplaats Rustige duurloop naar Wed/,
      }),
    );

    expect(onMove).toHaveBeenCalledWith(workout, '2026-09-23');
  });
});
