"""전원 구역 원화를 2월드 단위당 1픽셀인 게임 자산으로 변환한다."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.agents/skills/generate2dmap/scripts'))
import forge_hibit as hibit


SOURCE = ROOT / 'art/levels/power-supply/return-loop/source'
OUTPUT = ROOT / 'assets/levels/power-supply/return-loop'
METAL = (
    '141c24', '1c262f', '263039', '303b45', '3b4752', '4c5961', '646f75', '859499', 'a4acaa',
    '382c29', '5e4036', '845743', 'b17451', 'c57d3f', 'ea9e43', 'f8c478',
    '1e3a3d', '325b58', '57928a', '6cc3ac', 'b9e9ca',
)
DEVICES = {
    'relay-off': ((342, 72, 733, 525), (52, 61)),
    'shutter-closed': ((1121, 0, 1305, 537), (23, 124)),
    'bridge': ((114, 765, 947, 832), (131, 14)),
    'feed-wire': ((1153, 574, 1232, 998), (18, 96)),
}


def bake(source, size, palette, *, smooth=False):
    width, height = size
    indexed = hibit.index_rgba(source, palette, alpha_threshold=192)
    reduced = hibit.mode_downsample(indexed, height, width, len(palette), coverage=.5)
    reduced = hibit.clean_isolated(reduced, palette)
    if smooth:
        reduced = hibit.mode_filter3(reduced, len(palette))
    return reduced


def save(name, reduced, palette):
    pixels = hibit.render(reduced, palette)
    image = Image.fromarray(pixels)
    image.save(OUTPUT / f'{name}.png', optimize=True)
    assert set(np.unique(pixels[..., 3])) <= {0, 255} and image.getbbox()
    return {
        'size': list(image.size),
        'opaque_colors': len(np.unique(reduced[reduced >= 0])),
        'sha256': hashlib.sha256((OUTPUT / f'{name}.png').read_bytes()).hexdigest(),
    }


def main():
    OUTPUT.mkdir(exist_ok=True)
    palette = np.array([hibit.parse_hex(color) for color in METAL], dtype=np.uint8)
    atlas = Image.open(SOURCE / 'device-atlas.png').convert('RGBA')
    assets = {}
    for name, (box, size) in DEVICES.items():
        reduced = bake(np.asarray(atlas.crop(box)), size, palette)
        if name == 'bridge':
            # 첫 줄을 실제 충돌 상단과 맞춘다.
            reduced[0] = 19
        assets[name] = save(name, reduced, palette) | {'crop': list(box)}
        if name == 'relay-off':
            lamp = reduced[12:25, 33:46]
            amber = (lamp >= 13) & (lamp <= 15)
            assert amber.sum() >= 16
            lamp[hibit.dilate4(amber) & ~amber & (lamp >= 0)] = 17
            lamp[amber] += 5
            assets['relay-on'] = save('relay-on', reduced, palette)
        elif name == 'shutter-closed':
            assets['shutter-open'] = save('shutter-open', reduced[:12], palette)
        elif name == 'feed-wire':
            conductor = (reduced >= 12) & (reduced <= 15)
            assert conductor.sum() >= 24
            reduced[conductor] += 5
            assets['feed-wire-on'] = save('feed-wire-on', reduced, palette)

    board = np.array(Image.open(SOURCE / 'pcb.png').convert('RGBA'))
    board[..., :3] = np.rint(board[..., :3] * .52 + [12, 16, 20]).astype(np.uint8)
    board_palette = hibit.kmeans_palette(board[..., :3][board[..., 3] >= 192], 18)
    reduced = bake(board, (320, 304), board_palette, smooth=True)
    assets['pcb'] = save('pcb', reduced, board_palette)

    sources = {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(SOURCE.iterdir())}
    provenance = {
        'art_source': 'host_image',
        'model': 'Codex ImageGen',
        'estimateUsd': None,
        'world_units_per_pixel': 2,
        'source_directory': SOURCE.relative_to(ROOT).as_posix(),
        'sources': sources,
        'assets': assets,
    }
    (OUTPUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
