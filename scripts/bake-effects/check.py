"""도구 Python: 제작 합성의 기존 기준·PNG 바이트·단계화 오차를 확인한다."""

import argparse
from hashlib import sha256
import json
from math import floor, nextafter, pi, sin
from pathlib import Path
from random import Random

import numpy as np
from PIL import Image, ImageDraw

from charge import ASSETS, OUT, ROOT, compose, frames, pixels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reference = json.loads((ROOT / 'tests/fixtures/charge_composition.json').read_text(encoding='utf-8'))
    source = [frames('inactive', 9, 72), frames('active', 9, 72), frames('pulse', 4, 10)]
    digest = sha256()
    for group in source:
        for frame in group:
            digest.update(frame.tobytes())
    assert digest.hexdigest() == reference['frames_sha256']
    off, on, wave = [list(map(pixels, group)) for group in source]
    rng, digest, count = Random(7), sha256(), 0
    for index in range(72):
        values = (.01, .125, .25, .5, .75, .875, .99, rng.random(), nextafter((index % 8 + 1) / 9, 1))
        for value in values:
            phase, lower = value * 9, floor(value * 9)
            for bob in (-1, 0, 1):
                result = compose(off[index], on[index], wave[lower], wave[min(9, lower+1)],
                                 value, phase-lower, bob)
                digest.update(result.tobytes())
                count += 1
    assert count == reference['samples']
    assert digest.hexdigest() == reference['composition_sha256'], '오프라인 합성 기준 변경'

    meta = json.loads((OUT / 'charge.json').read_text(encoding='utf-8'))
    w, h = meta['size']
    baked = []
    for step in range(meta['steps'] + 1):
        with Image.open(OUT / f'charge-{step:02}.png') as sheet:
            group, digest = [], sha256()
            for index in range(72):
                frame = Image.new('RGBA', (80, 80))
                frame.paste(sheet.crop((index % 9*w, index // 9*h, (index % 9+1)*w, (index // 9+1)*h)),
                            tuple(meta['crop'][:2]))
                group.append(frame)
                digest.update(frame.tobytes())
            assert digest.hexdigest() == meta['frame_sha256'][step], 'PNG 시트·메타데이터 불일치'
            baked.append(group)

    def shown(frame):
        rgba = np.asarray(frame, dtype=np.float64)
        a = rgba[:, :, 3:] / 255
        return rgba[:, :, :3] * a + np.array([200, 200, 210]) * (1-a)

    errors, comparisons = [], []
    for index in range(72):
        for value in (.01, .12, .24, .37, .51, .63, .76, .88, .99):
            phase, lower = value*9, floor(value*9)
            bob = floor(sin((index+.5)/72*2*pi)*1.2+.5)
            before = compose(off[index], on[index], wave[lower], wave[min(9, lower+1)], value, phase-lower, bob)
            after = baked[floor(value*meta['steps']+.5)][index]
            mask = np.maximum(np.asarray(before)[:, :, 3], np.asarray(after)[:, :, 3]) > 4
            error = np.abs(shown(before)-shown(after))
            errors.append(error[mask].ravel())
            if index in (0, 24, 48) and value in (.12, .51, .88):
                comparisons.append((index, value, before, after))
    errors = np.concatenate(errors)
    print(f'기존 합성{count}샘플·PNG2376프레임 SHA 일치; '
          f'648전환/유효픽셀 RGB 오차 평균={errors.mean():.3f}, p99={np.quantile(errors,.99):.3f}, 최대={errors.max():.3f}/255')
    contact = Image.new('RGB', (360, len(comparisons)*92), (200, 200, 210))
    draw = ImageDraw.Draw(contact)
    for row, (index, value, before, after) in enumerate(comparisons):
        draw.text((2, row*92+2), f'{index} / {value}', fill='black')
        for column, frame in enumerate((before, after)):
            contact.paste(Image.fromarray(np.rint(shown(frame)).astype(np.uint8)), (105+column*105, row*92+10))
    contact.save(args.output_dir / 'charge-before-after.png')


if __name__ == '__main__':
    main()
