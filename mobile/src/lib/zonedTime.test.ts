import { fromWallClock, shiftDate, toWallClock } from './zonedTime';

describe('zonedTime', () => {
  test('reads the wall clock of an instant in the given zone', () => {
    expect(toWallClock(new Date('2026-08-15T07:00:00Z'), 'Europe/Amsterdam'))
      .toEqual({ year: 2026, month: 8, day: 15, hour: 9, minute: 0 });
    expect(toWallClock(new Date('2026-01-15T07:00:00Z'), 'Europe/Amsterdam'))
      .toEqual({ year: 2026, month: 1, day: 15, hour: 8, minute: 0 });
  });

  test('turns a wall clock back into the exact instant, in summer and winter', () => {
    expect(fromWallClock({ year: 2026, month: 8, day: 15, hour: 9, minute: 0 }, 'Europe/Amsterdam').toISOString())
      .toBe('2026-08-15T07:00:00.000Z');
    expect(fromWallClock({ year: 2026, month: 1, day: 15, hour: 8, minute: 30 }, 'Europe/Amsterdam').toISOString())
      .toBe('2026-01-15T07:30:00.000Z');
    expect(fromWallClock({ year: 2026, month: 8, day: 15, hour: 6, minute: 15 }, 'America/New_York').toISOString())
      .toBe('2026-08-15T10:15:00.000Z');
  });

  test('round-trips around the autumn DST change', () => {
    const clock = { year: 2026, month: 10, day: 25, hour: 4, minute: 0 };
    expect(toWallClock(fromWallClock(clock, 'Europe/Amsterdam'), 'Europe/Amsterdam')).toEqual(clock);
  });

  test('shifts calendar dates across month and year boundaries', () => {
    expect(shiftDate({ year: 2027, month: 1, day: 1, hour: 0, minute: 0 }, 1)).toEqual({ year: 2026, month: 12, day: 31 });
  });
});
