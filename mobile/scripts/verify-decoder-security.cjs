// Verify a mechanical export-only adaptation and the real query-string consumer.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const vendor = path.join(__dirname, '../vendor/decode-uri-component');
const provenance = JSON.parse(fs.readFileSync(path.join(vendor, 'PROVENANCE.json')));
const original = fs.readFileSync(path.join(vendor, 'upstream-index.mjs'), 'utf8');
const adapted = fs.readFileSync(path.join(vendor, 'index.cjs'), 'utf8');
assert.equal(crypto.createHash('sha256').update(original).digest('hex'), provenance.upstream_source_sha256);
assert.equal(crypto.createHash('sha256').update(adapted).digest('hex'), provenance.adapted_source_sha256);
const reversed = adapted.replace(/^'use strict';\n\n/, '')
  .replace('module.exports = function decodeUriComponent(encodedURI) {', 'export default function decodeUriComponent(encodedURI) {')
  .replace(/};\n$/, '}\n');
assert.equal(reversed, original, 'The patched upstream algorithm must remain byte-identical after undoing export syntax');
const decode = require('decode-uri-component');
assert.equal(typeof decode, 'function');
const query = require('query-string');
const fixtures = [
  ['hello%20world', 'hello world'], ['%C3%A5', '\u00e5'], ['%F0%9F%98%80', '\ud83d\ude00'],
  ['literal+plus', 'literal+plus'], ['100%', '100%'], ['%G0', '%G0'],
  ['%C2', '\ufffd'], ['%FE%FF', '\ufffd\ufffd'], ['%41%FF%42', 'A%FFB'],
];
for (const [input, expected] of fixtures) assert.equal(decode(input), expected);
assert.throws(() => decode(null), TypeError);
assert.equal(query.parse('name=Wombo+test&return=%2Fcalendar').return, '/calendar');
assert.equal(query.parse('name=Wombo+test&return=%2Fcalendar').name, 'Wombo test');
// A process deadline contains a regression/hang without executing any input as code.
const child = spawnSync(process.execPath, ['-e', `
  const assert = require('node:assert/strict');
  const decode = require('decode-uri-component');
  const query = require('query-string');
  const input = '%41'.repeat(100000) + '%FF';
  assert.equal(decode(input), 'A'.repeat(100000) + '%FF');
  assert.equal(query.parse('x=' + input).x, 'A'.repeat(100000) + '%FF');
`], { cwd: path.join(__dirname, '..'), timeout: 10000, encoding: 'utf8' });
assert.ifError(child.error); assert.equal(child.status, 0, child.stderr);
console.log('PASS: patched decoder source provenance, CommonJS consumer, Unicode/malformed input and bounded adversarial decoding');
