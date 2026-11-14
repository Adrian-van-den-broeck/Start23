import { errorEnvelope } from './responseValidation';

test('only the allowlisted A5 planning discriminator survives untrusted details', () => {
  expect(errorEnvelope({ error: { code: 'validation_failed', details: {
    planning_code: 'v6_search_incomplete', frozen_context: 'private', node_count: 200001,
  } } })).toEqual({ error: { code: 'validation_failed', details: {
    violations: [], planning_code: 'v6_search_incomplete',
  } } });
});

test.each([
  ['validation_failed', 'private_unrecognized_code'],
  ['state_conflict', 'v6_search_incomplete'],
  ['validation_failed', { private: 'payload' }],
  ['validation_failed', null],
])('unrecognized planning details do not change the envelope for %s', (code, planning_code) => {
  expect(errorEnvelope({ error: { code, details: { planning_code } } })).toEqual({
    error: { code, details: { violations: [] } },
  });
});
