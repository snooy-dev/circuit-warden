import { readFileSync } from 'node:fs';
import { composite, createFrame, hex, painterFor } from '../../../.local-tools/pixelfx/src/core/index.js';

const palette = ['#002B64','#0050B1','#0091E5','#00C3ED','#19EFF6','#A3FDFD','#DCFFFF'].map(hex);
const stops = [[], [], [8,18,2], [8,35,7], [8,47,17], [16,66,11], [32,71,3.8], [], [], []];
const path = JSON.parse(readFileSync(0, 'utf8'));
const frames = [];

for (const [index, stop] of stops.entries()) {
  const frame = createFrame(208, 208);
  if (stop.length) {
    const painter = painterFor(frame);
    const [start, end, maxWidth] = stop;
    const arc = path.slice(start, end + 1);
    const curve = [];
    for (let i = 0; i < arc.length; i++) {
      const [x,y] = arc[i];
      const [a,b] = arc[Math.max(i - 1, 0)];
      const [c,d] = arc[Math.min(i + 1, arc.length - 1)];
      const length = Math.hypot(c-a,d-b);
      const t = i / (arc.length-1);
      const taper = Math.sin(Math.PI*t)**.72 * (.4+.6*t);
      curve.push({ x, y, nx: (d-b)/length, ny: (a-c)/length, width: maxWidth*taper });
    }
    const edge = (inner) => curve.map(({x,y,nx,ny,width}) =>
      [x+nx*width*inner, y+ny*width*inner]);
    const brightness = index === 4 ? 6 : index === 3 || index === 5 ? 5 : index === 2 ? 4 : 2;
    const shades = [0, 1, 2, 3, 4, brightness].map(i => palette[Math.min(i,brightness)]);
    const bands = [-.17, .06, .29, .53, .74, .87, 1.17];
    for (let i = 0; i < bands.length - 1; i++) {
      painter.poly([...edge(bands[i]), ...edge(bands[i+1]).reverse()], shades[i]);
    }
    if (index >= 3 && index <= 5) {
      const { x, y, nx, ny } = curve.at(-1);
      const [prevX, prevY] = arc.at(-3);
      painter.polyline([[prevX, prevY], [x, y], [x-2*nx, y-2*ny]], palette[3]);
    }
    const branches = index === 4 ? [.38,.63,.83] : index === 5 ? [.44,.72] : index === 3 ? [.66] : [];
    for (const [i,t] of branches.entries()) {
      const {x,y,nx,ny,width} = curve[Math.round(t*(curve.length-1))];
      const reach = maxWidth*(.38+.15*i);
      const points = [[x,y], [x-nx*2+ny*3,y-ny*2-nx*3],
        [x-nx*5-ny,y-ny*5+nx], [x-nx*(5+reach)+ny*4,y-ny*(5+reach)-nx*4]];
      for (let j = 1; j < points.length; j++) {
        painter.beam(...points[j-1], ...points[j], 2, palette[1]);
      }
      painter.polyline(points, palette[index === 4 ? 5 : 3]);
    }
  }
  frames.push(composite(frame, Buffer.alloc(frame.w * frame.h * 4)));
}
process.stdout.write(Buffer.concat(frames));
