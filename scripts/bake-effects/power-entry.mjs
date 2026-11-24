// 등장 전용 2픽셀 낙뢰 시트를 굽는다. node scripts/bake-effects/power-entry.mjs
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { composite, createFrame, hex, painterFor, Rng, sparkle } from '../../.local-tools/pixelfx/src/core/index.js';
import { stroke, zigzag } from '../../.local-tools/pixelfx/src/fx/lightning/_lib.js';
import { encodePNG } from '../../.local-tools/pixelfx/tools/lib/png.mjs';

const out = new URL('../../assets/levels/power-supply/', import.meta.url);
const map = JSON.parse(readFileSync(new URL('map.json', out), 'utf8'));
const spawn = map.spawns.find(({ id }) => id === 'start');
const [sourceX, sourceY] = spawn.entry_origin;
const scale = 2;
const [landingX, landingY] = [(spawn.x - sourceX) / scale, (spawn.feet_y - sourceY) / scale];
assert(Number.isInteger(landingX) && Number.isInteger(landingY), '시작점과 착지점은 2픽셀 격자에 있어야 한다.');

const width = 256, height = 312, pivot = [90, 39], columns = 4;
const frameMs = 20, impactFrame = 4, count = 17;
const palette = ['#0b1534', '#142d66', '#244aa4', '#447bda', '#5f9bf5', '#95c9ff', '#cbeaff', '#f8fcff'].map(hex);
const bolt = zigzag(new Rng(29), 0, 0, landingX, landingY, .15, 1);
const sparks = new Rng(41);
const debris = Array.from({length: 22}, (_, i) => ({
  dx: (i % 2 ? -1 : 1) * sparks.range(8, 48),
  height: sparks.range(3, 28),
  life: sparks.range(5, 12),
}));
const sheetWidth = width * columns;
const sheetHeight = height * Math.ceil(count / columns);
const sheet = new Uint8Array(sheetWidth * sheetHeight * 4);

for (let i = 0; i < count; i++) {
  const frame = createFrame(width, height);
  const p = painterFor(frame).place(...pivot);
  const after = i - impactFrame;
  if (after < 0) {
    sparkle(p, 0, 0, 2 + i * 2, palette[6], palette[4]);
    if (i > 1) stroke(p, {paths: [bolt.paths[0]]}, .38, palette, .55, {upTo: i === 2 ? .28 : .64, light: .1});
  } else {
    const strength = [1, .87, .66, .42, .28][after] ?? 0;
    stroke(p, bolt, strength, palette, after < 2 ? 2.0 : 1.25,
      {hero: after === 0, core: after < 2 ? 1.24 : .6, light: .18, a: after < 3 ? 1 : .55});
    if (after < 4) {
      p.glow(landingX, landingY - 4, 21, palette[5], .8 - .17 * after);
      sparkle(p, landingX, landingY - 1, 15 - 3 * after, palette[7], palette[5]);
    }
    for (const {dx, height: lift, life} of debris) {
      const t = (after + 1) / life;
      if (t >= 1) continue;
      const x = landingX + dx * t;
      const y = landingY - lift * 4 * t * (1 - t);
      p.line(x - dx * .08, y - 1, x, y, palette[t < .35 ? 6 : 4], 1 - t * .65);
    }
  }
  const rgba = new Uint8ClampedArray(width * height * 4);
  composite(frame, rgba, null);
  const alphaAt = (x, y) => rgba[((pivot[1] + y) * width + pivot[0] + x) * 4 + 3];
  for (let x = 0; x < width; x++) {
    assert(!rgba[x * 4 + 3] && !rgba[((height - 1) * width + x) * 4 + 3], '상하 여백');
  }
  for (let y = 0; y < height; y++) {
    assert(!rgba[y * width * 4 + 3] && !rgba[((y + 1) * width - 1) * 4 + 3], '좌우 여백');
  }
  if (i === impactFrame) {
    assert.equal(alphaAt(0, 0), 255, '케이블 접점');
    assert.equal(alphaAt(landingX, landingY), 255, '착지 접점');
  }
  if (i === count - 1) assert(!rgba.some(Boolean), '마지막 프레임은 비어 있어야 한다.');
  for (let y = 0; y < height; y++) {
    const start = y * width * 4;
    const row = Math.floor(i / columns) * height + y;
    sheet.set(rgba.subarray(start, start + width * 4), (row * sheetWidth + (i % columns) * width) * 4);
  }
}

const file = 'power-entry.png';
writeFileSync(new URL(file, out), encodePNG(sheetWidth, sheetHeight, sheet));
writeFileSync(new URL('power-entry.json', out), JSON.stringify({
  file, frameSize: [width, height], columns, count, pivot, scale, impactMs: impactFrame * frameMs,
  durationsMs: Array(count).fill(frameMs), loop: false,
}, null, 2) + '\n');
