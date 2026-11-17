// Review-run setup only. Preserve the existing proposal boundary assertions and
// use the Wednesday date their unchanged approved/pending workout fixtures name.
// No production source, Jest config, timer API or other test clock is changed.
const NativeDate = global.Date;
const fixtureTimestamp = NativeDate.parse('2026-10-07T12:00:00.000Z');
function FixtureDate(...args) {
  if (!new.target) return new NativeDate(fixtureTimestamp).toString();
  return Reflect.construct(NativeDate, args.length ? args : [fixtureTimestamp], new.target);
}
Object.setPrototypeOf(FixtureDate, NativeDate);
FixtureDate.prototype = NativeDate.prototype;
FixtureDate.now = () => fixtureTimestamp;
let originalDate;
beforeEach(() => {
  const name = expect.getState().currentTestName;
  if (name === 'distinct active and pending schedules stay separate before and after explicit approve'
      || name === 'distinct active and pending schedules stay separate before and after explicit reject') {
    originalDate = global.Date;
    global.Date = FixtureDate;
  }
});
afterEach(() => {
  if (originalDate) {
    global.Date = originalDate;
    originalDate = undefined;
  }
});
