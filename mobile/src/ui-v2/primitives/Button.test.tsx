import { act, fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { Button } from './Button';
import { Text } from './Text';

test('concise visible CTA retains the full supplied workout in its accessible name', async () => {
  const press = jest.fn();
  const view = await render(<Button label="View workout" accessibilityLabel="View workout · Exact supplied long name" onPress={press} />);
  expect(view.getByText('View workout')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'View workout · Exact supplied long name' }));
  expect(press).toHaveBeenCalledTimes(1);
});

test('busy button retains label, explicit busy/disabled state and suppresses duplicate calls', async () => {
  const press = jest.fn();
  const view = await render(<Button label="Read workout" busy onPress={press} />);
  const button = view.getByRole('button', { name: 'Read workout' });
  expect(button.props.accessibilityState).toEqual({ busy: true, disabled: true });
  expect(view.getByText('Read workout').props.accessible).toBe(false);
  expect(view.getByText('Read workout').props.importantForAccessibility).toBe('no');
  await fireEvent.press(button);
  await fireEvent.press(button);
  expect(press).not.toHaveBeenCalled();
});

test('synchronous lock suppresses rapid calls until an async handler completes', async () => {
  let resolve!: () => void;
  const task = new Promise<void>((done) => { resolve = done; });
  const press = jest.fn(() => task);
  const view = await render(<Button label="Read" onPress={press} />);
  await fireEvent.press(view.getByRole('button'));
  await fireEvent.press(view.getByRole('button'));
  expect(press).toHaveBeenCalledTimes(1);
  await act(async () => { resolve(); await task; });
  expect(view.getByRole('button').props.accessibilityState.busy).toBe(false);
});

test('disabled reason, selected/expanded semantics, 52dp primary and unclamped scalable typography', async () => {
  const view = await render(<><Button label="Compare" disabled disabledReason="Reason" onPress={jest.fn()}
    accessibilityState={{ selected: true, expanded: false }} /><Text accessibilityRole="header">Heading</Text></>);
  const button = view.getByRole('button');
  expect(button.props.accessibilityHint).toBe('Reason');
  expect(button.props.accessibilityState).toMatchObject({ selected: true, disabled: true, expanded: false });
  expect(StyleSheet.flatten(button.props.style).minHeight).toBe(52);
  const heading = view.getByText('Heading');
  expect(heading.props.allowFontScaling).toBe(true);
  expect(heading.props.maxFontSizeMultiplier).toBeUndefined();
  expect(StyleSheet.flatten(heading.props.style).lineHeight).toBe(24);
});
