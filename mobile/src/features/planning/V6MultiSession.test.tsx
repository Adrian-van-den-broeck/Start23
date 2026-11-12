import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import * as api from '../../api/client';
import type { WeeklyPlan } from '../../api/types';
import { TrainingCalendar } from '../../components/TrainingCalendar';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { activityWorkoutId } from '../activities/activityCreateInput';
import { PlanningFlowProvider, usePlanningCalendar, usePlanningFlow } from './PlanningFlowProvider';
import fixture from './v6-multi-session-http.test-fixture.json';

// Actual local FastAPI/PostgreSQL public outputs, TEST_ONLY frequency authority.
// Transport, sessions and secure storage are simulated; no device claim.
const trace = fixture as unknown as {
  checkinPending: WeeklyPlan; swiped: WeeklyPlan; active: WeeklyPlan;
  before: WeeklyPlan; after: WeeklyPlan; latest: WeeklyPlan;
  calendar: Awaited<ReturnType<typeof api.getCalendar>>;
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

test('calendar renders five repeated-sport occurrences and opens each exact physical activity target', async () => {
  const opened = jest.fn();
  const view = await render(<LanguageProvider><TrainingCalendar initialDate="2026-10-26" loading={false}
    onRangeChange={jest.fn()} onOpenWorkout={opened} restDays={trace.calendar.rest_days} workouts={trace.calendar.workouts} /></LanguageProvider>);
  for (const name of new Set(trace.calendar.workouts.map(w => w.name))) {
    expect(view.getAllByText(name)).toHaveLength(trace.calendar.workouts.filter(w => w.name === name).length);
  }
  for (const name of new Set(trace.calendar.workouts.map(w => w.name))) {
    for (const card of view.getAllByText(name)) await fireEvent.press(card);
  }
  expect(opened).toHaveBeenCalledTimes(5);
  expect(new Set(opened.mock.calls.map(([workout]) => activityWorkoutId(workout))).size).toBe(5);
  expect(trace.calendar.workouts.filter(w => w.discipline === 'run')).toHaveLength(2);
  expect(trace.calendar.workouts.filter(w => w.discipline === 'bike')).toHaveLength(2);
  expect(JSON.stringify(view.toJSON())).not.toMatch(/tss|planned_load|realized_load/i);
});

test('moving unfinished RUN-B preserves completed RUN-A, dates, source and activity mapping', async () => {
  await render(<Host />);
  await waitFor(() => expect(flow.activePlan).toBe(trace.before));
  const completed = trace.before.workouts.find(w => w.discipline === 'run' && w.status === 'completed')!;
  const target = trace.before.workouts.find(w => w.discipline === 'run' && w.status === 'scheduled')!;
  const moved = trace.after.workouts.find(w => w.id === target.id)!;
  jest.mocked(api.getCalendar).mockResolvedValue({ ...trace.calendar, workouts: trace.before.workouts });
  await act(async () => { calendar.ensureCalendarRange('2026-10-26', '2026-11-02'); });
  await waitFor(() => expect(calendar.calendarWorkouts).toHaveLength(5));
  jest.mocked(api.movePlannedWorkout).mockResolvedValue(trace.after);
  await act(async () => { flow.requestWorkoutMove(target, moved.scheduled_date); });
  await waitFor(() => expect(flow.activePlan).toBe(trace.after));
  expect(api.movePlannedWorkout).toHaveBeenCalledWith('local-token', target.physical_workout_id, trace.before.revision, moved.scheduled_date);
  expect(flow.activePlan!.workouts.find(w => w.id === completed.id)).toEqual(completed);
  expect(activityWorkoutId(moved)).toBe(moved.physical_workout_id);
  expect(activityWorkoutId(moved)).not.toBe(target.physical_workout_id);
  expect(moved.source_prescription).toEqual(target.source_prescription);
  expect(calendar.calendarWorkouts.filter(w => w.id === target.id)).toHaveLength(1);
});

test('pending duplicate templates keep distinct IDs and remain separate from the active week on resume', async () => {
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: null, pending: trace.checkinPending, draft: null });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.checkinPending);
  const view = await render(<Host />);
  await waitFor(() => expect(flow.plan).toBe(trace.checkinPending));
  const runs = flow.plan!.workouts.filter(w => w.discipline === 'run');
  expect(runs).toHaveLength(2);
  expect(runs[0].template_id).toBe(runs[1].template_id);
  expect(runs[0].id).not.toBe(runs[1].id);
  expect(activityWorkoutId(runs[0])).not.toBe(activityWorkoutId(runs[1]));
  expect(flow.activePlan).toBeNull();
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  await view.unmount();
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: trace.latest, pending: null, draft: null });
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.latest);
  await render(<Host />);
  await waitFor(() => expect(flow.activePlan).toBe(trace.latest));
  expect(flow.activePlan!.workouts).toHaveLength(5);
  expect(new Set(flow.activePlan!.workouts.map(w => w.id)).size).toBe(5);
});
