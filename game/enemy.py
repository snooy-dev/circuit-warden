"""금속 먼지와 전원 구역 설비 몬스터."""

import json
from math import inf
from pathlib import Path

import pico2d.pico2d as pico

from engine.rendering.drawing import _sdl
from game_framework import Collider, GameObject, RenderItem, SpritePlayer, draw_rect, draw_sprite

from .character import GROUND_Y, _load_clip


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'enemies'
BODY_HEIGHT = 78
HURT_HALF_WIDTH = 42
SPAWN_X = 220.0
IDLE_SECONDS = .18
APPROACH_SPEED = 100
RETURN_SPEED = 65
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
                 for name in enemy_type.CLIP_NAMES}
        for name, clip in clips.items():
            if clip.loop != (name in enemy_type.LOOP_CLIPS):
                raise ValueError(f'{name}의 반복 설정이 전투 상태와 다릅니다.')
            if not clip.loop and abs(sum(clip.durations) - enemy_type.TIMINGS[name]) > 1e-9:
                raise ValueError(f'{name} 클립 시간이 전투 시간과 다릅니다.')
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'적 애니메이션 설정 오류: {path}: {error}') from error
    if enemy_type.DRAW_SCALE == 2:
        for image in {clip.frames[0].image for clip in clips.values()}:
            _sdl(pico.SDL_SetTextureScaleMode(image._borrow().texture, pico.SDL_ScaleModeNearest))
    return clips


class Enemy(GameObject):
    MAX_HP = 3
    CHARGE_SPEED = CHARGE_SPEED
    HITS_WHILE_BLOCKED = True
    DRAW_SCALE = 1
    TIMINGS = {'idle': IDLE_SECONDS, 'approach': 0, 'windup': WINDUP_SECONDS,
               'charge': CHARGE_SECONDS, 'recover': RECOVER_SECONDS}
    CLIP_NAMES = tuple(TIMINGS)
    LOOP_CLIPS = ('idle', 'approach')
    body = Collider((-HURT_HALF_WIDTH, 0, HURT_HALF_WIDTH, BODY_HEIGHT), 'enemy',
                    blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = body
    colliders = (body,)
    extra_attacks = ()

    def __init__(self, clips, *, position=(SPAWN_X, float(GROUND_Y)), x_limits=(-inf, inf), room=None):
        super().__init__()
        self.clips = clips
        self.animation = SpritePlayer(clips['idle'])
        self.x, self.y = position
        self.home_x = self.x
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
            if self.state in ('windup', 'charge'):
                self._wait_for_target(0)
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
            home_gap = self.home_x - self.x
            if abs(home_gap) <= 1e-7:
                return self._wait_for_target(dt)
            self.facing = 1 if home_gap > 0 else -1
            step = min(dt, abs(home_gap) / RETURN_SPEED)
            return step, self.facing * RETURN_SPEED * step, False
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
            stationary_hit = charge_id if self.HITS_WHILE_BLOCKED else None
            self.motion.append(((travel_end, end), self.collision_position, (0, 0), stationary_hit))

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
    HITS_WHILE_BLOCKED = False
    TIMINGS = Enemy.TIMINGS | {'windup': .48, 'charge': .46, 'recover': .64}
    body = Collider((-26, 0, 26, 38), 'enemy', blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = body
    colliders = (body,)

    def _approach(self, target, dt):
        if abs(target.x - self.x) > 200 or abs(target.center[1] - (self.y + 19)) > 110:
            return self._wait_for_target(dt)
        reach = CHARGE_SPEED * self.TIMINGS['charge']
        left, right = self.horizontal_distance(-reach), self.horizontal_distance(reach)
        distance = right if target.x >= self.x else left
        if abs(distance) < self.body.bounds[2] - self.body.bounds[0]:
            distance = max((left, right), key=abs)
        if not distance:
            return self._wait_for_target(dt)
        self.facing = 1 if distance > 0 else -1
        self.CHARGE_SPEED = abs(distance) / self.TIMINGS['charge']
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


class PowerAssembly(Enemy):
    MAX_HP = 8
    DRAW_SCALE = 2
    CHARGE_SPEED = 0
    TIMINGS = {'idle': .36, 'lash_windup': .58, 'lash': .18, 'shot_windup': .72, 'shot': 1.12,
               'jump_windup': .64, 'leap': .70, 'slam': .20, 'recover': .96}
    CLIP_NAMES = (*TIMINGS, 'bolt')
    LOOP_CLIPS = ('idle', 'bolt')
    NEXT = {'lash_windup': 'lash', 'shot_windup': 'shot', 'jump_windup': 'leap', 'leap': 'slam',
            'lash': 'recover', 'shot': 'recover', 'slam': 'recover', 'recover': 'idle'}
    body = Collider((-64, 0, 64, 136), 'enemy', blocks={'terrain'}, overlaps={'player', 'sword'})
    attack_body = body
    colliders = (body,)
    lash_boxes = {-1: Collider((-164, 6, -36, 96), 'boss-lash'),
                  1: Collider((36, 6, 164, 96), 'boss-lash')}
    slam_box = Collider((-146, 0, 146, 54), 'boss-slam')
    bolt_box = Collider((-12, -10, 12, 10), 'boss-bolt')

    def __init__(self, clips, *, position, x_limits, room):
        super().__init__(clips, position=position, x_limits=x_limits, room=room)
        self.floor = self.y
        self.extra_attacks = []
        self.landing = self.leap_start = self.x
        self.bolt = None
        self.bolt_animation = SpritePlayer(clips['bolt'])

    def take_hit(self, direction=0):
        super().take_hit()

    def update(self, dt):
        self.motion.clear()
        self.extra_attacks.clear()
        target = self.level.player
        if self.level.layout.room_at(target.center) != self.room:
            if self.state != 'idle':
                self.y = self.floor
                self.bolt = None
                self._set_state('idle')
            return
        self.hit_remaining = max(0.0, self.hit_remaining - dt)
        elapsed = 0.0
        while elapsed + 1e-9 < dt:
            step = min(dt - elapsed, self.state_remaining)
            if self.state == 'leap':
                step = min(step, 1 / 60)
            self._advance(elapsed, step)
            elapsed += step
            self.state_remaining -= step
            if self.state_remaining > 1e-9:
                continue
            if self.state == 'idle':
                gap = target.x - self.x
                if abs(gap) <= 540:
                    self._choose_attack(target, gap)
                else:
                    self.state_remaining = self.TIMINGS['idle']
            else:
                self._set_state(self.NEXT[self.state])

    def _set_state(self, state):
        self.state = state
        self.state_remaining = self.TIMINGS[state]
        self.animation.play(self.clips[state], restart=True)
        if state == 'shot':
            self.bolt = self.x + 70 * self.facing, self.y + 44
            self.bolt_animation.play(self.clips['bolt'], restart=True)
        elif state == 'recover':
            self.bolt = None

    def _choose_attack(self, target, gap):
        if gap:
            self.facing = 1 if gap > 0 else -1
        self._charge_id += 1
        if self._charge_id % 3 == 0:
            self.leap_start = self.x
            left, right = self.x_limits
            self.landing = min(right, max(left, target.x + self.facing * 40))
            self._set_state('jump_windup')
        else:
            self._set_state('lash_windup' if abs(gap) <= 170 else 'shot_windup')

    def _advance(self, elapsed, step):
        times = elapsed, elapsed + step
        x, y = self.collision_position
        if self.state == 'leap':
            phase = 1 - max(0, self.state_remaining - step) / self.TIMINGS['leap']
            self.x = self.leap_start + phase * (self.landing - self.leap_start)
            self.y = self.floor + 760 * phase * (1 - phase)
        delta = self.x - x, self.y - y
        self.motion.append((times, (x, y), delta, None))
        self.animation.update(step)
        if self.state == 'lash':
            self.extra_attacks.append((self.lash_boxes[self.facing], (times, (x, y), delta, self._charge_id)))
        elif self.state == 'slam':
            self.extra_attacks.append((self.slam_box, (times, (x, y), delta, self._charge_id)))
        elif self.bolt is not None:
            self._advance_bolt(elapsed, step)

    def _advance_bolt(self, elapsed, step):
        x, y = self.bolt
        layout = self.level.layout
        left = layout.rooms[self.room][0]
        right = layout.boss_gate[0]
        speed = self.facing * 430
        distance = min(right - 12, max(left + 12, x + speed * step)) - x
        if distance and self._charge_id != self.last_contact_charge:
            ids = self._charge_id
            self.extra_attacks.append((self.bolt_box, ((elapsed, elapsed + distance / speed),
                                                      (x, y), (distance, 0), ids)))
        next_x = x + distance
        self.bolt = (next_x, y) if left + 12 < next_x < right - 12 else None
        self.bolt_animation.update(step)

    def _draw(self, transform, opacity):
        super()._draw(transform, opacity)
        if self.bolt is not None and self.last_contact_charge != self._charge_id:
            frame = self.bolt_animation.frame
            width, height = frame.rect[2:]
            draw_sprite(frame, transform, self.bolt, (width * 2, height * 2), opacity,
                        flip_x=self.facing < 0)

    def _draw_warning(self, transform, opacity):
        if self.state in ('jump_windup', 'leap', 'slam'):
            left, right = self.landing - 146, self.landing + 146
            color = (255, 202, 114) if self.state == 'slam' else (231, 101, 64)
        elif self.state in ('lash_windup', 'lash'):
            left, _, right, _ = self.lash_boxes[self.facing].bounds_at(self.collision_position)
            color = (255, 217, 130) if self.state == 'lash' else (194, 116, 58)
        else:
            return
        for x in range(round(left), round(right), 18):
            draw_rect(transform, (x, self.floor + 3, min(x + 11, right), self.floor + 7), color, opacity)
        for x in (left, right - 4):
            draw_rect(transform, (x, self.floor + 3, x + 4, self.floor + 15), color, opacity)

    def render_items(self):
        return (RenderItem(self._draw_warning, -1), *super().render_items())


ENEMY_TYPES = {'metal_dust': Enemy, 'cooling_fan': CoolingFan, 'leaking_capacitor': LeakingCapacitor,
               'power_assembly': PowerAssembly}
