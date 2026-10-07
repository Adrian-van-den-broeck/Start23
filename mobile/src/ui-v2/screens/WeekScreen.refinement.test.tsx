import { fireEvent, render, within } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { StyleSheet, View } from 'react-native';
import * as Native from 'react-native';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { activePlan, draft, pendingPlan } from '../../features/planning/planning.test-fixtures';
import { weekHomeViewModel, type WeekHomeViewModel } from '../utils/weekHomeViewModel';
import { colors } from '../tokens';
import { WeekScreen } from './WeekScreen';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
const base = { plan: null, activePlan: null, draft: null, today: '2026-10-07', resumeState: 'ready' as const, activeReadState: 'ready' as const };
const restPlan = { ...activePlan, workouts: [], rest_days: [{ date: base.today, reason: 'restriction_rest' as const }] };
const cases = [
  { state: 'A', model: weekHomeViewModel(base), task: true, hero: false, en: 'Prepare your training week', nl: 'Bereid je trainingsweek voor' },
  { state: 'B', model: weekHomeViewModel({ ...base, draft }), task: true, hero: false, en: 'Choose your workouts', nl: 'Kies je trainingen' },
  { state: 'C', model: weekHomeViewModel({ ...base, draft: { ...draft, state: 'placement' } }), task: true, hero: false, en: 'Confirm your training dates', nl: 'Bevestig je trainingsdatums' },
  { state: 'D', model: weekHomeViewModel({ ...base, plan: pendingPlan }), task: true, hero: false, en: 'Review your week', nl: 'Controleer je week' },
  { state: 'E', model: weekHomeViewModel({ ...base, plan: activePlan, activePlan }), task: false, hero: true, en: 'Today · 1 workout', nl: 'Vandaag · 1 training' },
  { state: 'F', model: weekHomeViewModel({ ...base, plan: activePlan, activePlan, today: '2026-10-05' }), task: false, hero: true, en: 'Next training day', nl: 'Volgende trainingsdag' },
  { state: 'G', model: weekHomeViewModel({ ...base, plan: pendingPlan, activePlan }), task: false, hero: true, en: 'Approved · new proposal awaiting review', nl: 'Goedgekeurd · nieuw voorstel wacht op jou' },
  { state: 'H', model: weekHomeViewModel({ ...base, plan: restPlan, activePlan: restPlan }), task: false, hero: false, en: 'Rest due to a confirmed restriction', nl: 'Rust vanwege een bevestigde beperking' },
];
const actions = { onAction: jest.fn(), onOpenWorkout: jest.fn(), onProfile: jest.fn(), onActivities: jest.fn(), onCheckIn: jest.fn(), onZones: jest.fn(), onGoal: jest.fn() };
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });
afterEach(() => jest.restoreAllMocks());
const screen = (model: WeekHomeViewModel, goalName: string | null = null, controls = <View testID="supplied-dev-controls" />) =>
  <LanguageProvider><WeekScreen {...actions} model={model} error={null} busy={false} goalName={goalName} controls={controls} /></LanguageProvider>;

describe.each(['nl', 'en'] as const)('%s approved state compositions', (language) => {
  test.each(cases)('$state preserves model content/actions in the new grouping', async ({ model, task, hero, en, nl }) => {
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
    const before = JSON.stringify(model);
    const view = await render(screen(Object.freeze(model)));
    await view.findByText(language === 'nl' ? nl : en);
    expect(!!view.queryByTestId('week-task-card')).toBe(task);
    expect(!!view.queryByTestId('week-session-hero')).toBe(hero);
    expect(view.getAllByText(language === 'nl' ? nl : en)).toHaveLength(1);
    if (model.mainAction) {
      const button = within(view.getByTestId('week-task-card')).getByRole('button');
      await fireEvent.press(button);
      expect(actions.onAction).toHaveBeenCalledWith(model.mainAction);
    }
    if (hero) {
      const button = within(view.getByTestId('week-session-hero')).getByRole('button');
      expect(button.props.accessibilityLabel).toContain(model.sessions[0].summary.name);
      await fireEvent.press(button);
      expect(actions.onOpenWorkout).toHaveBeenCalledWith(model.sessions[0].id);
    }
    expect(JSON.stringify(model)).toBe(before);
  });
});

test('pending warning follows week navigation; neutral pending is not amber or an active schedule', async () => {
  const view = await render(screen(cases[3].model));
  expect(view.queryByTestId('week-session-hero')).toBeNull();
  const task = view.getByTestId('week-task-card');
  expect(StyleSheet.flatten(task.props.style).backgroundColor).toBe(colors.surface);
  expect(StyleSheet.flatten(view.getByTestId('week-attention-warnings').props.style).backgroundColor).toBe(colors.warningSoft);
  const labels = view.getAllByRole('button').map((button) => button.props.accessibilityLabel);
  expect(labels.indexOf('Review attention items')).toBeGreaterThan(labels.indexOf('View week'));
});

test('active plus draft and pending preserves draft priority when no future session exists', async () => {
  const model = weekHomeViewModel({ ...base, today: '2026-10-11', plan: pendingPlan, activePlan, draft });
  const view = await render(screen(model));
  const task = within(view.getByTestId('week-task-card'));
  expect(task.getByText('Choose your workouts')).toBeTruthy();
  await fireEvent.press(task.getByRole('button', { name: 'Continue choosing' }));
  expect(actions.onAction).toHaveBeenLastCalledWith('draft');
  await fireEvent.press(view.getByRole('button', { name: 'Review proposal' }));
  expect(actions.onAction).toHaveBeenLastCalledWith('review');
  expect(view.getByText('Approved · new proposal awaiting review')).toBeTruthy();
});

test('tools keep their exact order and callbacks; goal follows them without changing confirmation', async () => {
  const name = 'Supplied long race goal '.repeat(6);
  const view = await render(screen(cases[1].model, name));
  const tools = within(view.getByTestId('week-training-tools')).getAllByRole('button');
  expect(tools.map((button) => button.props.accessibilityLabel)).toEqual(['Activities and RPE', 'Check-in', 'My zones', 'Prepare week']);
  for (const tool of tools) await fireEvent.press(tool);
  expect(actions.onActivities).toHaveBeenCalledTimes(1);
  expect(actions.onCheckIn).toHaveBeenCalledTimes(1);
  expect(actions.onZones).toHaveBeenCalledTimes(1);
  expect(actions.onAction).toHaveBeenLastCalledWith('prepare');
  await fireEvent.press(view.getByRole('button', { name: `Goal · ${name}` }));
  expect(actions.onGoal).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'Profile' }));
  expect(actions.onProfile).toHaveBeenCalledTimes(1);
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  expect(actions.onAction).toHaveBeenLastCalledWith('calendar');
});

test('no-plan has a single Prepare action; absent goal has no row', async () => {
  const view = await render(screen(cases[0].model));
  expect(view.getAllByRole('button', { name: 'Prepare week' })).toHaveLength(1);
  expect(view.queryByTestId('week-goal-row')).toBeNull();
  expect(view.getByTestId('week-development-footer')).toBeTruthy();
});

test('non-development rendering reserves no footer or comparison controls', async () => {
  const original = __DEV__;
  try {
    Object.assign(globalThis, { __DEV__: false });
    const view = await render(screen(cases[1].model));
    expect(view.queryByTestId('week-development-footer')).toBeNull();
    expect(view.queryByTestId('supplied-dev-controls')).toBeNull();
  } finally { Object.assign(globalThis, { __DEV__: original }); }
});

test('200% header and full Profile target grow without vertical flex shrinking', async () => {
  jest.spyOn(Native, 'useWindowDimensions').mockReturnValue({ width: 320, height: 800, fontScale: 2, scale: 1 });
  const view = await render(screen(cases[1].model));
  expect(StyleSheet.flatten(view.getByTestId('week-header-title').props.style)).toMatchObject({ width: '100%', flexGrow: 0, flexShrink: 0, flexBasis: 'auto' });
  expect(StyleSheet.flatten(view.getByRole('button', { name: 'Profile' }).props.style)).toMatchObject({ alignSelf: 'stretch', minHeight: 48 });
});

test.each(['rejected', 'expired'] as const)('%s still enters the supplied planning action', async (revision_state) => {
  const model = weekHomeViewModel({ ...base, plan: { ...pendingPlan, revision_state } });
  const view = await render(screen(model));
  await fireEvent.press(view.getByRole('button', { name: 'Open weekly planning' }));
  expect(actions.onAction).toHaveBeenCalledWith('planning');
});

test('no future session remains a truthful quiet empty message and literal single-workout progress', async () => {
  const model = weekHomeViewModel({ ...base, today: '2026-10-11', plan: activePlan, activePlan });
  const view = await render(screen(model));
  expect(view.queryByTestId('week-session-hero')).toBeNull();
  expect(view.getByText('No upcoming workout planned in this week')).toBeTruthy();
  expect(view.getByText('0 of 1 planned workout completed')).toBeTruthy();
});

test('same-day siblings use complete summaries, preserve all source fields and have independent occurrence actions', async () => {
  const second = { ...activePlan.workouts[0], id: 'second-occurrence', name: 'Long exact source name '.repeat(6) };
  const plan = { ...activePlan, workouts: [activePlan.workouts[0], second] };
  const model = weekHomeViewModel({ ...base, plan, activePlan: plan });
  const view = await render(screen(model));
  expect(view.getAllByTestId('week-session-hero')).toHaveLength(1);
  const sibling = within(view.getByTestId('week-session-sibling'));
  expect(sibling.getByText(second.name)).toBeTruthy();
  expect(sibling.getByText('30.5 min')).toBeTruthy();
  expect(sibling.getByText('1200 m')).toBeTruthy();
  expect(sibling.getByText('Easy')).toBeTruthy();
  expect(sibling.getByText('Scheduled')).toBeTruthy();
  expect(sibling.getByText(model.sessions[1].summary.description!)).toBeTruthy();
  await fireEvent.press(sibling.getByRole('button', { name: `View workout · ${second.name}` }));
  expect(actions.onOpenWorkout).toHaveBeenCalledWith('second-occurrence');
  expect(view.getByText('Today · 2 workouts')).toBeTruthy();
});

test('dual-state cards expose only active occurrences and a separate pending review callback', async () => {
  const proposal = { ...pendingPlan, workouts: [{ ...activePlan.workouts[0], id: 'pending-only', name: 'Pending-only occurrence' }] };
  const model = weekHomeViewModel({ ...base, plan: proposal, activePlan });
  const view = await render(screen(model));
  expect(view.queryByText('Pending-only occurrence')).toBeNull();
  expect(view.queryByTestId('week-task-card')).toBeNull();
  const active = within(view.getByTestId('week-session-hero'));
  expect(active.getByText(activePlan.workouts[0].name)).toBeTruthy();
  await fireEvent.press(active.getByRole('button'));
  expect(actions.onOpenWorkout).toHaveBeenCalledWith(activePlan.workouts[0].id);
  const pending = within(view.getByTestId('week-attention-proposal'));
  await fireEvent.press(pending.getByRole('button', { name: 'Review proposal' }));
  expect(actions.onAction).toHaveBeenCalledWith('review');
  expect(view.getByText('0 of 1 planned workout completed')).toBeTruthy();
});

test('sparse Week summary omits absent measures and description while keeping status and detail', async () => {
  const plan = { ...activePlan, workouts: [{ ...activePlan.workouts[0], duration_minutes: null, distance_meters: null, description: '' }] };
  const view = await render(screen(weekHomeViewModel({ ...base, plan, activePlan: plan })));
  const active = within(view.getByTestId('week-session-hero'));
  expect(active.queryByText(/\bmin\b|\bm\b/)).toBeNull();
  expect(active.getByText('Easy')).toBeTruthy();
  expect(active.getByText('Scheduled')).toBeTruthy();
  await fireEvent.press(active.getByRole('button'));
  expect(actions.onOpenWorkout).toHaveBeenCalledWith(plan.workouts[0].id);
});
