import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward current',
  size: [160, 192], origin: [80, 112], duration: .18, fps: 60, loop: false, bg: 'dark',
};

const ink = ['#071657', '#005FE5', '#00B5F5', '#4CDDFF', '#C3F7FF'].map(hex);
const points = [[11, 33], [12, 41], [11, 50], [8, 59], [4, 67], [0, 74]];

export function draw(p, t) {
  const frame = Math.floor(t * meta.fps + 1e-7);
  const last = points.length - 1;
  const end = frame <= 1 ? last : Math.max(0, last - (frame - 1));
  for (let i = 0; i < end; i++) {
    const from = points[i], to = points[i + 1];
    const width = Math.max(1, 5 - i - Math.max(0, frame - 1));
    p.beam(...from, ...to, width + 2, ink[0]);
    p.beam(...from, ...to, width, ink[1]);
    p.beam(...from, ...to, Math.max(1, width - 2), ink[frame < 2 ? 3 : 2]);
    if (frame < 2) p.polyline([from, to], ink[4]);
  }
}
