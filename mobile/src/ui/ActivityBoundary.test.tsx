import { act, fireEvent, render, within } from '@testing-library/react-native';
import { useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as api from '../api/client';
import type { CompletedActivity } from '../api/types';
import { ActivityFlowProvider, useActivityFlow } from '../features/activities/ActivityFlowProvider';
import { activityOnboarding, completeActivity, externalActivity, pendingActivity } from '../features/activities/activities.test-fixtures';
import { workout } from '../features/planning/planning.test-fixtures';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { ActivityBoundary, type ActivityView } from './ActivityBoundary';
import { UiVersionProvider } from './UiVersionProvider';
import type { UiVersion } from './uiVersion';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en') }));
jest.mock('../api/client', () => ({ confirmActivityMatch: jest.fn(), createActivity: jest.fn(), getCalendar: jest.fn(), getOnboarding: jest.fn(), listActivities: jest.fn(), listPlannedExternalActivities: jest.fn(), submitActivityRpeWithRefresh: jest.fn() }));
let rows: CompletedActivity[];
let flow: ReturnType<typeof useActivityFlow>;
const rootBack = jest.fn(), busyChange = jest.fn();
function Presentation() {
  flow = useActivityFlow();
  const [version, setVersion] = useState<UiVersion>('v2');
  const [view, setView] = useState<ActivityView>('history');
  const [correctionId, setCorrectionId] = useState<string | null>(null);
  return <ActivityBoundary version={version} onVersion={setVersion} view={view} onView={setView}
    correctionId={correctionId} onCorrection={setCorrectionId} switchLocked={false}
    onBack={rootBack} onOpenProfile={jest.fn()} onSignOut={jest.fn(async () => undefined)} onNavigationBusyChange={busyChange} />;
}
function Host({ token = 'token-a', identity = 'athlete-a', visible = true }: { token?: string; identity?: string; visible?: boolean }) {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 320, height: 640 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><ActivityFlowProvider accessToken={token} athleteIdentity={identity}>
      {visible ? <Presentation /> : null}
    </ActivityFlowProvider></UiVersionProvider></LanguageProvider>
  </SafeAreaProvider>;
}
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (value: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
beforeEach(() => {
  jest.clearAllMocks(); process.env.EXPO_PUBLIC_UI_VERSION = 'v2'; rows = [];
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.mocked(api.listActivities).mockImplementation(async (_token, pending) => pending ? rows.filter(row => row.processing_state === 'awaiting_rpe') : rows);
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: '2026-09-21', to_date: '2026-10-19', workouts: [], rest_days: [] });
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding); jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.createActivity).mockImplementation(async () => { rows = [pendingActivity]; return pendingActivity; });
  jest.mocked(api.submitActivityRpeWithRefresh).mockImplementation(async (_token, activity, rpe) => {
    const updated = { ...activity, rpe, processing_state: 'complete' as const, qualitative_result: 'unplanned' as const };
    rows = rows.map(row => row.id === activity.id ? updated : row); return updated;
  });
});
afterEach(async () => {
  // Settle FlashList's deferred layout callback inside the test transaction.
  await act(() => new Promise<void>(resolve => setTimeout(resolve, 20)));
  delete process.env.EXPO_PUBLIC_UI_VERSION;
});
async function openEntry() {
  const view = await render(<Host />); await view.findByText('No activities recorded yet.');
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' })); return view;
}
const rpeFour = 'Save RPE · Focus nodig, praten in zinnen. (RPE 4)';

test('V2 create validates existing fields, calls exact shared payload, then same pending feedback and one authoritative save', async () => {
  const view = await openEntry(); await fireEvent.changeText(view.getByLabelText('Actual start (ISO including time zone)'), '2026-10-06T10:00:00Z');
  await fireEvent.changeText(view.getByLabelText('Distance (metres, optional)'), '5000');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  await view.findByText('Activity feedback'); expect(flow.feedbackActivity?.id).toBe(pendingActivity.id);
  expect(api.createActivity).toHaveBeenCalledWith('token-a', expect.stringMatching(/^[\da-f-]{36}$/), { discipline: 'run', duration_minutes: '45', distance_meters: 5000, started_at: '2026-10-06T10:00:00Z', timezone: 'Europe/Amsterdam' });
  expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled(); expect(view.getAllByRole('radio')).toHaveLength(10); expect(view.getAllByTestId('activity-feedback-scroll')).toHaveLength(1);
  await fireEvent.changeText(view.getByLabelText('Average heart rate (bpm)'), '151');
  await fireEvent.press(view.getByRole('radio', { name: rpeFour })); await view.findByTestId('v2-activities');
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', pendingActivity, 4, 151);
  expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1); expect(flow.pendingRpe).toEqual([]);
  expect(api.listActivities).toHaveBeenCalledTimes(3); expect(api.createActivity).toHaveBeenCalledTimes(1);
});
test.each([['Actual duration (minutes)', '0', 'Vul een geldige duur in minuten in.'], ['Distance (metres, optional)', '1.5', 'Vul afstand in hele meters in.'], ['Actual start (ISO including time zone)', 'invalid', 'Gebruik een geldig werkelijk starttijdstip in ISO-formaat.']])('invalid %s stays populated; no mutation', async (field, value, message) => {
  const view = await openEntry(); await fireEvent.changeText(view.getByLabelText(field), value); await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  expect(view.getByRole('alert')).toHaveTextContent(message); expect(view.getByLabelText(field).props.value).toBe(value); expect(api.createActivity).not.toHaveBeenCalled();
});
test('double press/rerender while create unresolved gives one create and shared disabled navigation/switch', async () => {
  const request = deferred<CompletedActivity>(); jest.mocked(api.createActivity).mockReturnValue(request.promise);
  const view = await openEntry(); const save = view.getByRole('button', { name: 'Save activity' });
  await fireEvent.press(save); await fireEvent.press(save); await view.rerender(<Host token="rotated-token" />);
  expect(api.createActivity).toHaveBeenCalledTimes(1); expect(view.getByRole('button', { name: 'UI V1' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Back to Activities' })).toBeDisabled(); expect(busyChange).toHaveBeenLastCalledWith(true);
  await act(() => { rows = [pendingActivity]; request.resolve(pendingActivity); }); await view.findByText('Activity feedback');
  expect(api.createActivity).toHaveBeenCalledTimes(1); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
});
test('ambiguous create plus presentation return and explicit retry retain the logical key/form', async () => {
  jest.mocked(api.createActivity).mockRejectedValueOnce(new Error('Safe ambiguous failure')).mockImplementationOnce(async () => { rows = [pendingActivity]; return pendingActivity; });
  const view = await openEntry(); await fireEvent.changeText(view.getByLabelText('Distance (metres, optional)'), '6000');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); expect(view.getByRole('alert')).toHaveTextContent('Safe ambiguous failure');
  const key = jest.mocked(api.createActivity).mock.calls[0][1];
  await fireEvent.press(view.getByRole('button', { name: 'Back to Activities' })); await fireEvent.press(view.getByRole('button', { name: 'Add activity' }));
  expect(view.getByLabelText('Distance (metres, optional)').props.value).toBe('6000');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); expect(jest.mocked(api.createActivity).mock.calls[1][1]).toBe(key);
});
test('Back from pending does not write or clear; second create blocked and exact continuation remains', async () => {
  rows = [pendingActivity]; const view = await render(<Host />); await view.findByTestId('activity-pending');
  expect(view.getByRole('button', { name: 'Add activity' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' })); await fireEvent.press(view.getByRole('button', { name: 'Back to Activities' }));
  expect(flow.feedbackActivity).toBe(pendingActivity); expect(api.createActivity).not.toHaveBeenCalled(); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
  await view.rerender(<Host visible={false} />); await view.rerender(<Host />); await view.findByTestId('activity-pending');
  expect(api.listActivities).toHaveBeenCalledTimes(1); await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' }));
  expect(view.getByTestId(`activity-summary-${pendingActivity.id}`)).toBeTruthy();
});
test('feedback failure/retry, rapid press and rerender never rebind exact activity or discard HR', async () => {
  rows = [pendingActivity]; const request = deferred<CompletedActivity>(); jest.mocked(api.submitActivityRpeWithRefresh).mockReturnValueOnce(request.promise);
  const view = await render(<Host />); await view.findByTestId('activity-pending'); await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' }));
  await fireEvent.changeText(view.getByLabelText('Average heart rate (bpm)'), '151');
  const choice = view.getByRole('radio', { name: rpeFour }); await fireEvent.press(choice); await fireEvent.press(choice);
  await fireEvent.press(view.getByRole('radio', { name: "Save RPE · 'Sweet spot', comfortabel oncomfortabel. (RPE 5)" }));
  await view.rerender(<Host />); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(1);
  await act(() => request.reject(new Error('Safe feedback failure'))); expect(view.getByRole('alert')).toHaveTextContent('Safe feedback failure');
  expect(flow.feedbackActivity).toBe(pendingActivity); expect(view.getByLabelText('Average heart rate (bpm)').props.value).toBe('151');
  await fireEvent.press(view.getByRole('radio', { name: rpeFour })); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledTimes(2);
  expect(jest.mocked(api.submitActivityRpeWithRefresh).mock.calls.map(call => [call[1].id, call[2], call[3]])).toEqual([[pendingActivity.id, 4, 151], [pendingActivity.id, 4, 151]]);
});
test('safe V1/V2 presentation switch preserves owner, pending identity/HR/draft and causes no full reread/mutation', async () => {
  rows = [pendingActivity]; const view = await render(<Host />); await view.findByTestId('activity-pending'); const owner = flow.ensureActivitiesLoaded;
  await act(() => { flow.setDistance('5000'); flow.setHeartRateByActivity({ [pendingActivity.id]: '148' }); });
  await fireEvent.press(view.getByRole('button', { name: 'Complete feedback' }));
  await fireEvent.press(view.getByRole('button', { name: 'UI V1' })); await view.findByText('Record a workout');
  expect(flow.ensureActivitiesLoaded).toBe(owner); expect(flow.feedbackActivity?.id).toBe(pendingActivity.id);
  await fireEvent.press(view.getByRole('button', { name: 'UI V2' })); await view.findByText('Activity feedback');
  expect(view.getByLabelText('Average heart rate (bpm)').props.value).toBe('148'); expect(flow.distance).toBe('5000');
  expect(api.listActivities).toHaveBeenCalledTimes(1); expect(api.createActivity).not.toHaveBeenCalled(); expect(api.submitActivityRpeWithRefresh).not.toHaveBeenCalled();
});
test('sign-out/athlete replacement resets visible feedback, stored selection and drafts', async () => {
  rows = [pendingActivity]; const view = await render(<Host />); await view.findByTestId('activity-pending');
  await act(() => { flow.setDistance('9876'); flow.setHeartRateByActivity({ [pendingActivity.id]: '199' }); });
  const oldOwner = flow.ensureActivitiesLoaded; await view.rerender(<Host visible={false} />);
  rows = []; await view.rerender(<Host identity="athlete-b" token="token-b" />); await view.findByText('No activities recorded yet.');
  expect(flow.ensureActivitiesLoaded).not.toBe(oldOwner); expect(flow.pendingRpe).toEqual([]); expect(flow.heartRateByActivity).toEqual({});
  expect(flow.distance).toBe(''); expect(view.queryByTestId(`activity-summary-${pendingActivity.id}`)).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' })); expect(view.getByLabelText('Distance (metres, optional)').props.value).toBe('');
  expect(view.queryByRole('radio', { name: rpeFour })).toBeNull();
});
test('athlete replacement gets a fresh logical key rather than A’s ambiguous create attempt', async () => {
  jest.mocked(api.createActivity).mockRejectedValue(new Error('Safe uncertain result'));
  const view = await openEntry(); await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  const firstKey = jest.mocked(api.createActivity).mock.calls[0][1];
  await view.rerender(<Host identity="athlete-b" token="token-b" />); await view.findByText('No activities recorded yet.');
  await fireEvent.press(view.getByRole('button', { name: 'Add activity' })); await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  expect(jest.mocked(api.createActivity).mock.calls[1][0]).toBe('token-b');
  expect(jest.mocked(api.createActivity).mock.calls[1][1]).not.toBe(firstKey);
});
test('current-week correction uses stored RPE and same snapshot; historical correction is absent', async () => {
  const recent = { ...completeActivity, started_at: new Date().toISOString() };
  rows = [recent, { ...completeActivity, id: 'historical', started_at: '2020-01-01T12:00:00Z' }];
  const view = await render(<Host />); const record = within(await view.findByTestId(`activity-row-${recent.id}`));
  expect(within(view.getByTestId('activity-row-historical')).queryByRole('button', { name: /Correct this week/ })).toBeNull();
  await fireEvent.press(record.getByRole('button', { name: /Correct this week/ }));
  expect(view.getByRole('radio', { name: 'Save RPE · Diepe ademhaling (10k wedstrijdtempo). (RPE 7)' })).toBeChecked();
  await fireEvent.press(view.getByRole('radio', { name: rpeFour })); expect(api.submitActivityRpeWithRefresh).toHaveBeenCalledWith('token-a', recent, 4, undefined);
});
test('planned source selection keeps exact workout ID in create', async () => {
  jest.mocked(api.getCalendar).mockResolvedValue({ from_date: 'from', to_date: 'to', workouts: [workout], rest_days: [] });
  const view = await openEntry(); await fireEvent.press(view.getByRole('button', { name: 'Choose a planned or extra workout' }));
  await fireEvent.press(view.getByRole('radio', { name: new RegExp(workout.name) }));
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' })); expect(jest.mocked(api.createActivity).mock.calls[0][2].planned_workout_id).toBe(workout.id);
});

test('V2 planned external selection uses its exact identity and existing duration default', async () => {
  const external = { ...externalActivity, name: 'Exact external ride', scheduled_at: '2026-10-06T10:00:00Z' };
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([external]);
  const view = await openEntry();
  await fireEvent.press(view.getByRole('button', { name: 'Choose a planned or extra workout' }));
  await fireEvent.press(view.getByRole('radio', { name: /Exact external ride.*Cycling.*Outside Wombo/ }));
  expect(view.getByLabelText('Actual duration (minutes)').props.value).toBe('60');
  expect(view.queryByRole('radio', { name: 'Running' })).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  const payload = jest.mocked(api.createActivity).mock.calls[0][2];
  expect(payload).toEqual(expect.objectContaining({ planned_external_activity_id: external.id, discipline: 'bike', duration_minutes: '60' }));
  expect(payload).not.toHaveProperty('planned_workout_id');
});

test('V2 swim distance-only entry preserves null duration without estimating time', async () => {
  const view = await openEntry();
  await fireEvent.press(view.getByRole('radio', { name: 'Swimming' }));
  await fireEvent.changeText(view.getByLabelText('Actual duration (minutes, optional with distance)'), '');
  await fireEvent.changeText(view.getByLabelText('Distance (metres, optional)'), '1500');
  await fireEvent.press(view.getByRole('button', { name: 'Save activity' }));
  expect(api.createActivity).toHaveBeenCalledTimes(1);
  expect(jest.mocked(api.createActivity).mock.calls[0][2]).toEqual(expect.objectContaining({ discipline: 'swim', duration_minutes: null, distance_meters: 1500 }));
});
