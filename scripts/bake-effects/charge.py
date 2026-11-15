"""도구 Python으로 승인 전하의 전환을 PNG에 굽는다. 게임에서는 실행하지 않는다."""

import json
from hashlib import sha256
from math import floor, pi, sin
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets/charge'
OUT = ASSETS / 'baked'
SIZE, COUNT, STEPS, COLUMNS = 80, 72, 32, 9


def pixels(data):
    result = np.asarray(data, dtype=np.float64).copy()
    result[:, :, :3] = result[:, :, :3] * result[:, :, 3:] / 255
    return result


def compose(inactive, active, pulse_a, pulse_b, value, fraction, bob):
    base = inactive * (1 - value) + active * value
    first, last = max(0, -bob), min(SIZE, SIZE - bob)
    pulse = pulse_a[first:last] * (1 - fraction) + pulse_b[first:last] * fraction
    target = base[first + bob:last + bob]
    target[:] = pulse + target * (1 - pulse[:, :, 3:] / 255)
    rgb, alpha = base[:, :, :3], base[:, :, 3:]
    np.divide(rgb * 255, alpha, out=rgb, where=alpha > 0)
    return Image.fromarray((base + .5).astype(np.uint8))


def frames(name, columns, count):
    with Image.open(ASSETS / f'{name}.png') as source:
        source = source.convert('RGBA')
        return [source.crop((i % columns * SIZE, i // columns * SIZE,
                             (i % columns + 1) * SIZE, (i // columns + 1) * SIZE))
                for i in range(count)]


def main():
    OUT.mkdir(exist_ok=True)
    inactive, active, pulse = frames('inactive', 9, 72), frames('active', 9, 72), frames('pulse', 4, 10)
    off, on, wave = [list(map(pixels, group)) for group in (inactive, active, pulse)]
    sheets = []
    crop = [SIZE, SIZE, 0, 0]
    for step in range(STEPS + 1):
        value = step / STEPS
        phase = value * 9
        lower = floor(phase)
        row = []
        for index in range(COUNT):
            bob = floor(sin((index + .5) / COUNT * 2 * pi) * 1.2 + .5)
            frame = (inactive[index] if step == 0 else active[index] if step == STEPS else
                     compose(off[index], on[index], wave[lower], wave[min(9, lower + 1)],
                             value, phase - lower, bob))
            box = frame.getchannel('A').getbbox()
            if box:
                crop = [min(crop[0], box[0]), min(crop[1], box[1]),
                        max(crop[2], box[2]), max(crop[3], box[3])]
            row.append(frame)
        sheets.append(row)
    width, height = crop[2] - crop[0], crop[3] - crop[1]
    digests = []
    for step, row in enumerate(sheets):
        sheet = Image.new('RGBA', (width * COLUMNS, height * (COUNT // COLUMNS)))
        digest = sha256()
        for index, frame in enumerate(row):
            digest.update(frame.tobytes())
            sheet.paste(frame.crop(crop), (index % COLUMNS * width, index // COLUMNS * height))
        sheet.save(OUT / f'charge-{step:02}.png')
        digests.append(digest.hexdigest())
    manifest = dict(steps=STEPS, count=COUNT, columns=COLUMNS, size=[width, height],
                    origin=[40 - crop[0], 40 - crop[1]], crop=crop,
                    source_sha256={name: sha256((ASSETS / f'{name}.png').read_bytes()).hexdigest()
                                   for name in ('inactive', 'active', 'pulse')},
                    frame_sha256=digests)
    (OUT / 'charge.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'전하 {len(sheets)}×{COUNT}프레임, crop={crop}, RGBA={width*height*4*COUNT*len(sheets)/2**20:.2f} MiB')


if __name__ == '__main__':
    main()
