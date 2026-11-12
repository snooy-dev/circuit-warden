"""Warden의 이동·점프·대시·단발 공격과 스프라이트 상태."""

import json
from pathlib import Path

import pico2d.pico2d as pico
from transitions import Machine

from game_framework import GameObject, RenderItem, SpriteClip, SpriteFrame, SpritePlayer, draw_sprite

from .effects import SwordTrail


GROUND_Y = -180
SPEED = 180
DISPLAY_SCALE = 1
# idle 최대 알파 높이 × 표시 배율로 얻은 월드 키(귀 포함, 투명 여백 제외).
BODY_HEIGHT = 83 * DISPLAY_SCALE
JUMP_HEIGHT = BODY_HEIGHT * 2
JUMP_APEX_SECONDS = .4
GRAVITY = 2 * JUMP_HEIGHT / JUMP_APEX_SECONDS ** 2
JUMP_SPEED = GRAVITY * JUMP_APEX_SECONDS
DASH_DISTANCE = BODY_HEIGHT * 2
DASH_SECONDS = .2
DASH_KEYS = {pico.SDLK_LSHIFT, pico.SDLK_RSHIFT}
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
    if type(animation['loop']) is not bool:
        raise ValueError('loop는 bool이어야 합니다.')
    x, y = animation['pivot']
    if any(type(value) not in (int, float) for value in (x, y)):
        raise ValueError('pivot은 숫자 픽셀 좌표 두 개여야 합니다.')
    pivot = (x / width, y / height)
    image = images.load(filename)
    frames = tuple(SpriteFrame(image, (i % columns * width, i // columns * height, width, height), pivot)
                   for i in range(count))
    return SpriteClip(frames, tuple(ms / 1000 for ms in durations), loop=animation['loop'])


def load_clips(images):
    path = images.root / 'animations.json'
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as error:
        raise ValueError(f'애니메이션 설정 읽기 실패: {path}: {error}') from error
    clips = {}
    for name in ('idle', 'run_left', 'run_right', 'attack', 'sword_trail'):
        try:
            clips[name] = _load_clip(images, animations[name])
            if clips[name].loop != (name in ('idle', 'run_left', 'run_right')):
                raise ValueError('loop는 idle/Run에서 true, attack/sword_trail에서 false여야 합니다.')
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
        self.y = float(GROUND_Y)
        self.velocity_y = 0.0
        self.facing = 1
        self.pressed = set()
        self.attack_requested = False
        self.jump_requested = False
        self.dash_requested = False
        self.dash_remaining = 0.0
        self.air_dash_used = False
        self._machine = Machine(
            states=('idle', 'run', 'attack', 'dash'), initial='idle', auto_transitions=False,
            transitions=[['move', 'idle', 'run'], ['stop', 'run', 'idle'],
                         ['attack', ['idle', 'run'], 'attack'], ['finish', 'attack', 'idle'],
                         ['dash', ['idle', 'run'], 'dash'], ['end_dash', 'dash', 'idle']],
        )
        self.view_bounds = None
        self._idle_margins = _margins(clips['idle'])
        # shortcut: 공격 끝부분은 화면에서 잘릴 수 있음, 검 전체 보존이 필요하면 경계 정책을 바꾼다.
        margins = (*(_margins(clips[name]) for name in ('run_left', 'run_right')),
                   self._idle_margins, self._idle_margins[::-1])
        self._left_margin = max(left for left, _ in margins)
        self._right_margin = max(right for _, right in margins)

    @property
    def state(self):
        return self._machine.state

    @property
    def grounded(self):
        return self.y == GROUND_Y and self.velocity_y == 0

    def control(self, event):
        if event.type == pico.SDL_WINDOWEVENT and event.event in (
                pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            self.pressed.clear()
            self.attack_requested = False
            self.jump_requested = False
            self.dash_requested = False
        elif event.type == pico.SDL_KEYDOWN and event.key in MOVE_KEYS | DASH_KEYS | {pico.SDLK_SPACE}:
            if (event.key == pico.SDLK_SPACE and event.key not in self.pressed
                    and self.grounded and self.state not in ('attack', 'dash')):
                self.jump_requested = True
            if (event.key in DASH_KEYS and not self.pressed & DASH_KEYS
                    and self.state in ('idle', 'run')
                    and (self.grounded or not self.air_dash_used)):
                self.dash_requested = True
            self.pressed.add(event.key)
        elif event.type == pico.SDL_KEYUP:
            self.pressed.discard(event.key)
        elif (event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_LEFT
              and self.state not in ('attack', 'dash') and self.grounded):
            self.attack_requested = True

    def update(self, dt):
        if (self.dash_requested and self.state in ('idle', 'run')
                and (self.grounded or not self.air_dash_used) and self.view_bounds is not None):
            self._machine.dash()
            self.dash_remaining = DASH_SECONDS
            self.air_dash_used = not self.grounded
            self.player.play(self.clips['run_right' if self.facing > 0 else 'run_left'])
        self.dash_requested = False
        if (self.jump_requested and self.grounded and self.state not in ('attack', 'dash')
                and self.view_bounds is not None):
            self.velocity_y = JUMP_SPEED
        self.jump_requested = False
        started = (self.attack_requested and self.grounded and self.state != 'dash'
                   and self.view_bounds is not None)
        self.attack_requested = False
        if started:
            self._machine.attack()
            self.player.play(self.clips['attack'], restart=True)
        attacking = self.state == 'attack'
        if attacking and not started:
            self.player.update(dt)
            if self.player.finished:
                self._machine.finish()

        if not self.grounded:
            self.y += self.velocity_y * dt - .5 * GRAVITY * dt ** 2
            self.velocity_y -= GRAVITY * dt
            # 시간 분할의 반올림 오차로 착지가 한 프레임 늦어지지 않게 한다.
            if self.velocity_y < 0 and self.y <= GROUND_Y + 1e-9:
                self.y, self.velocity_y = float(GROUND_Y), 0.0
                self.air_dash_used = False

        finished_dash = False
        if self.state == 'dash':
            step = min(dt, self.dash_remaining)
            if self.view_bounds is not None:
                left, _, right, _ = self.view_bounds
                low, high = left + self._left_margin, right - self._right_margin
                if low <= high:
                    start = min(max(self.x, low), high)
                    self.x = min(max(start + self.facing * DASH_DISTANCE / DASH_SECONDS * step,
                                     low), high)
                else:
                    self.x = (left + right) / 2
            self.player.update(step)
            self.dash_remaining = max(0.0, self.dash_remaining - step)
            if self.dash_remaining <= 1e-9:
                self.dash_remaining = 0.0
                self._machine.end_dash()
                finished_dash = True
            else:
                return

        clip = self.clips['idle']
        if self.view_bounds is None:
            self.pressed.clear()
        else:
            left, _, right, _ = self.view_bounds
            low, high = left + self._left_margin, right - self._right_margin
            if low <= high:
                start = min(max(self.x, low), high)
                direction = bool(self.pressed & RIGHT_KEYS) - bool(self.pressed & LEFT_KEYS)
                if self.state == 'attack':
                    direction = 0
                destination = min(max(start + direction * SPEED * dt, low), high)
                # 공격/대시 완료 갱신에서는 같은 시간을 이동에 중복 사용하지 않는다.
                self.x = start if attacking or finished_dash else destination
                if destination != start:
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

        if self.state == 'attack':
            if started and self.level is not None:
                self.level.spawn(SwordTrail(self.clips['sword_trail'], (self.x, GROUND_Y),
                                           self.facing, DISPLAY_SCALE))
            return
        if clip is self.clips['idle']:
            if self.state == 'run':
                self._machine.stop()
        elif self.state == 'idle':
            self._machine.move()

        if clip is self.player.clip:
            if not finished_dash:
                self.player.update(dt)
        else:
            self.player.play(clip)

    def _draw(self, transform, opacity):
        frame = self.player.frame
        width, height = frame.rect[2:]
        flip_x = self.state not in ('run', 'dash') and self.facing < 0
        draw_sprite(frame, transform, (self.x, self.y),
                    (width * DISPLAY_SCALE, height * DISPLAY_SCALE), opacity, flip_x=flip_x)

    def render_items(self):
        return (RenderItem(self._draw),)
