import { useState, type ReactElement } from 'react';
import { fireEvent, render as baseRender } from '@testing-library/react-native';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { DatePicker } from './DatePicker';

const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

function Controlled({ initial, onChange }: { initial: string; onChange: (value: string) => void }) {
  const [value, setValue] = useState(initial);
  return <DatePicker label="Racedatum" min="2026-11-24" max="2028-12-31" value={value}
    onChange={(next) => { setValue(next); onChange(next); }} />;
}

describe('DatePicker', () => {
  test('shows a readable date and picks day, month and year on wheels', async () => {
    const onChange = jest.fn();
    const screen = await render(<Controlled initial="2027-06-15" onChange={onChange} />);

    expect(screen.getByRole('button', { name: 'Racedatum: 15 juni 2027' })).toBeTruthy();
    expect(screen.queryByRole('textbox')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: /^Racedatum: / }));
    await fireEvent.press(screen.getByRole('radio', { name: 'Dag 20' }));
    await fireEvent.press(screen.getByRole('radio', { name: 'sep' }));
    await fireEvent.press(screen.getByRole('radio', { name: '2028' }));
    expect(onChange).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));

    expect(onChange).toHaveBeenCalledWith('2028-09-20');
  });

  test('keeps the day valid for the month and the date inside the allowed range', async () => {
    const onChange = jest.fn();
    const screen = await render(<Controlled initial="2027-01-31" onChange={onChange} />);

    await fireEvent.press(screen.getByRole('button', { name: /^Racedatum: / }));
    await fireEvent.press(screen.getByRole('radio', { name: 'feb' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    expect(onChange).toHaveBeenLastCalledWith('2027-02-28');

    await fireEvent.press(screen.getByRole('button', { name: /^Racedatum: / }));
    await fireEvent.press(screen.getByRole('radio', { name: '2026' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Klaar' }));
    expect(onChange).toHaveBeenLastCalledWith('2026-11-24');
  });

  test('an empty value shows the placeholder and opens on the latest allowed date', async () => {
    const screen = await render(<Controlled initial="" onChange={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Racedatum: nog niet ingesteld' })).toBeTruthy();
    expect(screen.getByText('Datum kiezen')).toBeTruthy();
  });
});
