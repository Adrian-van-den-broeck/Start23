import { fireEvent, render } from '@testing-library/react-native';
import { ChoiceChips, DayToggleStrip, IconAction, LinkRow } from './support';
import { isVerificationBuild } from './verificationBuild';

const levels = [{ value: 'low', label: 'Low' }, { value: 'high', label: 'High', accessibilityLabel: 'Fatigue: High' }] as const;

test('radio chips expose one checked option, their own labels and the pressed value', async () => {
  const onPress = jest.fn();
  const view = await render(<ChoiceChips mode="radio" accessibilityLabel="Fatigue" options={levels} isSelected={(value) => value === 'low'} onPress={onPress} />);
  expect(view.getByRole('radio', { name: 'Low' })).toBeChecked();
  expect(view.getByRole('radio', { name: 'Fatigue: High' })).not.toBeChecked();
  await fireEvent.press(view.getByRole('radio', { name: 'Fatigue: High' }));
  expect(onPress).toHaveBeenCalledWith('high');
});

test('checkbox chips stay independent and a disabled set reports nothing', async () => {
  const onPress = jest.fn();
  const view = await render(<ChoiceChips mode="checkbox" disabled options={levels} isSelected={() => true} onPress={onPress} />);
  for (const chip of view.getAllByRole('checkbox')) { expect(chip).toBeChecked(); expect(chip).toBeDisabled(); }
  await fireEvent.press(view.getByRole('checkbox', { name: 'Low' }));
  expect(onPress).not.toHaveBeenCalled();
});

test('the day strip marks days by position and keeps the weekday as the accessible name', async () => {
  const onToggle = jest.fn();
  const days = ['Mon', 'Tue', 'Wed'].map((label, index) => ({ label, date: 12 + index }));
  const view = await render(<DayToggleStrip days={days} isMarked={(index) => index === 2} onToggle={onToggle} />);
  expect(view.getByRole('checkbox', { name: 'Wed' })).toBeChecked();
  expect(view.getByRole('checkbox', { name: 'Mon' })).not.toBeChecked();
  // The date is decoration for the eye; the weekday stays the spoken name.
  expect(view.getByText('14', { includeHiddenElements: true })).toBeTruthy();
  expect(view.queryByText('14')).toBeNull();
  await fireEvent.press(view.getByRole('checkbox', { name: 'Tue' }));
  expect(onToggle).toHaveBeenCalledWith(1);
});

test('link rows and icon actions are named buttons', async () => {
  const open = jest.fn(); const remove = jest.fn();
  const view = await render(<><LinkRow icon="document" label="Tests" hint="Open the protocols." onPress={open} /><IconAction icon="close" label="Remove" onPress={remove} /></>);
  expect(view.getByText('Open the protocols.')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: 'Tests' }));
  await fireEvent.press(view.getByRole('button', { name: 'Remove' }));
  expect(open).toHaveBeenCalledTimes(1); expect(remove).toHaveBeenCalledTimes(1);
});

describe('verification build', () => {
  const keys = ['EXPO_PUBLIC_VERIFICATION_BUILD', 'EXPO_PUBLIC_API_BASE_URL', 'EXPO_PUBLIC_SUPABASE_URL'] as const;
  const saved = keys.map((key) => process.env[key]);
  afterEach(() => keys.forEach((key, index) => { if (saved[index] === undefined) delete process.env[key]; else process.env[key] = saved[index]; }));
  test('needs the flag and both staging hosts', () => {
    process.env.EXPO_PUBLIC_VERIFICATION_BUILD = '1';
    process.env.EXPO_PUBLIC_API_BASE_URL = 'https://r6-api-r6-staging.up.railway.app';
    process.env.EXPO_PUBLIC_SUPABASE_URL = 'https://isfumhgqphieoayqahjv.supabase.co';
    expect(isVerificationBuild()).toBe(true);
    process.env.EXPO_PUBLIC_API_BASE_URL = 'https://api.example.test';
    expect(isVerificationBuild()).toBe(false);
    process.env.EXPO_PUBLIC_API_BASE_URL = 'https://r6-api-r6-staging.up.railway.app';
    delete process.env.EXPO_PUBLIC_VERIFICATION_BUILD;
    expect(isVerificationBuild()).toBe(false);
  });
});
