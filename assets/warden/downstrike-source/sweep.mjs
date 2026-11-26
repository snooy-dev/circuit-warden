import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden downward sweep',
  size: [208, 208], origin: [104, 112], duration: .12, fps: 60, loop: false,
};

const ink = ['#071657', '#0034A5', '#007BDB', '#00B5F5', '#5BF7F9', '#DCFFFF'].map(hex);
const arcs = [
  {outside: [[61,-8],[68,16],[57,44],[37,64],[12,73],[-10,67]],
   inside: [[61,-8],[53,14],[40,33],[23,49],[5,59],[-10,67]]},
  {outside: [[-63,-10],[-77,16],[-67,44],[-43,65],[-15,77],[12,78],[41,67],[66,46],[77,17],[62,-10]],
   inside: [[-63,-10],[-57,12],[-47,30],[-30,42],[-10,47],[10,47],[29,42],[45,31],[57,12],[62,-10]]},
  {outside: [[-60,-2],[-72,20],[-58,46],[-36,62],[-9,70],[9,66]],
   inside: [[-60,-2],[-57,18],[-46,34],[-27,48],[-8,57],[9,66]]},
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
    p.polyline([[-60,34],[-46,49],[-34,52],[-21,61],[-8,59],[4,65],[18,58],[37,54],[55,41]], ink[5]);
    p.beam(-31,44,-10,48,3,ink[5]);
    p.beam(-10,48,12,48,3,ink[5]);
    p.beam(12,48,31,43,3,ink[5]);
    p.polyline([[-46,60],[-24,71],[2,74],[22,70],[42,60]], ink[2]);
    p.polyline([[3,68],[-4,74],[0,82]], ink[4]);
    p.polyline([[-55,45],[-64,50],[-61,57],[-70,61]], ink[4]);
  }
}
