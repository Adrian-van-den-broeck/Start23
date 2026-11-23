/**
 * Wall-clock time in an IANA time zone, to let an athlete pick "Saturday 07:15"
 * in their confirmed profile zone while the API still receives an exact instant.
 */
export type WallClock = { year: number; month: number; day: number; hour: number; minute: number };
export type CalendarDate = Pick<WallClock, 'year' | 'month' | 'day'>;

export function toWallClock(instant: Date, timeZone: string): WallClock {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(instant);
  const get = (type: Intl.DateTimeFormatPartTypes) => Number(parts.find((part) => part.type === type)?.value);
  return { year: get('year'), month: get('month'), day: get('day'), hour: get('hour') % 24, minute: get('minute') };
}

function asUtcMillis(clock: WallClock): number {
  return Date.UTC(clock.year, clock.month - 1, clock.day, clock.hour, clock.minute);
}

/** The instant at which `timeZone` shows `clock`. A skipped DST time resolves to the shifted instant. */
export function fromWallClock(clock: WallClock, timeZone: string): Date {
  const target = asUtcMillis(clock);
  let guess = target;
  // Two corrections settle the zone offset, including across a DST change.
  for (let step = 0; step < 2; step += 1) {
    guess += target - asUtcMillis(toWallClock(new Date(guess), timeZone));
  }
  return new Date(guess);
}

/** Calendar date `days` before the given wall-clock date, ignoring time of day. */
export function shiftDate(clock: CalendarDate, days: number): CalendarDate {
  const date = new Date(Date.UTC(clock.year, clock.month - 1, clock.day - days));
  return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1, day: date.getUTCDate() };
}

export function sameDate(a: CalendarDate, b: CalendarDate): boolean {
  return a.year === b.year && a.month === b.month && a.day === b.day;
}
