"""새 전원 구역의 이동면과 개구부에 hi-bit 판재와 이음쇠를 조립한다."""

import hashlib
import json

import numpy as np
from PIL import Image, ImageOps

from build_annex import save_overview
from build_transformer_hall import LEVEL, PARTS, ROOT, SOURCE, plate_png, quantize, write_bundle


ART = ROOT / 'art/levels/power-supply'
OUT = LEVEL / 'vertical'
NEW = ART / 'vertical/source'
ANNEX = ART / 'annex/source'
NETWORK = ART / 'network/source'
PLATES = {
    'central-distribution': (NEW / 'plenum.png', (.81, .83, .86), (.50, .54), 'steel'),
    'cooling-chimney': (NEW / 'riser.png', (.66, .76, .82), (.53, .47), 'sink'),
    'filter-gallery': (ANNEX / 'filter.png', (.76, .76, .74), (.48, .61), 'sink'),
    'relay-tower': (SOURCE / 'relay.png', (.76, .79, .80), (.53, .58), 'steel'),
    'diagnostic-loft': (NETWORK / 'diagnostic.png', (.78, .80, .78), (.51, .56), 'board'),
    'capacitor-reservoir': (ANNEX / 'capacitors.png', (.72, .78, .82), (.55, .53), 'board'),
    'thermal-bank': (ANNEX / 'thermal.png', (.77, .77, .78), (.48, .61), 'sink'),
    'coolant-sump': (SOURCE / 'transformer.png', (.67, .77, .84), (.47, .72), 'steel'),
    'load-test-chamber': (NETWORK / 'surge.png', (.74, .80, .81), (.46, .52), 'steel'),
    'output-terminal': (NEW / 'connector.png', (.85, .84, .79), (.63, .53), 'board'),
}
OPENINGS = (
    # 순서대로 개구부의 양쪽과 통과 좌표를 연결한다.
    ('intake', 'central-distribution', 'x', 1440, 1990),
    ('central-distribution', 'capacitor-reservoir', 'x', 2880, 1990),
    ('central-distribution', 'coolant-sump', 'y', 2120, 1800),
    ('coolant-sump', 'thermal-bank', 'x', 1440, 2700),
    ('thermal-bank', 'cooling-chimney', 'x', 480, 2700),
    ('cooling-chimney', 'filter-gallery', 'x', 480, 1280),
    ('filter-gallery', 'relay-tower', 'x', 1440, 1280),
    ('filter-gallery', 'relay-tower', 'x', 1440, 930),
    ('relay-tower', 'diagnostic-loft', 'x', 2880, 1280),
    ('capacitor-reservoir', 'diagnostic-loft', 'y', 1400, 3820),
    ('capacitor-reservoir', 'diagnostic-loft', 'y', 1400, 3180),
    ('central-distribution', 'relay-tower', 'y', 1400, 2576),
    ('filter-gallery', 'load-test-chamber', 'y', 680, 756),
    ('load-test-chamber', 'output-terminal', 'x', 2340, 560),
)
FRAME_BOXES = {
    'beam': (0, 175, 620, 395),
    'post': (660, 0, 907, 503),
    'elbow': (1032, 65, 1536, 486),
    'harness': (102, 510, 383, 1024),
    'bracket': (1051, 570, 1536, 999),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parts():
    atlas = Image.open(NEW / 'framing.png').convert('RGBA')
    result = {}
    for name, box in FRAME_BOXES.items():
        cell = atlas.crop(box)
        visible = cell.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
        result[name] = cell.crop(visible.getbbox())
    return result


def part_image(source, size, gain):
    pixels = np.array(source.resize(size, Image.Resampling.LANCZOS))
    pixels[..., :3] = np.rint(pixels[..., :3] * gain).astype(np.uint8)
    return Image.fromarray(quantize(pixels, size, 18, smooth=True))


def clip_interval(first, second, coordinate, point, axis, collision):
    a, b = (1, 3) if axis == 'x' else (0, 2)
    low = max(first[a], second[a])
    high = min(first[a] + first[b], second[a] + second[b])
    for x, y, width, height in collision:
        side, extent, start, end = (x, width, y, y + height) if axis == 'x' else (y, height, x, x + width)
        if side <= coordinate <= side + extent:
            assert not start < point < end, (axis, coordinate, point, (x, y, width, height))
            if end <= point:
                low = max(low, end)
            elif start >= point:
                high = min(high, start)
    assert low < point < high, (axis, coordinate, point, low, high)
    return low, high


def structure(room, material, collision, cap, finish, posts):
    x, y, width, height = room
    w, h = width // 2, height // 2
    shell = Image.new('RGBA', (w, h))
    body = ImageOps.fit(finish, (w, h), Image.Resampling.LANCZOS).convert('RGBA')
    body = Image.fromarray(quantize(body, body.size, 16, smooth=True))
    for left, top, length, depth in collision:
        a = max(0, (left - x + 1) // 2)
        b = min(w, (left + length - x) // 2)
        c = max(0, (top - y + 1) // 2)
        d = min(h, (top + depth - y) // 2)
        if a >= b or c >= d:
            continue
        shell.paste(body.crop((a, c, b, d)), (a, c))
        section = (b - a, d - c)
        if length <= 72 and depth > 104:
            wall = posts.resize(section, Image.Resampling.NEAREST)
            shell.alpha_composite(wall, (a, c))
        elif top >= y and length >= 48:
            deck = cap[material]
            cap_height = min(section[1], deck.height)
            strip = deck.resize((section[0], cap_height), Image.Resampling.BOX)
            shell.alpha_composite(strip, (a, c))
    return shell


def main():
    OUT.mkdir(exist_ok=True)
    route = LEVEL / 'map.json'
    data = json.loads(route.read_text(encoding='utf-8'))
    objects = [item for item in data['objects'] if not item['id'].startswith('vertical-')]
    named = {'circuit-hatch', 'circuit-bridge', 'fan-cavity', 'hall-busbar-live', 'hall-busbar-safe',
             'output-lit', 'relay-on', 'relay-off', 'shutter-closed', 'shutter-open',
             data['layers'][0]['rotor']['prop']}
    named.update(item['prop'] for item in objects)
    named.update(item['powered_prop'] for item in objects if 'powered_prop' in item)
    props = {key: data['props'][key] for key in sorted(named)}
    rooms = {item['id']: item['rect'] for item in data['camera']['rooms']}
    collision = data['collision']['rects']
    assets = {}
    sources = set()
    atlas = parts()

    def publish(name, image, source, layer, position, *, opacity=1):
        name = 'vertical-' + name
        path = OUT / (name + '.png')
        image.save(path, optimize=True)
        sources.update(source)
        props[name] = {'image': path.relative_to(LEVEL).as_posix(), 'sha256': sha(path),
                       'art_source': 'host_image'}
        assets[name] = props[name] | {'sources': [p.relative_to(ROOT).as_posix() for p in source],
                                      'logical_size': list(image.size)}
        objects.append({'id': name, 'prop': name, 'x': position[0], 'y': position[1], 'anchor_px': [0, 0],
                        'solid': False, 'layer': layer, 'sortY': 0, 'scale': 2, 'opacity': opacity})

    frame_source = NEW / 'framing.png'
    terrain_source = SOURCE / 'terrain.png'
    texture_source = NEW / 'riser.png'
    terrain = Image.open(terrain_source).convert('RGBA')
    raw = Image.open(texture_source).convert('RGB')
    cap = {}
    for material in ('steel', 'board', 'sink'):
        detail = terrain.crop(PARTS[material])
        cap[material] = Image.fromarray(quantize(detail, (722, 45), 18, smooth=True))
    finish = {
        'steel': raw.crop((975, 318, 1188, 789)),
        'board': Image.open(NEW / 'plenum.png').crop((1219, 201, 1435, 850)),
        'sink': raw.crop((708, 176, 988, 765)),
    }
    finish_source = {'board': NEW / 'plenum.png', 'steel': texture_source, 'sink': texture_source}
    wall = part_image(atlas['post'], (26, 182), (.50, .55, .59))

    for name, room in rooms.items():
        x, y, width, height = room
        if name in PLATES:
            source, gain, focus, material = PLATES[name]
            plate = plate_png(source.stem, (width // 2, height // 2), gain, focus, source_dir=source.parent)
            publish(name + '-rear', plate, [source], 'rear', (x, y))
        else:
            material = 'steel'
        source = np.array(finish[material].convert('RGB'))
        source = np.rint(source * [.36, .41, .45] + [10, 13, 15]).astype(np.uint8)
        skin = structure(room, material, collision, cap, Image.fromarray(source), wall)
        if skin.getbbox():
            publish(name + '-shell', skin, [terrain_source, finish_source[material], frame_source], 'structure', (x, y))

    for number, (a, b, axis, coordinate, point) in enumerate(OPENINGS, 1):
        low, high = clip_interval(rooms[a], rooms[b], coordinate, point, axis, collision)
        if axis == 'x':
            panel = part_image(atlas['post'], (24, (high - low) // 2 + 12), (.60, .65, .69))
            publish(f'frame-{number}', panel, [frame_source], 'rear', (coordinate - 24, low - 12), opacity=.80)
            beam = part_image(atlas['beam'], (74, 23), (.73, .74, .76))
            publish(f'lintel-{number}', beam, [frame_source], 'front', (coordinate - 74, low - 46), opacity=.8)
        else:
            trim = part_image(atlas['post'], (23, 104), (.68, .69, .68))
            for side, left, image in (('left', low - 27, trim),
                                      ('right', high - 19, ImageOps.mirror(trim))):
                publish(f'rim-{number}-{side}', image, [frame_source], 'rear', (left, coordinate - 104), opacity=.82)
            bracket = part_image(atlas['bracket'], (47, 36), (.69, .70, .72))
            publish(f'coupler-{number}', bracket, [frame_source], 'front', (low - 94, coordinate - 44), opacity=.8)

    for name, coord, size in (
        ('chimney-return', (88, 1060), (51, 154)), ('chimney-inlet', (302, 2460), (57, 178)),
        ('charge-conduit', (3960, 1450), (48, 184)), ('output-coupler', (3220, 580), (54, 44)),
    ):
        piece = 'bracket' if name == 'output-coupler' else 'harness'
        image = part_image(atlas[piece], size, (.60, .63, .63))
        publish(name, image, [frame_source], 'rear', coord, opacity=.8)
    elbow = part_image(atlas['elbow'], (83, 92), (.69, .69, .70))
    publish('cooling-elbow', elbow, [frame_source], 'rear', (328, 1094), opacity=.82)
    publish('switchback-elbow', ImageOps.mirror(elbow), [frame_source], 'rear', (894, 728), opacity=.85)
    for name, point, height, tilt in (
        ('hub-strut', (1960, 1588), 392, -60),
        ('capacitor-strut', (3164, 1446), 540, -57),
        ('chimney-left-rail', (32, 1350), 690, 0),
        ('chimney-right-rail', (402, 1198), 753, 0),
    ):
        rail = part_image(atlas['post'], (23, height), (.55, .59, .60))
        rail = rail.rotate(tilt, resample=Image.Resampling.NEAREST, expand=True)
        publish(name, rail, [frame_source], 'rear', point, opacity=.68)

    objects.sort(key=lambda item: item['id'] in ('output-socket', 'output-cable'))
    data.update(props=props, objects=objects)
    save_overview(data, OUT / 'overview.png')
    write_bundle(route, data)
    metadata = {'art_source': 'host_image', 'model': 'Codex ImageGen', 'estimateUsd': None,
                'world_units_per_pixel': 2, 'sources': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(sources)},
                'assets': assets}
    (OUT / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
