import { fireEvent, render, within } from '@testing-library/react-native';
import * as Native from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { visibleCalendarDates, calendarRangeFor } from '../../features/calendar/calendarDates';
import { workout } from '../../features/planning/planning.test-fixtures';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { calendarViewModel } from '../utils/calendarViewModel';
import { CalendarScreen } from './CalendarScreen';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
const callbacks = { onModeChange: jest.fn(), onMove: jest.fn(), onToday: jest.fn(), onSelectDate: jest.fn(), onRetry: jest.fn(), onOpenWorkout: jest.fn(), onBack: jest.fn() };
const makeModel = (mode: 'week' | 'month', selectedDate = '2026-10-07', known = true) => {
  const dates = visibleCalendarDates('2026-10-07', mode);
  return calendarViewModel({
    dates, anchor: '2026-10-07', selectedDate, today: '2026-10-05',
    workouts: [workout, { ...workout, id: 'second', name: 'Exact second occurrence', status: 'completed' }],
    restDays: [{ date: workout.scheduled_date, reason: 'restriction_rest' }], loadedRange: known ? calendarRangeFor(dates) : null
  });
};
function screen(mode: 'week' | 'month', model = makeModel(mode), error: string | null = null, loading = false) {
  return <LanguageProvider><CalendarScreen {...callbacks} mode={mode} anchor="2026-10-07" model={model} loading={loading} error={error} /></LanguageProvider>;
}
const originalDimensions = Native.Dimensions.get('window');
const dimensions = (width: number, fontScale: number) => Native.Dimensions.set({ window: { width, height: 800, scale: 1, fontScale } });
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); dimensions(412, 1); });
afterEach(() => { jest.restoreAllMocks(); Native.Dimensions.set({ window: originalDimensions }); });

test.each(['en', 'nl'] as const)('Week renders seven complete date sections, source fields, independent occurrences and rest in %s', async (language) => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  const view = await render(screen('week'));
  for (const date of visibleCalendarDates('2026-10-07', 'week')) expect(view.getByTestId(`calendar-day-${date}`)).toBeTruthy();
  const day = within(view.getByTestId('calendar-day-2026-10-07'));
  expect(day.getByText(workout.name)).toBeTruthy(); expect(day.getByText('Exact second occurrence')).toBeTruthy();
  expect(day.getAllByText('30.5 min')).toHaveLength(2); expect(day.getAllByText('1200 m')).toHaveLength(2);
  expect(day.getByText(language === 'en' ? 'Rest day' : 'Rustdag')).toBeTruthy();
  expect(day.getByText(language === 'en' ? 'Rest due to a confirmed restriction.' : 'Rust vanwege een bevestigde beperking.')).toBeTruthy();
  const buttons = day.getAllByRole('button'); for (const button of buttons) await fireEvent.press(button);
  expect(callbacks.onOpenWorkout.mock.calls).toEqual([[workout.id], ['second']]);
  expect(within(view.getByTestId('calendar-day-2026-10-11')).getByText(language === 'en' ? 'No workout planned.' : 'Geen training gepland.')).toBeTruthy();
});
test.each(['2026-10-06', '2026-10-07'])('Month selected date %s keeps empty/populated readable details below orientation grid', async (date) => {
  dimensions(412, 1);
  const view = await render(screen('month', makeModel('month', date)));
  const selected = within(view.getByTestId('calendar-selected-day'));
  expect(view.getByTestId('calendar-month-grid')).toBeTruthy();
  expect(within(view.getByTestId('calendar-month-grid')).queryByText(workout.name)).toBeNull();
  if (date === '2026-10-06') expect(selected.getByText('No workout planned.')).toBeTruthy();
  else expect(selected.getByText(workout.name)).toBeTruthy();
  expect(view.getByTestId(`calendar-date-${date}`).props.accessibilityState.selected).toBe(true);
  expect(view.getByTestId('calendar-date-2026-10-05').props.accessibilityLabel).toContain('Today');
  expect(view.getByTestId('calendar-date-2026-10-07').props.accessibilityLabel).toContain('2 workouts');
  expect(view.getByTestId('calendar-date-2026-09-28')).toBeTruthy();
  await fireEvent.press(selected.getByRole('button', { name: 'View this date’s week' }));
  expect(callbacks.onModeChange).toHaveBeenCalledWith('week');
});
test.each([[320, 1], [360, 1], [320, 2], [360, 2], [393, 2], [412, 2]])('Month uses nonoverlapping natural-height >=48 date targets at width %s/font %s', async (width, fontScale) => {
  dimensions(width, fontScale);
  const view = await render(screen('month'));
  const list = within(view.getByTestId('calendar-month-day-list'));
  expect(view.queryByTestId('calendar-month-grid')).toBeNull(); expect(list.getAllByRole('button')).toHaveLength(35);
  const date = view.getByTestId('calendar-date-2026-11-01');
  expect(Native.StyleSheet.flatten(date.props.style)).toMatchObject({ minWidth: 48, minHeight: 48, width: '100%' });
  expect(date.props.accessibilityLabel).toContain('Sunday, 1 November 2026');
  await fireEvent.press(date); expect(callbacks.onSelectDate).toHaveBeenCalledWith('2026-11-01');
});
test('initial loading and failed range never masquerade as a successfully empty week, and retry is explicit', async () => {
  const model = makeModel('week', '2026-10-07', false);
  const view = await render(screen('week', model, null, true));
  expect(view.getByText('Loading…')).toBeTruthy(); expect(view.queryByText('No workout planned.')).toBeNull();
  await view.rerender(screen('week', model, 'Safe range error'));
  expect(view.getByText('This period could not be loaded.')).toBeTruthy(); expect(view.getByText('Safe range error')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Reload period' })); expect(callbacks.onRetry).toHaveBeenCalledTimes(1);
  expect(view.queryByText('No workout planned.')).toBeNull();
});
test('failed new range keeps labelled last-known records and exact detail callback without attaching them to requested dates', async () => {
  const dates = visibleCalendarDates('2026-11-07', 'week');
  const model = calendarViewModel({
    dates, anchor: '2026-11-07', selectedDate: '2026-11-07', today: '2026-10-05', workouts: [workout], restDays: [],
    loadedRange: { fromDate: '2026-10-05', toDate: '2026-10-12' }
  });
  const view = await render(screen('week', model, 'Safe range error'));
  const retained = within(view.getByTestId('calendar-retained-range'));
  expect(retained.getByText(workout.name)).toBeTruthy();
  expect(retained.getByText(/Last loaded period:/)).toBeTruthy();
  expect(within(view.getByTestId('calendar-day-2026-11-07')).queryByText(workout.name)).toBeNull();
  await fireEvent.press(retained.getByRole('button', { name: 'View workout · ' + workout.name })); expect(callbacks.onOpenWorkout).toHaveBeenCalledWith(workout.id);
});
test('toolbar retains exclusive Week/Month semantics and every read-only navigation callback', async () => {
  const view = await render(screen('week'));
  expect(view.getByRole('tab', { name: 'Week' }).props.accessibilityState.selected).toBe(true);
  expect(view.getByRole('tab', { name: 'Month' }).props.accessibilityState.selected).toBe(false);
  await fireEvent.press(view.getByRole('tab', { name: 'Month' }));
  await fireEvent.press(view.getByRole('button', { name: 'Previous week' })); await fireEvent.press(view.getByRole('button', { name: 'Next week' }));
  await fireEvent.press(view.getByRole('button', { name: 'Today' })); await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(callbacks.onModeChange).toHaveBeenCalledWith('month'); expect(callbacks.onMove.mock.calls).toEqual([[-1], [1]]);
  expect(callbacks.onToday).toHaveBeenCalledTimes(1); expect(callbacks.onBack).toHaveBeenCalledTimes(1);
});


test('a returned rest-only date is prescribed rest and never displayed as an empty date', async () => {
  const model = calendarViewModel({ dates: visibleCalendarDates('2026-10-07', 'week'), anchor: '2026-10-07', selectedDate: '2026-10-06', today: '2026-10-05', workouts: [], restDays: [{ date: '2026-10-06', reason: 'planned_rest' }], loadedRange: { fromDate: '2026-10-05', toDate: '2026-10-12' } });
  const view = await render(screen('week', model));
  const day = within(view.getByTestId('calendar-day-2026-10-06'));
  expect(day.getByText('Rest day')).toBeTruthy();
  expect(day.queryByText('No workout planned.')).toBeNull();
  expect(day.queryAllByRole('button')).toHaveLength(0);
});

// Accepted summary anatomy supplies the same literal distance as the detail card.
test.each([393, 412])('Month keeps >=48 grid targets at default text/%sdp, with explicit count/rest meaning and distinct today/selected fills', async width => {
  dimensions(width, 1);
  const view = await render(screen('month'));
  expect(view.getByTestId('calendar-month-grid')).toBeTruthy();
  expect(view.getByText('Number = workout count')).toBeTruthy();
  const selected = view.getByTestId('calendar-date-2026-10-07');
  const today = view.getByTestId('calendar-date-2026-10-05');
  expect(Native.StyleSheet.flatten(selected.props.style)).toMatchObject({ minWidth: 48, minHeight: 64, backgroundColor: '#E7EFE8', borderColor: '#124D43' });
  expect(Native.StyleSheet.flatten(today.props.style)).toMatchObject({ backgroundColor: '#F8EED6' });
  expect(selected.props.accessibilityLabel).toContain('Rest day');
  expect(today.props.accessibilityState.selected).toBe(false);
});

test('each sibling retains independent detail and permitted move entry; unsupported siblings have no move action', async () => {
  const move = jest.fn();
  const view = await render(<LanguageProvider><CalendarScreen {...callbacks} mode="week" anchor="2026-10-07" model={makeModel('week')} loading={false} error={null}
    onMoveWorkout={id => id === workout.id ? move : undefined} /></LanguageProvider>);
  const first = within(view.getByTestId(`calendar-workout-${workout.id}`));
  const second = within(view.getByTestId('calendar-workout-second'));
  await fireEvent.press(first.getByRole('button', { name: 'Move ' + workout.name }));
  expect(move).toHaveBeenCalledTimes(1);
  expect(second.queryByRole('button', { name: /Move / })).toBeNull();
  await fireEvent.press(second.getByRole('button', { name: 'View workout \u00b7 Exact second occurrence' }));
  expect(callbacks.onOpenWorkout).toHaveBeenCalledWith('second');
});
