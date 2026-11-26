import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward sweep',
  size: [160, 192], origin: [80, 112], duration: .12, fps: 60, loop: false,
};

const ink = ['#071657', '#0034A5', '#007BDB', '#00B5F5', '#5BF7F9', '#DCFFFF'].map(hex);
const arcs = [
  {outside: [[42,5],[39,24],[32,39],[19,50],[4,55],[-12,51]],
   inside: [[42,5],[33,23],[24,33],[13,40],[1,46],[-12,51]]},
  {outside: [[-47,13],[-43,32],[-32,49],[-17,60],[-3,64],[13,61],[29,51],[40,35],[46,14]],
   inside: [[-47,13],[-32,28],[-23,38],[-12,44],[0,46],[13,44],[25,36],[36,27],[46,14]]},
  {outside: [[-46,18],[-41,37],[-31,50],[-18,55],[-5,54]],
   inside: [[-46,18],[-35,34],[-27,42],[-15,48],[-5,54]]},
];

export function draw(p, time) {
  const frame = Math.floor(time * meta.fps + 1e-7);
  const arc = arcs[frame];
  if (!arc) return;
  const { outside, inside } = arc;
  const reverse = [...inside].reverse();
  p.poly([...outside, ...reverse], ink[0]);
  const rim = outside.map(([x, y], i) => [x * .68 + inside[i][0] * .32, y * .68 + inside[i][1] * .32]);
  p.poly([...rim, ...reverse], ink[frame === 1 ? 3 : 2]);
  if (frame < 2) p.polyline(inside.slice(1,-1), ink[frame === 1 ? 4 : 3]);
  if (frame === 1) {
    p.polyline([[-25,41],[-15,49],[-6,47],[2,53],[16,49],[26,42]], ink[5]);
    p.polyline([[9,62],[2,69],[4,74]], ink[4]);
  }
}
