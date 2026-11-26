"""Joint-keyed Warden attack poses made from the approved side and front art."""

from math import atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, map_coordinates

ART = Path(__file__).resolve().parents[3] / 'art/warden'
SCALE = .22
OVERSAMPLE = 3

palette = Image.new('P', (1, 1))
colors = '020816 00193E 002B64 003E8B 0050B1 0064CA 007BDB 0091E5 00ABEA 00C3ED 00DAF2 19EFF6 5BF7F9 A3FDFD DCFFFF FFFFFF'.split()
palette.putpalette(list(bytes.fromhex(''.join(colors + [colors[-1]] * (256 - len(colors))))))
sword = Image.open(ART / 'reference/energy-sword-master-v2.png').convert('RGBA')
sword.putalpha(sword.getchannel('A').point(lambda a: 255 if a >= 194 else 0))
SWORD_GRIP = (419, 887)
SWORD_TIP = (1386, 79)
SWORD_ANGLE = degrees(atan2(SWORD_TIP[1] - SWORD_GRIP[1], SWORD_TIP[0] - SWORD_GRIP[0]))

y_grid, x_grid = np.mgrid[:480, :480]


def split_master(path, arm_outline):
    master = Image.open(ART / path).convert('RGBA').resize((480, 480), Image.Resampling.LANCZOS)
    pixels = np.array(master)
    r, g, b = pixels[:, :, :3].transpose(2, 0, 1)
    pixels[(r > 170) & (b > 165) & (g < 115)] = 0
    mask = Image.new('1', master.size)
    ImageDraw.Draw(mask).polygon(arm_outline, fill=1)
    covered = np.asarray(mask)
    arm = Image.fromarray(pixels.copy())
    arm.putalpha(Image.fromarray(np.where(covered, pixels[:, :, 3], 0).astype('uint8')))
    _, nearest = distance_transform_edt(covered, return_indices=True)
    pixels[covered] = pixels[tuple(nearest[:, covered])]
    return pixels, arm


side = split_master('shading-restore/proportion-fix-v1/warden-proportion-restored.png',
                    [(236, 315), (256, 315), (263, 326), (262, 341), (256, 351),
                     (248, 358), (239, 357), (234, 350), (231, 338), (230, 323)])
front = split_master('reference/master-source.png',
                     [(171, 319), (191, 320), (188, 342), (183, 360),
                      (174, 367), (164, 363), (161, 353)])


def point(p, origin, target, angle, scale=SCALE):
    x, y = ((p[i] - origin[i]) * scale for i in range(2))
    c, s = cos(radians(angle)), sin(radians(angle))
    return target[0] + c*x - s*y, target[1] + s*x + c*y


def place(image, pivot, target, angle, scale, canvas):
    ox, oy = pivot
    x, y = (v * OVERSAMPLE for v in target)
    k = scale * OVERSAMPLE
    c, s = cos(radians(angle)) / k, sin(radians(angle)) / k
    return image.transform(tuple(v * OVERSAMPLE for v in canvas), Image.Transform.AFFINE,
                           (c, s, ox - c*x - s*y, -s, c, oy + s*x - c*y),
                           resample=Image.Resampling.BICUBIC)


def draw(key, size, root):
    view, pitch, dx, dy, swing, reach, blade, length, cloth, tuck = key
    scale = SCALE
    if view == 'side':
        (pixels, arm), hip, shoulder, wrist = side, (276, 369), (248, 322), (246, 348)
    else:
        (pixels, arm), hip, shoulder, wrist = front, (246, 380), (178, 325), (173, 352)
        dy += 6
        scale = .215
    # The head stays registered at the neck while the cloth and legs settle separately.
    rear = np.clip((224 - x_grid) / 130, 0, 1) * np.clip((y_grid - 278) / 32, 0, 1)
    legs = np.clip((y_grid - 354) / 77, 0, 1) * (1 - rear)
    look = np.clip((276 - y_grid) / 36, 0, 1)
    turn = dx * 4 * look if view != 'side' else 0
    sx = x_grid - turn + legs * tuck * .65
    if view == 'quarter':
        sx += (x_grid - 242) * .23 * look
    sy = y_grid - rear * cloth - legs * tuck
    warped = Image.fromarray(np.stack([
        map_coordinates(pixels[:, :, i], (sy, sx), order=1) for i in range(4)
    ], axis=-1))
    pelvis = (root[0] + dx, root[1] + dy)
    joint = point(shoulder, hip, pelvis, pitch, scale)
    joint = (joint[0] + reach, joint[1])
    hand = point(wrist, shoulder, joint, swing, scale)
    frame = place(warped, hip, pelvis, pitch, scale, size)
    if length:
        weapon_scale = length / hypot(SWORD_TIP[0] - SWORD_GRIP[0], SWORD_TIP[1] - SWORD_GRIP[1])
        frame.alpha_composite(place(sword, SWORD_GRIP, hand, blade - SWORD_ANGLE, weapon_scale, size))
    frame.alpha_composite(place(arm, shoulder, joint, swing, scale, size))
    raster = frame.resize(size, Image.Resampling.LANCZOS)
    alpha = raster.getchannel('A').point(lambda a: 255 if a >= 144 else 0)
    raster = raster.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
    raster.putalpha(alpha)
    return raster


# View, body pitch, pelvis x/y, arm angle, reach, blade angle/length, cloth lag, leg tuck.
AIR = [
    ('side', -5, 0, 0,  -8, 0, -98, 0, -10, -21),
    ('side', -9, -2, 0,  58, 0, -147, 44, -14, -34),
    ('side', -6, -1, -1, 33, 0, -114, 46, -19, -40),
    ('side',  3, 1, -2, -56, 1, -38, 65, -24, -34),
    ('side',  9, 4, -1, -87, 3,    0, 56, -31, -23),
    ('side', 13, 4, 0,  -46, 1,   36, 52, -33, -15),
    ('side', 10, 3, 1,    7, 0,   75, 47, -18, -10),
    ('side',  5, 1, 1,   30, 0,  112, 36, -6, -9),
    ('side',  0, 0, 1,    6, 0,  102,  0, 5, -9),
]
AIR_TIMES = [0, 28, 64, 96, 124, 148, 175, 207, 245, 300]

DOWN = [
    ('side', -5, 0, 0,  -9, 0, -120, 0, -9, -18),
    ('quarter', -9, 3, -1, -125, 0, -40, 40, -14, -24),
    ('front', -7, 2, -2, -100, 0,   3, 46, -18, -23),
    ('front', -3, 1, -1,  -74, 1,  43, 55, -20, -17),
    ('front',  5, 0, 2,   -24, 2,  91, 61, -21,   1),
    ('front',  9, -1, 2,   29, 1, 141, 55, -13,  13),
    ('front',  5, 1, 0,    43, 0, 161, 45, 0,  -1),
    ('quarter',  0, 2, -2,   24, 0, 124, 32, 5, -12),
    ('side',   1, 1, -1,   16, 0, 121,  0, -4, -18),
    ('side',  -4, 0, 0,     4, 0,  98,  0, -9, -19),
]
