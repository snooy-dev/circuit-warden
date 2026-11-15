"""승인 전하 v5·중간 반전 v2의 거리 활성화와 픽셀 합성."""

from ctypes import string_at
from math import exp, floor, hypot, isfinite, pi, sin
from pathlib import Path

import pico2d.pico2d as pico

from game_framework import GameObject, RenderItem, draw_image
from engine.rendering.drawing import _sdl


ACTIVATION_DISTANCE = 300
CLICK_RADIUS = 24
SIZE = 80
ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'charge'


def _pixels(data):
    return {i: (data[i] * a / 255, data[i + 1] * a / 255, data[i + 2] * a / 255, a)
            for i in range(0, len(data), 4) if (a := data[i + 3])}


def _blend(first, second, value):
    result = {i: tuple(c * (1 - value) for c in pixel) for i, pixel in first.items()}
    for i, pixel in second.items():
        old = result.get(i, (0, 0, 0, 0))
        result[i] = tuple(a + b * value for a, b in zip(old, pixel))
    return result


def compose(inactive, active, pulse_a, pulse_b, value, fraction, bob):
    """premultiplied 보간 후 파동을 source-over; 마지막에만 straight RGBA로 복원."""
    base = _blend(inactive, active, value)
    for i, pixel in _blend(pulse_a, pulse_b, fraction).items():
        i += bob * SIZE * 4
        if 0 <= i < SIZE * SIZE * 4:
            old = base.get(i, (0, 0, 0, 0))
            base[i] = tuple(a + b * (1 - pixel[3] / 255) for a, b in zip(pixel, old))
    data = bytearray(SIZE * SIZE * 4)
    for i, (r, g, b, a) in base.items():
        if a > 0:
            data[i:i + 4] = bytes((min(255, floor(r * 255 / a + .5)),
                                   min(255, floor(g * 255 / a + .5)),
                                   min(255, floor(b * 255 / a + .5)), min(255, floor(a + .5))))
    return bytes(data)


def _load_frames(path, columns, count):
    source = pico.IMG_Load(str(path).encode('utf-8'))
    if not source:
        raise OSError(f'전하 이미지 읽기 실패: {path}: {pico.SDL_GetError()!r}')
    surface = None
    try:
        surface = pico.SDL_ConvertSurfaceFormat(source, pico.SDL_PIXELFORMAT_RGBA32, 0)
        if not surface:
            raise RuntimeError(f'전하 픽셀 변환 실패: {pico.SDL_GetError()!r}')
        s = surface.contents
        if s.w != columns * SIZE or s.h != ((count + columns - 1) // columns) * SIZE:
            raise ValueError(f'전하 시트 크기 오류: {path}')
        _sdl(pico.SDL_LockSurface(surface))
        try:
            data = string_at(s.pixels, s.pitch * s.h)
        finally:
            pico.SDL_UnlockSurface(surface)
        frames = []
        for index in range(count):
            x, y = index % columns * SIZE, index // columns * SIZE
            frames.append(b''.join(data[(y + row) * s.pitch + x * 4:
                                        (y + row) * s.pitch + (x + SIZE) * 4] for row in range(SIZE)))
        return frames
    finally:
        if surface:
            pico.SDL_FreeSurface(surface)
        pico.SDL_FreeSurface(source)


class ChargeArt:
    def __init__(self):
        self.frames = {name: _load_frames(ASSETS / f'{name}.png', columns, count)
                       for name, columns, count in (('inactive', 9, 72), ('active', 9, 72), ('pulse', 4, 10))}
        self.pixels = {name: [_pixels(frame) for frame in frames] for name, frames in self.frames.items()}

    def frame(self, elapsed, value):
        index = floor(elapsed * 24) % 72
        if value in (0, 1):
            return self.frames['active' if value else 'inactive'][index]
        phase = value * 9
        lower = floor(phase)
        bob = floor(sin(elapsed / 3 * 2 * pi) * 1.2 + .5)
        return compose(self.pixels['inactive'][index], self.pixels['active'][index],
                       self.pixels['pulse'][lower], self.pixels['pulse'][min(9, lower + 1)],
                       value, phase - lower, bob)


class Charge(GameObject):
    def __init__(self, art, position):
        super().__init__()
        self.art, self.position = art, tuple(position)
        self.elapsed = self.value = self.velocity = 0.0
        self.texture = None
        self.active = False
        self._frame_key = None

    def on_spawn(self):
        self.texture = pico.SDL_CreateTexture(pico.renderer, pico.SDL_PIXELFORMAT_RGBA32,
                                              pico.SDL_TEXTUREACCESS_STREAMING, SIZE, SIZE)
        if not self.texture:
            raise RuntimeError(f'전하 텍스처 생성 실패: {pico.SDL_GetError()!r}')
        _sdl(pico.SDL_SetTextureScaleMode(self.texture, pico.SDL_ScaleModeNearest))
        self.active = self.in_range(self.level.player)

    def on_destroy(self):
        texture, self.texture = self.texture, None
        if texture:
            pico.SDL_DestroyTexture(texture)

    def in_range(self, player):
        x, y = player.center
        return hypot(self.position[0] - x, self.position[1] - y) <= ACTIVATION_DISTANCE

    def update(self, dt):
        if not isfinite(dt) or dt < 0:
            raise ValueError('dt는 유한한 비음수 초여야 합니다.')
        self.active = self.in_range(self.level.player)
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
        key = (floor(self.elapsed * 24), self.value)
        if key != self._frame_key:
            data = self.art.frame(self.elapsed, self.value)
            _sdl(pico.SDL_UpdateTexture(self.texture, None, data, SIZE * 4))
            self._frame_key = key
        x, y = self.position
        draw_image(self, transform, (x - 40, y - 40, x + 40, y + 40), opacity)

    def render_items(self):
        return (RenderItem(self._draw, draw_order=-1),)
