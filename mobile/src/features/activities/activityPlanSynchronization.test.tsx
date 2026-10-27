import { act, render, waitFor } from '@testing-library/react-native';
import { useEffect } from 'react';
import * as api from '../../api/client';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from '../planning/PlanningFlowProvider';
import { activePlan, onboarding } from '../planning/planning.test-fixtures';
import { approvedNext, pendingNext } from '../planning/planningTask.test-fixtures';
import { ActivityFlowProvider, useActivityFlow } from './ActivityFlowProvider';
import { activityOnboarding } from './activities.test-fixtures';

jest.mock('../../api/client');
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => null), setItemAsync: jest.fn(async () => undefined), deleteItemAsync: jest.fn(async () => undefined) }));
let activity: ReturnType<typeof useActivityFlow>;
let planning: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
let serverWorkouts = activePlan.workouts;
let discovered = activePlan;
function Probe({ focused }: { focused: boolean }) {
  activity = useActivityFlow(); planning = usePlanningFlow(); calendar = usePlanningCalendar();
  useEffect(() => { activity.setActivitiesFocused(focused); return () => activity.setActivitiesFocused(false); }, [focused, activity.setActivitiesFocused]);
  return null;
}
function Host({ focused = true }: { focused?: boolean }) {
  return <LanguageProvider><ActivityFlowProvider accessToken="token-a" athleteIdentity="athlete-a">
    <PlanningFlowProvider accessToken="token-a" athleteIdentity="athlete-a" initialOnboarding={onboarding}>
      <Probe focused={focused} />
    </PlanningFlowProvider>
  </ActivityFlowProvider></LanguageProvider>;
}
beforeEach(() => {
  jest.useFakeTimers({ now: new Date('2026-10-06T12:00:00Z'), doNotFake: [
    'hrtime', 'nextTick', 'performance', 'queueMicrotask', 'requestAnimationFrame', 'cancelAnimationFrame',
    'requestIdleCallback', 'cancelIdleCallback', 'setImmediate', 'clearImmediate', 'setInterval', 'clearInterval', 'setTimeout', 'clearTimeout',
  ] });
  jest.clearAllMocks();
  for (const method of Object.values(api).filter(jest.isMockFunction)) method.mockReset();
  serverWorkouts = activePlan.workouts; discovered = activePlan;
  jest.mocked(api.listActivities).mockResolvedValue([]);
  jest.mocked(api.listPlannedExternalActivities).mockResolvedValue([]);
  jest.mocked(api.getOnboarding).mockResolvedValue(activityOnboarding);
  jest.mocked(api.discoverPlanning).mockImplementation(async () => ({ active: discovered, pending: null, draft: null }));
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(approvedNext);
  jest.mocked(api.getCalendar).mockImplementation(async (_token, from, to) => ({ from_date: from, to_date: to, workouts: serverWorkouts, rest_days: [] }));
  jest.mocked(api.approvePlanProposal).mockImplementation(async () => {
    serverWorkouts = approvedNext.workouts; discovered = approvedNext;
    return { state: 'applied', plan_id: approvedNext.id, active_revision: approvedNext.revision };
  });
});

test.each(['handoff', 'remote discovery'])('%s invalidates activity choices through the retained Planning owner', async trigger => {
  await render(<Host />);
  await waitFor(() => expect(planning.plan).toBe(activePlan));
  await waitFor(() => expect(activity.workouts).toEqual(activePlan.workouts));
  const owners = [activity.ensureActivitiesLoaded, planning.setWeekStart, calendar.loadCalendarRange];
  await act(() => activity.setDuration('58'));
  if (trigger === 'handoff') {
    await act(async () => { await planning.receiveTaskPlan('check-in:exact-checkin', pendingNext); });
    expect(activity.workouts).toEqual(activePlan.workouts); expect(api.getCalendar).toHaveBeenCalledTimes(1);
    await act(async () => { await planning.approveTaskPlan('check-in:exact-checkin', pendingNext); });
    expect(api.approvePlanProposal).toHaveBeenCalledWith('token-a', pendingNext.proposal!.id, 0);
    expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
  } else {
    serverWorkouts = approvedNext.workouts; discovered = approvedNext;
    await act(() => planning.retryResume());
    expect(api.approvePlanProposal).not.toHaveBeenCalled();
  }
  await waitFor(() => expect(activity.workouts).toEqual(approvedNext.workouts));
  expect(activity.workouts.map(row => row.id)).toEqual(['next-workout-1', 'next-workout-2']);
  expect(activity.duration).toBe('58'); expect(planning.activePlan).toBe(approvedNext);
  expect([activity.ensureActivitiesLoaded, planning.setWeekStart, calendar.loadCalendarRange]).toEqual(owners);
  expect(api.getCalendar).toHaveBeenCalledTimes(2);
  expect(api.createActivity).not.toHaveBeenCalled();
});

afterEach(() => jest.useRealTimers());

test('approved task while Activities is away marks context stale and refreshes on focus without clearing its form', async () => {
  const view = await render(<Host />);
  await waitFor(() => expect(activity.workouts).toEqual(activePlan.workouts));
  await waitFor(() => expect(planning.plan).toBe(activePlan));
  await act(() => { activity.setDistance('8000'); activity.setDuration('53'); });
  await view.rerender(<Host focused={false} />);
  await act(async () => { await planning.receiveTaskPlan('check-in:exact-checkin', pendingNext); });
  await act(async () => { await planning.approveTaskPlan('check-in:exact-checkin', pendingNext); });
  expect(api.getCalendar).toHaveBeenCalledTimes(1);
  await view.rerender(<Host />);
  await waitFor(() => expect(activity.workouts).toEqual(approvedNext.workouts));
  expect(activity.distance).toBe('8000'); expect(activity.duration).toBe('53');
  expect(api.getCalendar).toHaveBeenCalledTimes(2);
});
