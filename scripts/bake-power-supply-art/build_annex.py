"""확장한 파워 맵의 설비 공간을 2×2 픽셀 배율로 배치한다."""

import hashlib
import json

import numpy as np
from PIL import Image

from build_transformer_hall import LEVEL, PARTS, ROOT, SOURCE, plate_png, quantize, surface, write_bundle


SOURCES = ROOT / 'art/levels/power-supply/annex/source'
OUT = LEVEL / 'annex'
LOWER = (
    ('thermal', 3440, (.73, .79, .85), .50, 'steel'),
    ('capacitors', 4880, (.76, .77, .82), .47, 'board'),
    ('filter', 6320, (.75, .78, .83), .28, 'sink'),
)


def main():
    OUT.mkdir(exist_ok=True)
    route = LEVEL / 'map.json'
    data = json.loads(route.read_text(encoding='utf-8'))
    props = {key: item for key, item in data['props'].items() if not key.startswith('annex-')}
    extended = []
    details = {}

    def publish(key, art, source, left, top, layer):
        file = OUT / f'{key}.png'
        art.save(file, optimize=True)
        props[key] = {'image': file.relative_to(LEVEL).as_posix(), 'art_source': 'host_image',
                      'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
        details[key] = props[key] | {'source': source, 'logical_size': list(art.size)}
        extended.append({'id': key, 'prop': key, 'x': left, 'y': top, 'anchor_px': [0, 0],
                         'solid': False, 'layer': layer, 'sortY': 0, 'scale': 2})

    for name, x, gain, focus, _ in LOWER:
        art = plate_png(name, (720, 320), gain, (.5, focus), source_dir=SOURCES)
        publish('annex-' + name, art, f'{name}.png', x, 1280, 'rear')

    raceway = Image.open(SOURCES / 'raceway.png').convert('RGBA')
    for (name, x, *_), (left, top, right, bottom), gain in zip(LOWER,
            ((0, 56, 910, 800), (350, 18, 1190, 762), (650, 84, 1536, 837)),
            ((.63, .75, .87), (.76, .81, .82), (.84, .76, .65)), strict=True):
        pixels = np.array(raceway.crop((left, top, right, bottom)))
        pixels[..., :3] = np.rint(pixels[..., :3] * gain + [3, 5, 7]).astype(np.uint8)
        art = quantize(pixels, (720, 434), 24, smooth=True)
        yy, xx = np.ogrid[:434, :720]
        sides = np.minimum(xx / 41, (719 - xx) / 41)
        alpha = np.minimum(np.minimum(sides, yy / 34), np.minimum((433 - yy) / 34, 1))
        art[..., 3] = np.rint(alpha * 255).astype(np.uint8)
        publish('annex-race-' + name, Image.fromarray(art), 'raceway.png', x, 412, 'rear')

    atlas = Image.open(SOURCE / 'terrain.png').convert('RGBA')
    strips = {kind: atlas.crop(box) for kind, box in PARTS.items() if kind != 'busbar'}
    for x, y, width, height in data['collision']['rects']:
        if x < 2960 or y < 32 or y == 1256:
            continue
        limits = [x, *(edge for edge in (3440, 4880, 6320, 7760, 8600)
                       if width > 500 and x + 40 < edge < x + width - 40), x + width]
        for left, right in zip(limits, limits[1:]):
            width_px = (right - left) // 2
            kind = 'steel' if y < 1280 or left < 4880 else 'board' if left < 6320 or left >= 7760 else 'sink'
            if height > 130 and width <= 42:
                pixels = surface(strips['steel'], 'steel', (height // 2, width_px), offset=left % 150)
                pixels = np.rot90(pixels).copy()
                pixels[..., :3] = (pixels[..., :3] * .54).astype(np.uint8)
            else:
                depth = min(height, 102)
                pixels = surface(strips[kind], kind, (width_px, depth // 2), offset=left % 287 - 140)
            publish(f'annex-deck-{left}-{y}', Image.fromarray(pixels), 'terrain.png', left, y, 'structure')

    retained = [obj for obj in data['objects'] if not obj['id'].startswith('annex-')]
    data.update(props=props, objects=retained + extended)
    save_overview(data, OUT / 'overview.png')
    write_bundle(route, data)
    files = [*sorted(SOURCES.iterdir()), SOURCE / 'terrain.png']
    source_hashes = {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                     for file in files}
    (OUT / 'provenance.json').write_text(json.dumps({
        'art_source': 'host_image', 'model': 'Codex ImageGen', 'estimateUsd': None, 'world_units_per_pixel': 2,
        'sources': source_hashes, 'assets': details,
    }, indent=2) + '\n', encoding='utf-8')


def save_overview(data, path):
    overview = Image.new('RGBA', (data['world']['width'], data['world']['height']), (9, 15, 22))
    for obj in sorted(data['objects'], key=lambda item: ('rear', 'structure', 'front').index(item['layer'])):
        im = Image.open(LEVEL / data['props'][obj['prop']]['image']).convert('RGBA')
        anchor_x, anchor_y = obj['anchor_px']
        if obj.get('flip_x'):
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            anchor_x = im.width - anchor_x
        scale = obj.get('scale', 1)
        opacity = obj.get('opacity', 1)
        if opacity != 1:
            im.putalpha(im.getchannel('A').point(lambda channel: round(channel * opacity)))
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.NEAREST)
        overview.alpha_composite(im, (round(obj['x'] - anchor_x * scale), round(obj['y'] - anchor_y * scale)))
    overview.convert('RGB').save(path, optimize=True)
    data['layers'][0].update(image=path.relative_to(LEVEL).as_posix(), art_source='host_image',
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
