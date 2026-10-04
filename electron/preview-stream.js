'use strict';

class JpegFrameDecoder {
  constructor(maxFrameBytes = 512 * 1024) {
    this.maxFrameBytes = maxFrameBytes;
    this.buffer = Buffer.alloc(0);
  }

  push(chunk) {
    if (!Buffer.isBuffer(chunk)) chunk = Buffer.from(chunk);
    if (chunk.length) this.buffer = Buffer.concat([this.buffer, chunk]);

    const frames = [];
    while (this.buffer.length >= 4) {
      const length = this.buffer.readUInt32BE(0);
      if (length < 1 || length > this.maxFrameBytes) {
        this.buffer = Buffer.alloc(0);
        throw new Error(`Invalid preview frame length: ${length}`);
      }
      if (this.buffer.length < 4 + length) break;
      frames.push(Buffer.from(this.buffer.subarray(4, 4 + length)));
      this.buffer = this.buffer.subarray(4 + length);
    }
    return frames;
  }
}

module.exports = { JpegFrameDecoder };
