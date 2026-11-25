"""상하 출입구와 점검실을 오래된 전자 부품으로 마감한다."""

import hashlib
import json

import numpy as np
from PIL import Image, ImageOps

from build_annex import save_overview
from build_transformer_hall import LEVEL, PARTS, ROOT, SOURCE, plate_png, quantize, surface, write_bundle


SOURCES = ROOT / 'art/levels/power-supply/network/source'
OUT = LEVEL / 'network'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def facing(room, rectangles, source):
    """기존 캡에서 아래 판재로 어둡게 이어지고 개구부의 알파를 남긴다."""
    left, top, width, height = room
    size = width // 2, height // 2
    mask = np.zeros((size[1], size[0]), dtype=np.uint8)
    for (x, y), (w, h) in rectangles.items():
        if w < 120 or h < 95 or y < 850:
            continue
        a, b = max(0, (x - left + 1) // 2), min(size[0], (x + w - left) // 2)
        c, d = max(0, (y + 34 - top) // 2), min(size[1], (y + h - top) // 2)
        if a >= b or c >= d:
            continue
        depth = top + 2 * np.arange(c, d) - y
        strength = np.clip((depth - 33) / 58, 0, 1)
        shade = np.clip(1.04 - depth / 1370, .78, 1)
        blend = (239 * strength * shade).astype(np.uint8)
        mask[c:d, a:b] = np.maximum(mask[c:d, a:b], blend[:, None])
    if not mask.any():
        return None
    texture = ImageOps.fit(source, size, Image.Resampling.LANCZOS)
    pixels = quantize(texture.convert('RGBA'), size, 18, smooth=True).copy()
    pixels[..., :3] = (pixels[..., :3] * [.37, .40, .44] + [11, 14, 17]).astype(np.uint8)
    pixels[..., 3] = mask
    return Image.fromarray(pixels)


def main():
    OUT.mkdir(exist_ok=True)
    route = LEVEL / 'map.json'
    data = json.loads(route.read_text(encoding='utf-8'))
    props = {key: item for key, item in data['props'].items() if not key.startswith('network-')}
    objects = [obj for obj in data['objects'] if not obj['id'].startswith('network-')]
    details = {}

    def place(key, art, source, left, top, layer, *, instance=''):
        key = 'network-' + key
        if key not in props:
            file = OUT / f'{key}.png'
            art.save(file, optimize=True)
            props[key] = {'image': file.relative_to(LEVEL).as_posix(), 'art_source': 'host_image',
                          'sha256': digest(file)}
            details[key] = props[key] | {'source': source, 'logical_size': list(art.size)}
        objects.append({'id': key + instance, 'prop': key, 'x': left, 'y': top,
                        'anchor_px': [0, 0], 'solid': False, 'layer': layer, 'sortY': 0, 'scale': 2})

    attic = plate_png('diagnostic', (720, 264), (.79, .79, .79), (.5, .48), source_dir=SOURCES)
    place('diagnostic', attic, 'diagnostic.png', 4880, 132, 'rear')

    chamber, = (room['rect'] for room in data['camera']['rooms'] if room['id'] == 'load-test-chamber')
    chamber_left, chamber_top, chamber_width, _ = chamber
    chamber_art = plate_png('surge', (chamber_width // 2, (2470 - chamber_top) // 2),
                            (.83, .83, .81), (.5, .45), source_dir=SOURCES)
    place('surge', chamber_art, 'surge.png', chamber_left, chamber_top, 'rear')

    terrain = Image.open(SOURCE / 'terrain.png').convert('RGBA')
    steel = terrain.crop(PARTS['steel'])
    board = terrain.crop(PARTS['board'])
    rectangles = {(x, y): (width, height) for x, y, width, height in data['collision']['rects']}

    deck_positions = ((5750, 1070), (5900, 1190), (5750, 1310), (5900, 1430), (5750, 1550),
                      (5480, 795), (5300, 670), (4770, 660), (4864, 32), (4864, 660),
                      (7214, 1570), (7214, 1594), (7422, 1694), (7760, 1750), (9200, 1750),
                      (7032, 2360), (7050, 2250), (7254, 2148), (7336, 2030), (7254, 1910), (7336, 1792),
                      (9240, 2350), (9120, 2230), (9004, 2110), (9123, 1990), (9030, 1870),
                      (7000, 2470), (7000, 1920), (9408, 1920))
    for left, top in deck_positions:
        width, height = rectangles[left, top]
        if width <= 42:
            pixels = np.rot90(surface(steel, 'steel', (height // 2, width // 2))).copy()
            pixels[..., :3] = (pixels[..., :3] * [.59, .54, .52]).astype(np.uint8)
        else:
            kind = 'board' if left >= 5300 and top < 1800 else 'steel'
            pixels = surface(board if kind == 'board' else steel, kind,
                             (width // 2, min(height, 102) // 2), offset=left % 194 - 75)
        place(f'deck-{left}-{top}', Image.fromarray(pixels), 'terrain.png', left, top, 'structure')

    original = Image.open(SOURCES / 'diagnostic.png').convert('RGB')
    materials = {
        'steel': original.crop((20, 160, 942, 248)),
        'board': original.crop((540, 265, 668, 668)),
        'rust': original.crop((70, 681, 1500, 749)),
    }
    for room in data['camera']['rooms']:
        name, rect = room['id'], room['rect']
        material = 'board' if 'capacitor' in name else 'rust' if name in ('filter-gallery', 'load-test-chamber') else 'steel'
        backdrop = facing(rect, rectangles, materials[material])
        if backdrop is not None:
            bounds = backdrop.getbbox()
            place('facing-' + name, backdrop.crop(bounds), 'diagnostic.png',
                  rect[0] + 2 * bounds[0], rect[1] + 2 * bounds[1], 'structure')

    atlas = Image.open(SOURCES / 'aging.png').convert('RGBA')
    half_width, half_height = atlas.width // 2, atlas.height // 2
    surfaces = (
        ('lint', (110, 20), ((1230, 1464), (4516, 1724), (5034, 634), (7220, 1544), (7112, 2446), (9100, 2446))),
        ('rust', (114, 19), ((1696, 1004), (5514, 1022), (6774, 1543), (7512, 1018), (8554, 1752), (9030, 2474))),
        ('residue', (87, 18), ((5434, 1752), (5662, 1674), (5320, 923), (7196, 914), (7248, 2472))),
        ('grime', (109, 20), ((2940, 1785), (4912, 664), (5754, 1700), (7538, 1056), (7050, 2512))),
    )
    for quadrant, (key, size, positions) in enumerate(surfaces):
        x, y = quadrant % 2 * half_width, quadrant // 2 * half_height
        section = atlas.crop((x, y, x + half_width, y + half_height))
        bounds = section.getchannel('A').point(lambda a: 255 if a >= 120 else 0).getbbox()
        pixels = np.array(section.crop(bounds))
        pixels[..., :3] = np.rint(pixels[..., :3] * [.82, .81, .79]).astype(np.uint8)
        pixels = quantize(pixels, size, 16, smooth=True).copy()
        width, height = size
        y, x = np.ogrid[:height, :width]
        fade = np.minimum(np.minimum(x / 13, (width - 1 - x) / 13), (height - 1 - y) / 5)
        pixels[..., 3] = np.rint(pixels[..., 3] * np.clip(fade, 0, 1)).astype(np.uint8)
        art = Image.fromarray(pixels)
        for index, (left, top) in enumerate(positions):
            place(key, art, 'aging.png', left, top, 'structure', instance=f'-{index + 1}')
        if key == 'grime':
            post = art.transpose(Image.Transpose.ROTATE_270)
            for name, left, top, length in (
                ('capacitor-west', 5734, 1070, 596), ('capacitor-east', 5992, 1070, 596),
                ('filter-chute', 7472, 1010, 350), ('surge-intake', 7224, 1920, 350),
                ('surge-return', 9208, 1920, 414),
            ):
                trim = post.resize((18, length // 2), Image.Resampling.NEAREST)
                place('upright-' + name, trim, 'aging.png', left, top, 'rear')

    data.update(props=props, objects=objects)
    save_overview(data, OUT / 'overview.png')
    write_bundle(route, data)
    sources = [SOURCES / 'diagnostic.png', SOURCES / 'surge.png', SOURCES / 'aging.png', SOURCE / 'terrain.png']
    (OUT / 'provenance.json').write_text(json.dumps({
        'art_source': 'host_image', 'model': 'Codex ImageGen', 'world_units_per_pixel': 2,
        'sources': {file.relative_to(ROOT).as_posix(): digest(file) for file in sources},
        'assets': details,
    }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
