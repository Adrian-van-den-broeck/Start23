import { useState, type ReactElement } from 'react';
import { fireEvent, render as baseRender } from '@testing-library/react-native';

import { DurationPicker } from './DurationPicker';
import { LanguageProvider } from '../i18n/LanguageProvider';

// Dutch is the default language; every render goes through the provider like the app does.
const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

function ControlledDuration({ initial, required = false, units }: {
  initial: number | null; required?: boolean; units?: readonly ('hours' | 'minutes' | 'seconds')[];
}) {
  const [value, setValue] = useState(initial);
  return (
    <DurationPicker
      label="Totale richttijd"
      onChange={setValue}
      units={units}
      required={required}
      valueSeconds={value}
    />
  );
}

const openPicker = (screen: Awaited<ReturnType<typeof render>>) =>
  fireEvent.press(screen.getByRole('button', { name: /^Totale richttijd: / }));

describe('DurationPicker', () => {
  test('shows the saved duration in one compact field and edits it in a wheel sheet', async () => {
    const screen = await render(<ControlledDuration initial={13_530} />);

    expect(screen.getByLabelText('Totale richttijd: 03:45:30')).toBeTruthy();
    expect(screen.queryByRole('textbox')).toBeNull();
    expect(screen.queryByRole('radio')).toBeNull();

    await openPicker(screen);
    expect(screen.getByRole('radio', { name: '45 min' }).props.accessibilityState).toEqual({ checked: true });
    await fireEvent.press(screen.getByRole('radio', { name: '12 min' }));
    // The field keeps its value until the athlete confirms the draft.
    expect(screen.getByLabelText('Totale richttijd: 03:45:30')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));

    expect(screen.getByLabelText('Totale richttijd: 03:12:30')).toBeTruthy();
  });

  test('scrolling a wheel settles on the centred row', async () => {
    const screen = await render(<ControlledDuration initial={0} />);

    await openPicker(screen);
    await fireEvent.scroll(screen.getByLabelText('uur'), { nativeEvent: { contentOffset: { x: 0, y: 44 * 2 } } });
    await fireEvent.scroll(screen.getByLabelText('min'), { nativeEvent: { contentOffset: { x: 0, y: 44 * 5 + 10 } } });
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));

    expect(screen.getByLabelText('Totale richttijd: 02:05:00')).toBeTruthy();
  });

  test('closing the sheet without confirming discards the draft', async () => {
    const screen = await render(<ControlledDuration initial={3600} />);

    await openPicker(screen);
    await fireEvent.press(screen.getByRole('radio', { name: '3 uur' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Duurkeuze sluiten' }));

    expect(screen.getByLabelText('Totale richttijd: 01:00:00')).toBeTruthy();
  });

  test('an optional duration can be cleared and set again with touch controls', async () => {
    const screen = await render(<ControlledDuration initial={3600} />);

    await fireEvent.press(screen.getByRole('button', { name: 'Totale richttijd wissen' }));
    expect(screen.getByLabelText('Totale richttijd: nog niet ingesteld')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Totale richttijd wissen' })).toBeNull();

    await openPicker(screen);
    await fireEvent.press(screen.getByRole('radio', { name: '1 minuut' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    expect(screen.getByLabelText('Totale richttijd: 00:01:00')).toBeTruthy();
  });

  test('a required duration cannot be cleared', async () => {
    const screen = await render(<ControlledDuration initial={3600} required />);

    expect(screen.queryByRole('button', { name: 'Totale richttijd wissen' })).toBeNull();
  });

  test('an hours-and-minutes picker hides the seconds wheel and reports whole minutes', async () => {
    const screen = await render(<ControlledDuration initial={null} units={['hours', 'minutes']} />);

    await openPicker(screen);
    expect(screen.queryByLabelText('sec')).toBeNull();
    await fireEvent.press(screen.getByRole('radio', { name: '50 min' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));

    expect(screen.getByLabelText('Totale richttijd: 00:50:00')).toBeTruthy();
  });
});
