import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward current',
  size: [160, 192], origin: [80, 112], duration: .18, fps: 60, loop: false, bg: 'dark',
};

const ink = ['#071657', '#0034A5', '#005FE5', '#00B5F5',
  '#4CDDFF', '#C3F7FF', '#FFFFFF'].map(hex);
const points = [[41, -25], [45, -12], [44, 3], [40, 17], [32, 32],
  [22, 46], [9, 59], [-7, 68], [-21, 73]];

export function draw(p, t) {
  const frame = Math.floor(t * meta.fps + 1e-7);
  const end = points.length - 1;
  const start = frame < 3 ? 0 : (frame - 2);
  for (let i = start; i < end; i++) {
    const from = points[i], to = points[i + 1];
    const width = Math.max(1, 2 + Math.min(i, end - i + 1) - Math.max(0, frame - 3));
    p.beam(...from, ...to, width + 2, ink[0]);
    p.beam(...from, ...to, width, ink[2]);
    p.beam(...from, ...to, Math.max(1, width - 2), ink[frame < 4 ? 4 : 3]);
    p.polyline([from, to], ink[frame === 2 || frame === 3 ? 6 : 5]);
  }
  if (frame > 0 && frame < 6) {
    const [x, y] = points[Math.min(end, 6)];
    p.polyline([[x, y], [x + 7, y + 3], [x + 4, y + 8], [x + 10, y + 13]], ink[3]);
  }
}
