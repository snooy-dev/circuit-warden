import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward sweep',
  size: [160, 192], origin: [80, 112], duration: .12, fps: 60, loop: false,
};

const ink = ['#071657', '#0034A5', '#007BDB', '#00B5F5', '#5BF7F9', '#DCFFFF'].map(hex);
const arcs = [
  {outside: [[45,1],[52,22],[43,44],[28,59],[10,64],[-12,58]],
   inside: [[45,1],[38,21],[31,35],[19,45],[2,53],[-12,58]]},
  {outside: [[-42,13],[-60,34],[-49,55],[-26,68],[-4,74],[20,70],[45,55],[60,34],[46,10]],
   inside: [[-42,13],[-39,27],[-33,38],[-16,47],[0,50],[17,46],[33,36],[44,25],[46,10]]},
  {outside: [[-46,13],[-54,35],[-44,52],[-25,61],[-5,60]],
   inside: [[-46,13],[-41,32],[-33,43],[-21,50],[-5,60]]},
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
    p.polyline([[-37,40],[-26,50],[-14,48],[1,58],[16,53],[33,42]], ink[5]);
    p.beam(-18,47,1,50,2.4,ink[5]);
    p.beam(1,50,17,46,2.4,ink[5]);
    p.polyline([[-31,59],[-16,66],[1,68],[17,63],[30,59]], ink[2]);
    p.polyline([[9,65],[2,70],[4,75]], ink[4]);
    p.polyline([[-48,45],[-55,49],[-53,54],[-58,56]], ink[4]);
  }
}
