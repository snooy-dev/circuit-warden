"""캐릭터의 스프라이트와 좌우 이동."""

import json
from pathlib import Path

import pico2d.pico2d as pico

from game_framework import GameObject, RenderItem, SpriteClip, SpriteFrame, SpritePlayer, draw_sprite


GROUND_Y = -180
SPEED = 180
DISPLAY_SCALE = 2
LEFT_KEYS = {pico.SDLK_a}
RIGHT_KEYS = {pico.SDLK_d}
MOVE_KEYS = LEFT_KEYS | RIGHT_KEYS


def _load_clip(images, animation):
    filename = animation['file']
    if Path(filename).name != filename or Path(filename).suffix.lower() != '.png':
        raise ValueError('file은 에셋 폴더의 PNG 파일명이어야 합니다.')
    width, height = animation['frameSize']
    columns, count = animation['columns'], animation['count']
    if any(type(value) is not int or value <= 0 for value in (width, height, columns, count)):
        raise ValueError('frameSize, columns, count는 양의 정수여야 합니다.')
    durations = animation['durationsMs']
    if len(durations) != count or any(type(value) not in (int, float) for value in durations):
        raise ValueError('durationsMs는 프레임마다 하나의 밀리초 값이 필요합니다.')
    if animation['loop'] is not True:
        raise ValueError('loop는 true여야 합니다.')
    x, y = animation['pivot']
    if any(type(value) not in (int, float) for value in (x, y)):
        raise ValueError('pivot은 숫자 픽셀 좌표 두 개여야 합니다.')
    pivot = (x / width, y / height)
    image = images.load(filename)
    frames = tuple(SpriteFrame(image, (i % columns * width, i // columns * height, width, height), pivot)
                   for i in range(count))
    return SpriteClip(frames, tuple(ms / 1000 for ms in durations))


def load_clips(images):
    path = images.root / 'animations.json'
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as error:
        raise ValueError(f'애니메이션 설정 읽기 실패: {path}: {error}') from error
    clips = {}
    for name in ('idle', 'run_left', 'run_right'):
        try:
            clips[name] = _load_clip(images, animations[name])
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ValueError(f'애니메이션 설정 오류: {path} ({name}): {error}') from error
    return clips


def _margins(clip):
    left = right = 0
    for frame in clip.frames:
        width = frame.rect[2] * DISPLAY_SCALE
        pivot = frame.pivot[0]
        left, right = max(left, pivot * width), max(right, (1 - pivot) * width)
    return left, right


class Character(GameObject):
    def __init__(self, clips):
        super().__init__()
        self.clips = clips
        self.player = SpritePlayer(clips['idle'])
        self.x = 0.0
        self.facing = 1
        self.pressed = set()
        self.view_bounds = None
        self._idle_margins = _margins(clips['idle'])
        margins = (*(_margins(clips[name]) for name in ('run_left', 'run_right')),
                   self._idle_margins, self._idle_margins[::-1])
        self._left_margin = max(left for left, _ in margins)
        self._right_margin = max(right for _, right in margins)

    def control(self, event):
        if event.type == pico.SDL_WINDOWEVENT and event.event in (
                pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            self.pressed.clear()
        elif event.type == pico.SDL_KEYDOWN and event.key in MOVE_KEYS:
            self.pressed.add(event.key)
        elif event.type == pico.SDL_KEYUP:
            self.pressed.discard(event.key)

    def update(self, dt):
        clip = self.clips['idle']
        if self.view_bounds is None:
            self.pressed.clear()
        else:
            left, _, right, _ = self.view_bounds
            low, high = left + self._left_margin, right - self._right_margin
            if low <= high:
                start = min(max(self.x, low), high)
                direction = bool(self.pressed & RIGHT_KEYS) - bool(self.pressed & LEFT_KEYS)
                self.x = min(max(start + direction * SPEED * dt, low), high)
                if self.x != start:
                    self.facing = direction
                    clip = self.clips['run_right' if direction > 0 else 'run_left']
            else:
                self.x = (left + right) / 2
                idle_left, idle_right = self._idle_margins
                if self.facing < 0:
                    idle_left, idle_right = idle_right, idle_left
                # 전환할 여유가 없어도 현재 idle 한 장이 들어가면 화면 안에 둔다.
                if right - left >= idle_left + idle_right:
                    self.x = min(max(self.x, left + idle_left), right - idle_right)

        if clip is self.player.clip:
            self.player.update(dt)
        else:
            self.player.play(clip)

    def _draw(self, transform, opacity):
        frame = self.player.frame
        width, height = frame.rect[2:]
        flip_x = self.player.clip is self.clips['idle'] and self.facing < 0
        draw_sprite(frame, transform, (self.x, GROUND_Y),
                    (width * DISPLAY_SCALE, height * DISPLAY_SCALE), opacity, flip_x=flip_x)

    def render_items(self):
        return (RenderItem(self._draw),)
