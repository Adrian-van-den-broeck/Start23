import { act, fireEvent, render } from '@testing-library/react-native';
import { LanguageProvider, useLanguage } from '../../i18n/LanguageProvider';
import { WorkoutMoveScreen } from './WorkoutMoveScreen';
import { workout } from '../../features/planning/planning.test-fixtures';
import { workoutSummaryViewModel } from '../utils/workoutSummaryViewModel';
let language: ReturnType<typeof useLanguage>;
function Probe() { language = useLanguage(); return null; }
const actions = { onReview: jest.fn(), onConfirm: jest.fn(), onCancel: jest.fn() };
function surface(busy = false, warnings: { title: string; message: string }[] | null = null, available = true) {
  return <LanguageProvider><Probe /><WorkoutMoveScreen {...actions} summary={workoutSummaryViewModel({ ...workout, name: 'Full supplied workout name' })} currentDate="2026-10-07" weekStart="2026-10-05"
    targetDate={warnings ? '2026-10-10' : null} warnings={warnings} busy={busy} error={null} available={available} controls={null} /></LanguageProvider>;
}
beforeEach(() => jest.clearAllMocks());
test('Dutch chooser and English review use explicit localized actions and full dates', async () => {
  const view = await render(surface()); await act(() => language.setPreference('nl'));
  expect(view.getByText('Huidige datum: woensdag 7 oktober 2026')).toBeTruthy();
  await fireEvent.press(view.getByRole('radio', { name: 'zaterdag 10 oktober 2026' }));
  await fireEvent.press(view.getByRole('button', { name: 'Verplaatsing controleren' }));
  expect(actions.onReview).toHaveBeenCalledWith('2026-10-10'); expect(actions.onConfirm).not.toHaveBeenCalled();
  await view.rerender(surface(false, [{ title: 'Supplied title', message: 'Exact supplied public warning' }]));
  await act(() => language.setPreference('en'));
  expect(view.getByText('Exact supplied public warning')).toBeTruthy(); expect(view.getByText('New date: Saturday, 10 October 2026')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Move anyway' })); expect(actions.onConfirm).toHaveBeenCalledTimes(1);
});
test.each([false, true])('busy chooser/review %s suppresses all writes and dismissal with announced busy state', async warned => {
  const view = await render(surface(true, warned ? [{ title: 'Warning', message: 'Supplied warning' }] : null));
  await act(() => language.setPreference('en'));
  for (const button of view.getAllByRole('button')) expect(button).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: warned ? 'Move anyway' : 'Review move' }));
  for (const cancel of view.getAllByRole('button', { name: 'Cancel' })) await fireEvent.press(cancel);
  expect(actions.onReview).not.toHaveBeenCalled(); expect(actions.onConfirm).not.toHaveBeenCalled(); expect(actions.onCancel).not.toHaveBeenCalled();
  expect(view.getByText('Checking or applying the move...').props.accessibilityState).toEqual({ busy: true });
});
test('changed context retains warnings and Cancel but disables confirmation', async () => {
  const view = await render(surface(false, [{ title: 'Warning', message: 'Exact reviewed warning' }], false));
  await act(() => language.setPreference('en'));
  expect(view.getByRole('button', { name: 'Move anyway' })).toBeDisabled();
  await fireEvent.press(view.getAllByRole('button', { name: 'Cancel' })[0]); expect(actions.onCancel).toHaveBeenCalledTimes(1);
  expect(actions.onConfirm).not.toHaveBeenCalled();
});

test('date choices remain local, include exactly the origin week, and returning to origin restores the no-op lock', async () => {
  const view = await render(surface()); await act(() => language.setPreference('en'));
  expect(view.getAllByRole('radio')).toHaveLength(7);
  expect(view.getByRole('radio', { name: 'Monday, 5 October 2026' })).toBeTruthy();
  expect(view.getByRole('radio', { name: 'Sunday, 11 October 2026' })).toBeTruthy();
  await fireEvent.press(view.getByRole('radio', { name: 'Saturday, 10 October 2026' }));
  expect(view.getByRole('radio', { name: 'Saturday, 10 October 2026' })).toBeChecked();
  expect(actions.onReview).not.toHaveBeenCalled(); expect(actions.onConfirm).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('radio', { name: 'Wednesday, 7 October 2026 · Current date' }));
  expect(view.getByRole('button', { name: 'Review move' })).toBeDisabled();
  await fireEvent.press(view.getAllByRole('button', { name: 'Cancel' })[1]);
  expect(actions.onCancel).toHaveBeenCalledTimes(1); expect(actions.onReview).not.toHaveBeenCalled();
});

test('warning review retains complete source summary and every supplied warning without choosing or confirming', async () => {
  const view = await render(surface(false, [
    { title: 'First supplied title', message: 'First exact warning' },
    { title: 'Second supplied title', message: 'Second exact warning' },
  ]));
  await act(() => language.setPreference('en'));
  expect(view.getByText('Full supplied workout name')).toBeTruthy();
  expect(view.getByText('30.5 min')).toBeTruthy(); expect(view.getByText('1200 m')).toBeTruthy();
  expect(view.getByText('Current date: Wednesday, 7 October 2026')).toBeTruthy();
  expect(view.getByText('New date: Saturday, 10 October 2026')).toBeTruthy();
  expect(view.getByText('First exact warning')).toBeTruthy(); expect(view.getByText('Second exact warning')).toBeTruthy();
  expect(view.queryAllByRole('radio')).toHaveLength(0);
  expect(actions.onReview).not.toHaveBeenCalled(); expect(actions.onConfirm).not.toHaveBeenCalled();
});
