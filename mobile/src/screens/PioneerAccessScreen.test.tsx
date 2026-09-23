import { fireEvent, render, waitFor } from '@testing-library/react-native';

import { getPioneerRedemption, redeemPioneerAccess } from '../api/client';
import { PioneerAccessScreen } from './PioneerAccessScreen';

jest.mock('../api/client', () => ({
  getPioneerRedemption: jest.fn(),
  redeemPioneerAccess: jest.fn(),
}));

describe('PioneerAccessScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(getPioneerRedemption).mockResolvedValue(null);
  });

  test('redeems a valid normalized code with one idempotency key', async () => {
    jest.mocked(redeemPioneerAccess).mockResolvedValue({
      program: 'pioneer',
      status: 'active',
      redeemed_at: '2026-09-23T08:00:00Z',
    });
    const screen = await render(
      <PioneerAccessScreen accessToken="athlete-token" onBack={jest.fn()} />,
    );
    await screen.findByLabelText('Pioneer access-code');

    await fireEvent.changeText(
      screen.getByLabelText('Pioneer access-code'),
      'valid-code',
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Code inwisselen' }),
    );

    await waitFor(() =>
      expect(redeemPioneerAccess).toHaveBeenCalledWith(
        'athlete-token',
        expect.any(String),
        'VALID-CODE',
      ),
    );
    expect(await screen.findByText('Pioneer toegang actief')).toBeTruthy();
  });

  test('surfaces a deterministic rejected-code error', async () => {
    jest.mocked(redeemPioneerAccess).mockRejectedValue(
      new Error('The Pioneer access code has expired.'),
    );
    const screen = await render(
      <PioneerAccessScreen accessToken="athlete-token" onBack={jest.fn()} />,
    );
    await screen.findByLabelText('Pioneer access-code');

    await fireEvent.changeText(
      screen.getByLabelText('Pioneer access-code'),
      'EXPIRED1',
    );
    await fireEvent.press(
      screen.getByRole('button', { name: 'Code inwisselen' }),
    );

    expect(
      await screen.findByRole('alert', {
        name: 'The Pioneer access code has expired.',
      }),
    ).toBeTruthy();
  });
});
