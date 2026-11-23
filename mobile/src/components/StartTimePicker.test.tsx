import { useState, type ReactElement } from 'react';
import { fireEvent, render as baseRender } from '@testing-library/react-native';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { StartTimePicker } from './StartTimePicker';

const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

// Saturday 15 August 2026, 12:00 in Amsterdam.
const now = new Date('2026-08-15T10:00:00Z');

function ControlledStart({ initial, onChange }: { initial: string; onChange: (value: string) => void }) {
  const [value, setValue] = useState(initial);
  return <StartTimePicker label="Starttijd" now={now} timeZone="Europe/Amsterdam" valueIso={value}
    onChange={(next) => { setValue(next); onChange(next); }} />;
}

describe('StartTimePicker', () => {
  test('shows the start as a day and clock time in the profile time zone', async () => {
    const screen = await render(<ControlledStart initial="2026-08-15T07:15:00.000Z" onChange={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Starttijd: Vandaag · 09:15' })).toBeTruthy();
    expect(screen.queryByRole('textbox')).toBeNull();
  });

  test('picks yesterday at 18:30 and reports the exact instant', async () => {
    const onChange = jest.fn();
    const screen = await render(<ControlledStart initial="2026-08-15T07:15:00.000Z" onChange={onChange} />);

    await fireEvent.press(screen.getByRole('button', { name: /^Starttijd: / }));
    await fireEvent.press(screen.getByRole('radio', { name: 'Gisteren' }));
    await fireEvent.press(screen.getByRole('radio', { name: '18 uur' }));
    await fireEvent.press(screen.getByRole('radio', { name: '30 min' }));
    expect(onChange).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));

    expect(onChange).toHaveBeenCalledWith('2026-08-14T16:30:00.000Z');
    expect(screen.getByRole('button', { name: 'Starttijd: Gisteren · 18:30' })).toBeTruthy();
  });

  test('older days show their date, and closing without confirming keeps the value', async () => {
    const onChange = jest.fn();
    const screen = await render(<ControlledStart initial="2026-08-15T07:15:00.000Z" onChange={onChange} />);

    await fireEvent.press(screen.getByRole('button', { name: /^Starttijd: / }));
    expect(screen.getByRole('radio', { name: 'do 13 aug' })).toBeTruthy();
    await fireEvent.press(screen.getByRole('radio', { name: 'do 13 aug' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Tijdkeuze sluiten' }));

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Starttijd: Vandaag · 09:15' })).toBeTruthy();
  });
});
