import { hex } from '../../../.local-tools/pixelfx/src/core/index.js';

export const meta = {
  name: 'Warden aerial sword sweep',
  size: [224, 208], origin: [112, 120], duration: .3, fps: 60, loop: false,
};

const colors = ['#071657', '#0034A5', '#005FE5', '#00B5F5', '#4CDDFF', '#C3F7FF'].map(hex);
// Each pair ends at the narrow head of the stroke as it follows the fixed blade poses.
const sweeps = [
  [[[5,-59],[19,-66],[38,-63],[55,-49]], [[5,-59],[21,-61],[37,-58],[55,-49]]],
  [[[7,-61],[28,-69],[55,-65],[77,-51],[86,-32]], [[7,-61],[29,-61],[49,-55],[68,-45],[86,-32]]],
  [[[10,-69],[39,-72],[66,-61],[89,-44],[102,-22],[99,0],[86,12],[61,4]],
   [[10,-69],[37,-59],[55,-46],[72,-28],[83,-12],[77,0],[72,6],[61,4]]],
  [[[18,-66],[45,-68],[74,-53],[97,-32],[106,-7],[103,20],[89,43],[62,55],[42,51]],
   [[18,-66],[41,-55],[59,-41],[76,-22],[82,-2],[78,16],[65,36],[53,45],[42,51]]],
  [[[36,-56],[59,-57],[87,-38],[102,-13],[103,13],[89,38],[62,53],[37,49]],
   [[36,-56],[56,-48],[76,-31],[88,-9],[87,11],[75,32],[59,45],[37,49]]],
  [[[62,-37],[81,-36],[98,-15],[100,9],[90,31],[70,48],[48,49]],
   [[62,-37],[76,-30],[91,-12],[91,8],[82,27],[66,43],[48,49]]],
  [[[82,-17],[96,-5],[94,20],[80,37],[57,46]], [[82,-17],[88,-2],[87,17],[76,33],[57,46]]],
  [[[86,13],[85,30],[73,38],[54,43]], [[86,13],[80,28],[69,36],[54,43]]],
];

export function draw(p, t) {
  const frame = Math.floor(t * meta.fps + 1e-6) - 4;
  const sweep = sweeps[frame];
  if (!sweep) return;
  const [outer, inner] = sweep;
  const reverse = [...inner].reverse();
  const band = outer.map(([x,y], i) => [.7*x+.3*inner[i][0], .7*y+.3*inner[i][1]]);
  p.poly([...outer, ...reverse], colors[0]);
  p.poly([...band, ...reverse], colors[frame < 5 ? 2 : 1]);
  if (frame < 5) {
    const lead = outer.map(([x,y], i) => [.34*x+.66*inner[i][0], .34*y+.66*inner[i][1]]);
    p.poly([...lead, ...reverse], colors[3]);
    p.polyline(inner.slice(1, -1), colors[4]);
  }
  if (frame === 2 || frame === 3) {
    for (let i = 3; i < 6; i++) p.beam(...inner[i], ...inner[i+1], 2.4, colors[5]);
    const [x,y] = inner[5];
    p.polyline([[x-3,y-1],[x+7,y+5],[x+12,y-2],[x+17,y+4]], colors[4]);
    const [rimX,rimY] = outer[4];
    p.polyline([[rimX-8,rimY],[rimX-2,rimY-5],[rimX+1,rimY-3],[rimX+4,rimY-6]], colors[4]);
  }
}
