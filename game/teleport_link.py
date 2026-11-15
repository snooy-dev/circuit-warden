"""승인 v4 전류 효과. Pixelfx 및 Sprite Fusion 고지는 licenses/pixelfx-LICENSE.txt 참조."""

from itertools import accumulate
from math import atan2, ceil, cos, exp, floor, hypot, isfinite, log2, sin, sqrt, tau

import pico2d.pico2d as pico

from game_framework import GameObject, RenderItem, draw_image


DURATION = 0.1
FPS = 30
_FRAME_COUNT = 12
# 승인 시트의 30Hz 누적 시각을 보존해 0.2초 경계의 샘플까지 맞춘다.
_SAMPLE_TIMES = (0.0, *accumulate((1 / FPS,) * (_FRAME_COUNT - 1)))
_PALETTE = (0x081C45, 0x123675, 0x1851AD, 0x2475DF, 0x4599FF, 0x80BCFF, 0xC2DEFF, 0xF4F8FF)
_MASK = 0xFFFFFFFF
_MARGIN = 64


class _Rng:
    """Pixelfx의 32비트 해시 및 mulberry32."""

    def __init__(self, *keys):
        hashed = 0x9E3779B9
        for key in keys:
            hashed = ((hashed ^ (key & _MASK)) * 0x85EBCA6B) & _MASK
            hashed ^= hashed >> 13
            hashed = (hashed * 0xC2B2AE35) & _MASK
            hashed ^= hashed >> 16
        self.state = hashed or 1

    def next(self):
        self.state = (self.state + 0x6D2B79F5) & _MASK
        value = self.state
        value = ((value ^ (value >> 15)) * (value | 1)) & _MASK
        value ^= (value + (value ^ (value >> 7)) * (value | 61)) & _MASK
        return (value ^ (value >> 14)) / 4294967296

    def between(self, low, high):
        return low + (high - low) * self.next()

    def index(self, low, high):
        return floor(self.between(low, high + 1))

    def sign(self):
        return -1 if self.next() < 0.5 else 1


def _bolt(rng, start, end, jag, depth):
    points = [start, end]
    for _ in range(depth):
        displaced = [start]
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            dx, dy = bx - ax, by - ay
            length = hypot(dx, dy)
            offset = (rng.next() * 2 - 1) * jag * length
            displaced.append(((ax + bx) / 2 - dy / (length or 1) * offset,
                              (ay + by) / 2 + dx / (length or 1) * offset))
            displaced.append((bx, by))
        points = displaced
    return points


def _path(dx, dy, seed, phase, length):
    rng = _Rng(seed, phase, 31)
    count = max(2, ceil(length / 32))
    amplitude = min(8, length * 0.1)
    anchors = [(0, 0)]
    for i in range(1, count):
        u = (i + rng.between(-0.22, 0.22)) / count
        offset = rng.between(-amplitude, amplitude)
        anchors.append((dx * u - dy / length * offset, dy * u + dx / length * offset))
    anchors.append((dx, dy))
    points = [anchors[0]]
    for a, b in zip(anchors, anchors[1:]):
        depth = max(1, ceil(log2(hypot(b[0] - a[0], b[1] - a[1]) / 3)))
        points.extend(_bolt(rng, a, b, 0.2, depth)[1:])
    return points


def _raster_bounds(dx, dy):
    margin = _MARGIN
    return (floor(min(0, dx)) - margin, floor(min(0, dy)) - margin,
            ceil(max(0, dx)) + margin, ceil(max(0, dy)) + margin)


class _Raster:
    def __init__(self, dx, dy):
        self.left, self.top, self.right, self.bottom = _raster_bounds(dx, dy)
        self.stride = self.right - self.left
        self.pixel_origin = self.top * self.stride + self.left
        self.core = {}
        self.light = {}

    def line(self, start, end, color):
        x, y = map(floor, start)
        ex, ey = map(floor, end)
        dx, dy = abs(ex - x), -abs(ey - y)
        sx, sy = (1 if x < ex else -1), (1 if y < ey else -1)
        error = dx + dy
        while True:
            if self.left <= x < self.right and self.top <= y < self.bottom:
                self.core[y * self.stride + x - self.pixel_origin] = color
            if x == ex and y == ey:
                return
            twice = 2 * error
            if twice >= dy:
                error += dy
                x += sx
            if twice <= dx:
                error += dx
                y += sy

    def glow(self, start, end, radius, color, strength):
        if strength <= 0.004:
            return
        ax, ay = start
        bx, by = end
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        inv_length = 1 / sqrt(length_sq) if length_sq else 0
        red, green, blue = color >> 16, (color >> 8) & 255, color & 255
        radius_sq = radius * radius
        light = self.light
        first_x = max(self.left, ceil(min(ax, bx) - radius - 0.5))
        last_x = min(self.right, floor(max(ax, bx) + radius - 0.5) + 1)
        # 같은 열의 내적·외적 항과 끝점 거리 항은 행마다 재사용한다.
        columns = []
        for x in range(first_x, last_x):
            px, qx = x + 0.5 - ax, x + 0.5 - bx
            columns.append((x, px * dx, px * dy, px * px, qx * qx))
        first_y = max(self.top, ceil(min(ay, by) - radius - 0.5))
        last_y = min(self.bottom, floor(max(ay, by) + radius - 0.5) + 1)
        for y in range(first_y, last_y):
            py = y + 0.5 - ay
            qy = y + 0.5 - by
            py_sq, qy_sq = py * py, qy * qy
            y_projection = py * dy
            y_cross = py * dx
            row = y * self.stride - self.pixel_origin
            for x, x_projection, x_cross, px_sq, qx_sq in columns:
                projection = x_projection + y_projection
                if 0 < projection < length_sq:
                    distance = abs(x_cross - y_cross) * inv_length
                    if distance >= radius:
                        continue
                else:
                    distance_sq = px_sq + py_sq if projection <= 0 else qx_sq + qy_sq
                    if distance_sq >= radius_sq:
                        continue
                    distance = sqrt(distance_sq)
                falloff = 1 - distance / radius
                amount = falloff * falloff * strength
                if amount <= 0.004:
                    continue
                key = row + x
                r, g, b = light.get(key, (0, 0, 0))
                r, g, b = int(r + red * amount), int(g + green * amount), int(b + blue * amount)
                light[key] = (255 if r > 255 else r, 255 if g > 255 else g, 255 if b > 255 else b)

    def sparkle(self, point, arm, strength):
        count = floor(arm + 0.5)
        if count < 1:
            return
        x, y = map(floor, point)
        for d in range(1, count + 1):
            color = _PALETTE[4 if d > count * 0.6 else 7]
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                self.core[(y + dy) * self.stride + x + dx - self.pixel_origin] = color
        if count >= 3:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                self.core[(y + dy) * self.stride + x + dx - self.pixel_origin] = _PALETTE[7]
        self.core[y * self.stride + x - self.pixel_origin] = 0xFFFFFF
        self.glow(point, point, 4 + count * 2, _PALETTE[7], strength)

    def rgba(self):
        pixels = bytearray(self.stride * (self.bottom - self.top) * 4)
        for key, (r, g, b) in self.light.items():
            index = key * 4
            if key in self.core:
                continue
            alpha = max(r, g, b)
            if alpha:
                scale = alpha / 255
                pixels[index] = round(r / scale)
                pixels[index + 1] = round(g / scale)
                pixels[index + 2] = round(b / scale)
                pixels[index + 3] = alpha
        for key, color in self.core.items():
            index = key * 4
            r, g, b = self.light.get(key, (0, 0, 0))
            pixels[index] = min(255, (color >> 16) + r)
            pixels[index + 1] = min(255, ((color >> 8) & 255) + g)
            pixels[index + 2] = min(255, (color & 255) + b)
            pixels[index + 3] = 255
        return bytes(pixels)


def _channels(dx, dy, seed, phase, points, length):
    rng = _Rng(seed, phase, 75)
    yield points, 1, False
    for j in range(max(1, floor(length / 32))):
        i = rng.index(2, len(points) - 3)
        x, y = points[i]
        angle = atan2(dy, dx) + rng.sign() * rng.between(0.65, 1.65)
        branch_length = min(length * 0.2, rng.between(8, 15))
        end = (x + cos(angle) * branch_length, y + sin(angle) * branch_length)
        branch = _bolt(rng, (x, y), end, 0.35, 3)
        yield branch, 0.8, True
        bx, by = branch[4]
        turn = angle + rng.sign() * 0.8
        fork_end = (bx + cos(turn) * branch_length * 0.45, by + sin(turn) * branch_length * 0.45)
        yield _bolt(rng, (bx, by), fork_end, 0.35, 2), 0.45, True
        if j % 2 == 0:
            end = points[min(len(points) - 1, i + 15)]
            yield branch[:5] + _bolt(rng, (bx, by), end, 0.15, 3)[1:], 0.35, False


def _paint(raster, dx, dy, seed, frame):
    length = hypot(dx, dy)
    if length < 1 or not 0 <= frame < _FRAME_COUNT:
        return
    t = _SAMPLE_TIMES[frame]
    phase = (0, 1, 1, 2, 2, 3)[frame] if frame < 6 else 3
    points = _path(dx, dy, seed, phase, length)
    tail = max(0, 1 - (t - 0.2) / 0.2)
    power = (1, 0.65, 0.9, 0.48, 1, 0.62)[frame] if frame < 6 else tail * 0.65
    for channel, (path, weight, taper) in enumerate(_channels(dx, dy, seed, phase, points, length)):
        for i, (a, b) in enumerate(zip(path, path[1:]), start=1):
            if t >= 0.2 and _Rng(seed, channel, i // 3).next() > tail * 0.8:
                continue
            hot = power * weight * (1 - i / len(path) * 0.7 if taper else 1)
            raster.glow(a, b, 4 if weight == 1 else 3, _PALETTE[4], hot * 0.6)
            color = 7 if hot > 0.6 else 5 if hot > 0.3 else 3 if hot > 0.12 else 1
            raster.line(a, b, _PALETTE[color])

    debris = _path(dx, dy, seed, 2, length)
    rng = _Rng(seed, 88)
    for _ in range(max(5, ceil(length / 12))):
        ox, oy = debris[rng.index(0, len(debris) - 1)]
        angle = rng.between(0, tau)
        birth, lifetime = rng.between(0.035, 0.14), rng.between(0.1, 0.23)
        age, speed = t - birth, rng.between(25, 65)
        if not 0 <= age <= lifetime:
            continue
        k = 1 - age / lifetime
        distance = speed * (1 - exp(-age * 5)) / 5
        ca, sa = cos(angle), sin(angle)
        x, y = ox + ca * distance, oy + sa * distance
        tip = (x - ca * (1 + 3 * k), y - sa * (1 + 3 * k))
        raster.line((x, y), tip, _PALETTE[6 if k > 0.6 else 4 if k > 0.3 else 2])
        raster.glow((x, y), (x, y), 3, _PALETTE[4], 0.5 * k)

    flash = max(0, 1 - t / 0.17) * power
    if flash:
        for point in ((0, 0), (dx, dy)):
            raster.glow(point, point, 9, _PALETTE[4], flash * 0.7)
            raster.sparkle(point, 3 * flash, flash)


def render_link_frame(dx, dy, seed, frame):
    """Y-down 래스터 좌표의 끝점 차이에 대해 30fps RGBA 샘플을 만든다."""
    raster = _Raster(dx, dy)
    _paint(raster, dx, dy, seed, frame)
    return raster.rgba()


class TeleportLink(GameObject):
    def __init__(self, start, end, seed=7):
        super().__init__()
        self._start, self._end = tuple(start), tuple(end)
        sx, sy = self._start
        ex, ey = self._end
        self._dx, self._dy = ex - sx, sy - ey
        if not all(map(isfinite, (sx, sy, ex, ey, self._dx, self._dy))):
            raise ValueError('전류 끝점 좌표는 유한해야 합니다.')
        left, top, right, bottom = _raster_bounds(self._dx, self._dy)
        self.w, self.h = right - left, bottom - top
        self._bounds = (sx + left, sy - bottom, sx + right, sy - top)
        self._seed = seed
        self._elapsed = 0.0
        self._fresh = True
        self._uploaded_frame = None
        self.texture = None

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def on_spawn(self):
        self.texture = pico.SDL_CreateTexture(pico.renderer, pico.SDL_PIXELFORMAT_RGBA32,
                                              pico.SDL_TEXTUREACCESS_STREAMING, self.w, self.h)
        if not self.texture:
            raise RuntimeError(f'전류 텍스처 생성 실패 {pico.SDL_GetError()!r}')
        if pico.SDL_SetTextureScaleMode(self.texture, pico.SDL_ScaleModeNearest) < 0:
            raise RuntimeError(f'전류 텍스처 필터 설정 실패 {pico.SDL_GetError()!r}')

    def on_destroy(self):
        texture, self.texture = self.texture, None
        if texture:
            pico.SDL_DestroyTexture(texture)

    def update(self, dt):
        # 입력 단계에서 생성됐으므로 첫 dt는 생성 이전 프레임의 시간이다.
        if self._fresh:
            self._fresh = False
            return
        self._elapsed += dt
        if self._elapsed + 1e-12 >= DURATION:
            self.destroy()

    def _draw(self, transform, opacity):
        # shortcut: 동시 전류의 CPU 비용이 누적됨, 전투 규모가 커지면 네이티브 래스터로 전환한다.
        self._fresh = False
        frame = min(_FRAME_COUNT - 1, floor(self._elapsed / DURATION * _FRAME_COUNT + 1e-6))
        if frame != self._uploaded_frame:
            pixels = render_link_frame(self._dx, self._dy, self._seed, frame)
            if pico.SDL_UpdateTexture(self.texture, None, pixels, self.w * 4) < 0:
                raise RuntimeError(f'전류 텍스처 업데이트 실패 {pico.SDL_GetError()!r}')
            self._uploaded_frame = frame
        draw_image(self, transform, self._bounds, opacity)

    def render_items(self):
        return (RenderItem(self._draw, draw_order=-1, bounds=self._bounds),)
