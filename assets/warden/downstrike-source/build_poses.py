from math import atan2, cos, degrees, hypot, radians, sin, tau
from pathlib import Path


import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, map_coordinates

work = Path(__file__).resolve().parent
root = work.parents[2]
supersample = 3
cell = (160, 192)
working_size = tuple(side * supersample for side in cell)

body = Image.open(root / 'art/warden/shading-restore/proportion-fix-v1/warden-proportion-restored.png').convert('RGBA')
body = body.resize((480, 480), Image.Resampling.LANCZOS)

# Use the original character art for the limb geometry and finish the overlap under the scarf.
arm_mask = Image.new('L', body.size)
ImageDraw.Draw(arm_mask).polygon([(236, 315), (256, 315), (263, 326), (262, 341),
                                  (256, 351), (248, 358), (239, 357), (234, 350),
                                  (231, 338), (230, 323)], fill=255)
arm = body.copy()
arm.putalpha(arm_mask)
body_pixels = np.array(body)
covered = np.asarray(arm_mask) > 0
# Extend the adjacent torso/scarf texture into the small hole exposed by rotation.
_, nearest = distance_transform_edt(covered, return_indices=True)
body_pixels[covered] = body_pixels[tuple(nearest[:, covered])]


sword = Image.open(root / 'art/warden/reference/energy-sword-master-v2.png').convert('RGBA')
sword.putalpha(sword.getchannel('A').point(lambda opacity: 255 if opacity >= 194 else 0))

palette = Image.new('P', (1, 1))
colors = '020816 00193E 002B64 003E8B 0050B1 0064CA 007BDB 0091E5 00ABEA 00C3ED 00DAF2 19EFF6 5BF7F9 A3FDFD DCFFFF FFFFFF'.split()
palette.putpalette(list(bytes.fromhex(''.join(colors + [colors[-1]] * (256 - len(colors))))))

def transform_point(point, origin, target, angle, scale):
    x, y = ((position - anchor) * scale for position, anchor in zip(point, origin, strict=True))
    c, s = cos(radians(angle)), sin(radians(angle))
    return target[0] + c*x - s*y, target[1] + s*x + c*y


def place(image, origin, target, angle, scale):
    k = scale * supersample
    tx, ty = (v * supersample for v in target)
    c, s = cos(radians(angle))/k, sin(radians(angle))/k
    ox, oy = origin
    return image.transform(working_size, Image.Transform.AFFINE,
                           (c, s, ox - c*tx - s*ty, -s, c, oy + s*tx - c*ty),
                           resample=Image.Resampling.BICUBIC)


hip = (276, 369)
body_scale = 80 / 360
shoulder = (248, 322)
wrist = (246, 348)
weapon_grip = (419, 887)

weapon_axis = degrees(atan2(79-887, 1386-419))
weapon_scale = 51 / hypot(1386-419, 79-887)
# Torso, arm and weapon angles are authored in screen space. One grip drives every weapon pose.
keys = [(-9, 261, -128, -62, 2, 1), (-8, 265, -113, -36, 4, 3),
        (4, 274, -77, 32, -1, -3), (13, 270, -45, 68, -8, -9),
        (20, 265, -16, 100, -14, -14), (22, 257, 6, 119, -13, -8),
        (18, 256, 15, 119, -7, 0), (12, 258, 4, 106, -1, 5),
        (6, 260, -23, 78, 3, 3), (0, 257, -35, 54, 0, 0)]
y_grid, x_grid = np.mgrid[:480, :480]
cloth_weight = np.clip((217 - x_grid) / 125, 0, 1) * np.clip((365 - y_grid) / 25, 0, 1)
tail_weight = np.clip((230 - x_grid) / 140, 0, 1) * np.clip((y_grid - 325) / 43, 0, 1)
current_areas = [(220, 107, 29, 32, 4, 13), (271, 102, 25, 27, 4, 10),
                 (277, 178, 61, 31, 18, -5), (286, 249, 38, 17, -10, 3),
                 (293, 364, 27, 29, 6, -9), (159, 391, 44, 23, -15, 4)]
regions = [np.clip(1 - ((x_grid - x)/w)**2 - ((y_grid - y)/h)**2, 0, 1)**2
           for x, y, w, h, dx, dy in current_areas]
times_ms = [0, 8, 18, 30, 47, 66, 85, 103, 120, 162]
frames = []
for time, (body_angle, mount_x, arm_angle, sword_angle, tail, scarf) in zip(times_ms, keys, strict=True):
    pelvis = (80, 98)
    joint = transform_point((mount_x, 322), hip, pelvis, body_angle, body_scale)
    hand = transform_point(wrist, shoulder, joint, arm_angle, body_scale)
    source_y = y_grid - tail_weight * tail - cloth_weight * scarf
    source_x = x_grid.astype(float)
    for index, (region, (_, _, _, _, dx, dy)) in enumerate(zip(regions, current_areas, strict=True)):
        wave = sin(tau * time / 300 + index * .72)
        source_x -= region * dx * wave
        source_y -= region * dy * wave
    posed = Image.fromarray(np.stack([map_coordinates(body_pixels[:, :, channel], (source_y, source_x),
                                                       order=1) for channel in range(4)], axis=-1))
    frame = place(posed, hip, pelvis, body_angle, body_scale)
    rotation = sword_angle - weapon_axis
    frame.alpha_composite(place(sword, weapon_grip, hand, rotation, weapon_scale))
    frame.alpha_composite(place(arm, shoulder, joint, arm_angle, body_scale))
    frame = frame.resize(cell, Image.Resampling.LANCZOS)
    alpha = frame.getchannel('A').point(lambda opacity: 255 if opacity >= 144 else 0)
    frame = frame.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
    frame.putalpha(alpha)
    frames.append(frame)

sheet = Image.new('RGBA', (800, 384))
for index, frame in enumerate(frames):
    sheet.alpha_composite(frame, (index % 5 * 160, index // 5 * 192))
sheet.save(work / 'poses.png')
