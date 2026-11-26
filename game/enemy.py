"""금속 먼지와 전원 구역 설비 몬스터."""

import json
from math import inf
from pathlib import Path

import pico2d.pico2d as pico

from engine.rendering.drawing import _sdl
from game_framework import Collider, GameObject, RenderItem, SpritePlayer, draw_sprite

from .character import GROUND_Y, _load_clip


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'enemies'
BODY_HEIGHT = 78
HURT_HALF_WIDTH = 42
SPAWN_X = 220.0
IDLE_SECONDS = .18
APPROACH_SPEED = 100
WINDUP_RANGE = 72
WINDUP_SECONDS = .45
CHARGE_SPEED = 350
CHARGE_SECONDS = .28
RECOVER_SECONDS = .60
HIT_REACTION_SECONDS = .18
HIT_RECOIL_SECONDS = .065
HIT_RECOIL_SPEED = 8 / HIT_RECOIL_SECONDS

NEXT_STATE = {'idle': 'approach', 'windup': 'charge', 'charge': 'recover', 'recover': 'idle'}


def load_enemy_clips(images, kind='metal_dust'):
    enemy_type = ENEMY_TYPES[kind]
    path = ASSETS / ('animations.json' if kind == 'metal_dust' else 'field-enemies.json')
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
        if kind != 'metal_dust':
            animations = animations[kind]
        clips = {name: _load_clip(images, animations[name], ASSETS)
                 for name in ('idle', 'approach', 'windup', 'charge', 'recover')}
        for name, clip in clips.items():
            if clip.loop != (name in ('idle', 'approach')):
                raise ValueError('idle/approach만 반복해야 합니다.')
        for name in ('windup', 'charge', 'recover'):
            seconds = enemy_type.TIMINGS[name]
            if abs(sum(clips[name].durations) - seconds) > 1e-9:
                raise ValueError(f'{name} 클립 시간이 전투 시간과 다릅니다.')
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'적 애니메이션 설정 오류: {path}: {error}') from error
    if enemy_type.DRAW_SCALE == 2:
        texture = clips['idle'].frames[0].image._borrow().texture
        _sdl(pico.SDL_SetTextureScaleMode(texture, pico.SDL_ScaleModeNearest))
    return clips


class Enemy(GameObject):
    MAX_HP = 3
    CHARGE_SPEED = CHARGE_SPEED
    DRAW_SCALE = 1
    TIMINGS = {'idle': IDLE_SECONDS, 'approach': 0, 'windup': WINDUP_SECONDS,
               'charge': CHARGE_SECONDS, 'recover': RECOVER_SECONDS}
    body = Collider((-HURT_HALF_WIDTH, 0, HURT_HALF_WIDTH, BODY_HEIGHT), 'enemy',
                    blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = body
    colliders = (body,)

    def __init__(self, clips, *, position=(SPAWN_X, float(GROUND_Y)), x_limits=(-inf, inf), room=None):
        super().__init__()
        self.clips = clips
        self.animation = SpritePlayer(clips['idle'])
        self.x, self.y = position
        self.x_limits = x_limits
        self.room = room
        self.facing = -1
        self.hp = self.MAX_HP
        self.hit_remaining = 0.0
        self._recoil_remaining = 0.0
        self._recoil_direction = 0
        self.state = 'idle'
        self.state_remaining = self.TIMINGS['idle']
        self.motion = []
        self._charge_id = 0
        self.last_hit_attack = 0
        self.last_contact_charge = None

    @property
    def frame(self):
        return self.animation.frame

    @property
    def hurt_box(self):
        return self.hurt_box_at(self.x)

    def hurt_box_at(self, x):
        return self.body.bounds_at((x, self.y))

    @property
    def collision_position(self):
        return self.x, self.y

    def take_hit(self, direction=0):
        if self.hp > 0:
            self.hp -= 1
            self.hit_remaining = HIT_REACTION_SECONDS
            self._recoil_remaining = HIT_RECOIL_SECONDS if direction else 0.0
            self._recoil_direction = direction
            if self.hp == 0:
                self.destroy()

    def update(self, dt):
        self.motion.clear()
        target = self.level.player
        if self.room is not None and self.level.layout.room_at(target.center) != self.room:
            return
        self.hit_remaining = max(0.0, self.hit_remaining - dt)
        self.animation.play(self.clips[self.state])
        elapsed = min(dt, self._recoil_remaining)
        if elapsed:
            self._record_motion(0.0, elapsed, self._recoil_direction * HIT_RECOIL_SPEED * elapsed, None)
            self._recoil_remaining -= elapsed
            dt -= elapsed
        while dt > 0:
            charge_id = None
            distance = 0.0
            if self.state == 'approach':
                step, distance, ready = self._approach(target, dt)
                if ready:
                    self.state, self.state_remaining = 'windup', self.TIMINGS['windup']
                    self._charge_id += 1
            else:
                step = min(dt, self.state_remaining)
                if self.state == 'charge':
                    distance = self.facing * self.CHARGE_SPEED * step
                    charge_id = self._charge_id
                self.state_remaining -= step
                if self.state_remaining == 0:
                    self.state = NEXT_STATE[self.state]
                    self.state_remaining = self.TIMINGS[self.state]
            if step > 0:
                self.animation.update(step)
                self._record_motion(elapsed, step, distance, charge_id)
            self.animation.play(self.clips[self.state])
            elapsed += step
            dt -= step

    def _approach(self, target, dt):
        gap = target.x - self.x
        if self.room is not None and (abs(gap) > 280 or abs(target.y - self.y) > 90):
            return self._wait_for_target(dt)
        if gap:
            self.facing = 1 if gap > 0 else -1
        time_to_windup = max(0.0, (abs(gap) - WINDUP_RANGE) / APPROACH_SPEED)
        step = min(dt, time_to_windup)
        return step, self.facing * APPROACH_SPEED * step, step == time_to_windup

    def _wait_for_target(self, dt):
        self.state, self.state_remaining = 'idle', self.TIMINGS['idle']
        self.animation.play(self.clips['idle'])
        return dt, 0.0, False

    def horizontal_distance(self, distance):
        left, right = self.x_limits
        distance = min(right, max(left, self.x + distance)) - self.x
        contact = self.level.blocking_contact(self, self.body, (distance, 0)) if distance else None
        return distance if contact is None else distance * contact

    def _record_motion(self, elapsed, step, distance, charge_id):
        moved = self.horizontal_distance(distance) if distance else 0.0
        fraction = min(1, max(0, moved / distance)) if distance else 1
        end = elapsed + step
        travel_end = elapsed + step * fraction
        if travel_end > elapsed:
            self.motion.append(((elapsed, travel_end), self.collision_position, (moved, 0), charge_id))
        self.x += moved
        if travel_end < end:
            self.motion.append(((travel_end, end), self.collision_position, (0, 0), charge_id))

    def _draw(self, transform, opacity):
        if 0 < self.hit_remaining < HIT_REACTION_SECONDS and int(self.hit_remaining / .045) % 2 == 0:
            opacity *= .3
        width, height = self.frame.rect[2:]
        draw_sprite(self.frame, transform, (self.x, self.y),
                    (width * self.DRAW_SCALE, height * self.DRAW_SCALE), opacity, flip_x=self.facing < 0)

    def render_items(self):
        return (RenderItem(self._draw),)


class CoolingFan(Enemy):
    MAX_HP = 2
    DRAW_SCALE = 2
    TIMINGS = Enemy.TIMINGS | {'windup': .48, 'charge': .46, 'recover': .64}
    body = Collider((-26, 0, 26, 38), 'enemy', blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = body
    colliders = (body,)

    def _approach(self, target, dt):
        if abs(target.x - self.x) > 200 or abs(target.center[1] - (self.y + 19)) > 110:
            return self._wait_for_target(dt)
        self.facing = -self.facing
        return 0.0, 0.0, True


class LeakingCapacitor(Enemy):
    MAX_HP = 2
    CHARGE_SPEED = 0
    DRAW_SCALE = 2
    TIMINGS = Enemy.TIMINGS | {'windup': .66, 'charge': .16, 'recover': .85}
    body = Collider((-24, 0, 24, 66), 'enemy', blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = Collider((-88, 0, 88, 52), 'enemy-pulse')
    colliders = (body,)

    def _approach(self, target, dt):
        if abs(target.x - self.x) > 142 or abs(target.y - self.y) > 70:
            return self._wait_for_target(dt)
        return 0.0, 0.0, True


ENEMY_TYPES = {'metal_dust': Enemy, 'cooling_fan': CoolingFan, 'leaking_capacitor': LeakingCapacitor}
