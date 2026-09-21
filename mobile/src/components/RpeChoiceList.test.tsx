import { fireEvent, render } from '@testing-library/react-native';

import { RpeChoiceList } from './RpeChoiceList';

describe('RpeChoiceList', () => {
  test('presents textual meaning and returns the canonical value', async () => {
    const onSelect = jest.fn();
    const screen = await render(
      <RpeChoiceList
        discipline="run"
        label="Hoe voelde dit?"
        onSelect={onSelect}
      />,
    );

    expect(screen.getAllByRole('radio')).toHaveLength(10);
    await fireEvent.press(
      screen.getByRole('radio', {
        name: 'Diepe ademhaling (10k wedstrijdtempo). (RPE 7)',
      }),
    );
    expect(onSelect).toHaveBeenCalledWith(7);
  });
});
