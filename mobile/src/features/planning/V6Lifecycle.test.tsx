import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import * as api from '../../api/client';
import type { PendingWorkoutAlternatives, SwipeWeekDraft, WeeklyPlan, WorkoutDeckItem } from '../../api/types';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { SelectionScreen } from '../../ui-v2/screens/PlanningCreationScreens';
import { WorkoutDetailScreen } from '../../ui-v2/screens/WorkoutDetailScreen';
import { planningCreationViewModel } from '../../ui-v2/utils/planningCreationViewModel';
import { sourceBlocksViewModel, workoutDetailViewModel } from '../../ui-v2/utils/workoutDetailViewModel';
import { SessionSequence } from '../../ui-v2/components/SessionSequence';
import { calendarViewModel } from '../../ui-v2/utils/calendarViewModel';
import { activityCreateInput, activityWorkoutId } from '../activities/activityCreateInput';
import { PlanningFlowProvider, usePlanningFlow } from './PlanningFlowProvider';
import traceJson from './v6-http.test-fixture.json';

// Recorded actual V6 selector + HTTP outputs. Transport/storage/session are simulated here.
const trace = traceJson as unknown as {
  initial: SwipeWeekDraft; passed: SwipeWeekDraft; accepted: SwipeWeekDraft;
  placement: SwipeWeekDraft; dated: SwipeWeekDraft;
  alternatives: PendingWorkoutAlternatives; approval: Awaited<ReturnType<typeof api.approvePlanProposal>>;
  sourceWithWallRest: WorkoutDeckItem;
  pending: WeeklyPlan; edited: WeeklyPlan; active: WeeklyPlan;
};
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));
jest.mock('../../api/client');
let flow: ReturnType<typeof usePlanningFlow>;
function Probe() {
  flow = usePlanningFlow();
  return flow.swipeDraft ? <SelectionScreen model={planningCreationViewModel(flow.swipeDraft)} busy={flow.busy}
    error={flow.error} onBack={jest.fn()} controls={null} onContinue={jest.fn()} onTransition={flow.transitionDraft} /> : null;
}
function Host() {
  return <LanguageProvider><PlanningFlowProvider accessToken="synthetic-token" athleteIdentity="synthetic-athlete"><Probe /></PlanningFlowProvider></LanguageProvider>;
}
beforeEach(() => {
  jest.clearAllMocks();
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: null, pending: null, draft: null });
  jest.mocked(api.getOnboarding).mockResolvedValue({ primary_goal: null } as never);
});

test('actual source wall rests preserve sequence and seconds without zone, distance or effort', async () => {
  const source = trace.sourceWithWallRest.source_prescription!;
  const blocks = sourceBlocksViewModel(source);
  const rests = blocks.filter(b => b.target.kind === 'rest');
  expect(rests.length).toBeGreaterThan(0);
  for (const rest of rests) {
    expect(rest.measures).toEqual({ durationMinutes: null, distanceMeters: null });
    expect(rest.rpeTarget).toBeNull();
    expect(rest.durationSeconds).not.toBeNull();
  }
  const view = await render(<LanguageProvider><SessionSequence segments={blocks} /></LanguageProvider>);
  expect(view.getAllByText('Stationary wall rest')).toHaveLength(rests.length);
});

test('existing owner displays real cards, passes, accepts, submits pending and explicitly confirms', async () => {
  jest.mocked(api.createSwipeWeekDraft).mockResolvedValue(trace.initial);
  jest.mocked(api.transitionSwipeWeekDraft).mockResolvedValueOnce(trace.passed).mockResolvedValueOnce(trace.accepted);
  jest.mocked(api.submitSwipeWeekDraft).mockResolvedValue({ plan: trace.pending, proposal: trace.pending.proposal! });
  const view = await render(<Host />);
  await waitFor(() => expect(flow.resumeState).toBe('ready'));
  await act(async () => { await flow.generate(); });
  expect(view.getByRole('header', { name: trace.initial.current_candidate!.name })).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: `Pass · ${trace.initial.current_candidate!.name}` }));
  await waitFor(() => expect(flow.swipeDraft).toBe(trace.passed));
  expect(api.transitionSwipeWeekDraft).toHaveBeenLastCalledWith('synthetic-token', trace.initial.id, {
    expected_revision: trace.initial.revision, action: 'pass', candidate_template_id: trace.initial.current_candidate!.id,
    candidate_occurrence_id: trace.initial.current_candidate!.occurrence_id,
  });
  await act(async () => { flow.transitionDraft('accept'); });
  await waitFor(() => expect(flow.swipeDraft).toBe(trace.accepted));
  expect(flow.swipeDraft!.accepted_workouts[0]).toEqual(trace.accepted.accepted_workouts[0]);
  // Resume the backend's completed selection through the existing server discovery.
  jest.mocked(api.discoverPlanning).mockResolvedValue({ active: null, pending: null, draft: { id: trace.dated.id, revision: trace.dated.revision, week_start: trace.dated.week_start, state: trace.dated.state as 'placement' } });
  jest.mocked(api.getSwipeWeekDraft).mockResolvedValue(trace.dated);
  await act(async () => { flow.retryResume(); });
  await waitFor(() => expect(flow.swipeDraft).toBe(trace.dated));
  await act(async () => { flow.submitDraft('automatic'); });
  await waitFor(() => expect(flow.plan).toBe(trace.pending));
  expect(flow.activePlan).toBeNull();
  expect(api.approvePlanProposal).not.toHaveBeenCalled();
  jest.mocked(api.getPendingWorkoutAlternatives).mockResolvedValue(trace.alternatives);
  jest.mocked(api.editPendingWorkout).mockResolvedValue({ plan: trace.edited, proposal: trace.edited.proposal! });
  const target = trace.alternatives.workout_id;
  await act(async () => { await flow.pendingWorkouts.load(target); });
  await act(async () => { await flow.pendingWorkouts.apply(target, trace.alternatives.alternatives[0].id); });
  await waitFor(() => expect(flow.plan).toBe(trace.edited));
  const retained = trace.pending.workouts.find(w => w.id !== target)!;
  expect(flow.plan!.workouts.find(w => w.id === retained.id)!.template_id).toBe(retained.template_id);
  expect(flow.plan!.workouts.find(w => w.id === retained.id)!.scheduled_date).toBe(retained.scheduled_date);
  jest.mocked(api.getWeeklyPlan).mockResolvedValue(trace.active);
  jest.mocked(api.approvePlanProposal).mockResolvedValue(trace.approval);
  await act(async () => { flow.approve(); });
  await waitFor(() => expect(flow.activePlan).toBe(trace.active));
  expect(api.approvePlanProposal).toHaveBeenCalledTimes(1);
});

test.each(['nl', 'en'])('source swimming blocks and qualified estimate render in %s without recovery RPE', async language => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  const swim = trace.active.workouts.find(w => w.discipline === 'swim')!;
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={swim} onClose={jest.fn()} /></LanguageProvider>);
  const model = workoutDetailViewModel(swim);
  expect(model.expectedRpe).toBeNull();
  expect(model.segments.map(s => s.name)).toEqual(swim.source_prescription!.blocks.map(b => b.text));
  expect(swim.duration_minutes).toBeNull();
  expect(view.getByText(new RegExp(language === 'nl' ? 'Geschatte actieve tijd' : 'Estimated active time'))).toBeTruthy();
  expect(JSON.stringify(view.toJSON())).not.toMatch(/tss|planned_load|realized_load/i);
  expect(model.segments.every(s => s.rpeTarget === null && s.protocolTarget === null)).toBe(true);
});

test('calendar keeps logical IDs while activity/registration uses exact physical occurrence and measured duration', () => {
  const workout = trace.active.workouts[0];
  const model = calendarViewModel({ dates: ['2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-10-31', '2026-11-01'], anchor: '2026-10-26', selectedDate: workout.scheduled_date,
    today: '2026-10-26', workouts: trace.active.workouts, restDays: trace.active.rest_days, loadedRange: { fromDate: '2026-10-26', toDate: '2026-11-02' } });
  expect(model.days.flatMap(d => d.workouts.map(w => w.id))).toEqual(expect.arrayContaining(trace.active.workouts.map(w => w.id)));
  const input = activityCreateInput({ discipline: workout.discipline, duration: '31', distance: '', startedAt: '2026-10-28T10:00:00+01:00', athleteTimezone: 'Europe/Amsterdam', selectedWorkout: workout, selectedExternal: null });
  expect(input.planned_workout_id).toBe(workout.physical_workout_id);
  expect(input.duration_minutes).toBe('31');
  expect(input.distance_meters).toBeUndefined();
  expect(activityWorkoutId(workout)).not.toBe(workout.id);
  expect(() => activityWorkoutId({ ...workout, physical_workout_id: null })).toThrow();
});

test.each([2, 1, 0])('selection presentation supports %i sports without a missing-discipline error', async count => {
  // Presentation-only partial/rest fixture; genuine selection feasibility is tested in Python.
  const model = { ...planningCreationViewModel(trace.placement), accepted: planningCreationViewModel(trace.placement).accepted.slice(0, count) };
  const view = await render(<LanguageProvider><SelectionScreen model={model} busy={false} error={null}
    onBack={jest.fn()} controls={null} onContinue={jest.fn()} onTransition={jest.fn()} /></LanguageProvider>);
  expect(view.queryAllByTestId(/^selection-occurrence-/)).toHaveLength(count);
  expect(view.queryByRole('alert')).toBeNull();
});
