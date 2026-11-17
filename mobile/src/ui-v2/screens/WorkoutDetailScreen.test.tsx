import { fireEvent, render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { StyleSheet } from 'react-native';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { sourceSegment, sourceWorkout } from '../utils/workout.test-fixtures';
import { WorkoutDetailScreen } from './WorkoutDetailScreen';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));

beforeEach(() => { jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });

test.each(['nl', 'en'])('complete detail in %s preserves mixed units, all source instructions, expected RPE and targets', async (language) => {
  jest.mocked(SecureStore.getItemAsync).mockResolvedValue(language);
  const close = jest.fn();
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={sourceWorkout} onClose={close} /></LanguageProvider>);
  expect(view.getByRole('header', { name: sourceWorkout.name })).toBeTruthy();
  expect(view.getByText(sourceSegment.instructions)).toBeTruthy();
  expect(view.getByText(sourceWorkout.description)).toBeTruthy();
  expect(view.getByText('30.5 min')).toBeTruthy();
  expect(view.getByText('1200 m')).toBeTruthy();
  expect(view.getByText('12.5 min')).toBeTruthy();
  expect(view.getByText('800 m')).toBeTruthy();
  expect(view.getByText(language === 'nl' ? 'Verwachte RPE 2–3' : 'Expected RPE 2–3')).toBeTruthy();
  expect(view.getByText('Zone 2')).toBeTruthy();
  expect(view.getByText(language === 'nl' ? 'RPE-doel 3–4' : 'RPE target 3–4')).toBeTruthy();
  expect(view.getByText('Protocol · RPE 6–7')).toBeTruthy();
  expect(view.getByText(language === 'nl' ? 'Geannuleerd' : 'Cancelled')).toBeTruthy();
  expect(view.getAllByTestId('workout-detail-scroll')).toHaveLength(1);
  expect(view.queryByText('Exact source reference')).toBeNull();
  await fireEvent.press(view.getByRole('button', { name: language === 'nl' ? 'RPE-uitleg' : 'RPE reference' }));
  expect(view.getByText('Exact reference description.')).toBeTruthy();
  await fireEvent.press(view.getByRole('button', { name: language === 'nl' ? 'Sluiten' : 'Close' }));
  await fireEvent(view.getByTestId('workout-detail-modal'), 'requestClose');
  expect(close).toHaveBeenCalledTimes(2);
});

test('distance-only sparse swim uses distance hero, missing-detail state and no invented prescription', async () => {
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={{
    ...sourceWorkout,
    duration_minutes: null, segments: [], description: '', rpe_zones: []
  }} onClose={jest.fn()} /></LanguageProvider>);
  expect(view.getByText('1200 m')).toBeTruthy();
  expect(view.getByText('No further session detail available')).toBeTruthy();
  expect(view.queryByText(/\bmin\b|warm.up|cool.down|equipment|recovery/i)).toBeNull();
  expect(view.queryByText('RPE reference')).toBeNull();
});

test('recursive extra private fields cannot reach rendered text or accessibility props', async () => {
  const hidden = { tss: 987.654, planned_load: 987.654, realized_load: 987.654, physiological_private: 987.654 };
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={{
    ...sourceWorkout, ...hidden,
    segments: [{ ...sourceSegment, ...hidden }]
  }} onClose={jest.fn()} /></LanguageProvider>);
  const serialized = JSON.stringify(view.toJSON());
  expect(serialized).not.toMatch(/tss|planned_load|realized_load|physiological_private|987\.654/i);
});

test('null detail is invisible', async () => {
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={null} onClose={jest.fn()} /></LanguageProvider>);
  expect(view.queryByText('Session sequence')).toBeNull();
});

test('RPE reference retains expanded state and a growing accessible secondary target', async () => {
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={sourceWorkout} onClose={jest.fn()} /></LanguageProvider>);
  const toggle = view.getByRole('button', { name: 'RPE reference', expanded: false });
  expect(StyleSheet.flatten(toggle.props.style).minHeight).toBe(52);
  await fireEvent.press(toggle);
  expect(view.getByRole('button', { name: 'RPE reference', expanded: true })).toBeTruthy();
  expect(view.getByText('Exact reference description.')).toBeTruthy();
  await fireEvent.press(toggle);
  expect(view.queryByText('Exact reference description.')).toBeNull();
});

test('optional protocol, technique and required heart-rate observation survive their visual grouping', async () => {
  const view = await render(<LanguageProvider><WorkoutDetailScreen workout={{
    ...sourceWorkout, segments: [{ ...sourceSegment, is_swim_technique: true,
      protocol_target: { ...sourceSegment.protocol_target!, optional: true } }],
  }} onClose={jest.fn()} /></LanguageProvider>);
  expect(view.getByText('Optional protocol target')).toBeTruthy();
  expect(view.getByText('Technique')).toBeTruthy();
  expect(view.getByText('Heart-rate observation required')).toBeTruthy();
  expect(view.getByText(sourceSegment.instructions)).toBeTruthy();
  expect(view.queryByText(/Start workout|Begin training/i)).toBeNull();
});
