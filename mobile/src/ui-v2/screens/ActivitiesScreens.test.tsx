import { act, fireEvent, render, within } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { completeActivity, pendingActivity } from '../../features/activities/activities.test-fixtures';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { rpeChoices } from '../../lib/rpe';
import { activityViewModel } from '../utils/activityViewModel';
import { ActivitiesScreen, type ActivityRow } from './ActivitiesScreen';
import { ActivityEntryScreen } from './ActivityEntryScreen';
import { ActivityFeedbackScreen } from './ActivityFeedbackScreen';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en') }));
function host(child: ReactNode) { return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 320, height: 640 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}><LanguageProvider>{child}</LanguageProvider></SafeAreaProvider>; }
const complete = activityViewModel(completeActivity, 'en-GB', 'en');
const pending = activityViewModel(pendingActivity, 'en-GB', 'en');
const base = { busy: false, error: null, controls: null, onBack: jest.fn(), onProfile: jest.fn(), onAdd: jest.fn(), onFeedback: jest.fn(), onCorrect: jest.fn(), onMatch: jest.fn(async () => undefined) };
const row: ActivityRow = { activity: complete, canCorrect: true, match: null };
const entry = { discipline: 'run' as const, duration: '45', distance: '', startedAt: '2026-10-06T10:00:00Z', timezone: 'Europe/Amsterdam', choices: [], selectedId: null, selectedName: null, busy: false, error: null, blocked: false, controls: null, onDiscipline: jest.fn(), onDuration: jest.fn(), onDistance: jest.fn(), onStartedAt: jest.fn(), onChoose: jest.fn(), onSave: jest.fn(async () => undefined), onBack: jest.fn() };
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });

test('truthful empty history, heading and add action without analytics', async () => {
  const view = await render(host(<ActivitiesScreen {...base} rows={[]} pending={null} />));
  await view.findByRole('header', { name: 'Activities' }); expect(view.getByText('No activities recorded yet.')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' })); expect(base.onAdd).toHaveBeenCalledTimes(1);
});
test.each([{ busy: true, error: null }, { busy: false, error: 'Safe read failure' }])('loading/error never claims empty success (%j)', async state => {
  const view = await render(host(<ActivitiesScreen {...base} {...state} rows={[]} pending={null} />));
  await view.findByTestId('v2-activities'); expect(view.queryByText('No activities recorded yet.')).toBeNull();
  if (state.busy) expect(view.getByRole('button', { name: 'Add activity' })).toBeDisabled();
  if (state.error) expect(view.getByRole('alert')).toHaveTextContent(state.error);
});
test('one activity exposes sport, full date, supplied units, feedback and truthful canonical source', async () => {
  const view = await render(host(<ActivitiesScreen {...base} rows={[row]} pending={null} />));
  const summary = within(await view.findByTestId(`activity-row-${complete.id}`));
  expect(summary.getByText('Running')).toBeTruthy(); expect(summary.getByText(complete.date)).toBeTruthy();
  expect(summary.getByLabelText('45 minutes')).toBeTruthy(); expect(summary.getByText('Source: activity summary')).toBeTruthy();
  expect(summary.getByText(`${complete.rpeDescription} (RPE 7)`)).toBeTruthy(); expect(summary.queryByText(/synced|Garmin|manual/i)).toBeNull();
});
test('many rows preserve exact server order and exact-ID actions', async () => {
  const rows = [3, 1, 2].map(id => ({ ...row, activity: { ...complete, id: `activity-${id}` } }));
  const view = await render(host(<ActivitiesScreen {...base} rows={rows} pending={null} />));
  await view.findByTestId('activity-row-activity-3');
  expect(view.getAllByTestId(/^activity-row-/).map(node => node.props.testID)).toEqual(['activity-row-activity-3', 'activity-row-activity-1', 'activity-row-activity-2']);
  await fireEvent.press(within(view.getByTestId('activity-row-activity-1')).getByRole('button'));
  expect(base.onCorrect).toHaveBeenCalledWith('activity-1');
});
test('pending row consumes same supplied item; add blocked and continuation explicit, no second global banner/form', async () => {
  const view = await render(host(<ActivitiesScreen {...base} rows={[]} pending={pending} />));
  await view.findByTestId('activity-pending'); expect(view.getByRole('button', { name: 'Add activity' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' })); expect(base.onFeedback).toHaveBeenCalledTimes(1);
  expect(view.queryByRole('radiogroup')).toBeNull(); expect(view.queryByText(/waiting for RPE · open/)).toBeNull();
});
test.each([[null, 1500], ['45', null], ['45', 5000]] as const)('history independently renders duration/distance %s/%s', async (duration, distance) => {
  const activity = activityViewModel({ ...completeActivity, discipline: 'swim', duration_minutes: duration, distance_meters: distance }, 'en-GB', 'en');
  const view = await render(host(<ActivitiesScreen {...base} rows={[{ ...row, activity }]} pending={null} />));
  const scope = within(await view.findByTestId(`activity-row-${activity.id}`));
  if (duration !== null) expect(scope.getByLabelText('45 minutes')).toBeTruthy(); else expect(scope.queryByLabelText(/minutes$/)).toBeNull();
  if (distance !== null) expect(scope.getByLabelText(`${distance} meters`)).toBeTruthy();
});
test('matching is explicit, exact IDs; separate correction proposal remains pending', async () => {
  const view = await render(host(<ActivitiesScreen {...base} rows={[{ activity: { ...pending, correctionProposal: true }, canCorrect: false, match: { id: 'workout-a', name: 'Exact supplied workout' } }]} pending={null} />));
  await view.findByText('Exact supplied workout. Wombo never links this automatically.'); expect(base.onMatch).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: /Explicitly confirm match/ })); expect(base.onMatch).toHaveBeenCalledWith(pending.id, 'workout-a');
  expect(view.getByText('A separate correction proposal is ready. Nothing was adjusted automatically.')).toBeTruthy();
});
test('initial entry offers only existing supported fields; sport checked; no editable pace/HR at create', async () => {
  const view = await render(host(<ActivityEntryScreen {...entry} />)); await view.findByText('Record a workout');
  expect(view.getByRole('radio', { name: 'Running' })).toBeChecked(); expect(view.getByLabelText('Actual duration (minutes)').props.value).toBe('45');
  expect(view.getByLabelText('Actual start (ISO including time zone)').props.value).toBe(entry.startedAt);
  expect(view.queryByLabelText(/pace|heart rate/i)).toBeNull();
  await fireEvent.changeText(view.getByLabelText('Distance (metres, optional)'), '5000'); expect(entry.onDistance).toHaveBeenCalledWith('5000');
  await fireEvent.press(view.getByRole('radio', { name: 'Swimming' })); expect(entry.onDiscipline).toHaveBeenCalledWith('swim');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); expect(entry.onSave).toHaveBeenCalledTimes(1);
});
test('planned/external selector preserves exact occurrence ID and source context', async () => {
  const choices = [{ id: 'occurrence-a', kind: 'workout' as const, name: 'Same template', date: 'Tuesday, 6 October 2026', discipline: 'run' as const }, { id: 'occurrence-b', kind: 'workout' as const, name: 'Same template', date: 'Wednesday, 7 October 2026', discipline: 'run' as const }];
  const view = await render(host(<ActivityEntryScreen {...entry} choices={choices} />)); await view.findByText('Record a workout');
  await fireEvent.press(view.getByRole('button', { name: 'Choose a planned or extra workout' }));
  await fireEvent.press(view.getByRole('radio', { name: /Same template · Running · Wednesday/ })); expect(entry.onChoose).toHaveBeenCalledWith(choices[1]);
});
test.each([{ busy: true, blocked: false, timezone: entry.timezone }, { busy: false, blocked: true, timezone: entry.timezone }, { busy: false, blocked: false, timezone: '' }])('submit blocked by shared state %j', async state => {
  const view = await render(host(<ActivityEntryScreen {...entry} {...state} error="Safe validation error" />)); await view.findByRole('alert');
  expect(view.getByRole('button', { name: 'Save activity' })).toBeDisabled();
  if (state.busy) { expect(view.getByRole('button', { name: 'Back to Activities' })).toBeDisabled(); expect(view.getByLabelText('Actual duration (minutes)').props.editable).toBe(false); }
});
test('Back on an unsaved form is presentation-only', async () => {
  const view = await render(host(<ActivityEntryScreen {...entry} />)); await view.findByText('Record a workout');
  await fireEvent.press(view.getByRole('button', { name: 'Back to Activities' })); expect(entry.onBack).toHaveBeenCalledTimes(1); expect(entry.onSave).not.toHaveBeenCalled();
});
test.each(['swim', 'bike', 'run'] as const)('%s feedback uses all ten exact canonical save-on-tap choices and stored selected state', async discipline => {
  const onSelect = jest.fn(async () => undefined); const activity = { ...complete, discipline };
  const view = await render(host(<ActivityFeedbackScreen activity={activity} heartRate="151" busy={false} error={null} controls={null} onHeartRate={jest.fn()} onSelect={onSelect} onBack={jest.fn()} />));
  await view.findByText('Activity feedback'); const radios = view.getAllByRole('radio'); expect(radios).toHaveLength(10);
  rpeChoices(discipline).forEach(choice => expect(view.getByRole('radio', { name: `Save RPE · ${choice.description} (RPE ${choice.value})` })).toBeTruthy());
  expect(radios[6]).toBeChecked(); expect(view.getByLabelText('Average heart rate (bpm)').props.value).toBe('151');
  await fireEvent.press(radios[3]); expect(onSelect).toHaveBeenCalledWith(4); expect(view.queryByRole('button', { name: 'Save' })).toBeNull();
});
test('feedback busy/error is accessible, all targets >=48 and no fixed/clamped text', async () => {
  const view = await render(host(<ActivityFeedbackScreen activity={pending} heartRate="" busy error="Safe feedback failure" controls={null} onHeartRate={jest.fn()} onSelect={jest.fn()} onBack={jest.fn()} />));
  await view.findByRole('alert'); for (const radio of view.getAllByRole('radio')) { expect(radio).toBeDisabled(); expect(radio.props.accessibilityState.busy).toBe(true); }
  for (const button of view.getAllByRole('radio')) expect(StyleSheet.flatten(button.props.style).minHeight).toBeGreaterThanOrEqual(48);
  expect(view.getByLabelText('Average heart rate (bpm)').props.editable).toBe(false);
  expect(view.getByLabelText('Average heart rate (bpm)').props.allowFontScaling).toBe(true);
});
test('Dutch critical actions localized while canonical sport descriptions remain exact source text', async () => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue('nl');
  const view = await render(host(<ActivityFeedbackScreen activity={pending} heartRate="" busy={false} error={null} controls={null} onHeartRate={jest.fn()} onSelect={jest.fn()} onBack={jest.fn()} />));
  await view.findByText('Activiteitfeedback'); expect(view.getByText('Kies je gevoel om op te slaan. Je keuze wordt direct opgeslagen.')).toBeTruthy();
  expect(view.getByRole('radio', { name: 'RPE opslaan · Focus nodig, praten in zinnen. (RPE 4)' })).toBeTruthy();
});

test('a choice saves immediately once while unresolved, retains authoritative selection, and requires no extra Save', async () => {
  let acknowledge!: () => void;
  const onSelect = jest.fn(() => new Promise<void>(resolve => { acknowledge = resolve; }));
  const view = await render(host(<ActivityFeedbackScreen activity={complete} heartRate="151" busy={false} error={null}
    controls={null} onHeartRate={jest.fn()} onSelect={onSelect} onBack={jest.fn()} />));
  await view.findByText('Activity feedback');
  const choice = view.getByRole('radio', { name: `Save RPE · ${rpeChoices('run')[3].description} (RPE 4)` });
  await fireEvent.press(choice); await fireEvent.press(choice);
  expect(onSelect).toHaveBeenCalledTimes(1); expect(onSelect).toHaveBeenCalledWith(4);
  expect(choice).toBeDisabled(); expect(choice.props.accessibilityState.busy).toBe(true);
  expect(view.getAllByRole('radio')[6]).toBeChecked(); expect(choice).not.toBeChecked();
  expect(view.queryByRole('button', { name: /Save/ })).toBeNull();
  await act(() => acknowledge());
  expect(view.getAllByRole('radio')[6]).toBeChecked(); expect(choice).not.toBeDisabled();
});

test('history omits absent HR and correction capability while retaining every supplied notice and measure', async () => {
  const activity = { ...complete, averageHeartRate: null, durationMinutes: null, distanceMeters: 1500,
    distanceOnly: true, partialCoverage: true, correctionProposal: true,
    publicMessage: 'Exact public source explanation '.repeat(12) };
  const view = await render(host(<ActivitiesScreen {...base} rows={[{ activity, canCorrect: false, match: null }]} pending={null} />));
  const scope = within(await view.findByTestId(`activity-row-${activity.id}`));
  expect(scope.getByText(activity.publicMessage)).toBeTruthy(); expect(scope.getByLabelText('1500 meters')).toBeTruthy();
  expect(scope.getByText('Distance recorded. Duration and time in zone were not measured and are not inferred.')).toBeTruthy();
  expect(scope.getByText('Partial sensor coverage: only observed zone time was used; missing minutes were not estimated.')).toBeTruthy();
  expect(scope.getByText('A separate correction proposal is ready. Nothing was adjusted automatically.')).toBeTruthy();
  expect(scope.queryByText(/Average heart rate/)).toBeNull(); expect(scope.queryByRole('button')).toBeNull();
});
