"""Warden의 이동·점프·대시·단발 공격과 스프라이트 상태."""

import json
from math import isfinite, sqrt
from pathlib import Path

import pico2d.pico2d as pico
from transitions import Machine

from game_framework import (Collider, CollisionResponse, GameObject, RenderItem, SpriteClip,
                            SpriteFrame, SpritePlayer, draw_sprite)
from game_framework.collision import CONTACT_EPSILON

from .effects import SpriteEffect


GROUND_Y = -180
SPEED = 180
PUSHBACK_SPEED = 440
PUSHBACK_SECONDS = .12
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
    names = ('idle', 'run_left', 'run_right', 'attack', 'air_attack') + tuple(
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
    body = Collider((-24, 0, 24, BODY_HEIGHT), 'player', blocks={'terrain'}, overlaps={'enemy'})
    colliders = (body,)
    swords = {
        -1: Collider((-ATTACK_REACH, 8, 0, 70), 'sword', overlaps={'enemy'}),
        1: Collider((0, 8, ATTACK_REACH, 70), 'sword', overlaps={'enemy'}),
    }

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
        self.teleport_guard_remaining = 0.0
        self.pushback_direction = 0
        self.pushback_remaining = 0.0
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
        self.dash_effect = None
        self.air_dash_used = False
        self._machine = Machine(
            states=('idle', 'run', 'attack', 'dash', 'jump'), initial='idle', auto_transitions=False,
            transitions=[['move', 'idle', 'run'], ['stop', 'run', 'idle'],
                         ['attack', ['idle', 'run', 'jump'], 'attack'], ['finish', 'attack', 'idle'],
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
        if self.velocity_y != 0:
            return False
        hit = self._blocking_contact((0, -1))
        return hit is not None and hit <= CONTACT_EPSILON

    @property
    def collision_position(self):
        return self.x, self.y

    @property
    def hurt_box(self):
        return self.body.bounds_at(self.collision_position)

    def _blocking_contact(self, movement):
        if self.level is not None:
            return self.level.blocking_contact(self, self.body, movement)
        # 단독 캐릭터 시뮬레이션에는 레벨의 바닥 객체가 없다.
        dy = movement[1]
        if dy < 0 and self.y + dy <= GROUND_Y + 1e-9:
            return min(1, max(0, (GROUND_Y - self.y) / dy))
        return None

    def _move_horizontal(self, destination):
        distance = destination - self.x
        hit = self._blocking_contact((distance, 0)) if distance else None
        self.x = destination if hit is None else self.x + distance * hit

    def move_enemy_push(self, destination):
        if self.view_bounds is not None:
            left, _, right, _ = self.view_bounds
            low, high = left + self._left_margin, right - self._right_margin
            if low > high:
                return
            destination = min(max(destination, low), high)
        self._move_horizontal(destination)

    def begin_enemy_push(self, direction, elapsed):
        if self.dash_effect is not None and self.state == 'dash':
            self.dash_effect.destroy()
            self.dash_effect = None
        if self.hp == 0:
            return
        if self.state == 'dash':
            self._machine.end_dash()
            self.dash_phase, self.dash_remaining = None, 0.0
            if self.jump_phase is None:
                self.player.play(self.clips['idle'])
            else:
                self._machine.jump()
                self._show_jump()
        if self.pushback_remaining == 0 or self.pushback_direction != direction:
            self.pushback_direction = direction
            self.pushback_remaining = PUSHBACK_SECONDS
            self._advance_pushback(elapsed)

    def _advance_pushback(self, dt):
        step = min(dt, self.pushback_remaining)
        if step:
            self.move_enemy_push(self.x + self.pushback_direction * PUSHBACK_SPEED * step)
            self.pushback_remaining -= step
        return step

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
        if not (left + self._left_margin <= x <= right - self._right_margin
                and GROUND_Y + BODY_HEIGHT / 2 <= y <= top - BODY_HEIGHT / 2):
            return False
        destination = x, y - BODY_HEIGHT / 2
        return self.level is None or not (self.level.collision_overlaps(
            self, self.body, destination, response=CollisionResponse.BLOCK)
            or self.level.collision_overlaps(self, self.body, destination))

    def teleport(self, position):
        if not self.can_teleport(position):
            return False
        self.active_attack = None
        self._machine.teleport()
        self.x, self.y = position[0], position[1] - BODY_HEIGHT / 2
        self.velocity_y = 0.0
        self.buffered_action, self.buffer_remaining = None, 0.0
        self.dash_phase, self.dash_remaining = None, 0.0
        self.pushback_remaining = 0.0
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
        elif event.type == pico.SDL_KEYDOWN and event.key in MOVE_KEYS | DASH_KEYS | {pico.SDLK_SPACE, pico.SDLK_j}:
            if event.key == pico.SDLK_SPACE and event.key not in self.pressed:
                self._queue_action('jump')
            if event.key == pico.SDLK_j and event.key not in self.pressed:
                self._queue_action('attack')
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
        if action == 'attack' and self.state == 'jump':
            allowed = self.jump_phase in ('rise', 'fall')
        if action == 'dash':
            allowed = (free or self.state == 'jump' and self.jump_phase in ('rise', 'fall')) and (
                self.grounded or not self.air_dash_used) and self.pushback_remaining == 0
        if action is None or not allowed or self.view_bounds is None:
            return None
        self.buffered_action = None
        return action

    def update(self, dt):
        self.invulnerability_remaining = max(0.0, self.invulnerability_remaining - dt)
        self.teleport_guard_remaining = max(0.0, self.teleport_guard_remaining - dt)
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
                self._update(dt - step, action, offset=step)
                return
            elif self.buffer_remaining <= 1e-9:
                self.buffered_action = None
        if dt > step:
            self._update(dt - step, offset=step)

    def _update(self, dt, action=None, offset=0):
        push_time = self._advance_pushback(dt)
        if action == 'dash':
            entry = 'prepare_run' if self.state == 'run' else 'prepare_idle'
            self._machine.dash()
            self.dash_effect = None
            self._play_dash_phase(entry)
            self.air_dash_used = not self.grounded
        elif action == 'jump' and self.state != 'jump':
            self._machine.jump()
            self.jump_phase, self.jump_elapsed = 'start', 0.0
        started = action == 'attack'
        if started:
            self._machine.attack()
            self.player.play(self.clips['attack' if self.grounded else 'air_attack'], restart=True)
            self.attack_id += 1
            self.attack_facing = self.facing
        attacking = self.state == 'attack'
        airborne_attack = attacking and self.jump_phase in ('rise', 'fall')
        flight_time = dt
        if airborne_attack:
            attack_y, attack_velocity = self.y, self.velocity_y
            flight_time = self._advance_vertical(dt)
        if attacking and not started:
            previous = self.player.elapsed
            self.player.update(flight_time)
            if (self.active_attack is None and previous < ATTACK_ACTIVE_END
                    and self.player.elapsed >= ATTACK_ACTIVE_START):
                start = offset + min(dt, max(0, ATTACK_ACTIVE_START - previous))
                stop = offset + ATTACK_ACTIVE_END - previous
                y = self.y
                velocity = 0
                if airborne_attack:
                    if self.grounded:
                        stop = min(stop, offset + flight_time)
                    # 활성 구간 양 끝의 높이를 잇는 속도로 검과 적의 상대 이동을 검사한다.
                    t0, t1 = start - offset, stop - offset
                    velocity = attack_velocity - .5 * GRAVITY * (t0 + t1)
                    y = attack_y + attack_velocity * t0 - .5 * GRAVITY * t0 ** 2 - velocity * start
                self.active_attack = (self.attack_id, self.swords[self.attack_facing],
                                      (self.x, y), (start, stop), velocity)
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
        elif airborne_attack:
            if self.grounded and self.state == 'attack':
                self._machine.finish()
            if self.state != 'attack':
                self._machine.jump()
                move_dt = self._update_jump(dt - flight_time)
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
                walk_time = min(move_dt, dt - push_time)
                destination = min(max(start + direction * SPEED * walk_time, low), high)
                # 공격/대시 완료 갱신에서는 같은 시간을 이동에 중복 사용하지 않는다.
                self.x = start
                if not (attacking or finished_dash):
                    self._move_horizontal(destination)
                    destination = self.x
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
                step = self._advance_vertical(remaining)
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
        remaining = dt
        while remaining > 0 and not self.grounded:
            velocity = self.velocity_y
            rising = velocity > 0
            apex = velocity / GRAVITY
            step = min(remaining, apex) if rising else remaining
            distance = velocity * step - .5 * GRAVITY * step ** 2
            hit = self._blocking_contact((0, distance))
            if hit is None:
                self.y += distance
                self.velocity_y = 0.0 if rising and step == apex else velocity - GRAVITY * step
                remaining -= step
                continue
            distance *= hit
            self.y += distance
            speed = sqrt(max(0, velocity ** 2 - 2 * GRAVITY * distance))
            # 이차식의 작은 양의 근을 유리화해 접촉 직전의 정밀도를 유지한다.
            remaining -= abs(2 * distance) / (abs(velocity) + speed) if distance else 0
            self.velocity_y = 0.0
            if not rising:
                if self.level is None:
                    self.y = float(GROUND_Y)
                self.air_dash_used = False
                break
        if self.jump_phase in ('rise', 'fall'):
            if self.grounded:
                self.jump_phase, self.jump_elapsed = 'land', 0.0
            else:
                self.jump_phase = 'rise' if self.velocity_y > 1e-9 else 'fall'
        return dt - max(0.0, remaining)

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
                    self.x = start
                    self._move_horizontal(min(max(start + self.facing * distance, low), high))
                    hit = self._blocking_contact((self.facing, 0))
                    can_continue = ((self.x < high if self.facing > 0 else self.x > low)
                                    and (hit is None or hit > CONTACT_EPSILON))
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
                    self.dash_effect = effect
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
        # 공중 공격 시트는 몸 중심, 지상·점프 시트는 발 위치를 기준으로 그린다.
        position = self.center if self.state == 'attack' and not self.grounded else (self.x, self.y)
        draw_sprite(frame, transform, position,
                    (width * DISPLAY_SCALE, height * DISPLAY_SCALE), opacity, flip_x=flip_x)

    def render_items(self):
        return (RenderItem(self._draw),)
