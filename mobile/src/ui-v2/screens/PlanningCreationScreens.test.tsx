import { fireEvent, render, within } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { ReactNode } from 'react';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { draft, occurrence } from '../../features/planning/planning.test-fixtures';
import { planningCreationViewModel } from '../utils/planningCreationViewModel';
import { AvailabilityScreen, SelectionScreen, PlacementScreen } from './PlanningCreationScreens';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en') }));
const task = { busy: false, error: null, onBack: jest.fn(), controls: null };
function host(children: ReactNode) {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 320, height: 640 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider>{children}</LanguageProvider></SafeAreaProvider>;
}
const availability = {
  ...task, weekStart: draft.week_start, selectedDays: new Set([0, 2, 5]), reusePreviousWeek: false,
  injuries: new Set<'run'>(['run']), crossTrainingOptIns: new Set<'bike'>(['bike']),
  onWeekStart: jest.fn(), onToggleDay: jest.fn(), onReuse: jest.fn(), onInjury: jest.fn(),
  onCrossTraining: jest.fn(), onCreate: jest.fn(async () => undefined),
};
beforeEach(() => jest.clearAllMocks());

test('availability shows Monday through Sunday with checked defaults, reuse, injury and opt-ins', async () => {
  const view = await render(host(<AvailabilityScreen {...availability} />));
  await view.findByText('When can you train?');
  expect(view.getByRole('checkbox', { name: 'Monday · 5 October' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Sunday · 11 October' })).not.toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Confirmed injury · Running' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Optional alternative training · Cycling' })).toBeChecked();
  expect(view.queryByRole('checkbox', { name: 'Optional alternative training · Running' })).toBeNull();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Tuesday · 6 October' }));
  expect(availability.onToggleDay).toHaveBeenCalledWith(1);
  await fireEvent.press(view.getByRole('checkbox', { name: 'Use the same available days as last week' }));
  expect(availability.onReuse).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('checkbox', { name: 'Confirmed injury · Running' }));
  expect(availability.onInjury).toHaveBeenCalledWith('run');
  await fireEvent.press(view.getByRole('checkbox', { name: 'Optional alternative training · Swimming' }));
  expect(availability.onCrossTraining).toHaveBeenCalledWith('swim');
});
test('empty dates disable create; explicit reuse permits create with no locally guessed days', async () => {
  const view = await render(host(<AvailabilityScreen {...availability} selectedDays={new Set()} />));
  await view.findByText('When can you train?');
  expect(view.getByRole('button', { name: 'Start choosing workouts' })).toBeDisabled();
  await view.rerender(host(<AvailabilityScreen {...availability} selectedDays={new Set()} reusePreviousWeek />));
  await fireEvent.press(view.getByRole('button', { name: 'Start choosing workouts' }));
  expect(availability.onCreate).toHaveBeenCalledTimes(1);
});
test('incomplete date typing retains weekday choices, uses existing parser, and invents no date repair', async () => {
  const view = await render(host(<AvailabilityScreen {...availability} weekStart="2026-10" />));
  await view.findByText('When can you train?');
  expect(view.getByRole('checkbox', { name: 'Monday' })).toBeChecked();
  await fireEvent.changeText(view.getByLabelText('Week starts on Monday'), '20261012');
  expect(availability.onWeekStart).toHaveBeenCalledWith('2026-10-12');
});
test('busy availability announces saving and disables all inputs and back', async () => {
  const view = await render(host(<AvailabilityScreen {...availability} busy />));
  await view.findByText('Saving action…');
  for (const control of view.getAllByRole('checkbox')) expect(control).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Week' })).toBeDisabled();
  expect(view.getByLabelText('Week starts on Monday').props.editable).toBe(false);
});
test.each([['Choose', 'accept'], ['Pass', 'pass'], ['Undo', 'undo'], ['Reset passed workouts', 'reset_passed']] as const)(
  '%s uses the authoritative transition callback', async (label, action) => {
    const transition = jest.fn();
    const view = await render(host(<SelectionScreen {...task} model={planningCreationViewModel({ ...draft, can_undo: true, passed_count: 1 })}
      onTransition={transition} onContinue={jest.fn()} />));
    await view.findByText('Choose your workouts');
    await fireEvent.press(view.getByRole('button', { name: action === 'accept' || action === 'pass' ? `${label} · ${occurrence.name}` : label }));
    expect(transition).toHaveBeenCalledWith(action);
  });
test('accepted list displays repeated occurrences in source order with supplied duration and distance', async () => {
  const repeat = { ...occurrence, occurrence_id: 'repeat', distance_meters: 2500 };
  const view = await render(host(<SelectionScreen {...task}
    model={planningCreationViewModel({ ...draft, current_candidate: null, accepted_workouts: [repeat, occurrence] })}
    onTransition={jest.fn()} onContinue={jest.fn()} />));
  await view.findByText('Choose your workouts');
  const list = within(view.getByTestId('accepted-occurrences'));
  expect(list.getAllByText(occurrence.name)).toHaveLength(2);
  expect(list.getByTestId('selection-occurrence-repeat')).toBeTruthy();
  expect(list.getByTestId('selection-occurrence-' + occurrence.occurrence_id)).toBeTruthy();
  expect(list.getByText('2500 m')).toBeTruthy();
});
test('server exhaustion has undo/reset, no choose/pass, and cannot continue even with accepted cards', async () => {
  const view = await render(host(<SelectionScreen {...task} model={planningCreationViewModel({
    ...draft,
    exhausted: true, current_candidate: null, accepted_workouts: [occurrence], passed_count: 1, can_undo: true
  })}
    onTransition={jest.fn()} onContinue={jest.fn()} />));
  await view.findByText('No new eligible cards. Reset passed workouts or undo your last choice.');
  expect(view.queryByRole('button', { name: `Choose · ${occurrence.name}` })).toBeNull();
  expect(view.getByRole('button', { name: 'Continue to placement' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Undo' })).toBeEnabled();
  expect(view.getByRole('button', { name: 'Reset passed workouts' })).toBeEnabled();
});
test('safe stale message retains candidate with busy locks and no implicit action/recreation', async () => {
  const transition = jest.fn();
  const view = await render(host(<SelectionScreen {...task} busy error="Refresh required"
    model={planningCreationViewModel(draft)} onTransition={transition} onContinue={jest.fn()} />));
  await view.findByText('Refresh required');
  expect(view.getByRole('button', { name: `Choose · ${occurrence.name}` })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: `Pass · ${occurrence.name}` }));
  expect(transition).not.toHaveBeenCalled();
  expect(view.getByTestId('selection-occurrence-' + occurrence.occurrence_id)).toBeTruthy();
});
const placed = {
  ...draft, state: 'placement' as const, current_candidate: null,
  accepted_workouts: [occurrence, { ...occurrence, occurrence_id: 'repeat' }]
};
const placementActions = { onMode: jest.fn(), onPlace: jest.fn(), onSubmit: jest.fn(), onSelection: jest.fn() };
test('automatic placement submits through the existing action without local scheduling', async () => {
  const view = await render(host(<PlacementScreen {...task} {...placementActions} model={planningCreationViewModel(placed)} mode="automatic" />));
  await view.findByText('Place your workouts');
  expect(view.getByRole('radio', { name: 'Automatic placement' })).toBeChecked();
  await fireEvent.press(view.getByRole('button', { name: 'Place automatically and submit proposal' }));
  expect(placementActions.onSubmit).toHaveBeenCalledWith('automatic');
  expect(placementActions.onPlace).not.toHaveBeenCalled();
});
test.each([['2026-10-05'], ['2026-10-05', '2026-10-07']])('manual choices use only allowed dates %j and exact occurrence callbacks', async (...dates: string[]) => {
  const view = await render(host(<PlacementScreen {...task} {...placementActions}
    model={planningCreationViewModel({ ...placed, available_dates: dates })} mode="manual" />));
  await view.findByText('Place your workouts');
  const repeat = within(view.getByTestId('selection-occurrence-repeat').parent!);
  const controls = repeat.getAllByRole('radio');
  expect(controls).toHaveLength(dates.length);
  await fireEvent.press(controls[0]);
  expect(placementActions.onPlace).toHaveBeenCalledWith('repeat', dates[0]);
  expect(view.getByRole('button', { name: 'Submit manual placement as proposal' })).toBeDisabled();
});
test('multiple occurrences on one date stay independently checked and manual completion enables pending submit', async () => {
  const model = planningCreationViewModel({
    ...placed, available_dates: ['2026-10-05'],
    placements: placed.accepted_workouts.map((workout) => ({ occurrence_id: workout.occurrence_id, scheduled_date: '2026-10-05' }))
  });
  const view = await render(host(<PlacementScreen {...task} {...placementActions} model={model} mode="manual" />));
  await view.findByText('Place your workouts');
  const dateChoices = [1, 2].map((number) => view.getByRole('radio', { name: `Choice ${number} · ${occurrence.name} · Monday, 5 October 2026` }));
  expect(dateChoices).toHaveLength(2);
  for (const choice of dateChoices) expect(choice).toBeChecked();
  await fireEvent.press(view.getByRole('button', { name: 'Submit manual placement as proposal' }));
  expect(placementActions.onSubmit).toHaveBeenCalledWith('manual');
});
test('busy placement locks date, mode, submit and navigation actions while keeping errors visible', async () => {
  const view = await render(host(<PlacementScreen {...task} {...placementActions} busy error="Choose another date"
    model={planningCreationViewModel(placed)} mode="manual" />));
  await view.findByText('Choose another date');
  for (const radio of view.getAllByRole('radio')) expect(radio).toBeDisabled();
  for (const button of view.getAllByRole('button')) expect(button).toBeDisabled();
});

test('placement mode changes and return to selection are explicit callbacks with no submit', async () => {
  const view = await render(host(<PlacementScreen {...task} {...placementActions}
    model={planningCreationViewModel(placed)} mode="manual" />));
  await fireEvent.press(view.getByRole('radio', { name: 'Automatic placement' }));
  expect(placementActions.onMode).toHaveBeenCalledWith('automatic');
  await fireEvent.press(view.getByRole('button', { name: 'Inspect workout choices' }));
  expect(placementActions.onSelection).toHaveBeenCalledTimes(1);
  expect(placementActions.onSubmit).not.toHaveBeenCalled();
});

test('incomplete placement retains the exact chosen occurrence and readable submit reason', async () => {
  const view = await render(host(<PlacementScreen {...task} {...placementActions} mode="manual"
    model={planningCreationViewModel({ ...placed, placements: [{ occurrence_id: occurrence.occurrence_id, scheduled_date: '2026-10-05' }] })} />));
  expect(view.getByRole('radio', { name: `Choice 1 · ${occurrence.name} · Monday, 5 October 2026` })).toBeChecked();
  expect(view.getByRole('radio', { name: `Choice 2 · ${occurrence.name} · Monday, 5 October 2026` })).not.toBeChecked();
  expect(view.getByText('Choose a date for every workout.')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Submit manual placement as proposal' }));
  expect(placementActions.onSubmit).not.toHaveBeenCalled();
});

// Final Batch 6 preserves mechanical inputs and source occurrence data.
test('one selected day creates once without a locally inferred frequency', async () => {
  const view = await render(host(<AvailabilityScreen {...availability} selectedDays={new Set([2])} />));
  await view.findByText('When can you train?');
  await fireEvent.press(view.getByRole('button', { name: 'Start choosing workouts' }));
  expect(availability.onCreate).toHaveBeenCalledTimes(1);
});
test('distance-only candidate omits invented time and default RPE description', async () => {
  const view = await render(host(<SelectionScreen {...task} model={planningCreationViewModel({ ...draft,
    current_candidate: { ...occurrence, duration_minutes: null, distance_meters: 2500, description: 'RPE 2-3' }
  })} onTransition={jest.fn()} onContinue={jest.fn()} />));
  await view.findByText('Choose your workouts');
  const candidate = within(view.getByTestId('selection-candidate'));
  expect(candidate.getByText('2500 m')).toBeTruthy();
  expect(candidate.queryByText(/ min$/)).toBeNull();
  expect(candidate.queryByText('RPE 2-3')).toBeNull();
});
test('loading with no candidate keeps source unavailability and all busy locks', async () => {
  const view = await render(host(<SelectionScreen {...task} busy model={planningCreationViewModel({ ...draft, current_candidate: null })}
    onTransition={jest.fn()} onContinue={jest.fn()} />));
  await view.findByText('Saving action\u2026');
  expect(view.getByTestId('selection-empty')).toBeTruthy();
  expect(view.queryByTestId('selection-candidate')).toBeNull();
  for (const button of view.getAllByRole('button')) expect(button).toBeDisabled();
});
test('placement-ready selection continues only through the existing callback', async () => {
  const onContinue = jest.fn();
  const view = await render(host(<SelectionScreen {...task} model={planningCreationViewModel(placed)} onTransition={jest.fn()} onContinue={onContinue} />));
  await view.findByText('Choose your workouts');
  await fireEvent.press(view.getByRole('button', { name: 'Continue to placement' }));
  expect(onContinue).toHaveBeenCalledTimes(1);
});
