import type { ReactElement } from 'react';
import { fireEvent, render as baseRender, within } from '@testing-library/react-native';

import { LanguageProvider } from '../../i18n/LanguageProvider';
import { RpeSelect } from './RpeSelect';

const render = (ui: ReactElement) => baseRender(ui, { wrapper: LanguageProvider });

describe('RpeSelect', () => {
  test('keeps the scale in a sheet and reports the canonical value on choice', async () => {
    const onSelect = jest.fn();
    const screen = await render(
      <RpeSelect discipline="swim" label="Hoe voelde dit blok?" onSelect={onSelect} selectedValue={null} />,
    );

    expect(screen.queryByRole('radio')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Hoe voelde dit blok?: Kies je RPE' }));

    const scale = within(screen.getByLabelText('Hoe voelde dit blok?'));
    expect(scale.getAllByRole('radio')).toHaveLength(10);
    await fireEvent.press(scale.getByRole('radio', { name: 'Vlotte, ritmische slag. (RPE 3)' }));

    expect(onSelect).toHaveBeenCalledWith(3);
    expect(screen.queryByRole('radio')).toBeNull();
  });

  test('shows the chosen score and its meaning in the compact field', async () => {
    const screen = await render(
      <RpeSelect discipline="swim" label="Hoe voelde dit blok?" onSelect={jest.fn()} selectedValue={3} />,
    );

    expect(screen.getByRole('button', { name: 'Hoe voelde dit blok?: Vlotte, ritmische slag. (RPE 3)' })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: /^Hoe voelde dit blok\?: / }));
    expect(screen.getByRole('radio', { name: 'Vlotte, ritmische slag. (RPE 3)' }).props.accessibilityState)
      .toEqual({ checked: true });
  });
});
