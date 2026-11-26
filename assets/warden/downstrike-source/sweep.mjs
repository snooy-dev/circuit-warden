import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward sweep',
  size: [160, 192], origin: [80, 112], duration: .12, fps: 60, loop: false,
};

const ink = ['#071657', '#0034A5', '#007BDB', '#00B5F5', '#5BF7F9', '#DCFFFF'].map(hex);
const arcs = [
  {outside: [[24,26],[34,34],[39,45],[34,56],[24,66],[12,72],[2,74]],
   inside:  [[24,26],[28,36],[29,44],[26,53],[19,61],[10,68],[2,74]]},
  {outside: [[-6,31],[-15,43],[-21,54],[-18,66],[-5,74],[9,73],[24,65],[34,51]],
   inside:  [[-6,31],[-9,47],[-10,55],[-7,61],[1,66],[12,67],[24,60],[34,51]]},
  {outside: [[-26,25],[-34,36],[-35,48],[-28,59],[-17,67],[-1,72],[10,68]],
   inside:  [[-26,25],[-29,37],[-28,47],[-21,55],[-11,62],[0,68],[10,68]]},
  {outside: [[-28,25],[-32,38],[-31,50],[-22,61],[-10,64],[1,64]],
   inside:  [[-28,25],[-29,38],[-27,49],[-20,57],[-8,61],[1,64]]},
  {outside: [[-17,30],[-24,36],[-28,47],[-27,54]],
   inside:  [[-17,30],[-22,38],[-25,47],[-27,54]]},
];

export function draw(p, time) {
  const frame = Math.floor(time * meta.fps + 1e-7);
  const arc = arcs[frame];
  if (!arc) return;
  const { outside, inside } = arc;
  p.poly([...outside, ...[...inside].reverse()], ink[0]);
  const innerEdge = outside.map(([x, y], i) => [x * .3 + inside[i][0] * .7, y * .3 + inside[i][1] * .7]);
  p.poly([...innerEdge, ...[...inside].reverse()], ink[frame < 3 ? 3 : 1]);
  if (frame < 3) p.polyline(inside.slice(1, -1), ink[frame === 1 ? 4 : 2]);
  if (frame === 1) p.polyline(inside.slice(3, 6), ink[5]);
}
