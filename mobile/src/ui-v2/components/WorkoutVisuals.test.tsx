import { render } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { StyleSheet } from 'react-native';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { sourceSegment, sourceWorkout } from '../utils/workout.test-fixtures';
import { workoutDetailViewModel } from '../utils/workoutDetailViewModel';
import { workoutSummaryViewModel } from '../utils/workoutSummaryViewModel';
import { WorkoutSummary } from './WorkoutSummary';
import { SessionSequence } from './SessionSequence';

jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn() }));
beforeEach(() => { jest.mocked(SecureStore.getItemAsync).mockResolvedValue('en'); });

test.each(['run', 'bike', 'swim'] as const)('%s summary retains every supplied measure, title and state without making effort a warning', async discipline => {
  const input = { ...sourceWorkout, discipline, intensity_bucket: 'high' as const };
  const before = JSON.stringify(input);
  const view = await render(<LanguageProvider><WorkoutSummary summary={workoutSummaryViewModel(input)} variant="focus" /></LanguageProvider>);
  expect(view.getByRole('header', { name: input.name })).toBeTruthy();
  expect(view.getByText('30.5 min')).toBeTruthy();
  expect(view.getByText('1200 m')).toBeTruthy();
  expect(view.getByText('Hard')).toBeTruthy();
  expect(view.getByText('Cancelled')).toBeTruthy();
  expect(JSON.stringify(input)).toBe(before);
  expect(view.queryByRole('button')).toBeNull();
});

test.each([[null, 1200], [null, null]] as const)('missing time with distance %s / %s never creates a time value or empty numeric fact', async (duration, distance) => {
  const view = await render(<LanguageProvider><WorkoutSummary summary={workoutSummaryViewModel({
    ...sourceWorkout, duration_minutes: duration, distance_meters: distance,
  })} /></LanguageProvider>);
  expect(view.queryByText(/\bmin\b/)).toBeNull();
  expect(view.queryByText('1200 m') !== null).toBe(distance !== null);
  expect(view.getByText('Easy')).toBeTruthy();
});

test('sequence keeps nonascending supplied order, every target branch and exact multiline instructions', async () => {
  const segments = [sourceSegment,
    { ...sourceSegment, sequence: 4, zone_target: null },
    { ...sourceSegment, sequence: 2, zone_target: null, rpe_target: null },
    { ...sourceSegment, sequence: 3, zone_target: null, rpe_target: null, protocol_target: null },
  ];
  const before = JSON.stringify(segments);
  const model = workoutDetailViewModel({ ...sourceWorkout, segments });
  const view = await render(<LanguageProvider><SessionSequence segments={model.segments} /></LanguageProvider>);
  expect(view.getAllByTestId(/segment-heading-/).map(node => node.props.children.join('')))
    .toEqual(['1. Source segment', '4. Source segment', '2. Source segment', '3. Source segment']);
  expect(view.getAllByText(sourceSegment.instructions)).toHaveLength(4);
  expect(view.getByText('Zone 2')).toBeTruthy();
  expect(view.getAllByText('RPE target 3–4')).toHaveLength(2);
  expect(view.getAllByText('Protocol · RPE 6–7')).toHaveLength(3);
  expect(view.getByText('Expected RPE 5')).toBeTruthy();
  expect(JSON.stringify(segments)).toBe(before);
  for (const heading of view.getAllByTestId(/segment-heading-/)) {
    expect(heading.props.numberOfLines).toBeUndefined();
    expect(heading.props.maxFontSizeMultiplier).toBeUndefined();
    expect(StyleSheet.flatten(heading.props.style).fontSize).toBe(22);
  }
});
