"""Warden의 이동·점프·대시·단발 공격과 스프라이트 상태."""

import json
from math import isfinite, sqrt
from pathlib import Path

import pico2d.pico2d as pico
from transitions import Machine

from game_framework import GameObject, RenderItem, SpriteClip, SpriteFrame, SpritePlayer, draw_sprite

from .effects import SpriteEffect


GROUND_Y = -180
SPEED = 180
DISPLAY_SCALE = 1
# idle 최대 알파 높이 × 표시 배율로 얻은 월드 키(귀 포함, 투명 여백 제외).
BODY_HEIGHT = 83 * DISPLAY_SCALE
JUMP_HEIGHT = BODY_HEIGHT * 2
JUMP_APEX_SECONDS = .4
GRAVITY = 2 * JUMP_HEIGHT / JUMP_APEX_SECONDS ** 2
JUMP_SPEED = GRAVITY * JUMP_APEX_SECONDS
TELEPORT_RISE_SECONDS = .24
DASH_DISTANCE = BODY_HEIGHT * 2
DASH_SECONDS = .2
ATTACK_ACTIVE_START = .10
ATTACK_ACTIVE_END = .20
ATTACK_REACH = 85
INPUT_BUFFER_SECONDS = .1
# 10ms 프레임 기준: 착지 6~8번의 압축 자세 → 시작 4번 자세.
LAND_CROUCH_START = .06
LAND_CROUCH_END = .09
JUMP_CROUCH_START = .04
DASH_KEYS = {pico.SDLK_LSHIFT, pico.SDLK_RSHIFT}
LEFT_KEYS = {pico.SDLK_a}
RIGHT_KEYS = {pico.SDLK_d}
MOVE_KEYS = LEFT_KEYS | RIGHT_KEYS


def _load_clip(images, animation, root=None):
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
    indices = animation.get('frameIndices', range(count))
    if len(indices) != count or any(type(i) is not int or i < 0 for i in indices):
        raise ValueError('frameIndices는 프레임마다 하나의 비음수 정수여야 합니다.')
    image = images.load(root / filename if root is not None else filename)
    frames = tuple(SpriteFrame(image, (i % columns * width, i // columns * height, width, height), pivot)
                   for i in indices)
    return SpriteClip(frames, tuple(ms / 1000 for ms in durations), loop=animation['loop'])


def load_clips(images):
    path = images.root / 'animations.json'
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as error:
        raise ValueError(f'애니메이션 설정 읽기 실패: {path}: {error}') from error
    clips = {}
    names = ('idle', 'run_left', 'run_right', 'attack', 'sword_trail') + tuple(
        f'{phase}_{direction}' for phase in (
            'prepare_idle', 'prepare_run', 'dash', 'recover_idle', 'recover_run', 'dash_fx',
            'jump_start', 'jump_rise', 'jump_fall', 'jump_land')
        for direction in ('left', 'right'))
    for name in names:
        try:
            clips[name] = _load_clip(images, animations[name])
            if clips[name].loop != (name in ('idle', 'run_left', 'run_right',
                                            'jump_fall_left', 'jump_fall_right')):
                raise ValueError('loop는 idle/Run/점프 낙하에서만 true여야 합니다.')
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
    MAX_HP = 5

    def __init__(self, clips):
        super().__init__()
        self.clips = clips
        self.player = SpritePlayer(clips['idle'])
        self.x = 0.0
        self.y = float(GROUND_Y)
        self.velocity_y = 0.0
        self.facing = 1
        self.hp = self.MAX_HP
        self.invulnerability_remaining = 0.0
        self.pressed = set()
        self.buffered_action = None
        self.buffer_remaining = 0.0
        self.attack_id = 0
        self.attack_facing = 1
        self.active_attack = None
        self.jump_phase = None
        self.jump_elapsed = 0.0
        self.dash_remaining = 0.0
        self.dash_phase = None
        self.air_dash_used = False
        self._machine = Machine(
            states=('idle', 'run', 'attack', 'dash', 'jump'), initial='idle', auto_transitions=False,
            transitions=[['move', 'idle', 'run'], ['stop', 'run', 'idle'],
                         ['attack', ['idle', 'run'], 'attack'], ['finish', 'attack', 'idle'],
                         ['dash', ['idle', 'run', 'jump'], 'dash'], ['end_dash', 'dash', 'idle'],
                         ['jump', ['idle', 'run'], 'jump'], ['end_jump', 'jump', 'idle'],
                         ['teleport', '*', 'idle']],
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

    @property
    def hurt_box(self):
        return self.x - 24, self.y, self.x + 24, self.y + BODY_HEIGHT

    def take_hit(self):
        if self.hp > 0 and self.invulnerability_remaining == 0:
            self.hp -= 1
            self.invulnerability_remaining = .75

    @property
    def center(self):
        return self.x, self.y + BODY_HEIGHT / 2

    def can_teleport(self, position):
        if self.view_bounds is None or not all(isfinite(v) for v in position):
            return False
        x, y = position
        left, _, right, top = self.view_bounds
        return (left + self._left_margin <= x <= right - self._right_margin
                and GROUND_Y + BODY_HEIGHT / 2 <= y <= top - BODY_HEIGHT / 2)

    def teleport(self, position):
        if not self.can_teleport(position):
            return False
        self.active_attack = None
        self._machine.teleport()
        self.x, self.y = position[0], position[1] - BODY_HEIGHT / 2
        self.velocity_y = 0.0
        self.buffered_action, self.buffer_remaining = None, 0.0
        self.dash_phase, self.dash_remaining = None, 0.0
        self.jump_phase, self.jump_elapsed = None, 0.0
        if self.grounded:
            self.air_dash_used = False
            self.player.play(self.clips['idle'])
        else:
            self._machine.jump()
            headroom = max(0, self.view_bounds[3] - self.y - BODY_HEIGHT)
            self.velocity_y = min(GRAVITY * TELEPORT_RISE_SECONDS, sqrt(2 * GRAVITY * headroom))
            self.jump_phase = 'rise' if self.velocity_y > 0 else 'fall'
            self._show_jump()
        return True

    def control(self, event):
        if event.type == pico.SDL_WINDOWEVENT and event.event in (
                pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            self.pressed.clear()
            self.buffered_action = None
        elif event.type == pico.SDL_KEYDOWN and event.key in MOVE_KEYS | DASH_KEYS | {pico.SDLK_SPACE}:
            if event.key == pico.SDLK_SPACE and event.key not in self.pressed:
                self._queue_action('jump')
            if event.key in DASH_KEYS and not self.pressed & DASH_KEYS:
                self._queue_action('dash')
            self.pressed.add(event.key)
        elif event.type == pico.SDL_KEYUP:
            self.pressed.discard(event.key)
        elif event.type == pico.SDL_MOUSEBUTTONDOWN and event.button == pico.SDL_BUTTON_LEFT:
            self._queue_action('attack')

    def _queue_action(self, action):
        self.buffered_action = action
        self.buffer_remaining = INPUT_BUFFER_SECONDS

    def _link_landing_jump(self):
        if (self.buffered_action == 'jump' and self.state == 'jump'
                and self.jump_phase == 'land' and self.grounded and self.view_bounds is not None
                and LAND_CROUCH_START - 1e-9 <= self.jump_elapsed < LAND_CROUCH_END - 1e-9):
            self.buffered_action = None
            self.jump_phase, self.jump_elapsed = 'start', JUMP_CROUCH_START
            return True
        return False

    def _consume_action(self):
        if self._link_landing_jump():
            return 'jump'
        action = self.buffered_action
        free = self.state in ('idle', 'run')
        allowed = free and self.grounded
        if action == 'dash':
            allowed = (free or self.state == 'jump' and self.jump_phase in ('rise', 'fall')) and (
                self.grounded or not self.air_dash_used)
        if action is None or not allowed or self.view_bounds is None:
            return None
        self.buffered_action = None
        return action

    def update(self, dt):
        self.invulnerability_remaining = max(0.0, self.invulnerability_remaining - dt)
        self.active_attack = None
        if self.view_bounds is None:
            self.buffered_action = None
        action = self._consume_action()
        # 만료 시점을 넘는 갱신도 오래된 입력을 실행하지 않도록 나눈다.
        step = min(dt, self.buffer_remaining) if self.buffered_action else dt
        self._update(step, action)
        if self.buffered_action:
            self.buffer_remaining -= step
            action = self._consume_action()
            if action is not None:
                self._update(0, action, offset=step)
                # 새 베기는 이번 Level 갱신에 포함되지 않으므로 공격도 첫 프레임을 유지한다.
                if action == 'attack':
                    return
            elif self.buffer_remaining <= 1e-9:
                self.buffered_action = None
        if dt > step:
            self._update(dt - step, offset=step)

    def _update(self, dt, action=None, offset=0):
        if action == 'dash':
            entry = 'prepare_run' if self.state == 'run' else 'prepare_idle'
            self._machine.dash()
            self._play_dash_phase(entry)
            self.air_dash_used = not self.grounded
        elif action == 'jump' and self.state != 'jump':
            self._machine.jump()
            self.jump_phase, self.jump_elapsed = 'start', 0.0
        started = action == 'attack'
        if started:
            self._machine.attack()
            self.player.play(self.clips['attack'], restart=True)
            self.attack_id += 1
            self.attack_facing = self.facing
        attacking = self.state == 'attack'
        if attacking and not started:
            previous = self.player.elapsed
            self.player.update(dt)
            if (self.active_attack is None and previous < ATTACK_ACTIVE_END
                    and self.player.elapsed >= ATTACK_ACTIVE_START):
                end = self.x + self.attack_facing * ATTACK_REACH
                box = min(self.x, end), self.y + 8, max(self.x, end), self.y + 70
                start = offset + min(dt, max(0, ATTACK_ACTIVE_START - previous))
                stop = offset + ATTACK_ACTIVE_END - previous
                self.active_attack = self.attack_id, box, (start, stop)
            if self.player.finished:
                self._machine.finish()

        finished_dash = self.state == 'dash'
        move_dt = dt
        if finished_dash:
            remaining = self._update_dash(dt)
            if self.state == 'dash':
                return
            if self.jump_phase is not None:
                self._machine.jump()
                self._update_jump(remaining)
        elif self.state == 'jump':
            move_dt = self._update_jump(dt)
        else:
            self._advance_vertical(dt)

        clip = self.clips['idle']
        if self.view_bounds is None:
            self.pressed.clear()
        else:
            left, _, right, _ = self.view_bounds
            low, high = left + self._left_margin, right - self._right_margin
            if low <= high:
                start = min(max(self.x, low), high)
                direction = bool(self.pressed & RIGHT_KEYS) - bool(self.pressed & LEFT_KEYS)
                if (self.state == 'attack' or self.jump_phase in ('start', 'land')
                        and (move_dt == 0 or finished_dash)):
                    direction = 0
                destination = min(max(start + direction * SPEED * move_dt, low), high)
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
                self.level.spawn(SpriteEffect(self.clips['sword_trail'], (self.x, GROUND_Y),
                                           self.facing, DISPLAY_SCALE))
            return
        if self.state == 'jump':
            self._show_jump()
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
            if finished_dash:
                # 복귀 마지막 자세 다음 프레임으로 이어간다. 반대 방향 전환은 첫 프레임이다.
                if self.dash_phase == 'recover_idle' and clip is self.clips['idle']:
                    self.player.update(clip.durations[0])
                elif (self.dash_phase == 'recover_run' and self.facing == self.dash_facing
                      and clip is not self.clips['idle']):
                    self.player.update(sum(clip.durations[:15]))

    def _update_jump(self, dt):
        remaining, airborne_time = dt, 0.0
        while self.state == 'jump':
            if self.jump_phase in ('start', 'land'):
                direction = 'right' if self.facing > 0 else 'left'
                duration = sum(self.clips[f'jump_{self.jump_phase}_{direction}'].durations)
                if (self.jump_phase == 'land' and self.buffered_action == 'jump'
                        and self.view_bounds is not None and self.jump_elapsed < LAND_CROUCH_START):
                    duration = LAND_CROUCH_START
                step = min(remaining, max(0, duration - self.jump_elapsed))
                self.jump_elapsed += step
                remaining = max(0.0, remaining - step)
                if duration - self.jump_elapsed > 1e-9:
                    break
                if self.jump_phase == 'land':
                    if self._link_landing_jump():
                        continue
                    self.jump_phase = None
                    self._machine.end_jump()
                    break
                self.jump_phase, self.jump_elapsed = 'rise', 0.0
                self.velocity_y = JUMP_SPEED
            else:
                if self.velocity_y > 1e-9:
                    boundary = self.velocity_y / GRAVITY
                else:
                    boundary = (self.velocity_y + sqrt(self.velocity_y ** 2 +
                                2 * GRAVITY * max(0, self.y - GROUND_Y))) / GRAVITY
                step = min(remaining, max(0.0, boundary))
                self._advance_vertical(step)
                airborne_time += step
                remaining = max(0.0, remaining - step)
            if remaining <= 1e-9:
                break
        return airborne_time

    def _show_jump(self):
        direction = 'right' if self.facing > 0 else 'left'
        clip = self.clips[f'jump_{self.jump_phase}_{direction}']
        elapsed = self.jump_elapsed
        if self.jump_phase == 'rise':
            elapsed = (JUMP_SPEED - self.velocity_y) / GRAVITY / JUMP_APEX_SECONDS * sum(clip.durations)
        elif self.jump_phase == 'fall':
            elapsed = max(0.0, -self.velocity_y / GRAVITY)
        self.player.play(clip, restart=True)
        self.player.update(elapsed)

    def _advance_vertical(self, dt):
        if not self.grounded:
            self.y += self.velocity_y * dt - .5 * GRAVITY * dt ** 2
            self.velocity_y -= GRAVITY * dt
            if self.velocity_y < 0 and self.y <= GROUND_Y + 1e-9:
                self.y, self.velocity_y = float(GROUND_Y), 0.0
                self.air_dash_used = False
                if self.jump_phase in ('rise', 'fall'):
                    self.jump_phase, self.jump_elapsed = 'land', 0.0
            elif self.jump_phase in ('rise', 'fall'):
                self.jump_phase = 'rise' if self.velocity_y > 1e-9 else 'fall'

    def _play_dash_phase(self, phase):
        self.dash_phase = phase
        self.dash_facing = self.facing
        direction = 'right' if self.facing > 0 else 'left'
        self.player.play(self.clips[f'{phase}_{direction}'], restart=True)
        self.dash_remaining = sum(self.player.clip.durations)

    def _update_dash(self, dt):
        effect = None
        remaining = dt
        while self.state == 'dash':
            step = min(remaining, self.dash_remaining)
            if self.dash_phase != 'dash':
                self._advance_vertical(step)
            can_continue = False
            if self.view_bounds is not None:
                left, _, right, _ = self.view_bounds
                low, high = left + self._left_margin, right - self._right_margin
                if low <= high:
                    start = min(max(self.x, low), high)
                    distance = DASH_DISTANCE / DASH_SECONDS * step if self.dash_phase == 'dash' else 0
                    self.x = min(max(start + self.facing * distance, low), high)
                    can_continue = self.x < high if self.facing > 0 else self.x > low
                else:
                    self.x = (left + right) / 2
            self.player.update(step)
            if effect is not None:
                effect.update(step)
            remaining = max(0.0, remaining - step)
            self.dash_remaining = max(0.0, self.dash_remaining - step)
            if self.dash_remaining > 1e-9:
                return
            if self.dash_phase.startswith('prepare_'):
                self._play_dash_phase('dash')
                if self.level is not None and can_continue:
                    direction = 'right' if self.facing > 0 else 'left'
                    # shortcut: 고정 직선 잔상, 공중 궤적/벽 추종이 필요하면 효과 제작 방식을 바꾼다.
                    effect = self.level.spawn(SpriteEffect(self.clips[f'dash_fx_{direction}'],
                                                          (self.x, self.y), 1, DISPLAY_SCALE))
            elif self.dash_phase == 'dash':
                direction = bool(self.pressed & RIGHT_KEYS) - bool(self.pressed & LEFT_KEYS)
                self._play_dash_phase('recover_run' if direction == self.facing and can_continue
                                      else 'recover_idle')
            else:
                self.dash_remaining = 0.0
                self._machine.end_dash()
                # 수평 일반 이동은 다음 갱신부터지만 중력 시간은 버리지 않는다.
                if self.jump_phase is None:
                    self._advance_vertical(remaining)
                if effect is not None:
                    effect.update(remaining)
                return remaining
            if remaining <= 1e-9:
                return

    def _draw(self, transform, opacity):
        frame = self.player.frame
        width, height = frame.rect[2:]
        flip_x = self.state not in ('run', 'dash', 'jump') and self.facing < 0
        if self.hp == 0 or (self.invulnerability_remaining > 0
                            and int(self.invulnerability_remaining / .0625) % 2 == 0):
            opacity *= .35
        draw_sprite(frame, transform, (self.x, self.y),
                    (width * DISPLAY_SCALE, height * DISPLAY_SCALE), opacity, flip_x=flip_x)

    def render_items(self):
        return (RenderItem(self._draw),)
