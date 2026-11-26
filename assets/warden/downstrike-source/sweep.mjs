import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward current',
  size: [160, 192], origin: [80, 112], duration: .18, fps: 60, loop: false, bg: 'dark',
};

const ink = ['#071657', '#0034A5', '#005FE5', '#00B5F5',
  '#4CDDFF', '#C3F7FF', '#FFFFFF'].map(hex);
const points = [[36, 8], [32, 19], [24, 28], [16, 33], [10, 35],
  [7, 46], [1, 53], [3, 60], [-2, 65], [0, 73]];

export function draw(p, t) {
  const frame = Math.floor(t * meta.fps + 1e-7);
  const end = points.length - 1;
  const start = frame < 2 ? 0 : Math.min(end, frame + 1);
  const stop = frame === 0 ? 7 : end;
  for (let i = start; i < stop; i++) {
    const from = points[i], to = points[i + 1];
    const width = Math.max(1, 1 + Math.min(i, end - i + 1) - Math.max(0, frame - 2));
    p.beam(...from, ...to, width + 2, ink[0]);
    p.beam(...from, ...to, width, ink[2]);
    p.beam(...from, ...to, Math.max(1, width - 2), ink[frame < 4 ? 4 : 3]);
    p.polyline([from, to], ink[frame === 2 || frame === 3 ? 6 : 5]);
  }
}
