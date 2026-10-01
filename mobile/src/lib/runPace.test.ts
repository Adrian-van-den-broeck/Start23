import { formatRunPace, observedRunPace, parseRunPace } from './runPace';

test('run pace is converted between min:sec/km and canonical whole seconds/km', () => {
  expect(parseRunPace('5:00')).toBe(300);
  expect(parseRunPace('4:35')).toBe(275);
  expect(formatRunPace(300)).toBe('5:00 /km');
  expect(formatRunPace('275')).toBe('4:35 /km');
});

test('30 km in 150 minutes is displayed as 5:00 /km without changing calibration', () => {
  expect(observedRunPace('150', 30000)).toBe('5:00 /km');
});

test('invalid or ambiguous run pace is rejected', () => {
  expect(parseRunPace('300')).toBeNull();
  expect(parseRunPace('5:60')).toBeNull();
  expect(parseRunPace('0:00')).toBeNull();
  expect(formatRunPace(null)).toBe('open');
});
