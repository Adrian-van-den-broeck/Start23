// Audit diagnostic only: restore the date assumed by October 5 fixture workouts.
const RealDate = Date;
const fixed = RealDate.parse('2026-10-05T12:00:00Z');
global.Date = class extends RealDate {
  constructor(...args) { super(...(args.length ? args : [fixed])); }
  static now() { return fixed; }
};
