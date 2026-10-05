import { act, fireEvent, render } from '@testing-library/react-native';
import { LanguageProvider, useLanguage } from '../../i18n/LanguageProvider';
import { WorkoutMoveScreen } from './WorkoutMoveScreen';
let language: ReturnType<typeof useLanguage>;
function Probe() { language = useLanguage(); return null; }
const actions = { onReview: jest.fn(), onConfirm: jest.fn(), onCancel: jest.fn() };
function surface(busy = false, warnings: { title: string; message: string }[] | null = null, available = true) {
  return <LanguageProvider><Probe /><WorkoutMoveScreen {...actions} name="Full supplied workout name" currentDate="2026-10-07" weekStart="2026-10-05"
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
