// 승인 pixelfx 원본을 제작 단계에서만 실행한다. node scripts/bake-effects/link.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createFrame, painterFor, composite } from '../../.local-tools/pixelfx/src/core/index.js';
import { encodePNG } from '../../.local-tools/pixelfx/tools/lib/png.mjs';
import * as link from '../../art/charge/approved-teleport-link-v4/link.js';

const out = new URL('../../assets/charge/baked/', import.meta.url);
mkdirSync(out, { recursive: true });
const lengths = [...Array.from({ length: 32 }, (_, i) => i + 1),
  ...Array.from({ length: 8 }, (_, i) => 36 + i * 4),
  ...Array.from({ length: 32 }, (_, i) => 72 + i * 8)];
const sheets = [];
let bytes = 0;
for (const length of lengths) {
  const width = length + 128, height = 128, frames = [];
  let left = width, top = height, right = 0, bottom = 0, time = 0;
  for (let index = 0; index < 12; index++, time += 1 / 30) {
    const frame = createFrame(width, height);
    link.draw(painterFor(frame).place(64, 64), time, { ...link.meta.options, dx: length, dy: 0, seed: 7 });
    const rgba = new Uint8ClampedArray(width * height * 4);
    composite(frame, rgba, null);
    frames.push(rgba);
    for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
      if (!rgba[(y * width + x) * 4 + 3]) continue;
      left = Math.min(left, x); right = Math.max(right, x);
      top = Math.min(top, y); bottom = Math.max(bottom, y);
    }
  }
  for (const x of [64, 64 + length])
    assert.equal(frames[0][(64 * width + x) * 4 + 3], 255, '첫 섬광 끝점');
  if (length === 48) assert.equal(createHash('sha256').update(frames[0]).digest('hex'),
    '4c7acb9c879b6354a468e756d946ae0f9a8172f6a15e700905bfe8f227491c78');
  // 중앙대칭 여백은 회전·가로 배율 후 두 끝점의 위치를 보존한다.
  const padX = Math.max(64 - left, right - 64 - length) + 1;
  const padY = Math.max(64 - top, bottom - 64) + 1;
  const w = length + 2 * padX + 1, h = 2 * padY + 1, columns = 4;
  const sheetWidth = w * columns, sheet = new Uint8Array(sheetWidth * h * 3 * 4);
  const digest = createHash('sha256');
  frames.forEach((rgba, index) => {
    digest.update(rgba);
    for (let y = 0; y < h; y++) {
      const start = ((64 - padY + y) * width + 64 - padX) * 4;
      const target = ((Math.floor(index / columns) * h + y) * sheetWidth + index % columns * w) * 4;
      sheet.set(rgba.subarray(start, start + w * 4), target);
    }
  });
  const file = `link-${String(length).padStart(3, '0')}.png`;
  writeFileSync(new URL(file, out), encodePNG(sheetWidth, h * 3, sheet));
  sheets.push({ length, file, size: [w, h], pad: [padX, padY], frames_sha256: digest.digest('hex') });
  bytes += sheet.byteLength;
}
const source = new URL('../../art/charge/approved-teleport-link-v4/link.js', import.meta.url);
writeFileSync(new URL('link.json', out), JSON.stringify({ count: 12, columns: 4, seed: 7,
  source_sha256: createHash('sha256').update(readFileSync(source)).digest('hex'), sheets }, null, 2) + '\n');
console.log(`${sheets.length}길이 × 12프레임, RGBA ${(bytes / 2 ** 20).toFixed(2)}MiB → ${fileURLToPath(out)}`);
