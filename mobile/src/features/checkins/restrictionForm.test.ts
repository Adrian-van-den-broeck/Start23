import type { CheckInRestriction, RestrictionStatus } from '../../api/types';
import { activeRestriction, none, restrictedAnswers } from './checkIn.test-fixtures';
import { restoreRestrictions, restrictionPayload } from './restrictionForm';

test.each<RestrictionStatus>(['none', 'self_reported_limited', 'self_reported_blocked', 'professional_restricted', 'clearance_required', 'expired'])(
  '%s survives restore and unchanged serialization with complete provenance', status => {
    const decision: CheckInRestriction = { ...restrictedAnswers[0], status, athlete_plan_choice: status === 'none' ? 'resume_unrestricted' : status === 'self_reported_limited' ? 'train_low_only' : 'keep_blocked' };
    const form = restoreRestrictions([decision], []);
    expect(restrictionPayload('run', form.run)).toEqual(decision);
    expect(form.swim.choice).toBeNull();
    expect(form.bike.choice).toBeNull();
  },
);
test.each([undefined, null, 'Fysiotherapeut: bewaarde tekst'])('retains optional/null advice representation %s', advice => {
  const decision: CheckInRestriction = { ...none('run'), professional_advice: advice, professional_advice_at: advice ? '2026-10-01T12:00:00Z' : advice };
  expect(restrictionPayload('run', restoreRestrictions([decision], []).run)).toEqual(decision);
});
test('missing answers are not unrestricted decisions', () => {
  const form = restoreRestrictions([], []);
  expect(Object.values(form).every(value => value.choice === null)).toBe(true);
  expect(() => restrictionPayload('run', form.run)).toThrow('Beoordeel');
});
test('active restrictions remain blocked beyond their review date and require explicit review', () => {
  const decision = restrictedAnswers[0];
  const form = restoreRestrictions([], [activeRestriction(decision)]);
  expect(form.run.choice).toBe('professional');
  expect(form.run.reviewed).toBe(false);
  expect(() => restrictionPayload('run', form.run)).toThrow('Beoordeel');
  expect(restrictionPayload('run', { ...form.run, reviewed: true })).toEqual(decision);
});
test('saved explicit choice is presented alongside earlier advice rather than replaced', () => {
  const form = restoreRestrictions([none('run')], [activeRestriction()]);
  expect(form.run.choice).toBe('none');
  expect(form.run.previous?.professional_advice).toBe(restrictedAnswers[0].professional_advice);
  expect(() => restrictionPayload('run', form.run)).toThrow('Beoordeel');
});
test('explicit athlete resumption retains the advice shown during that choice', () => {
  const form = restoreRestrictions(restrictedAnswers, []);
  expect(restrictionPayload('run', { ...form.run, choice: 'none' })).toEqual({
    ...restrictedAnswers[0], status: 'none', source: 'athlete', athlete_plan_choice: 'resume_unrestricted',
  });
});
test('retains saved order and never includes cleared historical restrictions', () => {
  const form = restoreRestrictions(restrictedAnswers, [{ ...activeRestriction(), cleared_at: '2026-10-20T12:00:00Z' }]);
  expect(Object.keys(form).map(key => restrictionPayload(key as CheckInRestriction['discipline'], form[key as CheckInRestriction['discipline']]))).toEqual(restrictedAnswers);
  expect(form.run.previous).toBeNull();
});
test('ambiguous duplicate decisions or an unsupported prior source fail closed', () => {
  expect(() => restoreRestrictions([none('run'), none('run')], [])).toThrow('eenduidig');
  expect(() => restoreRestrictions([], [activeRestriction(), activeRestriction()])).toThrow('eenduidig');
  expect(() => restoreRestrictions([], [{ ...activeRestriction(), source: 'unrecognized' }])).toThrow('bron');
});

test.each(['status', 'athlete_plan_choice'] as const)('missing saved %s cannot become an unrestricted answer', field => {
  const incomplete = { ...none('run') };
  delete (incomplete as Partial<CheckInRestriction>)[field];
  expect(() => restoreRestrictions([incomplete], [])).toThrow('onvolledig');
});

test('an absent cleared marker is not evidence that an active restriction was cleared', () => {
  const incomplete = { ...activeRestriction() };
  delete (incomplete as Partial<typeof incomplete>).cleared_at;
  expect(() => restoreRestrictions([], [incomplete])).toThrow('onvolledig');
});
