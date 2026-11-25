"""변압실 원화에서 2×2 게임용 원경과 충돌에 맞는 표면을 만든다."""

import hashlib
import json

import numpy as np
from PIL import Image

from build import ROOT, bake, hibit


LEVEL = ROOT / 'assets/levels/power-supply'
OUT = LEVEL / 'transformer-hall'
SOURCE = ROOT / 'art/levels/power-supply/transformer-hall/source'
PLATES = {
    'intake': ((0, 374, 1152, 768), (.71, .78, .82), (.34, .55)),
    'transformer': ((1050, 384, 1230, 790), (.71, .72, .81), (.47, .77)),
    'relay': ((2120, 242, 740, 898), (.78, .77, .81), (.5, .82)),
}
PARTS = {
    'steel': (15, 110, 1521, 228),
    'board': (15, 356, 1521, 455),
    'sink': (15, 577, 1521, 748),
    'busbar': (15, 835, 1521, 991),
}


def quantize(source, size, colors, *, smooth=False):
    pixels = np.asarray(source)
    palette = hibit.kmeans_palette(pixels[..., :3][pixels[..., 3] >= 192], colors)
    return hibit.render(bake(pixels, size, palette, smooth=smooth), palette)


def plate_png(name, size, gain, focus, *, source_dir=SOURCE):
    source = Image.open(source_dir / f'{name}.png').convert('RGBA')
    crop = hibit.plate_crop(source.width, source.height, *size, y_frac=focus[1], x_frac=focus[0])
    pixels = np.array(source.crop(crop))
    pixels[..., :3] = np.rint(pixels[..., :3] * gain + [3, 5, 7]).astype(np.uint8)
    if name == 'transformer':
        sy, sx = np.ogrid[:pixels.shape[0], :pixels.shape[1]]
        bay = np.clip(1 - ((sx / pixels.shape[1] - .74) / .28) ** 2
                      - ((sy / pixels.shape[0] - .88) / .16) ** 2, 0, 1)
        pixels[..., :3] += np.rint(bay[..., None] * [4, 18, 30]).astype(np.uint8)
    out = quantize(pixels, size, 24, smooth=True)
    xx, yy = np.meshgrid(np.arange(size[0]), np.arange(size[1]))
    edges = [np.ones_like(xx), yy / 30, (size[1] - 1 - yy) / 13]
    if name != 'intake':
        edges.append(xx / 57)
    if name != 'relay':
        edges.append((size[0] - 1 - xx) / 51)
    alpha = np.min(edges, axis=0)
    if name == 'intake':
        # 메쉬의 밝은 테두리를 살리고 안쪽 어두운 칸으로 회전자를 보이게 한다.
        radius = np.hypot(xx - 170, yy - 230)
        mesh = np.clip((out[..., :3].min(axis=-1).astype(float) - 26) / 66, 0, 1)
        reveal = np.clip((111 - radius) / 7, 0, 1) * (1 - mesh)
        alpha *= 1 - .78 * reveal
    out[..., 3] = np.rint(alpha * 255).astype(np.uint8)
    return Image.fromarray(out)


def surface(source, kind, size, offset=0):
    total = source.width
    ratio = size[0] / size[1]
    length = min(total, round(source.height * ratio))
    left = min(total - length, max(0, (total - length) // 2 + offset))
    section = source.crop((left, 0, left + length, source.height))
    pixels = quantize(section, size, 16)
    if kind != 'busbar':
        # 솔리드의 충돌선으로 픽셀을 맞추고 프레임 아래의 모양은 알파를 유지한다.
        pixels[0, :, :3] = {'steel': (140, 157, 173), 'board': (167, 156, 95),
                            'sink': (174, 159, 144), 'bridge': (125, 208, 185)}[kind]
        pixels[0, :, 3] = 255
    return pixels


def write_bundle(path, level):
    lines = ['{']
    for key, value in level.items():
        if key == 'camera' and 'rooms' in value:
            lines += ['  "camera": {', f'    "bounds": {json.dumps(value["bounds"])},', '    "rooms": [',
                      ',\n'.join('      ' + json.dumps(row) for row in value['rooms']), '    ]', '  },']
        elif key in {'layers', 'objects', 'spawns', 'interactions'}:
            lines += [f'  "{key}": [', ',\n'.join('    ' + json.dumps(row) for row in value), '  ],']
        elif key in {'props', 'anchors'}:
            lines += [f'  "{key}": {{', ',\n'.join(f'    "{name}": {json.dumps(row)}' for name, row in value.items()),
                      '  },']
        elif key == 'collision':
            rows = []
            for name, part in value.items():
                if name in {'rects', 'power_devices', 'teleport_barriers'}:
                    rows.append(f'    "{name}": [\n' + ',\n'.join('      ' + json.dumps(row) for row in part)
                                + '\n    ]')
                else:
                    rows.append(f'    "{name}": {json.dumps(part)}')
            lines += ['  "collision": {', ',\n'.join(rows), '  },']
        else:
            lines.append(f'  "{key}": {json.dumps(value)},')
    lines[-1] = lines[-1].removesuffix(',')
    path.write_text('\n'.join(lines + ['}']) + '\n', encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    path = LEVEL / 'map.json'
    level = json.loads(path.read_text(encoding='utf-8'))
    foreground = level['layers'][0]
    foreground.update(
        rotor={'prop': 'fan-rotor', 'rect': [110, 604, 460, 460],
               'diameter_px': 430, 'degrees_per_second': 72},
    )
    for key in ('chambers', 'girders', 'lights'):
        foreground.pop(key, None)
    generated = {}
    objects = []
    world = level['world']
    overview = Image.new('RGBA', (world['width'], world['height']), (9, 15, 22))

    def register(key, art, source, *, at=None, layer='structure', sort=0):
        file = OUT / f'{key}.png'
        art.save(file, optimize=True)
        entry = {'image': file.relative_to(LEVEL).as_posix(), 'art_source': 'host_image',
                 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
        generated[key] = entry | {'source': source, 'logical_size': list(art.size)}
        if at is not None:
            x, y = at
            objects.append({'id': key, 'prop': key, 'x': x, 'y': y,
                            'anchor_px': [0, 0], 'solid': False, 'layer': layer,
                            'sortY': sort, 'scale': 2})
            full = art.resize((art.width * 2, art.height * 2), Image.Resampling.NEAREST)
            overview.alpha_composite(full, (x, y))

    for name, (rect, gain, focus) in PLATES.items():
        x, y, width, height = rect
        art = plate_png(name, (width // 2, height // 2), gain, focus)
        register(f'hall-{name}', art, f'{name}.png', at=(x, y), layer='rear', sort=-10)
        if name == 'relay':
            active = np.array(art)
            traces = active[166:293, 142:242, :3]
            red, green, blue = traces.astype(float).transpose(2, 0, 1)
            copper = (red > 67) & (red > green * 1.25) & (green > blue * 1.25)
            assert copper.sum() > 30
            traces[copper] = np.where((red[copper] > 112)[:, None], (80, 159, 136), (47, 94, 84))
            register('hall-relay-powered', Image.fromarray(active), 'relay.png')
            objects[-1]['powered_prop'] = 'hall-relay-powered'

    atlas = Image.open(SOURCE / 'terrain.png').convert('RGBA')
    strips = {key: atlas.crop(box) for key, box in PARTS.items()}
    for x, width, height, kind in ((0, 1084, 102, 'steel'), (1084, 1132, 144, 'sink'),
                                  (2216, 644, 110, 'board')):
        pixels = surface(strips[kind], kind, (width // 2, height // 2))
        register(f'hall-plinth-{kind}', Image.fromarray(pixels), 'terrain.png', at=(x, 1140))

    for x, y, width, height in level['collision']['rects']:
        if y in (0, 1140) or width < 30:
            continue
        kind = 'steel' if x < 1100 else 'sink' if x < 2200 else 'board'
        pixels = surface(strips[kind], kind, (round(width / 2), round(height / 2)), offset=x % 231 - 115)
        if y > 1000 and width < 40:
            collar = atlas.crop((97, 835, 161, 988))
            pixels = quantize(collar, (round(width / 2), round(height / 2)), 12)
        elif y == 420 or width < 40:
            pixels = np.flipud(pixels).copy()
            pixels[..., :3] = (pixels[..., :3] * .66).astype(np.uint8)
        else:
            assert np.all(pixels[0, :, 3] == 255)
        register(f'hall-deck-{x}-{y}', Image.fromarray(pixels), 'terrain.png', at=(x, y))

    bridge = next(device['rect'] for device in level['collision']['power_devices'] if device['kind'] == 'bridge')
    pixels = surface(strips['board'], 'bridge', (bridge[2] // 2, bridge[3] // 2))
    register('hall-bridge', Image.fromarray(pixels), 'terrain.png')
    _, _, width, height = level['collision']['busbar']
    strip = strips['busbar']
    sample = Image.new('RGBA', (630, strip.height))
    for left, src in ((0, 0), (170, 670), (460, strip.width - 170)):
        end = 170 if left != 170 else 290
        sample.paste(strip.crop((src, 0, src + end, strip.height)), (left, 0))
    busbar = surface(sample, 'busbar', (width // 2, height // 2))
    rgb = busbar[..., :3].astype(np.int16)
    live = (rgb[..., 0] > 190) & (rgb[..., 1] > 65) & (rgb[..., 2] < 130)
    assert live.sum() >= 8
    cold = busbar.copy()
    cold[live, :3] = (77, 111, 106)
    register('hall-busbar-safe', Image.fromarray(cold), 'terrain.png')
    busbar[live, :3] = (255, 176, 51)
    arc_source = 'maintenance/arc-live.png'
    spark = np.array(Image.open(LEVEL / arc_source).convert('RGBA'))
    red, green, blue, alpha = spark.astype(float).transpose(2, 0, 1)
    arc = (green > red + 35) & (blue > red + 30) & (alpha > 160)
    spark[..., 3] = np.where(arc, 255, 0)
    spark[arc, :3] = np.where((green[arc] > 200)[:, None], (255, 232, 168), (236, 121, 52))
    discharge = Image.fromarray(spark)
    discharge = discharge.crop(discharge.getbbox()).resize((width // 2 - 14, 6), Image.Resampling.NEAREST)
    live_art = Image.fromarray(busbar)
    live_art.alpha_composite(discharge, (7, 0))
    register('hall-busbar-live', live_art, f'terrain.png + {arc_source}')

    props = {key: item for key, item in level['props'].items() if not key.startswith('hall-')
             and key not in {'pcb', 'coil', 'capacitors', 'return-bridge', 'chamber-light'}}
    props.update({key: {field: entry[field] for field in ('image', 'art_source', 'sha256')}
                  for key, entry in generated.items()})
    remaining = [obj for obj in level['objects'] if not obj['id'].startswith('hall-')
                 and obj['prop'] in props]
    for obj in remaining:
        if obj['id'] == 'relay-feed':
            obj.update(powered_prop='feed-wire-on', opacity=.94)
    level.update(props=props, objects=objects + remaining)
    panorama = OUT / 'overview.png'
    overview.convert('RGB').save(panorama, optimize=True)
    foreground.update(image=panorama.relative_to(LEVEL).as_posix(), art_source='host_image',
                      sha256=hashlib.sha256(panorama.read_bytes()).hexdigest())
    write_bundle(path, level)
    meta = {
        'art_source': 'host_image', 'model': 'Codex ImageGen', 'estimateUsd': None, 'world_units_per_pixel': 2,
        'source_directory': SOURCE.relative_to(ROOT).as_posix(),
        'sources': {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(SOURCE.iterdir())},
        'assets': generated,
    }
    (OUT / 'provenance.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
