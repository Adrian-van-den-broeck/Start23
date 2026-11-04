// Local, deterministic compatibility probes; never executes quoted shell input.
const assert = require('node:assert/strict');
const quote = require('shell-quote');
for (const newline of ['\n', '\r', '\u2028', '\u2029']) {
  assert.throws(() => quote.quote(['echo', { comment: 'comment' }, `a${newline}ignored`]), TypeError);
}
assert.deepEqual(quote.parse(quote.quote(['hello world', 'a$b', 'literal;value'])), ['hello world', 'a$b', 'literal;value']);
const { DOMParser, XMLSerializer } = require('@xmldom/xmldom');
const xml = new DOMParser().parseFromString('<root><name>Wombo &amp; test</name></root>', 'text/xml');
assert.equal(xml.documentElement.textContent, 'Wombo & test');
assert.match(new XMLSerializer().serializeToString(xml), /Wombo &amp; test/);
const plist = require('plist');
assert.deepEqual(plist.parse(plist.build({ name: 'Wombo', enabled: true })), { name: 'Wombo', enabled: true });
const brace = require('brace-expansion').expand;
assert.deepEqual(brace('file-{a,b}.js'), ['file-a.js', 'file-b.js']);
const legacyBrace = require('../node_modules/@jest/reporters/node_modules/brace-expansion');
assert.deepEqual(legacyBrace('file-{a,b}.js'), ['file-a.js', 'file-b.js']);
const forge = require('node-forge');
assert.equal(forge.md.sha256.create().update('abc').digest().toHex(), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
const { SourceMapGenerator, SourceMapConsumer } = require('source-map-js');
const generator = new SourceMapGenerator({ file: 'app.js' });
generator.addMapping({ source: 'input.js', original: { line: 1, column: 0 }, generated: { line: 1, column: 0 } });
assert.equal(new SourceMapConsumer(generator.toJSON()).originalPositionFor({ line: 1, column: 0 }).source, 'input.js');
console.log('PASS: patched shell quoting, XML/plist, brace expansion, crypto and source-map compatibility');
