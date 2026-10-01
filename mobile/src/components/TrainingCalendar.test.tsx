import { fireEvent, render, waitFor } from '@testing-library/react-native';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { TrainingCalendar } from './TrainingCalendar';

test('rapid Month and Week switching keeps a seven-day week and requests its latest range', async () => {
  const onRangeChange = jest.fn();
  const screen = await render(
    <LanguageProvider>
      <TrainingCalendar initialDate="2026-09-23" loading={false}
        onOpenWorkout={jest.fn()} onRangeChange={onRangeChange}
        restDays={[]} workouts={[]} />
    </LanguageProvider>,
  );
  for (const mode of ['Month', 'Week', 'Month', 'Week']) {
    await fireEvent.press(screen.getByRole('tab', { name: mode }));
  }
  await waitFor(() => expect(onRangeChange).toHaveBeenLastCalledWith('2026-09-21', '2026-09-28'));
  expect(screen.getByRole('tab', { name: 'Week' }).props.accessibilityState.selected).toBe(true);
});
