import { render } from '@testing-library/react-native';
import { workoutDetailViewModel } from '../ui-v2/utils/workoutDetailViewModel';
import { sourceWorkout } from '../ui-v2/utils/workout.test-fixtures';
import { SegmentProfile } from './SegmentProfile';

const segment = workoutDetailViewModel(sourceWorkout).segments[0];
test.each([
  [[{ durationMinutes: '5', distanceMeters: null }, { durationMinutes: '15', distanceMeters: null }], [5, 15]],
  [[{ durationMinutes: null, distanceMeters: 200 }, { durationMinutes: null, distanceMeters: 400 }], [200, 400]],
  [[{ durationMinutes: '5', distanceMeters: null }, { durationMinutes: null, distanceMeters: 400 }], null],
  [[], null],
] as const)('draws only comparable public segments in source order', async (measures, expected) => {
  const segments = measures.map(item => ({ ...segment, measures: item }));
  const view = await render(<SegmentProfile segments={segments} />);
  const strip = view.queryByTestId('segment-profile', { includeHiddenElements: true });
  if (!expected) expect(strip).toBeNull();
  else {
    expect(strip?.props.accessibilityElementsHidden).toBe(true);
    expect(strip?.props.children.map((bar: { props: { style: { flexGrow: number } } }) => bar.props.style.flexGrow)).toEqual(expected);
  }
});
