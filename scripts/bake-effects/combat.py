"""전하 소멸·적중 시트를 게임 팔레트와 기준점에 맞춰 굽는다."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


ASSETS = Path(__file__).resolve().parents[2] / 'assets' / 'combat'
SOURCE = ASSETS / 'source'
CHARGE_ANCHORS = ((323, 333), (306, 333), (320, 312), (314, 315))


def quantize(frame, palette, opacity, premultiplied):
    pixels = np.asarray(frame, dtype=np.int32).copy()
    if premultiplied:
        # pixelfx 시트의 투명 캔버스 합성이 RGB에 이미 적용한 알파를 푼다.
        alpha = np.maximum(pixels[:, :, 3:4], 1)
        pixels[:, :, :3] = np.minimum((pixels[:, :, :3] * 255 + alpha // 2) // alpha, 255)
        pixels[:, :, 3] = (alpha[:, :, 0] ** 2 + 127) // 255
    difference = pixels[:, :, None, :3] - palette
    colors = np.argmin((difference ** 2).sum(axis=-1), axis=-1)
    pixels[:, :, :3] = palette[colors]
    alpha = np.round(pixels[:, :, 3] * opacity / 32) * 32
    pixels[:, :, 3] = np.minimum(alpha, 255).astype(np.uint8)
    pixels[pixels[:, :, 3] == 0] = 0
    return Image.fromarray(pixels.astype(np.uint8))


def frame_box(index, columns, width, height):
    x, y = index % columns * width, index // columns * height
    return x, y, x + width, y + height


def main():
    clips = json.loads((ASSETS / 'animations.json').read_text(encoding='utf-8'))
    colors = json.loads((SOURCE / 'hit-spark.options.json').read_text(encoding='utf-8'))['palette']
    palette = np.array([[int(color[i:i + 2], 16) for i in (1, 3, 5)] for color in colors],
                       dtype=np.int32)
    for name, clip in clips.items():
        width, height = clip['frameSize']
        columns, count = clip['columns'], clip['count']
        source = Image.open(SOURCE / clip['file']).convert('RGBA')
        rows = (count + columns - 1) // columns
        atlas = Image.new('RGBA', (width * columns, height * rows))
        extent = []
        for index in range(count):
            if name == 'charge_spent':
                raw = source.crop(frame_box(index, columns, source.width // 2, source.height // 2))
                x, y = CHARGE_ANCHORS[index]
                # 광원의 중심을 먼저 정렬하고 같은 배율로 축소한다.
                frame = raw.crop((x - 192, y - 192, x + 192, y + 192))
                frame = frame.resize((width, height), Image.Resampling.BOX)
                opacity = (1, .92, .74, .45)[index]
            else:
                frame = source.crop(frame_box(index, columns, width, height))
                opacity = min(1, (count - index) / 4)
            frame = quantize(frame, palette, opacity, premultiplied=(name == 'hit_spark'))
            bounds = frame.getbbox()
            assert bounds and 0 < bounds[0] < bounds[2] < width and 0 < bounds[1] < bounds[3] < height, (
                name, index, bounds)
            extent.append((bounds[2] - bounds[0], bounds[3] - bounds[1]))
            atlas.paste(frame, frame_box(index, columns, width, height)[:2])
        if name == 'charge_spent':
            assert all(w0 > w1 and h0 > h1 for (w0, h0), (w1, h1) in zip(extent, extent[1:])), extent
        atlas.save(ASSETS / clip['file'])
        print(name, count, sum(clip['durationsMs']), extent)


if __name__ == '__main__':
    main()
