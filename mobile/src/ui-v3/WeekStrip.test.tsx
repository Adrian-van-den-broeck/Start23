import { fireEvent, render, within } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { activePlan, workout } from '../features/planning/planning.test-fixtures';
import { weekHomeViewModel } from '../ui-v2/utils/weekHomeViewModel';
import { WeekStrip } from './WeekStrip';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
beforeEach(() => { jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });

const plan = {
  ...activePlan,
  workouts: [
    { ...workout, id: 'done', scheduled_date: '2026-10-05', status: 'completed' as const },
    workout,
    { ...workout, id: 'bike', discipline: 'bike' as const, scheduled_date: '2026-10-09' },
    { ...workout, id: 'dropped', scheduled_date: '2026-10-11', status: 'cancelled' as const },
  ],
  rest_days: [{ date: '2026-10-10', reason: 'planned_rest' as const }],
};
const model = weekHomeViewModel({ plan, activePlan: plan, draft: null, today: '2026-10-06', resumeState: 'ready', activeReadState: 'ready' });

test('day summaries cover the active Monday-Sunday with literal counts and no cancelled rows', () => {
  expect(model.days.map((day) => day.date)).toEqual(['2026-10-05', '2026-10-06', '2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10', '2026-10-11']);
  expect(model.days[0]).toMatchObject({ planned: 1, completed: 1, disciplines: [workout.discipline] });
  expect(model.days[1]).toMatchObject({ today: true, next: false, planned: 0 });
  expect(model.days[2]).toMatchObject({ next: true, planned: 1, completed: 0 });
  expect(model.days[5]).toMatchObject({ rest: true, planned: 0 });
  expect(model.days[6]).toMatchObject({ planned: 0, disciplines: [] });
});

test('pending-only and no-plan states have no strip days', () => {
  expect(weekHomeViewModel({ plan: null, activePlan: null, draft: null, today: '2026-10-06', resumeState: 'ready', activeReadState: 'ready' }).days).toEqual([]);
});

test('one named target opens the calendar, carries progress as its hint and respects busy', async () => {
  const onOpen = jest.fn();
  const strip = (disabled: boolean) => <LanguageProvider><WeekStrip days={model.days} progress={model.progress!} disabled={disabled} onOpen={onOpen} /></LanguageProvider>;
  const view = await render(strip(false));
  const button = await view.findByRole('button', { name: 'View week' });
  expect(button.props.accessibilityHint).toBe('1 of 3 planned workouts completed');
  expect(view.getAllByRole('button')).toHaveLength(1);
  expect(within(view.getByTestId('week-strip')).queryByText('1/3 done', { includeHiddenElements: true })).toBeTruthy();
  await fireEvent.press(button);
  expect(onOpen).toHaveBeenCalledTimes(1);
  await view.rerender(strip(true));
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  expect(onOpen).toHaveBeenCalledTimes(1);
});
