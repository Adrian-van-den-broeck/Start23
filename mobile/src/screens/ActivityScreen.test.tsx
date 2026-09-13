import { render } from '@testing-library/react-native';

import { ActivityMeasurementNotices } from './ActivityScreen';

describe('ActivityMeasurementNotices', () => {
  test('distance-only activity explicitly refuses duration inference', async () => {
    const screen = await render(
      <ActivityMeasurementNotices
        distanceMeters={1500}
        durationMinutes={null}
        language="en"
        zoneMinutes={null}
      />,
    );

    expect(
      screen.getByText(
        'Distance recorded. Duration and time in zone were not measured and are not inferred.',
      ),
    ).toBeTruthy();
  });

  test('partial HR coverage says missing minutes were not estimated', async () => {
    const screen = await render(
      <ActivityMeasurementNotices
        distanceMeters={10000}
        durationMinutes="60"
        language="en"
        zoneMinutes={['10', '20', '8', '3', '0']}
      />,
    );

    expect(
      screen.getByText(
        'Partial sensor coverage: only observed zone time was used; missing minutes were not estimated.',
      ),
    ).toBeTruthy();
  });
});
