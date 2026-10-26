import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import * as api from '../api/client';
import type { WeeklyCheckIn } from '../api/types';
import { activeRestriction, alarmLabel, answers, none, recurringLabel, restrictedAnswers, savedCheckIn } from '../features/checkins/checkIn.test-fixtures';
import { CheckInScreen } from './CheckInScreen';

jest.mock('../api/client', () => ({
  approvePlanProposal: jest.fn(), confirmWeeklyCheckInContext: jest.fn(), createCheckInPlanProposal: jest.fn(),
  extractWeeklyCheckInContextCandidate: jest.fn(), getInjuryRestrictions: jest.fn(),
  saveWeeklyCheckInContext: jest.fn(), startWeeklyCheckIn: jest.fn(),
}));
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
let stored: WeeklyCheckIn;
beforeEach(() => {
  jest.resetAllMocks();
  jest.useFakeTimers({ now: new Date('2026-10-26T12:00:00Z'), doNotFake: [
    'hrtime', 'nextTick', 'performance', 'queueMicrotask', 'requestAnimationFrame', 'cancelAnimationFrame',
    'requestIdleCallback', 'cancelIdleCallback', 'setImmediate', 'clearImmediate', 'setInterval', 'clearInterval', 'setTimeout', 'clearTimeout',
  ] });
  stored = clone(savedCheckIn);
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([]);
  jest.mocked(api.startWeeklyCheckIn).mockImplementation(async () => clone(stored));
  jest.mocked(api.saveWeeklyCheckInContext).mockImplementation(async (_token, id, { expected_revision, ...payload }) => {
    expect(id).toBe(stored.id);
    expect(expected_revision).toBe(stored.context_revision);
    const revision = expected_revision + 1;
    stored = { ...stored, context_revision: revision, context: {
      ...savedCheckIn.context!, ...payload, revision, state: 'draft', fingerprint: String(revision).repeat(64), confirmed_at: null,
    } };
    return clone(stored);
  });
  jest.mocked(api.confirmWeeklyCheckInContext).mockImplementation(async (_token, id, revision, fingerprint) => {
    expect(id).toBe(stored.id);
    expect(revision).toBe(stored.context_revision);
    expect(fingerprint).toBe(stored.context!.fingerprint);
    stored = { ...stored, context: { ...stored.context!, state: 'confirmed', confirmed_at: '2026-10-26T12:00:00Z' } };
    return clone(stored);
  });
});
afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

type View = Awaited<ReturnType<typeof render>>;
const back = jest.fn();
const signOut = jest.fn(async () => undefined);
function screen(identity = 'athlete-a', token = 'token-a') {
  return <CheckInScreen athleteIdentity={identity} accessToken={token} onBack={back} onSignOut={signOut} />;
}
async function begin(view: View) {
  await fireEvent.changeText(view.getByLabelText('Week start op maandag'), stored.week_start);
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Week van ' + stored.week_start);
}
async function open() {
  const view = await render(screen());
  await begin(view);
  return view;
}
async function save(view: View) {
  const calls = jest.mocked(api.saveWeeklyCheckInContext).mock.calls.length;
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  await waitFor(() => expect(api.saveWeeklyCheckInContext).toHaveBeenCalledTimes(calls + 1));
  await waitFor(() => expect(view.getByRole('button', { name: 'Context opslaan' })).toBeEnabled());
}
function lastPayload() {
  const { expected_revision: _revision, ...payload } = jest.mocked(api.saveWeeklyCheckInContext).mock.calls.at(-1)![2];
  return payload;
}
function expectRestored(view: View) {
  expect(view.getByRole('radio', { name: 'Lopen: Professioneel advies' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Zwemmen: Geblokkeerd' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Fietsen: Alleen rustig' })).toBeChecked();
  expect(view.getByLabelText('Advies en herleidbare bron').props.value).toBe(restrictedAnswers[0].professional_advice);
  expect(view.getByRole('checkbox', { name: alarmLabel })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Wo' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Vr' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Matig' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Blessure' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: recurringLabel })).toBeChecked();
  expect(view.getByText('Clubtraining')).toBeTruthy();
}

test.each(['navigate away', 'app remount'])('save -> %s -> reload preserves every persisted answer structurally', async departure => {
  const expected = clone(answers(stored.context!));
  let view = await open();
  expectRestored(view);
  await save(view);
  expect(lastPayload()).toStrictEqual(expected);
  if (departure === 'navigate away') await fireEvent.press(view.getByRole('button', { name: 'Weekplanning' }));
  await view.unmount();
  view = await open();
  expectRestored(view);
  await save(view);
  expect(lastPayload()).toStrictEqual(expected);
  expect(answers(stored.context!)).toStrictEqual(expected);
});

test('repeated unchanged saves retain professional source/date, nulls, flags and sequence', async () => {
  const expected = clone(answers(stored.context!));
  const view = await open();
  await save(view);
  jest.setSystemTime(new Date('2026-10-27T14:00:00Z'));
  await save(view);
  expect(lastPayload()).toStrictEqual(expected);
  expect(jest.mocked(api.saveWeeklyCheckInContext).mock.calls.map(call => call[2].expected_revision)).toEqual([4, 5]);
});

test('explicit no restrictions, no fatigue and false alarm acknowledgement stay explicit', async () => {
  stored.context = { ...stored.context!, restrictions: [none('swim'), none('bike'), none('run')], fatigue_level: 'none', alarm_symptoms_acknowledged: false, missed_workout_reasons: [], external_activities: [], blocked_dates: [] };
  const expected = clone(answers(stored.context));
  const view = await open();
  for (const sport of ['Zwemmen', 'Fietsen', 'Lopen']) expect(view.getByRole('radio', { name: `${sport}: Vrij` })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Geen' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: alarmLabel })).not.toBeChecked();
  await save(view);
  expect(lastPayload()).toStrictEqual(expected);
});

test('one saved injured sport is restored while absent sport answers remain unanswered', async () => {
  stored.context = { ...stored.context!, restrictions: [restrictedAnswers[1]] };
  const view = await open();
  expect(view.getByRole('radio', { name: 'Zwemmen: Geblokkeerd' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).not.toBeChecked();
  expect(view.getByRole('radio', { name: 'Fietsen: Vrij' })).not.toBeChecked();
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  for (const sport of ['Lopen', 'Fietsen']) await fireEvent.press(view.getByRole('radio', { name: `${sport}: Vrij` }));
  await save(view);
  expect(lastPayload().restrictions[0]).toStrictEqual(restrictedAnswers[1]);
  expect(lastPayload().restrictions).toHaveLength(3);
});

test.each(['fatigue_level', 'alarm_symptoms_acknowledged', 'recurring_activities_confirmed', 'restrictions'] as const)('missing %s is not restored as a negative answer', async field => {
  delete (stored.context! as Partial<NonNullable<WeeklyCheckIn['context']>>)[field];
  const view = await open();
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  if (field === 'fatigue_level') expect(view.getByRole('radio', { name: 'Geen' })).not.toBeChecked();
  expect(api.saveWeeklyCheckInContext).not.toHaveBeenCalled();
});

test('saved false recurring confirmation is retained and still requires the existing confirmation', async () => {
  stored.context = { ...stored.context!, recurring_activities_confirmed: false };
  const view = await open();
  expect(view.getByRole('checkbox', { name: recurringLabel })).not.toBeChecked();
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  expect(api.saveWeeklyCheckInContext).not.toHaveBeenCalled();
});

test('prior active restrictions remain visible after review is due; incomplete review cannot save or confirm', async () => {
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue(restrictedAnswers.map(activeRestriction));
  const view = await open();
  expect(view.getAllByText(/De beperking vervalt niet door tijdsverloop/)).toHaveLength(3);
  expect(view.getByText(/Opgeslagen advies \(physician\)/)).toBeTruthy();
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  for (const sport of ['Zwemmen', 'Fietsen']) await fireEvent.press(view.getByRole('checkbox', { name: `Ik heb de bestaande beperking voor ${sport} opnieuw beoordeeld.` }));
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Ik heb de bestaande beperking voor Lopen opnieuw beoordeeld.' }));
  await save(view);
  expect(lastPayload().restrictions).toStrictEqual(restrictedAnswers);
});

test.each(['clearance_required', 'expired'] as const)('%s from an earlier week is retained without an invented clinical rule', async status => {
  const decision = { ...restrictedAnswers[0], status };
  stored.context = { ...stored.context!, restrictions: [none('swim'), none('bike')] };
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([activeRestriction(decision)]);
  const view = await open();
  expect(view.getByRole('radio', { name: 'Lopen: Bestaande beperking behouden' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).not.toBeChecked();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Ik heb de bestaande beperking voor Lopen opnieuw beoordeeld.' }));
  await save(view);
  expect(lastPayload().restrictions.find(item => item.discipline === 'run')).toStrictEqual(decision);
});

test('a new check-in carries prior blocked input rather than an unrestricted default', async () => {
  stored = { ...stored, context_revision: 0, context: null };
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([activeRestriction(restrictedAnswers[1])]);
  const view = await open();
  expect(view.getByRole('radio', { name: 'Zwemmen: Geblokkeerd' })).toBeChecked();
  for (const sport of ['Lopen', 'Fietsen']) await fireEvent.press(view.getByRole('radio', { name: `${sport}: Vrij` }));
  await fireEvent.press(view.getByRole('radio', { name: 'Geen' }));
  await fireEvent.press(view.getByRole('checkbox', { name: alarmLabel }));
  await fireEvent.press(view.getByRole('checkbox', { name: recurringLabel }));
  expect(view.getByRole('button', { name: 'Context opslaan' })).toBeDisabled();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Ik heb de bestaande beperking voor Zwemmen opnieuw beoordeeld.' }));
  await save(view);
  expect(lastPayload().restrictions.find(item => item.discipline === 'swim')).toStrictEqual(restrictedAnswers[1]);
});

test('explicit supported resumption retains advice and requires saving before exact confirmation and next-week request', async () => {
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([activeRestriction()]);
  const view = await open();
  await fireEvent.press(view.getByRole('radio', { name: 'Lopen: Vrij' }));
  expect(view.getByText(/Arts: lopen geblokkeerd/)).toBeTruthy();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  await save(view);
  expect(lastPayload().restrictions[0]).toStrictEqual({ ...restrictedAnswers[0], source: 'athlete', status: 'none', athlete_plan_choice: 'resume_unrestricted' });
  await fireEvent.press(view.getByRole('button', { name: 'Deze context bevestigen' }));
  await view.findByText('Context bevestigd');
  expect(api.confirmWeeklyCheckInContext).toHaveBeenCalledWith('token-a', 'check-in-a', 5, '5'.repeat(64));
  expect(api.createCheckInPlanProposal).not.toHaveBeenCalled();
  jest.mocked(api.createCheckInPlanProposal).mockRejectedValue(new Error('Synthetic proposal stop'));
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await view.findByText('Synthetic proposal stop');
  expect(api.createCheckInPlanProposal).toHaveBeenCalledWith('token-a', 'check-in-a');
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test.each(['stale revision 409', 'network error'])('%s preserves edited restrictions and never silently confirms or reloads', async message => {
  const view = await open();
  await fireEvent.press(view.getByRole('radio', { name: 'Zwemmen: Alleen rustig' }));
  jest.mocked(api.saveWeeklyCheckInContext).mockRejectedValueOnce(new Error(message));
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  await view.findByText(message);
  const failed = clone(jest.mocked(api.saveWeeklyCheckInContext).mock.calls[0][2]);
  expect(view.getByRole('radio', { name: 'Zwemmen: Alleen rustig' })).toBeChecked();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  expect(api.startWeeklyCheckIn).toHaveBeenCalledTimes(1);
  expect(api.confirmWeeklyCheckInContext).not.toHaveBeenCalled();
  await save(view);
  expect(jest.mocked(api.saveWeeklyCheckInContext).mock.calls[1][2]).toStrictEqual(failed);
});

test.each(['context read', 'restriction read'])('%s error exposes no default injury answers; explicit reopen retries safely', async failure => {
  const method = failure === 'context read' ? api.startWeeklyCheckIn : api.getInjuryRestrictions;
  jest.mocked(method).mockRejectedValueOnce(new Error('Synthetic reload failure'));
  const view = await render(screen());
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Synthetic reload failure');
  expect(view.queryByRole('radio', { name: 'Lopen: Vrij' })).toBeNull();
  expect(api.saveWeeklyCheckInContext).not.toHaveBeenCalled();
  await begin(view);
  expectRestored(view);
});

test('confirmation error retains saved answers and the same exact revision/fingerprint', async () => {
  const view = await open();
  jest.mocked(api.confirmWeeklyCheckInContext).mockRejectedValueOnce(new Error('Synthetic stale confirmation'));
  await fireEvent.press(view.getByRole('button', { name: 'Deze context bevestigen' }));
  await view.findByText('Synthetic stale confirmation');
  expectRestored(view);
  expect(api.createCheckInPlanProposal).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Deze context bevestigen' }));
  await view.findByText('Context bevestigd');
  expect(jest.mocked(api.confirmWeeklyCheckInContext).mock.calls).toEqual([
    ['token-a', 'check-in-a', 4, 'a'.repeat(64)], ['token-a', 'check-in-a', 4, 'a'.repeat(64)],
  ]);
});

function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(yes => { resolve = yes; }); return { promise, resolve }; }
test('in-flight save locks edits and repeated Save sends one reviewed snapshot', async () => {
  const view = await open();
  const pending = deferred<WeeklyCheckIn>();
  jest.mocked(api.saveWeeklyCheckInContext).mockReturnValue(pending.promise);
  const button = view.getByRole('button', { name: 'Context opslaan' });
  await fireEvent.press(button);
  await fireEvent.press(button);
  expect(api.saveWeeklyCheckInContext).toHaveBeenCalledTimes(1);
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).toBeDisabled();
  expect(view.getByLabelText('Advies en herleidbare bron').props.editable).toBe(false);
  await act(async () => pending.resolve(stored));
  expectRestored(view);
});

test('switching athlete during a read discards late previous-account hydration', async () => {
  const pending = deferred<WeeklyCheckIn>();
  jest.mocked(api.startWeeklyCheckIn).mockReturnValueOnce(pending.promise);
  const view = await render(screen());
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.rerender(screen('athlete-b', 'token-b'));
  stored = { ...stored, id: 'check-in-b', context: { ...stored.context!, restrictions: [none('swim'), none('bike'), none('run')], external_activities: [] } };
  await begin(view);
  await act(async () => pending.resolve(savedCheckIn));
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).toBeChecked();
  expect(view.queryByLabelText('Advies en herleidbare bron')).toBeNull();
  await save(view);
  expect(api.saveWeeklyCheckInContext).toHaveBeenCalledWith('token-b', 'check-in-b', expect.any(Object));
});

test('token rotation for the same athlete preserves answers and uses the new token', async () => {
  const view = await open();
  await view.rerender(screen('athlete-a', 'rotated-token'));
  expectRestored(view);
  await save(view);
  expect(api.saveWeeklyCheckInContext).toHaveBeenCalledWith('rotated-token', 'check-in-a', expect.any(Object));
});

test('confirmed context with unanswered disciplines requires explicit review before planning', async () => {
  stored.context = { ...stored.context!, state: 'confirmed', restrictions: [] };
  const view = await render(screen());
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Klaar voor het voorstel');
  expect(view.getByRole('button', { name: 'Maak planvoorstel' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Antwoorden opnieuw beoordelen' }));
  for (const sport of ['Zwemmen', 'Fietsen', 'Lopen']) await fireEvent.press(view.getByRole('radio', { name: `${sport}: Vrij` }));
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  await save(view);
  expect(stored.context!.state).toBe('draft');
  expect(api.createCheckInPlanProposal).not.toHaveBeenCalled();
});

test('a newer active restriction prevents an old confirmed unrestricted answer from driving planning', async () => {
  stored.context = { ...stored.context!, state: 'confirmed', restrictions: [none('swim'), none('bike'), none('run')] };
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([activeRestriction()]);
  const view = await open();
  expect(view.queryByRole('button', { name: 'Maak planvoorstel' })).toBeNull();
  expect(view.getByText(/Opgeslagen advies \(physician\)/)).toBeTruthy();
  expect(view.getByRole('checkbox', { name: 'Ik heb de bestaande beperking voor Lopen opnieuw beoordeeld.' })).not.toBeChecked();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
  await fireEvent.press(view.getByRole('radio', { name: 'Lopen: Geblokkeerd' }));
  await save(view);
  expect(lastPayload().restrictions.find(item => item.discipline === 'run')).toMatchObject({ status: 'self_reported_blocked', athlete_plan_choice: 'keep_blocked' });
  expect(api.createCheckInPlanProposal).not.toHaveBeenCalled();
});

test('account switch during Save cannot restore the previous athlete snapshot or confirm it', async () => {
  const view = await open();
  const pending = deferred<WeeklyCheckIn>();
  jest.mocked(api.saveWeeklyCheckInContext).mockReturnValueOnce(pending.promise);
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  await view.rerender(screen('athlete-b', 'token-b'));
  stored = { ...stored, id: 'check-in-b', context: { ...stored.context!, restrictions: [none('swim'), none('bike'), none('run')] } };
  await begin(view);
  await act(async () => pending.resolve(savedCheckIn));
  expect(view.getByRole('radio', { name: 'Lopen: Vrij' })).toBeChecked();
  expect(view.queryByLabelText('Advies en herleidbare bron')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'Deze context bevestigen' }));
  await view.findByText('Context bevestigd');
  expect(api.confirmWeeklyCheckInContext).toHaveBeenCalledWith('token-b', 'check-in-b', 4, 'a'.repeat(64));
});

test('edited professional advice receives one entry timestamp that survives retry and later saves', async () => {
  const view = await open();
  await fireEvent.changeText(view.getByLabelText('Advies en herleidbare bron'), 'Arts: nieuw vastgelegd advies.');
  jest.mocked(api.saveWeeklyCheckInContext).mockRejectedValueOnce(new Error('Synthetic save failure'));
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  await view.findByText('Synthetic save failure');
  jest.setSystemTime(new Date('2026-10-27T12:00:00Z'));
  await save(view);
  expect(lastPayload().restrictions[0]).toMatchObject({ source: 'physician', professional_advice: 'Arts: nieuw vastgelegd advies.', professional_advice_at: '2026-10-26T12:00:00.000Z' });
  await save(view);
  expect(lastPayload().restrictions[0].professional_advice_at).toBe('2026-10-26T12:00:00.000Z');
});

test('new professional restriction cannot be submitted without attributable advice', async () => {
  stored.context = { ...stored.context!, restrictions: [none('swim'), none('bike'), none('run')] };
  const view = await open();
  await fireEvent.press(view.getByRole('radio', { name: 'Lopen: Professioneel advies' }));
  await fireEvent.press(view.getByRole('button', { name: 'Context opslaan' }));
  await view.findByText('Vul het professionele advies en de herleidbare bron in.');
  expect(api.saveWeeklyCheckInContext).not.toHaveBeenCalled();
  expect(view.getByRole('button', { name: 'Deze context bevestigen' })).toBeDisabled();
});

test('different prior and saved professional advice both remain visible with their provenance', async () => {
  const previous = activeRestriction();
  stored.context = { ...stored.context!, restrictions: [{ ...restrictedAnswers[0], source: 'physiotherapist', professional_advice: 'Fysio: nieuwer opgeslagen advies.', professional_advice_at: '2026-10-24T10:00:00Z' }, ...restrictedAnswers.slice(1)] };
  const expected = clone(stored.context.restrictions);
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([previous]);
  const view = await open();
  expect(view.getByText(/Opgeslagen advies \(physician\).*Arts: lopen geblokkeerd/)).toBeTruthy();
  expect(view.getByText(/Advies in dit opgeslagen antwoord \(physiotherapist\).*nieuwer opgeslagen advies.*2026-10-24/)).toBeTruthy();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Ik heb de bestaande beperking voor Lopen opnieuw beoordeeld.' }));
  await save(view);
  expect(lastPayload().restrictions).toStrictEqual(expected);
});
