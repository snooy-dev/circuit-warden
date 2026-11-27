"""Render the Warden's own master artwork on the aerial attack poses."""
from argparse import ArgumentParser
from math import atan2, cos, hypot, pi, sin
from pathlib import Path
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import map_coordinates
from scipy.spatial import Delaunay

from attack_motion import AIR, DOWN, clip, pose, project
from build import AIR_TIMES, DOWN_SIZE, DOWN_TIMES, SIZE, WARDEN, sheet

ROOT = WARDEN.parents[1]
ART = ROOT / 'art/warden'
SS = 3
SIDE_ART = Image.open(
    ART / 'shading-restore/proportion-fix-v1/warden-proportion-restored.png'
).convert('RGBA').resize((480, 480), Image.Resampling.LANCZOS)
COLORS = '020816 00193E 002B64 003E8B 0050B1 0064CA 007BDB 0091E5 00ABEA 00C3ED 00DAF2 19EFF6 5BF7F9 A3FDFD DCFFFF FFFFFF'.split()
PALETTE = Image.new('P', (1, 1))
PALETTE.putpalette(list(bytes.fromhex(''.join(COLORS + [COLORS[-1]] * (256 - len(COLORS))))))

SWORD = Image.open(ART/'reference/energy-sword-master-v2.png').convert('RGBA')
SWORD.putalpha(SWORD.getchannel('A').point(lambda a:255 if a>=194 else 0))
GRIP = (419,887)
TIP = (1386,79)


def place(image, origin, position, angle, scale, size):
    ox,oy=origin
    x,y=(k*SS for k in position)
    c,s=cos(angle)/(scale*SS),sin(angle)/(scale*SS)
    return image.transform((size[0]*SS,size[1]*SS),Image.Transform.AFFINE,
                           (c,s,ox-c*x-s*y,-s,c,oy+s*x-c*y),Image.Resampling.BICUBIC)


FRONT_ART = Image.open(ART / 'reference/master-source.png').convert('RGBA')
FRONT_ART = FRONT_ART.resize((480, 480), Image.Resampling.LANCZOS)
front_pixels = np.array(FRONT_ART)
r, g, b = front_pixels[:, :, :3].transpose(2, 0, 1)
front_pixels[(r > 155) & (g < 145) & (b > 150)] = 0
FRONT_ART = Image.fromarray(front_pixels)


def cut(image, polygon):
    mask = Image.new('1', image.size)
    ImageDraw.Draw(mask).polygon(polygon, fill=1)
    art = Image.new('RGBA', image.size)
    art.paste(image, (0, 0), mask)
    return art


SIDE_HEAD = cut(SIDE_ART, [(168,60),(361,60),(369,226),(342,253),(315,267),
                          (281,269),(245,266),(203,248),(168,222)])
FRONT_HEAD = cut(FRONT_ART, [(127,29),(348,29),(348,220),(325,240),(293,256),
                            (256,265),(221,264),(190,256),(153,241),(127,218)])
# Corresponding landmarks include both ears, the eye rims and the jaw.
FRONT_HEAD_POINTS = (
    (132,34),(348,34),(132,265),(348,265),
    (137,70),(160,38),(194,43),(214,84),(216,114),(263,109),
    (266,79),(274,44),(304,38),(328,64),(333,99),(323,139),
    (156,156),(155,204),(170,238),(210,261),(255,262),(298,248),
    (333,221),(343,188),(329,156),
    (185,184),(211,154),(235,186),(210,219),
    (269,187),(294,154),(318,186),(295,219),
)
SIDE_HEAD_POINTS = (
    (169,69),(368,69),(169,272),(368,272),
    (187,110),(204,79),(233,78),(246,108),(247,128),(259,123),
    (252,96),(263,78),(285,74),(303,92),(309,115),(306,133),
    (206,163),(197,203),(215,241),(245,263),(280,268),(316,259),
    (346,237),(359,207),(350,169),
    (288,205),(308,178),(330,208),(310,238),
    (347,206),(352,183),(356,206),(353,231),
)


class Mesh:
    def __init__(self, front_image, side_image, front_points, side_points,
                 front_pivot, side_pivot, front_scale, side_scale):
        self.images = [np.asarray(im.convert('RGBa'), dtype=np.float32)
                       for im in (front_image, side_image)]
        self.points = np.array((front_points, side_points), dtype=float)
        self.local = np.array(((self.points[0]-front_pivot)*front_scale,
                               (self.points[1]-side_pivot)*side_scale))
        self.faces = Delaunay((self.local[0] + self.local[1])/2).simplices

    def render(self, yaw, angle, anchor, size, *, offset=None):
        blend = np.clip(abs(yaw)/72, 0, 1)
        local = (1-blend)*self.local[0] + blend*self.local[1]
        if offset is not None:
            local += offset
        c, s = np.cos(angle), np.sin(angle)
        dst = (local @ np.array(((c, s), (-s, c))) + anchor)*SS
        layers = np.zeros((size[1]*SS, size[0]*SS, 4), dtype=np.uint8)
        for face in self.faces:
            target = dst[face]
            left, top = np.floor(target.min(0)).astype(int).clip(0)
            right, bottom = np.minimum(np.ceil(target.max(0)).astype(int), layers.shape[:2][::-1])
            if right <= left or bottom <= top:
                continue
            matrix = (target[1:] - target[0]).T
            if abs(np.linalg.det(matrix)) < 1e-3:
                continue
            y, x = np.mgrid[top:bottom, left:right]
            xy = np.stack((x+.5,y+.5), axis=-1)
            bc = (xy-target[0]) @ np.linalg.inv(matrix).T
            keep = (bc >= -1e-6).all(axis=2) & (bc.sum(axis=2) <= 1+1e-6)
            if not keep.any():
                continue
            weights = np.column_stack((1-bc[keep].sum(axis=1),bc[keep]))
            color = np.zeros((len(weights), 4))
            for amount, source, pixels in zip((1-blend, blend), self.points, self.images):
                if amount:
                    xf, yf = (weights @ source[face]).T
                    color += amount*np.stack([map_coordinates(pixels[...,k], (yf,xf), order=1)
                                              for k in range(4)], axis=-1)
            layers[y[keep],x[keep]] = color.round().astype(np.uint8)
        return Image.frombytes('RGBa', (size[0]*SS,size[1]*SS), layers.tobytes()).convert('RGBA')


HEAD = Mesh(FRONT_HEAD, SIDE_HEAD, FRONT_HEAD_POINTS, SIDE_HEAD_POINTS,
            (237,258),(273,267),.183,.214)

# The profile master has a hand painted over the coat. Replace that paint with
# adjacent fabric before adding the animated arm to the same shoulder.
arm_mask = Image.new('L', SIDE_ART.size)
ImageDraw.Draw(arm_mask).polygon([(231,324),(251,321),(263,331),(261,350),
                                 (250,361),(235,360),(229,347)], fill=255)
side_fabric = SIDE_ART.transform(SIDE_ART.size, Image.Transform.AFFINE, (1,0,26,0,1,2))
side_body = Image.composite(side_fabric, SIDE_ART, arm_mask.filter(ImageFilter.GaussianBlur(2)))
SIDE_COAT = cut(side_body, [(209,258),(273,257),(335,263),(337,315),(320,337),
                           (318,370),(302,438),(229,438),(226,407),(229,375),
                           (226,357),(222,337),(207,330)])
FRONT_COAT = cut(FRONT_ART, [(173,248),(253,245),(310,252),(326,272),(342,331),(316,335),
                             (298,336),(290,353),(303,451),(179,451),(188,366),(190,337),
                             (159,333),(149,327),(154,285)])
COAT = Mesh(
    FRONT_COAT, SIDE_COAT,
    [(145,245),(345,245),(145,455),(345,455),(181,257),(240,251),(298,254),(160,292),
     (325,287),(159,325),(234,326),(332,325),(190,346),(293,346),(210,371),(273,371),
     (183,401),(300,401),(209,438),(269,439),(237,409)],
    [(200,255),(345,255),(200,447),(345,447),(219,265),(267,260),(313,265),(215,294),
     (326,288),(211,325),(268,326),(331,323),(226,346),(314,345),(248,373),(299,373),
     (230,397),(313,392),(251,427),(287,422),(275,410)],
    (241,360),(272,362),.181,.207)

SCARF = cut(SIDE_ART, [(89,345),(95,320),(114,299),(139,292),(171,294),(197,279),
                      (222,269),(243,270),(239,291),(214,308),(185,326),(144,331),
                      (125,347),(104,354)]).crop((85,264,246,359))
TAIL = cut(SIDE_ART, [(104,382),(126,368),(155,362),(184,363),(208,354),(235,335),
                     (251,341),(245,367),(224,397),(198,418),(149,432),(119,422),
                     (105,407)]).crop((99,331,253,437))
ARM = cut(SIDE_ART, [(234,324),(245,325),(255,331),(259,343),(252,354),
                    (246,358),(239,355),(234,348)]).crop((231,322,262,360))
HAND = ARM.crop((4,18,26,35))


def part(pixels, src_a, src_b, a, b, width, size):
    ax, ay = src_a
    dx, dy = src_b[0]-ax, src_b[1]-ay
    vx, vy = b[0]-a[0], b[1]-a[1]
    angle = atan2(vy, vx)-atan2(dy,dx)
    scale = max(.03, hypot(vx,vy)/hypot(dx,dy))
    c, s = np.cos(angle), np.sin(angle)
    # Scale along and across each material piece independently.
    u = np.array((dx,dy))/hypot(dx,dy)
    rotation = np.array(((c,-s),(s,c)))
    inverse = rotation @ (np.eye(2)/width + np.outer(u,u)*(1/scale-1/width))/SS
    offset = np.array(src_a) - np.array(a)*SS @ inverse
    return pixels.transform((size[0]*SS,size[1]*SS), Image.Transform.AFFINE,
                            (*inverse[:,0],offset[0],*inverse[:,1],offset[1]),
                            Image.Resampling.BICUBIC)


def render(rig, time, size, anchor):
    p = pose(rig, time)
    q = {name: project(value, anchor) for name, value in p.items()
         if isinstance(value, np.ndarray)}
    frame = Image.new('RGBA', (size[0]*SS, size[1]*SS))
    layers = []
    layers.append((-32, part(TAIL,(140,24),(20,70),q['hip'],q['tail'],.215,size)))
    layers.append((-31, part(SCARF,(143,15),(15,72),q['chest'],q['scarf'],.213,size)))
    angle = atan2(q['neck'][0]-q['hip'][0], q['hip'][1]-q['neck'][1])
    legs = np.zeros_like(COAT.local[0])
    for knee, foot, knee_edge, toe, rest_x in (
        ('knee', 'foot', 16, 18, -4), ('other_knee', 'other_foot', 17, 19, 4),
    ):
        leg_x, leg_y = np.subtract(q[foot], q['hip'])
        legs[toe] = (.33 * (leg_x - rest_x), .65 * (leg_y - 20))
        legs[knee_edge] = (.22 * (q[knee][0] - q['hip'][0] - rest_x),
                           .40 * (q[knee][1] - q['hip'][1] - 10))
    legs[20] = (legs[16] + legs[17]) / 2
    layers.append((0, COAT.render(p['yaw'],angle,q['hip'],size,offset=legs)))
    for shoulder, elbow, hand in [('shoulder','elbow','hand'),
                                  ('other_shoulder','other_elbow','other_hand')]:
        if hand == 'hand':
            vx, vy = np.subtract(q['tip'], q[hand])
        else:
            vx, vy = np.subtract(q[hand], q[elbow])
        heading = atan2(vy, vx)
        layers.append((p[shoulder][1] - 1,part(ARM,(14,4),(15,28),q[shoulder],q[elbow],.35,size)))
        layers.append((p[elbow][1],part(ARM,(14,5),(15,29),q[elbow],q[hand],.27,size)))
        depth = p[hand][1]
        if hand == 'hand' and p['length'] > 5:
            layers.append((depth, part(SWORD,GRIP,TIP,q[hand],q['tip'],.039,size)))
        layers.append((depth,place(HAND,(11,6),q[hand],heading-pi/2,.31,size)))
    for _, image in sorted(layers, key=lambda item:item[0]):
        frame.alpha_composite(image)
    look_down = np.clip(1-abs(p['head_yaw'])/35,0,1)
    eyes = np.zeros_like(HEAD.local[0])
    eyes[25:, 1] = look_down*2.5
    neck = (q['neck'][0], q['neck'][1] + 3.8 + .7*look_down)
    frame.alpha_composite(HEAD.render(p['head_yaw'],angle*.55,neck,size,offset=eyes))
    reduced = frame.resize(size, Image.Resampling.LANCZOS)
    alpha = reduced.getchannel('A').point(lambda a: 255 if a >= 158 else 0)
    reduced = reduced.convert('RGB').quantize(palette=PALETTE,dither=Image.Dither.NONE).convert('RGBA')
    reduced.putalpha(alpha)
    reduced.paste((0,0,0,0), (0,0,*size), alpha.point(lambda a: 255-a))
    return reduced



def main():
    parser = ArgumentParser()
    parser.add_argument('output', type=Path, nargs='?', default=WARDEN)
    out = parser.parse_args().output
    (out / 'attack-source').mkdir(parents=True, exist_ok=True)
    (out / 'downstrike-source').mkdir(parents=True, exist_ok=True)

    air = clip(AIR)
    air_frames = [render(air, t, SIZE, (126,154)) for t in AIR_TIMES[:-1]]
    sheet(air_frames, SIZE, 6).save(out / 'attack-source/air-poses.png')

    down = clip(DOWN)
    anchor = (103,96)
    # Keep the deployed frame times and sample the deepest part of the stroke in cel 4.
    down_samples = [35 if t == 30 else t for t in DOWN_TIMES]
    down_frames = [render(down, t, DOWN_SIZE, anchor) for t in down_samples]
    sheet(down_frames, DOWN_SIZE, 5).save(out / 'downstrike-source/poses.png')

    tips = [project(pose(down, t)['tip'], anchor) for t in range(86)]
    result = subprocess.run(
        ['node', Path(__file__).with_name('down-sweep.mjs')],
        input=json.dumps(tips).encode(),
        stdout=subprocess.PIPE,
        check=True,
    )
    count = DOWN_SIZE[0]*DOWN_SIZE[1]*4
    assert len(result.stdout) == len(down_samples)*count
    fx = [Image.frombytes('RGBA', DOWN_SIZE, result.stdout[i:i+count])
          for i in range(0, len(result.stdout), count)]
    sweep = Image.new('RGBA', (DOWN_SIZE[0]*5, DOWN_SIZE[1]*2))
    for i, frame in enumerate(fx):
        sweep.alpha_composite(frame, (i % 5 * DOWN_SIZE[0], i // 5 * DOWN_SIZE[1]))
    sweep.save(out / 'downstrike-source/sweep.png')


if __name__ == '__main__':
    main()
