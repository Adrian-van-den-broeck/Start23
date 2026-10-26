import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import { useState, type PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import type { CalendarResponse } from '../api/types';
import * as api from '../api/client';
import type { WeeklyPlan } from '../api/types';
import { activePlan, onboarding, workout } from '../features/planning/planning.test-fixtures';
import { approvedNext, nextProposal, nextWorkout, pendingNext } from '../features/planning/planningTask.test-fixtures';
import { savedCheckIn } from '../features/checkins/checkIn.test-fixtures';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from '../features/planning/PlanningFlowProvider';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { PlanningPresentationProvider } from '../navigation/PlanningPresentationProvider';
import { UiVersionProvider } from '../ui/UiVersionProvider';
import { PlanningBoundary } from './PlanningScreen';
import { CheckInScreen } from './CheckInScreen';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn(), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'device-only' }));
jest.mock('expo-localization', () => ({ getLocales: () => [{ languageCode: 'en' }] }));
jest.mock('../api/client', () => ({
  approvePlanProposal: jest.fn(), createSwipeWeekDraft: jest.fn(), editPendingWorkout: jest.fn(), getCalendar: jest.fn(),
  getOnboarding: jest.fn(), getPendingWorkoutAlternatives: jest.fn(), getSwipeWeekDraft: jest.fn(), getWeeklyPlan: jest.fn(),
  markGoalAchieved: jest.fn(), movePlannedWorkout: jest.fn(), placeSwipeWeekWorkout: jest.fn(), rejectPlanProposal: jest.fn(),
  submitSwipeWeekDraft: jest.fn(), transitionSwipeWeekDraft: jest.fn(), validatePlanLayout: jest.fn(),
  startWeeklyCheckIn: jest.fn(), getInjuryRestrictions: jest.fn(), saveWeeklyCheckInContext: jest.fn(),
  confirmWeeklyCheckInContext: jest.fn(), createCheckInPlanProposal: jest.fn(), extractWeeklyCheckInContextCandidate: jest.fn(),
}));
jest.mock('@gorhom/bottom-sheet', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const RN = jest.requireActual<typeof import('react-native')>('react-native');
  return {
    BottomSheetBackdrop: () => null,
    BottomSheetView: ({ children }: PropsWithChildren) => <RN.View>{children}</RN.View>,
    BottomSheetScrollView: ({ children }: PropsWithChildren) => <RN.ScrollView>{children}</RN.ScrollView>,
    BottomSheetModal: React.forwardRef((_props: PropsWithChildren, ref) => {
      React.useImperativeHandle(ref, () => ({ present: jest.fn(), dismiss: jest.fn() })); return null;
    }),
  };
});
jest.mock('react-native-reanimated-carousel', () => ({ Carousel: () => null }));

let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let stored: Map<string, string>;
let server: Map<string, WeeklyPlan>;
function Probe() { flow = usePlanningFlow(); calendar = usePlanningCalendar(); return null; }
function Routes({ identity, token }: { identity: string; token: string }) {
  const [route, setRoute] = useState<'week' | 'calendar' | 'check-in'>('week');
  return <><Probe />{route === 'check-in' ? <CheckInScreen athleteIdentity={identity} accessToken={token} onBack={() => setRoute('week')} onSignOut={async () => undefined} /> : <PlanningBoundary
    destination={route} onBackToOnboarding={jest.fn()} onSignOut={async () => undefined} onOpenCheckIn={() => setRoute('check-in')}
    onOpenActivities={jest.fn()} onOpenIntegrations={jest.fn()} onOpenProfile={jest.fn()} onOpenZoneProfile={jest.fn()}
    onCalendarRoot={() => setRoute('calendar')} onWeekRoot={() => setRoute('week')} />}</>;
}
function Host({ identity = 'athlete-a', token = 'token-a' }: { identity?: string; token?: string }) {
  return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 360, height: 800 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}>
    <LanguageProvider><UiVersionProvider><PlanningFlowProvider accessToken={token} athleteIdentity={identity}><PlanningPresentationProvider><Routes identity={identity} token={token} /></PlanningPresentationProvider></PlanningFlowProvider></UiVersionProvider></LanguageProvider>
  </SafeAreaProvider>;
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
beforeEach(() => {
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  jest.useFakeTimers({ now: new Date('2026-10-05T12:00:00Z'), doNotFake: ['hrtime', 'nextTick', 'performance', 'queueMicrotask', 'requestAnimationFrame', 'cancelAnimationFrame', 'requestIdleCallback', 'cancelIdleCallback', 'setImmediate', 'clearImmediate', 'setInterval', 'clearInterval', 'setTimeout', 'clearTimeout'] });
  process.env.EXPO_PUBLIC_UI_VERSION = 'v2';
  stored = new Map([['start23.latest-plan-id', activePlan.id], ['start23.language-preference', 'en']]);
  server = new Map([[activePlan.id, activePlan]]);
  jest.mocked(SecureStore.getItemAsync).mockImplementation(async key => stored.get(key) ?? null);
  jest.mocked(SecureStore.setItemAsync).mockImplementation(async (key, value) => { stored.set(key, value); });
  jest.mocked(SecureStore.deleteItemAsync).mockImplementation(async key => { stored.delete(key); });
  jest.mocked(api.getOnboarding).mockResolvedValue(onboarding);
  jest.mocked(api.getWeeklyPlan).mockImplementation(async (_token, id) => {
    const plan = server.get(id); if (!plan) throw new Error('Unknown synthetic plan'); return plan;
  });
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, rest_days: [], workouts: [...server.values()].filter(plan => plan.revision_state === 'active').flatMap(plan => plan.workouts).filter(item => item.scheduled_date >= from && item.scheduled_date < to) }));
  jest.mocked(api.startWeeklyCheckIn).mockResolvedValue({ ...savedCheckIn, week_start: pendingNext.week_start, context: { ...savedCheckIn.context!, state: 'confirmed' } });
  jest.mocked(api.getInjuryRestrictions).mockResolvedValue([]);
  jest.mocked(api.createCheckInPlanProposal).mockImplementation(async () => { server.set(pendingNext.id, pendingNext); return { plan: pendingNext, proposal: nextProposal }; });
  jest.mocked(api.approvePlanProposal).mockImplementation(async (_token, id, base) => {
    expect(id).toBe(nextProposal.id); expect(base).toBe(0);
    server.set(approvedNext.id, approvedNext);
    return { state: 'applied', plan_id: approvedNext.id, active_revision: approvedNext.revision };
  });
});
afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); delete process.env.EXPO_PUBLIC_UI_VERSION; });

async function generated() {
  const view = await render(<Host />);
  await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('button', { name: /check-in/i }));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Klaar voor het voorstel');
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await view.findByText('Voorstel voor ' + pendingNext.week_start);
  return view;
}

test('WOMBO-005: explicit check-in approval replaces the retained old Week and remembered identity', async () => {
  const view = await generated();
  expect(flow.activePlan).toBe(activePlan);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  expect(server.get(pendingNext.id)).toBe(approvedNext);
  await view.findByText(nextWorkout.name);
  expect(flow.plan).toBe(approvedNext);
  expect(flow.activePlan).toBe(approvedNext);
  expect(stored.get('start23.latest-plan-id')).toBe(approvedNext.id);
  expect(flow.plan?.workouts.map(item => item.id)).toEqual(['next-workout-1', 'next-workout-2']);
  expect(flow.plan?.revision_id).toBe('next-revision-1');
  expect(flow.plan?.revision).toBe(1);
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  await view.findByText('Training calendar');
  await view.findByText(nextWorkout.name);
  expect(calendar.calendarWorkouts.map(item => item.id)).toEqual(['next-workout-1', 'next-workout-2']);
  await waitFor(() => expect(api.getWeeklyPlan).toHaveBeenCalledWith('token-a', approvedNext.id, 1));
  await view.unmount();
  const restarted = await render(<Host />);
  await restarted.findByText(nextWorkout.name);
  expect(flow.activePlan).toBe(approvedNext);
  expect(api.getWeeklyPlan).toHaveBeenLastCalledWith('token-a', approvedNext.id);
});

test('pending next week remains distinct through navigation away and back; no locator or Calendar mutation', async () => {
  const view = await generated();
  expect(flow.plan).toBe(activePlan); expect(flow.activePlan).toBe(activePlan);
  expect(flow.taskHandoff?.plan).toBe(pendingNext);
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
  expect(api.getCalendar).not.toHaveBeenCalled();
  await fireEvent.press(view.getByRole('button', { name: 'Later beslissen' }));
  await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('button', { name: /check-in/i }));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Voorstel voor ' + pendingNext.week_start);
  expect(api.createCheckInPlanProposal).toHaveBeenCalledTimes(1);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  expect(view.queryByRole('button', { name: 'Maak planvoorstel' })).toBeNull();
});

test('failed generation preserves the active week and exact confirmed A3 context', async () => {
  jest.mocked(api.createCheckInPlanProposal).mockRejectedValue(new Error('No valid planning result'));
  const view = await render(<Host />); await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('button', { name: /check-in/i }));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Klaar voor het voorstel');
  await view.findByText(/physician: Arts: lopen geblokkeerd tot herbeoordeling\./);
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await view.findByText('No valid planning result');
  expect(api.createCheckInPlanProposal).toHaveBeenCalledWith('token-a', savedCheckIn.id);
  expect(api.saveWeeklyCheckInContext).not.toHaveBeenCalled();
  expect(flow.plan).toBe(activePlan); expect(flow.taskHandoff).toBeNull();
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
});

test.each([409, 422])('rejected/stale approval (%i) cannot publish a new active revision', async status => {
  const view = await generated();
  jest.mocked(api.approvePlanProposal).mockRejectedValue(Object.assign(new Error('Proposal unavailable'), { status }));
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText('Proposal unavailable');
  expect(flow.plan).toBe(activePlan); expect(flow.taskHandoff?.phase).toBe('pending');
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
  expect(api.getWeeklyPlan).not.toHaveBeenCalledWith('token-a', pendingNext.id, 1);
});

test('known approval success survives a failed follow-up read; recovery reads the exact revision without another POST', async () => {
  const view = await generated();
  jest.mocked(api.getWeeklyPlan).mockRejectedValueOnce(new Error('Read unavailable'));
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText('Read unavailable');
  expect(flow.taskHandoff?.receipt).toEqual({ state: 'applied', plan_id: pendingNext.id, active_revision: 1 });
  expect(flow.taskHandoff?.phase).toBe('read'); expect(flow.plan).toBe(activePlan);
  await fireEvent.press(view.getByRole('button', { name: 'Synchronisatie hervatten' }));
  await view.findByText(nextWorkout.name);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  expect(api.getWeeklyPlan).toHaveBeenLastCalledWith('token-a', pendingNext.id, 1);
});

test('local persistence failure keeps authoritative success; only storage is retried', async () => {
  const view = await generated();
  jest.mocked(SecureStore.setItemAsync).mockRejectedValueOnce(new Error('Storage unavailable'));
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText('Storage unavailable');
  expect(flow.activePlan).toBe(approvedNext); expect(flow.taskHandoff?.phase).toBe('persist');
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
  const reads = jest.mocked(api.getWeeklyPlan).mock.calls.length;
  await fireEvent.press(view.getByRole('button', { name: 'Synchronisatie hervatten' }));
  await view.findByText(nextWorkout.name);
  expect(api.getWeeklyPlan).toHaveBeenCalledTimes(reads);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  expect(stored.get('start23.latest-plan-id')).toBe(approvedNext.id);
});

test.each([true, false])('ambiguous approval checks server status before another decision (committed=%s)', async committed => {
  const view = await generated();
  jest.mocked(api.approvePlanProposal).mockImplementationOnce(async () => {
    if (committed) server.set(approvedNext.id, approvedNext);
    throw new Error('Connection lost');
  });
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText('Connection lost');
  expect(flow.taskHandoff?.phase).toBe('verify');
  await fireEvent.press(view.getByRole('button', { name: 'Goedkeuringsstatus controleren' }));
  if (committed) { await view.findByText(nextWorkout.name); expect(flow.activePlan).toBe(approvedNext); }
  else { await view.findByRole('button', { name: 'Voorstel goedkeuren' }); expect(flow.plan).toBe(activePlan); }
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
});

test.each(['receipt', 'snapshot'] as const)('conflicting %s cannot switch to an unreviewed revision', async conflict => {
  const view = await generated();
  if (conflict === 'receipt') jest.mocked(api.approvePlanProposal).mockResolvedValue({ state: 'applied', plan_id: 'wrong-plan', active_revision: 2 });
  else jest.mocked(api.getWeeklyPlan).mockResolvedValueOnce({ ...approvedNext, revision: 2, revision_id: 'unreviewed' });
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await waitFor(() => expect(flow.busy).toBe(false));
  expect(flow.plan).toBe(activePlan); expect(flow.taskHandoff?.phase).toBe('read');
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
  expect(view.getByRole('button', { name: 'Synchronisatie hervatten' })).toBeTruthy();
});

test('same-tick duplicate approval is locked, and completion survives leaving the screen', async () => {
  const view = await generated();
  const response = deferred<Awaited<ReturnType<typeof api.approvePlanProposal>>>();
  jest.mocked(api.approvePlanProposal).mockReturnValue(response.promise);
  let first!: Promise<boolean>, second!: Promise<unknown>;
  await act(() => {
    first = flow.approveTaskPlan(`check-in:${savedCheckIn.id}`, pendingNext);
    second = flow.approveTaskPlan(`check-in:${savedCheckIn.id}`, pendingNext).catch(error => error);
  });
  expect(await second).toBeInstanceOf(Error);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'Later beslissen' }));
  server.set(approvedNext.id, approvedNext);
  await act(async () => { response.resolve({ state: 'applied', plan_id: approvedNext.id, active_revision: 1 }); await first; });
  await view.findByText(nextWorkout.name);
  expect(flow.taskHandoff?.phase).toBe('complete');
  expect(stored.get('start23.latest-plan-id')).toBe(approvedNext.id);
});

test('a delayed Calendar read cannot restore obsolete next-week rows after approval', async () => {
  const view = await generated();
  const range = { from_date: '2026-10-05', to_date: '2026-10-19', workouts: [workout], rest_days: [] };
  jest.mocked(api.getCalendar).mockResolvedValueOnce(range);
  await act(() => calendar.loadCalendarRange(range.from_date, range.to_date));
  const late = deferred<CalendarResponse>();
  jest.mocked(api.getCalendar).mockReturnValueOnce(late.promise);
  await act(() => calendar.loadCalendarRange(range.from_date, range.to_date));
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText(nextWorkout.name);
  await act(() => late.resolve(range));
  expect(calendar.calendarWorkouts.map(item => item.id)).toEqual([workout.id, 'next-workout-1', 'next-workout-2']);
  expect(flow.activePlan).toBe(approvedNext);
});

test('athlete replacement ignores the previous owner follow-up response and cannot overwrite the new locator', async () => {
  const view = await generated();
  const response = deferred<WeeklyPlan>();
  jest.mocked(api.getWeeklyPlan).mockReturnValueOnce(response.promise);
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  expect(flow.taskHandoff?.phase).toBe('read');
  const otherPlan: WeeklyPlan = { ...activePlan, id: 'athlete-b-plan', workouts: [] };
  stored.set('start23.latest-plan-id', otherPlan.id); server.set(otherPlan.id, otherPlan);
  await view.rerender(<Host identity="athlete-b" />);
  await waitFor(() => expect(flow.plan).toBe(otherPlan));
  await act(() => response.resolve(approvedNext));
  expect(flow.plan).toBe(otherPlan); expect(flow.taskHandoff).toBeNull();
  expect(stored.get('start23.latest-plan-id')).toBe(otherPlan.id);
});

test.each(['success', 'failure'] as const)('an old resume %s cannot overwrite a completed task handoff or its locator', async outcome => {
  const view = await generated();
  const late = deferred<WeeklyPlan>();
  jest.mocked(api.getWeeklyPlan).mockReturnValueOnce(late.promise);
  await view.rerender(<Host token="refreshed-token" />);
  await waitFor(() => expect(api.getWeeklyPlan).toHaveBeenCalledWith('refreshed-token', activePlan.id));
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText(nextWorkout.name);
  await act(() => { if (outcome === 'success') late.resolve(activePlan); else late.reject(new Error('Old read failed')); });
  expect(flow.activePlan).toBe(approvedNext); expect(flow.resumeState).toBe('ready');
  expect(stored.get('start23.latest-plan-id')).toBe(approvedNext.id);
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalledWith('start23.latest-plan-id');
});

test('an already-issued old-owner storage write finishes before the new owner locator, without an old-owner draft deletion', async () => {
  const view = await generated();
  const writing = deferred<void>();
  jest.mocked(SecureStore.setItemAsync).mockImplementationOnce(async (key, value) => { await writing.promise; stored.set(key, value); });
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  expect(flow.activePlan).toBe(approvedNext); expect(flow.taskHandoff?.phase).toBe('persist');
  stored.delete('start23.latest-plan-id');
  await view.rerender(<Host identity="athlete-b" token="token-b" />);
  await waitFor(() => expect(flow.taskHandoff).toBeNull());
  const otherPlan: WeeklyPlan = { ...approvedNext, id: 'athlete-b-plan', workouts: [] };
  let completion!: Promise<boolean>;
  await act(() => { completion = flow.receiveTaskPlan('support:athlete-b', otherPlan); });
  await act(async () => { writing.resolve(); await completion; });
  expect(flow.activePlan).toBe(otherPlan);
  expect(stored.get('start23.latest-plan-id')).toBe(otherPlan.id);
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledTimes(1);
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('start23.latest-swipe-draft-id');
});

test('generation that finishes after navigation still retains the exact pending proposal in the shared owner', async () => {
  const response = deferred<Awaited<ReturnType<typeof api.createCheckInPlanProposal>>>();
  jest.mocked(api.createCheckInPlanProposal).mockReturnValue(response.promise);
  const view = await render(<Host />); await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('button', { name: /check-in/i }));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Klaar voor het voorstel');
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await fireEvent.press(view.getByRole('button', { name: 'Weekplanning' }));
  await act(() => response.resolve({ plan: pendingNext, proposal: nextProposal }));
  expect(flow.taskHandoff?.reviewed).toBe(pendingNext); expect(flow.activePlan).toBe(activePlan);
  expect(stored.get('start23.latest-plan-id')).toBe(activePlan.id);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('a task cannot stage a proposal targeting another revision', async () => {
  const view = await render(<Host />); await view.findByText(workout.name);
  await act(async () => {
    await expect(flow.receiveTaskPlan('invalid-task', { ...pendingNext, proposal: { ...nextProposal, target_plan_revision_id: 'another-revision' } })).rejects.toThrow('planrevisie');
  });
  expect(flow.taskHandoff).toBeNull(); expect(flow.activePlan).toBe(activePlan);
});

test('the same handoff accepts an already-authoritative task result without reapproval or a pending downgrade', async () => {
  await generated();
  await act(async () => { await flow.receiveTaskPlan(`check-in:${savedCheckIn.id}`, approvedNext); });
  expect(flow.plan).toBe(approvedNext); expect(flow.taskHandoff?.reviewed).toBe(pendingNext);
  expect(flow.taskHandoff?.phase).toBe('complete');
  expect(stored.get('start23.latest-plan-id')).toBe(approvedNext.id);
  await act(async () => { await flow.receiveTaskPlan(`check-in:${savedCheckIn.id}`, pendingNext); });
  expect(flow.plan).toBe(approvedNext); expect(flow.taskHandoff?.plan).toBe(approvedNext);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});


function recoveryServer({ loseFirst = false }: { loseFirst?: boolean } = {}) {
  let generatedCount = 0;
  let attached = false;
  let first = true;
  jest.mocked(api.startWeeklyCheckIn).mockImplementation(async () => ({
    ...savedCheckIn, week_start: pendingNext.week_start,
    status: attached ? 'completed' : 'open', plan_proposal_id: attached ? nextProposal.id : null,
    context: { ...savedCheckIn.context!, state: 'confirmed' },
  }));
  jest.mocked(api.createCheckInPlanProposal).mockImplementation(async (token, id) => {
    expect(token).toBe('token-a'); expect(id).toBe(savedCheckIn.id);
    if (!attached) { generatedCount++; attached = true; server.set(pendingNext.id, pendingNext); }
    const plan = server.get(pendingNext.id)!;
    if (first && loseFirst) { first = false; throw new Error('Response lost after commit'); }
    // get_weekly_plan includes the proposal for its exact revision, even terminal.
    return { plan, proposal: plan.proposal! };
  });
  return { count: () => generatedCount, attach: (plan: WeeklyPlan) => { attached = true; server.set(plan.id, plan); } };
}
async function openCheckin(view: Awaited<ReturnType<typeof render>>) {
  await view.findByText(workout.name);
  await fireEvent.press(view.getByRole('button', { name: /check-in/i }));
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
}

test.each([false, true])('A5 commit/response loss recovers exact pending proposal (restart=%s), then A4 updates Week/Calendar', async restart => {
  const persisted = recoveryServer({ loseFirst: true });
  let view = await render(<Host />); await openCheckin(view);
  await view.findByText('Klaar voor het voorstel');
  await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' }));
  await view.findByText('Response lost after commit');
  expect(server.get(pendingNext.id)).toBe(pendingNext);
  expect(flow.activePlan).toBe(activePlan); expect(api.approvePlanProposal).not.toHaveBeenCalled();
  if (restart) { await view.unmount(); view = await render(<Host />); await openCheckin(view); }
  else { await fireEvent.press(view.getByRole('button', { name: 'Maak planvoorstel' })); }
  await view.findByText('Voorstel voor ' + pendingNext.week_start);
  expect(flow.taskHandoff?.plan).toBe(pendingNext);
  expect(flow.taskHandoff?.reviewed.proposal).toEqual(nextProposal);
  expect(flow.taskHandoff?.plan.workouts.map(item => item.id)).toEqual(['next-workout-1', 'next-workout-2']);
  expect(persisted.count()).toBe(1); expect(flow.activePlan).toBe(activePlan);
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel goedkeuren' }));
  await view.findByText(nextWorkout.name);
  expect(server.get(pendingNext.id)).toBe(approvedNext);
  expect(flow.activePlan).toBe(approvedNext);
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  await view.findByText('Training calendar'); await view.findByText(nextWorkout.name);
  expect(calendar.calendarWorkouts.map(item => item.id)).toEqual(['next-workout-1', 'next-workout-2']);
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1); expect(persisted.count()).toBe(1);
});

test('A5 restart recovers an already applied attachment without approving again', async () => {
  const persisted = recoveryServer(); persisted.attach(approvedNext);
  const view = await render(<Host />); await openCheckin(view);
  await view.findByText('Goedkeuring ontvangen');
  expect(flow.activePlan).toBe(approvedNext); expect(flow.taskHandoff?.phase).toBe('complete');
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(persisted.count()).toBe(0);
});

test.each(['rejected', 'expired', 'superseded'] as const)('A5 authoritative %s clears retained pending review and cannot be revived', async state => {
  const persisted = recoveryServer(); const view = await generated();
  const terminal: WeeklyPlan = { ...pendingNext, revision_state: state, proposal: { ...nextProposal, state: state === 'superseded' ? 'applied' : state } };
  persisted.attach(terminal);
  await fireEvent.press(view.getByRole('button', { name: 'Later beslissen' }));
  await openCheckin(view);
  await view.findByText('Voorstel afgesloten');
  expect(flow.taskHandoff).toBeNull(); expect(flow.activePlan).toBe(activePlan);
  expect(view.queryByRole('button', { name: 'Voorstel goedkeuren' })).toBeNull();
  expect(view.queryByRole('button', { name: 'Maak planvoorstel' })).toBeNull();
  expect(server.get(pendingNext.id)).toBe(terminal); expect(persisted.count()).toBe(1);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('A5 recovered proposal can be explicitly rejected without activating it', async () => {
  const persisted = recoveryServer(); persisted.attach(pendingNext);
  jest.mocked(api.rejectPlanProposal).mockImplementation(async (_token, id) => {
    expect(id).toBe(nextProposal.id);
    const rejected: WeeklyPlan = { ...pendingNext, revision_state: 'rejected', proposal: { ...nextProposal, state: 'rejected' } };
    server.set(rejected.id, rejected);
    return { state: 'rejected', plan_id: rejected.id, active_revision: null };
  });
  const view = await render(<Host />); await openCheckin(view);
  await view.findByText('Wacht op jouw goedkeuring');
  await fireEvent.press(view.getByRole('button', { name: 'Voorstel afwijzen' }));
  await view.findByText('Voorstel afgesloten');
  expect(server.get(pendingNext.id)?.proposal?.state).toBe('rejected');
  expect(flow.activePlan).toBe(activePlan); expect(flow.taskHandoff).toBeNull();
  expect(api.approvePlanProposal).not.toHaveBeenCalled(); expect(persisted.count()).toBe(0);
});

test.each(['replace', 'signout'] as const)('A5 late recovery cannot publish after account %s', async action => {
  const persisted = recoveryServer(); persisted.attach(pendingNext);
  const response = deferred<Awaited<ReturnType<typeof api.createCheckInPlanProposal>>>();
  jest.mocked(api.createCheckInPlanProposal).mockReturnValue(response.promise);
  const view = await render(<Host />); await openCheckin(view);
  await waitFor(() => expect(api.createCheckInPlanProposal).toHaveBeenCalledTimes(1));
  if (action === 'signout') await view.unmount();
  else { stored.delete('start23.latest-plan-id'); await view.rerender(<Host identity="athlete-b" token="token-b" />); }
  await act(() => response.resolve({ plan: pendingNext, proposal: nextProposal }));
  if (action === 'replace') expect(flow.taskHandoff).toBeNull();
  expect(stored.get('start23.latest-plan-id')).not.toBe(pendingNext.id);
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
});

test('A5 failed recovery keeps review unavailable and permits explicit reload', async () => {
  const persisted = recoveryServer(); persisted.attach(pendingNext);
  jest.mocked(api.createCheckInPlanProposal).mockRejectedValueOnce(new Error('Recovery unavailable'));
  const view = await render(<Host />); await openCheckin(view);
  await view.findByText('Recovery unavailable');
  expect(flow.taskHandoff).toBeNull(); expect(flow.activePlan).toBe(activePlan);
  await fireEvent.press(view.getByRole('button', { name: 'Start check-in' }));
  await view.findByText('Wacht op jouw goedkeuring');
  expect(flow.taskHandoff?.plan).toBe(pendingNext); expect(persisted.count()).toBe(0);
});
