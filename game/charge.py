"""사전 생성 PNG 전하와 거리 활성화. 픽셀 생성은 제작 도구에서만 수행한다."""

import json
from math import exp, floor, hypot, isfinite
from pathlib import Path

import pico2d.pico2d as pico
from engine.rendering.drawing import _sdl

from game_framework import GameObject, RenderItem, SpriteFrame, draw_sprite


ACTIVATION_DISTANCE = 300
CLICK_RADIUS = 48
SIZE = 80
ASSETS = Path(__file__).resolve().parents[1] / 'assets/charge/baked'


class ChargeArt:
    def __init__(self, images):
        data = json.loads((ASSETS / 'charge.json').read_text(encoding='utf-8'))
        self.steps = data['steps']
        width, height = data['size']
        columns = data['columns']
        pivot = tuple(v / n for v, n in zip(data['origin'], data['size']))
        self.frames = []
        for step in range(self.steps + 1):
            image = images.load(ASSETS / f'charge-{step:02}.png')
            _sdl(pico.SDL_SetTextureScaleMode(image._borrow().texture, pico.SDL_ScaleModeNearest))
            self.frames.append(tuple(SpriteFrame(image, (i % columns * width, i // columns * height,
                                                        width, height), pivot)
                                     for i in range(data['count'])))

    def frame(self, elapsed, value):
        # shortcut: 표시값은33단계, 단계 차이가 보이면 생성기의 샘플 수를 늘린다.
        step = floor(value * self.steps + .5)
        return self.frames[step][floor(elapsed * 24) % 72]


class Charge(GameObject):
    def __init__(self, art, position):
        super().__init__()
        self.art, self.position = art, tuple(position)
        self.elapsed = self.value = self.velocity = 0.0
        self.active = False
        self.spent = False
        self.spent_elapsed = 0.0

    def on_spawn(self):
        self.active = self.in_range(self.level.mode.activation_origin)

    def spend(self):
        self.spent = True
        self.active = False

    def on_destroy(self):
        self.art = None

    def in_range(self, origin):
        x, y = origin
        return not self.spent and hypot(self.position[0] - x, self.position[1] - y) <= ACTIVATION_DISTANCE

    def update(self, dt):
        if not isfinite(dt) or dt < 0:
            raise ValueError('dt는 유한한 비음수 초여야 합니다.')
        if self.spent:
            self.spent_elapsed += dt
            return
        self.active = self.in_range(self.level.mode.activation_origin)
        if dt == 0:
            return
        self.elapsed = (self.elapsed + dt) % 3
        w = 18 if self.active else 14
        error = self.value - self.active
        c, decay = self.velocity + w * error, exp(-w * dt)
        self.value = self.active + (error + c * dt) * decay
        self.velocity = (self.velocity - w * c * dt) * decay
        if not 0 <= self.value <= 1:
            self.value, self.velocity = min(1, max(0, self.value)), 0.0
        if abs(self.value - self.active) < .00005 and abs(self.velocity) < .001:
            self.value, self.velocity = float(self.active), 0.0

    def _draw(self, transform, opacity):
        frame = self.art.frame(self.elapsed, self.value)
        draw_sprite(frame, transform, self.position, frame.rect[2:], opacity)

    def render_items(self):
        return () if self.spent else (RenderItem(self._draw, draw_order=-1),)
