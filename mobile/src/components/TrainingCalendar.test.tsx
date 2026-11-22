import { fireEvent, render, waitFor } from '@testing-library/react-native';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { TrainingCalendar } from './TrainingCalendar';
// These assertions are written in English; Dutch is now the default, so choose English explicitly.
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(async () => 'en'), setItemAsync: jest.fn(async () => undefined), WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'unlocked' }));

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
