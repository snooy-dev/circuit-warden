"""승인 pixelfx v4를 길이별 PNG로 재생한다. 고지는 licenses/pixelfx-LICENSE.txt 참조."""

from bisect import bisect_left
import json
from math import atan2, cos, degrees, floor, hypot, isfinite, sin
from pathlib import Path

import pico2d.pico2d as pico
from engine.rendering.drawing import _sdl

from game_framework import GameObject, RenderItem, SpriteFrame, SpritePlayer, draw_image, draw_sprite


DURATION = 0.1
_FRAME_COUNT = 12
ASSETS = Path(__file__).resolve().parents[1] / 'assets/charge/baked'


class LinkArt:
    def __init__(self, images):
        data = json.loads((ASSETS / 'link.json').read_text(encoding='utf-8'))
        self.lengths, self.frames = [], []
        for sheet in data['sheets']:
            image = images.load(ASSETS / sheet['file'])
            _sdl(pico.SDL_SetTextureScaleMode(image._borrow().texture, pico.SDL_ScaleModeNearest))
            width, height = sheet['size']
            columns = data['columns']
            self.lengths.append(sheet['length'])
            self.frames.append(tuple(SpriteFrame(image, (i % columns * width, i // columns * height,
                                                        width, height)) for i in range(_FRAME_COUNT)))

    def choose(self, length):
        index = min(bisect_left(self.lengths, length), len(self.lengths) - 1)
        if index and length - self.lengths[index - 1] < self.lengths[index] - length:
            index -= 1
        # shortcut: 최대320px 시트, 활성 거리를 늘릴 때 긴 시트를 추가한다.
        return self.lengths[index], self.frames[index]


class TeleportLink(GameObject):
    def __init__(self, start, end, art, arrival=None):
        super().__init__()
        self._start, self._end = tuple(start), tuple(end)
        sx, sy = self._start
        ex, ey = self._end
        dx, dy = ex - sx, ey - sy
        if not all(map(isfinite, (sx, sy, ex, ey, dx, dy))):
            raise ValueError('전류 끝점 좌표는 유한해야 합니다.')
        self._length = hypot(dx, dy)
        length, self._frames = art.choose(self._length)
        width, height = self._frames[0].rect[2:]
        # 극단적으로 짧은 연결은 광륜을 늘리지 않고 끝점 오차를0.25px 이내로 제한한다.
        width *= self._length / length if self._length >= 8 else 1
        cx, cy = (sx + ex) / 2, (sy + ey) / 2
        radians = atan2(dy, dx)
        self._angle = -degrees(radians)
        self._draw_bounds = (cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2)
        rx = (abs(cos(radians)) * width + abs(sin(radians)) * height) / 2
        ry = (abs(sin(radians)) * width + abs(cos(radians)) * height) / 2
        self._bounds = (cx - rx, cy - ry, cx + rx, cy + ry)
        self._elapsed = 0.0
        self._fresh = True
        self.arrival = SpritePlayer(arrival) if arrival is not None else None

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def elapsed(self):
        return self._elapsed

    @property
    def frame_index(self):
        return min(_FRAME_COUNT - 1, floor(self._elapsed / DURATION * _FRAME_COUNT + 1e-6))

    def on_destroy(self):
        self._frames = None
        self.arrival = None

    def update(self, dt):
        # 입력 단계에서 생성됐으므로 첫 dt는 생성 이전 프레임의 시간이다.
        if self._fresh:
            self._fresh = False
            return
        self._elapsed += dt
        if self._elapsed + 1e-12 >= DURATION:
            self.destroy()
        elif self.arrival is not None:
            self.arrival.update(dt)

    def _draw(self, transform, opacity):
        self._fresh = False
        if self._length < 1:
            return
        frame = self._frames[self.frame_index]
        draw_image(frame.image._borrow(), transform, self._draw_bounds, opacity,
                   source=frame.rect, angle=self._angle)

    def render_items(self):
        link = RenderItem(self._draw, draw_order=-1, bounds=self._bounds)
        if self.arrival is None:
            return (link,)
        return link, RenderItem(self._draw_arrival, draw_order=1)

    def _draw_arrival(self, transform, opacity):
        frame = self.arrival.frame
        draw_sprite(frame, transform, self.end, frame.rect[2:], opacity)
