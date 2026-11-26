"""Bake the air pose sequence with the six exact ground slash layers."""
from itertools import accumulate
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
WARDEN = ROOT / 'assets/warden'
ART = ROOT / 'art/warden'
SIZE = (256, 224)
PIVOT = (128, 136)
COLUMNS = 6
GROUND_FX_START = 100
GROUND_FX_FRAME_MS = 20
# The air clip is drawn from the body center, 41.5 px above the ground clip anchor.
AIR_FX_ANCHOR_OFFSET = (0, 42)


def tile(atlas, index, size, columns):
    w, h = size
    x, y = index % columns * w, index // columns * h
    return atlas.crop((x, y, x + w, y + h))


def ground_layers():
    folder = ART / 'ground-crescent-discharge-refined'
    slash = Image.open(folder / 'slash.png').convert('RGBA')
    discharge = Image.open(folder / 'discharge.png').convert('RGBA')
    for index in range(6):
        effect = tile(slash, index, (224, 208), 6)
        effect.alpha_composite(tile(discharge, index, (224, 208), 6))
        left, top, right, bottom = effect.getchannel('A').getbbox()
        box = (round((right - left) * 1.2), round((bottom - top) * 1.2))
        origin = (PIVOT[0] + round((left - 112) * 1.2), PIVOT[1] + round((top - 128) * 1.2))
        canvas = Image.new('RGBA', SIZE)
        canvas.alpha_composite(effect.crop((left, top, right, bottom)).resize(box, Image.Resampling.NEAREST), origin)
        yield canvas


def main():
    effects = list(ground_layers())
    ground = Image.open(WARDEN / 'attack.png').convert('RGBA')
    body_dir = ART / 'provisional-approved/basic-attack-hk-v6-arm-v3/frames'
    for fx_index, body_index in enumerate((6, 7, 8, 9, 10, 10)):
        body = Image.open(body_dir / f'frame_{body_index:03}.png').convert('RGBA')
        expected = Image.new('RGBA', SIZE)
        expected.alpha_composite(body, (32, 16))
        expected.alpha_composite(effects[fx_index])
        assert expected.tobytes() == tile(ground, fx_index + 5, SIZE, COLUMNS).tobytes(), fx_index

    source = ART / 'provisional-approved/air-rebound-v9-current-v4'
    timing = json.loads((source / 'timing/selection.json').read_text(encoding='utf-8'))
    poses = [Image.open(source / 'frames' / name).convert('RGBA') for name in timing['sourceFiles']]
    starts = [0, *accumulate(timing['durations_ms'])]
    fx_end = GROUND_FX_START + len(effects) * GROUND_FX_FRAME_MS
    edges = sorted(set(starts).union(range(GROUND_FX_START, fx_end + 1, GROUND_FX_FRAME_MS)))
    durations = [b - a for a, b in zip(edges, edges[1:])]
    atlas = Image.new('RGBA', (SIZE[0] * COLUMNS, SIZE[1] * ((len(durations) + COLUMNS - 1) // COLUMNS)))
    for index, elapsed in enumerate(edges[:-1]):
        body_index = next(i for i, stop in enumerate(starts[1:]) if elapsed < stop)
        frame = Image.new('RGBA', SIZE)
        frame.alpha_composite(poses[body_index], (32, 24))
        if GROUND_FX_START <= elapsed < fx_end:
            frame.alpha_composite(effects[(elapsed - GROUND_FX_START) // GROUND_FX_FRAME_MS], AIR_FX_ANCHOR_OFFSET)
        atlas.alpha_composite(frame, (index % COLUMNS * SIZE[0], index // COLUMNS * SIZE[1]))
    atlas.save(WARDEN / 'air_attack.png')
    print(json.dumps({'frameSize': SIZE, 'pivot': PIVOT, 'count': len(durations), 'durationsMs': durations}))


if __name__ == '__main__':
    main()
