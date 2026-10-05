import { fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { colors, layout } from '../tokens';
import { WeekTaskCard } from './WeekTaskCard';
import { QuickActionRow } from './QuickActionRow';
import { GoalSummaryRow } from './GoalSummaryRow';

test('task groups supplied facts and the existing action in one unshadowed focus surface', async () => {
  const action = jest.fn();
  const view = await render(<WeekTaskCard status="Supplied status" heading="Supplied task" supporting="Supplied fact" actionLabel="Continue" onAction={action} />);
  const card = view.getByTestId('week-task-card');
  expect(StyleSheet.flatten(card.props.style)).toMatchObject({ backgroundColor: colors.surface, borderRadius: 20, padding: 24 });
  expect(StyleSheet.flatten(card.props.style).height).toBeUndefined();
  expect(view.getByRole('header', { name: 'Supplied task' })).toBeTruthy();
  expect(view.getByText('Supplied fact')).toBeTruthy();
  expect(StyleSheet.flatten(view.getByRole('button', { name: 'Continue' }).props.style).minHeight).toBe(layout.primaryButton);
  await fireEvent.press(view.getByRole('button', { name: 'Continue' }));
  expect(action).toHaveBeenCalledTimes(1);
});

test.each([false, true])('quick row retains one action and a full accessible label; disabled=%s', async (disabled) => {
  const action = jest.fn();
  const view = await render(<QuickActionRow label="Short label" accessibilityLabel="Full supplied destination" onAction={action} disabled={disabled} />);
  const row = view.getByRole('button', { name: 'Full supplied destination' });
  expect(view.getAllByRole('button')).toHaveLength(1);
  expect(StyleSheet.flatten(row.props.style)).toMatchObject({ minHeight: layout.touch, flexDirection: 'row' });
  expect(view.getByText('Short label', { includeHiddenElements: true }).props.numberOfLines).toBeUndefined();
  await fireEvent.press(row);
  expect(action).toHaveBeenCalledTimes(disabled ? 0 : 1);
});

test('busy quick row blocks its action and preserves its label', async () => {
  const action = jest.fn();
  const view = await render(<QuickActionRow label="View week" busy onAction={action} />);
  const row = view.getByRole('button', { name: 'View week' });
  expect(row).toBeDisabled();
  expect(row.props.accessibilityState.busy).toBe(true);
  await fireEvent.press(row);
  expect(action).not.toHaveBeenCalled();
});

test('goal preserves a long source name and has one confirmation entry', async () => {
  const action = jest.fn();
  const name = 'Exact supplied race goal name '.repeat(8);
  const view = await render(<GoalSummaryRow label="Goal" name={name} accessibilityLabel={`Goal · ${name}`} onAction={action} />);
  const row = view.getByRole('button', { name: `Goal · ${name}` });
  expect(view.getAllByRole('button')).toHaveLength(1);
  expect(StyleSheet.flatten(row.props.style).minHeight).toBe(layout.touch);
  expect(view.getByText(name, { includeHiddenElements: true }).props.numberOfLines).toBeUndefined();
  await fireEvent.press(row);
  expect(action).toHaveBeenCalledTimes(1);
});

test('disabled goal cannot invoke confirmation', async () => {
  const action = jest.fn();
  const view = await render(<GoalSummaryRow label="Goal" name="Supplied goal" accessibilityLabel="Goal · Supplied goal" disabled onAction={action} />);
  await fireEvent.press(view.getByRole('button'));
  expect(action).not.toHaveBeenCalled();
});
