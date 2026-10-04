import { fireEvent, render, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { activePlan, draft, pendingPlan, workout } from '../../features/planning/planning.test-fixtures';
import { weekHomeViewModel } from '../utils/weekHomeViewModel';
import { WeekScreen } from './WeekScreen';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
const input = { plan: activePlan, activePlan, draft: null, today: '2026-10-07', resumeState: 'ready' as const, activeReadState: 'ready' as const };
const callbacks = { onAction: jest.fn(), onOpenWorkout: jest.fn(), onProfile: jest.fn(), onActivities: jest.fn(), onCheckIn: jest.fn(), onZones: jest.fn(), onGoal: jest.fn() };
beforeEach(() => { jest.clearAllMocks(); jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });
test.each(['nl', 'en'])('all repeated same-date occurrences have full named actions in %s', async (language) => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  const plan = { ...activePlan, workouts: [workout, { ...workout, id: 'repeat', name: 'Second supplied session' }] };
  const view = await render(<LanguageProvider><WeekScreen {...callbacks} model={weekHomeViewModel({ ...input, plan, activePlan: plan })} error={null} busy={false} goalName={null} controls={null} /></LanguageProvider>);
  const prefix = language === 'nl' ? 'Bekijk training' : 'View workout';
  await waitFor(() => expect(view.getByRole('button', { name: prefix + ' · Second supplied session' })).toBeTruthy());
  await fireEvent.press(view.getByRole('button', { name: prefix + ' · Second supplied session' }));
  expect(callbacks.onOpenWorkout).toHaveBeenCalledWith('repeat');
  expect(view.getAllByRole('button', { name: new RegExp(prefix) })).toHaveLength(2);
});
test('known attention shows at most two rows while all three remain reachable', async () => {
  const model = weekHomeViewModel({ ...input, plan: pendingPlan, draft });
  const view = await render(<LanguageProvider><WeekScreen {...callbacks} model={model} error={null} busy={false} goalName={null} controls={null} /></LanguageProvider>);
  await view.findByText('Attention · 3');
  expect(view.queryByText('Week needs attention')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: 'All attention items' }));
  expect(view.getByText('Week needs attention')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Review attention items' }));
  expect(callbacks.onAction).toHaveBeenCalledWith('review');
});
test('initial load uses static skeleton, failed load clears it and never claims no plan', async () => {
  const model = weekHomeViewModel({ ...input, plan: null, activePlan: null, resumeState: 'loading' });
  const renderScreen = (resumeState: 'loading' | 'failed') => <LanguageProvider><WeekScreen {...callbacks} model={weekHomeViewModel({ ...input, plan: null, activePlan: null, resumeState })} error={null} busy={false} goalName={null} controls={null} /></LanguageProvider>;
  expect(model.mainAction).toBeNull();
  const view = await render(renderScreen('loading'));
  expect(view.getByTestId('week-skeleton', { includeHiddenElements: true }).props.importantForAccessibility).toBe('no-hide-descendants');
  await view.rerender(renderScreen('failed'));
  expect(view.queryByTestId('week-skeleton')).toBeNull();
  expect(view.queryByText('Prepare your training week')).toBeNull();
  expect(view.getByText(/could not be fully loaded/)).toBeTruthy();
});
test('busy root actions stay disabled and safe error is visible beside retained known plan', async () => {
  const view = await render(<LanguageProvider><WeekScreen {...callbacks} model={weekHomeViewModel(input)} error="Safe supplied error" busy goalName={null} controls={null} /></LanguageProvider>);
  await view.findByText('Safe supplied error');
  expect(view.getByRole('button', { name: 'Prepare week' })).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'View week' }));
  expect(callbacks.onAction).not.toHaveBeenCalled();
  expect(view.getByText(workout.name)).toBeTruthy();
});
