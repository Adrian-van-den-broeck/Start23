import * as query from 'query-string';

const decode = jest.requireActual('decode-uri-component') as (input: string) => string;

test.each([
  ['%2Fcalendar%3Fweek%3D2026-11-09', '/calendar?week=2026-11-09'],
  ['%C3%A5', '\u00e5'], ['%F0%9F%98%80', '\ud83d\ude00'],
  ['%G0', '%G0'], ['%C2', '\ufffd'], ['%41%FF%42', 'A%FFB'],
  ['%2541%FF', '%41%FF'], ['%ED%A0%80', '%ED%A0%80'],
])('patched CJS decoder preserves %s -> %s', (input, expected) => {
  expect(decode(input)).toBe(expected);
});

test('the existing router query-string consumer retains path and Unicode round trips', () => {
  const input = { pathname: '/calendar', name: 'Wombo \u00e5', revision: '7' };
  expect({ ...query.parse(query.stringify(input)) }).toEqual(input);
  expect(query.parse('return=%2Fcalendar&name=Wombo+test')).toEqual({ return: '/calendar', name: 'Wombo test' });
});

test('long malformed percent runs are decoded once without recursive replacement', () => {
  const input = '%41'.repeat(20000) + '%FF';
  expect(query.parse('return=' + input).return).toBe('A'.repeat(20000) + '%FF');
});
