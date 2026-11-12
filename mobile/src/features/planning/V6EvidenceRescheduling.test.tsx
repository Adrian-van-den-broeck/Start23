import { act, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import * as api from '../../api/client';
import type { WeeklyPlan } from '../../api/types';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { activityWorkoutId } from '../activities/activityCreateInput';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from './PlanningFlowProvider';
import traceJson from './v6-evidence-http.test-fixture.json';

// Actual FastAPI + PostgreSQL public outputs. Sessions, storage and transport
// are simulated in these component/controller tests; this is not a device test.
const trace = traceJson as unknown as {
  before: WeeklyPlan; after: WeeklyPlan; multipleCompleted: WeeklyPlan;
  latest: WeeklyPlan; calendar: Awaited<ReturnType<typeof api.getCalendar>>;
};
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../../api/client');
let flow: ReturnType<typeof usePlanningFlow>;
let calendar: ReturnType<typeof usePlanningCalendar>;
function Probe() { flow = usePlanningFlow(); calendar = usePlanningCalendar(); return null; }
function Host() {
  return <LanguageProvider><PlanningFlowProvider accessToken="local-token" athleteIdentity="local-subject"><Probe /></PlanningFlowProvider></LanguageProvider>;
}
beforeEach(() => {
  jest.clearAllMocks();
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  jest.mocked(api.getOnboarding).mockResolvedValue({ primary_goal: null } as never);
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: trace.before, pending: null, draft: null });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.before);
  jest.mocked(api.validatePlanLayout).mockResolvedValue({ valid_for_generated_schedule: true, warnings: [] });
});
const workout = trace.before.workouts.find(w => w.discipline === 'bike')!;
const moved = trace.after.workouts.find(w => w.id === workout.id)!;

async function loaded() {
  const view = await render(<Host />);
  await waitFor(() => expect(flow.resumeState).toBe('ready'));
  expect(flow.plan).toBe(trace.before);
  return view;
}

test('confirmed V6 date move replaces active calendar and keeps exact source and occurrence mapping', async () => {
  await loaded();
  jest.mocked(api.getCalendar).mockResolvedValue({ ...trace.calendar, workouts: trace.before.workouts });
  await act(async () => { calendar.ensureCalendarRange('2026-10-26', '2026-11-02'); });
  await waitFor(() => expect(calendar.calendarWorkouts).toEqual(trace.before.workouts));
  jest.mocked(api.movePlannedWorkout).mockResolvedValue(trace.after);
  await act(async () => { flow.requestWorkoutMove(workout, moved.scheduled_date); });
  await waitFor(() => expect(flow.activePlan).toBe(trace.after));
  expect(api.movePlannedWorkout).toHaveBeenCalledWith('local-token', workout.physical_workout_id, trace.before.revision, moved.scheduled_date);
  expect(calendar.calendarWorkouts.find(w => w.id === workout.id)?.scheduled_date).toBe(moved.scheduled_date);
  expect(calendar.calendarWorkouts.filter(w => w.id === workout.id && w.scheduled_date === workout.scheduled_date)).toEqual([]);
  expect(moved.id).toBe(workout.id);
  expect(moved.physical_workout_id).not.toBe(workout.physical_workout_id);
  expect(moved.source_prescription).toEqual(workout.source_prescription);
  expect(activityWorkoutId(moved)).toBe(moved.physical_workout_id);
  for (const original of trace.before.workouts.filter(w => w.id !== workout.id)) {
    const retained = flow.activePlan!.workouts.find(w => w.id === original.id)!;
    expect(retained.physical_workout_id).toBe(original.physical_workout_id);
    expect(retained.status).toBe(original.status);
    expect(retained.scheduled_date).toBe(original.scheduled_date);
    expect(retained.source_prescription).toEqual(original.source_prescription);
  }
  const completed = trace.before.workouts.find(w => w.status === 'completed')!;
  expect(calendar.calendarWorkouts.filter(w => w.id === completed.id)).toHaveLength(1);
  expect(activityWorkoutId(completed)).toBe(completed.physical_workout_id);
});

test('restart discovers latest confirmed mapping while preserving pending distinction', async () => {
  const view = await loaded();
  await view.unmount();
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: trace.multipleCompleted, pending: null, draft: null });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.multipleCompleted);
  await render(<Host />);
  await waitFor(() => expect(flow.activePlan).toBe(trace.multipleCompleted));
  expect(flow.plan?.revision_state).toBe('active');
  expect(trace.multipleCompleted.workouts.filter(w => w.status === 'completed')).toHaveLength(2);
  expect(flow.plan?.workouts.find(w => w.id === moved.id)?.physical_workout_id).toBe(moved.physical_workout_id);
  jest.mocked(api.getCalendar).mockResolvedValue(trace.calendar);
  await act(async () => { calendar.ensureCalendarRange('2026-10-26', '2026-11-02'); });
  await waitFor(() => expect(calendar.calendarWorkouts).toEqual(trace.calendar.workouts));
  expect(calendar.calendarWorkouts).toHaveLength(3);
  expect(new Set(calendar.calendarWorkouts.map(w => w.id)).size).toBe(3);
  expect(calendar.calendarWorkouts.filter(w => w.status === 'completed')).toHaveLength(2);
});

test('move conflict retains reviewed revision and exposes the reload message', async () => {
  await loaded();
  jest.mocked(api.movePlannedWorkout).mockRejectedValue(Object.assign(new Error('De weekplanning is gewijzigd. Vernieuw de planning.'), { status: 409 }));
  await act(async () => { flow.requestWorkoutMove(workout, moved.scheduled_date); });
  await waitFor(() => expect(flow.busy).toBe(false));
  expect(flow.plan).toBe(trace.before);
  expect(flow.error).toContain('Vernieuw');
  expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
});

test('lost acknowledgement reloads authoritative confirmed result without another move', async () => {
  await loaded();
  jest.mocked(api.movePlannedWorkout).mockRejectedValue(Object.assign(new Error('Connection lost'), { outcome: 'unknown' }));
  await act(async () => { flow.requestWorkoutMove(workout, moved.scheduled_date); });
  await waitFor(() => expect(flow.busy).toBe(false));
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.after);
  await act(async () => { flow.requestWorkoutMove(workout, moved.scheduled_date); });
  await waitFor(() => expect(flow.activePlan).toBe(trace.after));
  expect(api.movePlannedWorkout).toHaveBeenCalledTimes(1);
  expect(flow.error).toContain('Controleer de opgeslagen planning');
});
