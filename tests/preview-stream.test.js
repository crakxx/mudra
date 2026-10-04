'use strict';

const assert = require('node:assert/strict');
const { JpegFrameDecoder } = require('../electron/preview-stream');

function packet(payload) {
  const body = Buffer.from(payload);
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.length, 0);
  return Buffer.concat([header, body]);
}

const decoder = new JpegFrameDecoder(1024);

assert.deepEqual(decoder.push(packet('frame-one')), [Buffer.from('frame-one')]);

const split = packet('split-frame');
assert.deepEqual(decoder.push(split.subarray(0, 2)), []);
assert.deepEqual(decoder.push(split.subarray(2, 7)), []);
assert.deepEqual(decoder.push(split.subarray(7)), [Buffer.from('split-frame')]);

const joined = Buffer.concat([packet('a'), packet('bc'), packet('def')]);
assert.deepEqual(
  decoder.push(joined),
  [Buffer.from('a'), Buffer.from('bc'), Buffer.from('def')]
);

const invalid = Buffer.alloc(4);
invalid.writeUInt32BE(2048, 0);
assert.throws(() => decoder.push(invalid), /Invalid preview frame length/);

console.log('Preview stream decoder tests passed.');
