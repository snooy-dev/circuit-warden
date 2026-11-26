"""Composite the selected airborne animation cels with the sword effects."""
from argparse import ArgumentParser
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
WARDEN = ROOT / 'assets/warden'
ART = ROOT / 'art/warden'
AIR_TIMES = [0, 18, 82, 120, 140, 160, 180, 200, 220, 246, 274, 300]
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


def sheet(frames, size, columns):
    w, h = size
    atlas = Image.new('RGBA', (w * columns, h * ((len(frames) + columns - 1) // columns)))
    for i, frame in enumerate(frames):
        bounds = frame.getchannel('A').getbbox()
        assert bounds and min(bounds[:2]) > 0 and bounds[2] < w and bounds[3] < h, (i, bounds)
        atlas.alpha_composite(frame, (i % columns * w, i // columns * h))
    return atlas


def down_layer(effect):
    # Point the horizontal electrical sweep down, with a broad opening at the feet.
    rotated = effect.transpose(Image.Transpose.ROTATE_270)
    pivot_x, pivot_y = SIZE[1] - 1 - 90, PIVOT[0]
    left, top, right, bottom = rotated.getchannel('A').getbbox()
    stretch, depth = 1.32, .72
    cropped = rotated.crop((left, top, right, bottom))
    scaled = cropped.resize((round(cropped.width * stretch), round(cropped.height * depth)),
                             Image.Resampling.NEAREST)
    target = (104 + round((left - pivot_x) * stretch), 77 + round((top - pivot_y) * depth))
    return scaled, target


def main():
    parser = ArgumentParser()
    parser.add_argument('output', type=Path, nargs='?', default=WARDEN)
    out = parser.parse_args().output
    effects = list(ground_layers())
    ground = Image.open(WARDEN / 'attack.png').convert('RGBA')
    body_dir = ART / 'provisional-approved/basic-attack-hk-v6-arm-v3/frames'
    for fx_index, body_index in enumerate((6, 7, 8, 9, 10, 10)):
        body = Image.open(body_dir / f'frame_{body_index:03}.png').convert('RGBA')
        expected = Image.new('RGBA', SIZE)
        expected.alpha_composite(body, (32, 16))
        expected.alpha_composite(effects[fx_index])
        assert expected.tobytes() == tile(ground, fx_index + 5, SIZE, COLUMNS).tobytes(), fx_index

    air_art = Image.open(WARDEN / 'attack-source/air-poses.png').convert('RGBA')
    poses = [tile(air_art, i, SIZE, COLUMNS) for i in range(len(AIR_TIMES) - 1)]
    fx_end = GROUND_FX_START + len(effects) * GROUND_FX_FRAME_MS
    edges = sorted(set(AIR_TIMES).union(range(GROUND_FX_START, fx_end + 1, GROUND_FX_FRAME_MS)))
    frames = []
    for elapsed in edges[:-1]:
        body_index = next(i for i, stop in enumerate(AIR_TIMES[1:]) if elapsed < stop)
        frame = poses[body_index].copy()
        if GROUND_FX_START <= elapsed < fx_end:
            frame.alpha_composite(effects[(elapsed - GROUND_FX_START) // GROUND_FX_FRAME_MS], AIR_FX_ANCHOR_OFFSET)
        frames.append(frame)
    sheet(frames, SIZE, COLUMNS).save(out / 'air_attack.png')

    down_size = (208, 208)
    down_art = Image.open(WARDEN / 'downstrike-source/poses.png').convert('RGBA')
    down = [tile(down_art, i, down_size, 5) for i in range(10)]
    for frame_index, fx_index in enumerate((1, 2, 3, 4, 5), start=3):
        down[frame_index].alpha_composite(*down_layer(effects[fx_index]))
    sheet(down, down_size, 5).save(out / 'downstrike.png')
    print(json.dumps({'count': len(frames), 'durationsMs': [b - a for a, b in zip(edges, edges[1:])]}))


if __name__ == '__main__':
    main()
