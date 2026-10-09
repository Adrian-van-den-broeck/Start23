import { useState } from 'react';
import { fireEvent, render } from '@testing-library/react-native';

import { DurationPicker } from './DurationPicker';

function ControlledDuration({ initial, appearance }: { initial: number | null; appearance: 'default' | 'final' }) {
  const [value, setValue] = useState(initial);
  return (
    <DurationPicker
      appearance={appearance}
      label="Totale richttijd"
      onChange={setValue}
      valueSeconds={value}
    />
  );
}

describe.each(['default', 'final'] as const)('DurationPicker (%s)', (appearance) => {
  test('loads and displays an exact saved duration without a keyboard', async () => {
    const screen = await render(<ControlledDuration initial={13_530} appearance={appearance} />);

    expect(screen.getByLabelText('Totale richttijd: 03:45:30')).toBeTruthy();
    expect(screen.queryByRole('textbox')).toBeNull();

    await fireEvent.press(
      screen.getByRole('button', {
        name: 'Kies minuten voor Totale richttijd',
      }),
    );
    await fireEvent.press(screen.getByRole('radio', { name: '12 min' }));

    expect(screen.getByLabelText('Totale richttijd: 03:12:30')).toBeTruthy();
  });

  test('an optional duration can be cleared and restored with touch controls', async () => {
    const screen = await render(<ControlledDuration initial={3600} appearance={appearance} />);

    await fireEvent.press(
      screen.getByRole('button', { name: 'Totale richttijd wissen' }),
    );
    expect(
      screen.getByLabelText('Totale richttijd: nog niet ingesteld'),
    ).toBeTruthy();

    await fireEvent.press(
      screen.getByRole('button', {
        name: 'Verhoog minuten voor Totale richttijd',
      }),
    );
    expect(screen.getByLabelText('Totale richttijd: 00:01:00')).toBeTruthy();
  });
});
