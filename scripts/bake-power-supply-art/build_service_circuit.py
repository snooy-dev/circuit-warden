"""전원 구역의 새 접속부와 지형을 기존 hi-bit 에셋과 조합한다."""

import hashlib
import json

import numpy as np
from PIL import Image

from build_transformer_hall import LEVEL, PARTS, ROOT, SOURCE, plate_png, quantize, surface, write_bundle


SOURCE_ROOM = ROOT / 'art/levels/power-supply/service-circuit/source'
OUT = LEVEL / 'service-circuit'


def main():
    OUT.mkdir(exist_ok=True)
    path = LEVEL / 'map.json'
    level = json.loads(path.read_text(encoding='utf-8'))
    image_layer = level['layers'][0]
    world = level['world']
    overview = Image.new('RGBA', (world['width'], world['height']), (9, 15, 22))
    props = {key: item for key, item in level['props'].items()
             if not key.startswith(('circuit-', 'hall-deck-', 'hall-plinth-'))}
    props.update({key: {'image': f'transformer-hall/{key}.png', 'art_source': 'host_image',
                        'sha256': hashlib.sha256((LEVEL / 'transformer-hall' / f'{key}.png').read_bytes()).hexdigest()}
                  for key in ('hall-intake', 'hall-transformer', 'hall-relay', 'hall-relay-powered')})
    objects = []
    produced = {}

    def place(key, prop, x, y, layer, *, powered=None):
        item = {'id': key, 'prop': prop, 'x': x, 'y': y, 'anchor_px': [0, 0],
                'solid': False, 'layer': layer, 'sortY': 0, 'scale': 2}
        if powered:
            item['powered_prop'] = powered
        objects.append(item)
        image = Image.open(LEVEL / props[prop]['image']).convert('RGBA')
        overview.alpha_composite(image.resize((image.width * 2, image.height * 2),
                                              Image.Resampling.NEAREST), (x, y))

    def publish(key, art, source):
        file = OUT / f'{key}.png'
        art.save(file, optimize=True)
        props[key] = {'image': file.relative_to(LEVEL).as_posix(), 'art_source': 'host_image',
                      'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
        produced[key] = props[key] | {'source': source, 'logical_size': list(art.size)}

    vent = Image.open(SOURCE / 'intake.png').convert('RGBA').crop((830, 320, 1536, 1000))
    plenum = quantize(vent, (377, 344), 19, smooth=True)
    edge = np.minimum(1, np.minimum(np.arange(plenum.shape[0]), np.arange(plenum.shape[0])[::-1]) / 28)
    plenum[..., 3] = np.rint(plenum[..., 3] * edge[:, None]).astype(np.uint8)
    publish('circuit-plenum', Image.fromarray(plenum), 'intake.png')

    junction = plate_png('junction', (373, 483), (.73, .78, .79), (.52, .47), source_dir=SOURCE_ROOM)
    publish('circuit-junction', junction, 'junction.png')
    bank = Image.open(SOURCE / 'transformer.png').convert('RGBA').crop((924, 82, 1536, 1010))
    rectifier = quantize(bank, (388, 472), 21, smooth=True)
    rectifier[..., :3] = (rectifier[..., :3] * .68).astype(np.uint8)
    xx, yy = np.meshgrid(np.arange(388), np.arange(472))
    edge = np.minimum.reduce([xx / 42, (387 - xx) / 46, yy / 34, (471 - yy) / 18, np.ones_like(xx)])
    rectifier[..., 3] = np.rint(rectifier[..., 3] * edge).astype(np.uint8)
    publish('circuit-rectifier', Image.fromarray(rectifier), 'transformer.png')
    place('circuit-room-plenum', 'circuit-plenum', 30, 1062, 'rear')
    place('circuit-room-transformer', 'hall-transformer', 470, 960, 'rear')
    place('circuit-room-intake', 'hall-intake', 0, 374, 'rear')
    place('circuit-room-junction', 'circuit-junction', 1110, 658, 'rear')
    place('circuit-room-rectifier', 'circuit-rectifier', 1800, 806, 'rear')
    place('circuit-room-relay', 'hall-relay', 2530, 852, 'rear', powered='hall-relay-powered')

    atlas = Image.open(SOURCE / 'terrain.png').convert('RGBA')
    strips = {key: atlas.crop(box) for key, box in PARTS.items()}
    ceilings = {tuple(p) for p in image_layer['ceilings']}
    for x, y, width, height in level['collision']['rects']:
        if y == 0 or width < 28:
            continue
        # 큰 격벽의 바깥면만 세로 결을 쓰고, 넓은 면은 재료 구간마다 이어 붙인다.
        edges = [x, *(point for point in (920, 1650, 2350, 2810)
                      if width > 540 and x + 50 < point < x + width - 50), x + width]
        for start, end in zip(edges, edges[1:]):
            material = 'steel' if y < 1510 and start < 1650 else 'sink' if start < 2350 else 'board'
            w, h = round((end - start) / 2), round(min(height, 142) / 2)
            if height > 90 and width < height:
                pixels = surface(strips['steel'], 'steel', (round(height / 2), w), offset=start % 137 - 68)
                pixels = np.rot90(pixels).copy()
                pixels[..., :3] = (pixels[..., :3] * .53).astype(np.uint8)
            else:
                pixels = surface(strips[material], material, (w, h), offset=start % 231 - 115)
                if (x, y) in ceilings:
                    pixels = np.flipud(pixels).copy()
                    pixels[..., :3] = (pixels[..., :3] * .66).astype(np.uint8)
            key = f'circuit-deck-{start}-{y}'
            publish(key, Image.fromarray(pixels), 'terrain.png')
            place(key, key, start, y, 'structure')

    for device in level['collision']['power_devices']:
        if device['kind'] in {'bridge', 'hatch'}:
            _, _, w, h = device['rect']
            kind = 'board' if device['kind'] == 'bridge' else 'steel'
            style = 'bridge' if device['kind'] == 'bridge' else 'steel'
            pixels = surface(strips[kind], style, (w // 2, h // 2))
            if device['kind'] == 'hatch':
                pixels[0, :, :3] = (184, 136, 76)
                yy, xx = np.ogrid[:h // 2, :w // 2]
                marked = (yy > 0) & (yy < 5) & ((xx + yy) % 13 < 6) & (pixels[..., 3] == 255)
                pixels[marked, :3] = (154, 110, 62)
            publish('circuit-' + device['kind'], Image.fromarray(pixels), 'terrain.png')

    remaining = [obj for obj in level['objects'] if not obj['id'].startswith(('hall-', 'circuit-'))
                 and obj['prop'] in props]
    level.update(props=props, objects=objects + remaining)
    panorama = OUT / 'overview.png'
    overview.convert('RGB').save(panorama, optimize=True)
    image_layer.update(image=panorama.relative_to(LEVEL).as_posix(), art_source='host_image',
                       sha256=hashlib.sha256(panorama.read_bytes()).hexdigest())
    write_bundle(path, level)
    info = {
        'art_source': 'host_image', 'model': 'Codex ImageGen', 'estimateUsd': None, 'world_units_per_pixel': 2,
        'sources': {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                    for file in (SOURCE_ROOM / 'junction.png', SOURCE_ROOM / 'junction-prompt.txt',
                                 SOURCE / 'intake.png', SOURCE / 'terrain.png', SOURCE / 'transformer.png')},
        'assets': produced,
    }
    (OUT / 'provenance.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
