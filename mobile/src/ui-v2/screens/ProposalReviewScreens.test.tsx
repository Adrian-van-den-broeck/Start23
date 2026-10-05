import { fireEvent, render } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { ReactNode } from 'react';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { pendingPlan, occurrence, proposal, workout } from '../../features/planning/planning.test-fixtures';
import { proposalAlternativesViewModel, proposalReviewViewModel } from '../utils/proposalReviewViewModel';
import { ProposalAlternativesScreen, ProposalReviewScreen } from './ProposalReviewScreens';
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en') }));
const task = { busy: false, error: null, controls: null, onBack: jest.fn() };
const model = proposalReviewViewModel(pendingPlan);
const options = proposalAlternativesViewModel({ plan_id: pendingPlan.id, revision: 3, proposal_id: proposal.id, workout_id: workout.id, can_remove: true, alternatives: [occurrence] });
function host(children: ReactNode) { return <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 320, height: 640 }, insets: { top: 24, bottom: 24, left: 0, right: 0 } }}><LanguageProvider>{children}</LanguageProvider></SafeAreaProvider>; }
const actions = { onEdit: jest.fn(), onApprove: jest.fn(), onReject: jest.fn() };
const alternativeActions = { onSelect: jest.fn(), onReplace: jest.fn(), onRemove: jest.fn(), onRetry: jest.fn() };
beforeEach(() => jest.clearAllMocks());

test('review heading/state/warnings and independent edit controls are accessible without implicit decisions', async () => {
  const repeated = proposalReviewViewModel({ ...pendingPlan, workouts: [workout, { ...workout, id: 'repeat' }] });
  const view = await render(host(<ProposalReviewScreen {...task} {...actions} model={repeated} />));
  expect(view.getByRole('header', { name: 'Review your week proposal' })).toBeTruthy();
  expect(view.getByText('Proposal awaiting your approval. These workouts are not active yet.')).toBeTruthy();
  const controls = view.getAllByRole('button', { name: /^View alternatives/ }); expect(controls).toHaveLength(2);
  await fireEvent.press(controls[1]); expect(actions.onEdit).toHaveBeenCalledWith('repeat');
  await fireEvent.press(view.getByRole('button', { name: 'Back to Week' }));
  expect(actions.onApprove).not.toHaveBeenCalled(); expect(actions.onReject).not.toHaveBeenCalled();
});
test('busy review disables Back, edit and both separated explicit decisions and exposes busy state', async () => {
  const view = await render(host(<ProposalReviewScreen {...task} {...actions} busy model={model} />));
  for (const button of view.getAllByRole('button')) expect(button).toBeDisabled();
  await fireEvent.press(view.getByRole('button', { name: 'Approve week' })); expect(actions.onApprove).not.toHaveBeenCalled();
  expect(view.getByText('Please wait. The action is processing.').props.accessibilityState).toEqual({ busy: true });
});
test('expired review shows unavailable state without alternatives or a functional decision', async () => {
  const view = await render(host(<ProposalReviewScreen {...task} {...actions} model={{ ...model, pending: false, state: 'expired' }} />));
  expect(view.getByRole('button', { name: 'Approve week' })).toBeDisabled(); expect(view.getByRole('button', { name: 'Reject proposal' })).toBeDisabled();
  expect(view.queryByRole('button', { name: /^View alternatives/ })).toBeNull();
});
test('alternative selection exposes checked state and source measures without inventing comparisons', async () => {
  const view = await render(host(<ProposalAlternativesScreen {...task} {...alternativeActions} model={model} workout={model.workouts[0]} options={options} selectedId={occurrence.id} loading={false} />));
  expect(view.getByRole('radio').props.accessibilityState.checked).toBe(true);
  expect(view.getByRole('button', { name: 'Replace workout in proposal' })).toBeEnabled();
  await fireEvent.press(view.getByRole('radio')); expect(alternativeActions.onSelect).toHaveBeenCalledWith(occurrence.id);
});
test('removal asks twice, names pending-only consequence, and allows keeping the workout', async () => {
  const view = await render(host(<ProposalAlternativesScreen {...task} {...alternativeActions} model={model} workout={model.workouts[0]} options={options} selectedId={null} loading={false} />));
  await fireEvent.press(view.getByRole('button', { name: 'Remove workout from proposal' }));
  expect(alternativeActions.onRemove).not.toHaveBeenCalled();
  expect(view.getByText(`Removing ${workout.name} changes only this proposal. Your active plan is unchanged.`)).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Confirm removal from proposal' })); expect(alternativeActions.onRemove).toHaveBeenCalledTimes(1);
});
test('loading and safe error are announced; all alternatives/actions stay locked', async () => {
  const view = await render(host(<ProposalAlternativesScreen {...task} {...alternativeActions} busy loading error="Safe stale edit" model={model} workout={model.workouts[0]} options={options} selectedId={occurrence.id} />));
  expect(view.getByRole('alert')).toBeTruthy(); for (const button of view.getAllByRole('button')) expect(button).toBeDisabled();
  expect(view.getByRole('radio')).toBeDisabled();
});
