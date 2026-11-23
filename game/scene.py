"""플레이 레벨 배치와 장면·창 조작."""

import json
from ctypes import byref, c_int
from math import hypot, inf
from pathlib import Path
from random import choice

import pico2d.pico2d as pico

from engine import Engine, HEIGHT
from engine.rendering.drawing import _sdl
from game_framework import Collider, GameObject, ImageStore, Level, LevelScene, RenderItem, draw_rect
from game_framework.collision import TIME_EPSILON, blocking_contact, overlaps

from .character import GROUND_Y, Character, _load_clip, load_clips
from .effects import SpriteEffect
from .enemy import Enemy, load_enemy_clips
from .charge import ACTIVATION_DISTANCE, CLICK_RADIUS, Charge, ChargeArt
from .mode import GameplayMode
from .teleport_link import DURATION, LinkArt, TeleportLink


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
COMBAT_ASSETS = ASSETS.parent / 'combat'
DEFAULT_SIZE = (1280, 720)
ALTERNATE_SIZE = (1024, 720)
CAST_COOLDOWN = .8
ENVIRONMENT_RECHARGE = 2.5
ENVIRONMENT_SITES = (
    ((-328, -84), (-320, -64), (-312, -92)),
    ((-172, 64), (-160, 70), (-148, 82)),
    ((140, -133), (146, -131), (152, -130)),
    ((312, 80), (320, 90), (332, 92)),
    ((-12, 190), (0, 200), (12, 212)),
)


def load_combat_clips(images):
    path = COMBAT_ASSETS / 'animations.json'
    try:
        animations = json.loads(path.read_text(encoding='utf-8'))
        clips = {name: _load_clip(images, animations[name], COMBAT_ASSETS)
                 for name in ('hit_spark', 'charge_spent')}
        if any(clip.loop for clip in clips.values()):
            raise ValueError('전투 효과는 단발 클립이어야 합니다.')
        if abs(sum(clips['charge_spent'].durations) - DURATION) > 1e-9:
            raise ValueError('전하 소모 효과 길이는 연결 시간과 같아야 합니다.')
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'전투 효과 설정 오류: {path}: {error}') from error
    for clip in clips.values():
        texture = clip.frames[0].image._borrow().texture
        _sdl(pico.SDL_SetTextureScaleMode(texture, pico.SDL_ScaleModeNearest))
    return clips


class _Ground(GameObject):
    colliders = (Collider((-inf, -inf, inf, GROUND_Y), 'terrain', blocks={'player'}),)

    def render_items(self):
        return (RenderItem(self._draw, draw_order=-2),)

    def _draw(self, transform, opacity):
        left, bottom, right, _ = transform.bounds
        draw_rect(transform, (left, bottom, right, GROUND_Y), (74, 79, 93), opacity)


class GameplayLevel(Level):
    def __init__(self, images):
        super().__init__(GameplayMode())
        self.images = images
        self.player = None
        self.enemy = None
        self._last_hit_attack = 0
        self._last_contact_charge = None
        self.charges = []
        self.charge_art = None
        self.skill_charge = None
        self._cast_cooldown = 0.0
        self.link_art = None
        self.combat_clips = {}

    def on_open(self):
        self.spawn(_Ground())
        self.player = self.spawn(Character(load_clips(self.images)))
        self.enemy = self.spawn(Enemy(load_enemy_clips(self.images)))
        self._last_hit_attack = 0
        self._last_contact_charge = None

        self.charge_art = ChargeArt(self.images)
        self.link_art = LinkArt(self.images)
        self.combat_clips = load_combat_clips(self.images)
        self._reset_environment()

    def _reset_environment(self):
        previous = tuple(charge.position for charge in self.charges)
        for charge in self.charges:
            charge.destroy()
        self.charges = [
            self.spawn(Charge(self.charge_art, choice([point for point in site if point != last])))
            for site, last in zip(ENVIRONMENT_SITES, previous or (None,) * len(ENVIRONMENT_SITES),
                                  strict=True)
        ]

    def _update_environment(self):
        for index, site in enumerate(ENVIRONMENT_SITES):
            charge = self.charges[index]
            if charge.spent_elapsed + TIME_EPSILON < ENVIRONMENT_RECHARGE:
                continue
            positions = [point for point in site if point != charge.position
                         and self._valid_charge_position(point)]
            if positions:
                self.charges[index] = self.spawn(Charge(self.charge_art, choice(positions)))
                charge.destroy()

    def _valid_charge_position(self, position):
        return self.player.can_teleport(position) and all(
            hypot(position[0] - charge.position[0], position[1] - charge.position[1]) >= CLICK_RADIUS
            for charge in self.charges if charge.level is self and not charge.spent)

    def cast_charge(self, position):
        if position is None or self.skill_charge is not None or self._cast_cooldown > TIME_EPSILON:
            return
        x, y = self.mode.activation_origin
        distance = hypot(position[0] - x, position[1] - y)
        if CLICK_RADIUS <= distance <= ACTIVATION_DISTANCE and self._valid_charge_position(position):
            self.skill_charge = self.spawn(Charge(self.charge_art, position))
            self.charges.append(self.skill_charge)
            self._cast_cooldown = CAST_COOLDOWN

    def spend_charge(self, charge):
        charge.spend()
        if charge is self.skill_charge:
            self._remove_skill_charge()

    def _remove_skill_charge(self):
        if self.skill_charge is not None:
            charge, self.skill_charge = self.skill_charge, None
            self.charges.remove(charge)
            charge.destroy()

    def reset_combat(self):
        clips, enemy_clips = self.player.clips, self.enemy.clips
        view_bounds = self.player.view_bounds
        for obj in self.objects:
            if isinstance(obj, (SpriteEffect, TeleportLink)):
                obj.destroy()
        self.mode.pending_charge = self.mode.teleport_link = None
        self._remove_skill_charge()
        self._cast_cooldown = 0.0
        self.player.destroy()
        self.enemy.destroy()
        self.player = self.spawn(Character(clips))
        self.player.view_bounds = view_bounds
        self.enemy = self.spawn(Enemy(enemy_clips))
        self._reset_environment()
        self._last_hit_attack = 0
        self._last_contact_charge = None

    def update(self, dt):
        if self.player is None or self.player.level is not self or self.player.hp == 0:
            return
        self._cast_cooldown = max(0.0, self._cast_cooldown - dt)
        player_position = self.player.collision_position
        protected_until = max(self.player.invulnerability_remaining, self.player.teleport_guard_remaining)
        super().update(dt)
        self._update_environment()
        if self.enemy.level is not self:
            return
        self._resolve_sword()
        if self.enemy.level is self:
            self._resolve_enemy_contact(dt, player_position, protected_until)
            if self.player.hp == 0:
                for obj in self.objects:
                    if isinstance(obj, SpriteEffect):
                        obj.destroy()

    def _resolve_sword(self):
        attack = self.player.active_attack
        if attack is None:
            return
        attack_id, sword, position, window, velocity_y = attack
        if attack_id == self._last_hit_attack:
            return
        for times, x, dx, _ in self.enemy.motion:
            relative_position = x, self.enemy.y - velocity_y * times[0]
            motion = dx, -velocity_y * (times[1] - times[0])
            contact = self.enemy.body.overlap_contact(sword, relative_position, position,
                                                      times, motion, window)
            if contact is not None:
                enemy_x = x + dx * (contact - times[0]) / (times[1] - times[0])
                left, bottom, right, top = self.enemy.hurt_box_at(enemy_x)
                sword_x, sword_y = position
                sword_left, sword_bottom, sword_right, sword_top = sword.bounds_at(
                    (sword_x, sword_y + velocity_y * contact))
                facing = 1 if sword is self.player.swords[1] else -1
                point = (max(left, sword_left) if facing > 0 else min(right, sword_right),
                         (max(bottom, sword_bottom) + min(top, sword_top)) / 2)
                self._last_hit_attack = attack_id
                self.enemy.take_hit()
                self.spawn(SpriteEffect(self.combat_clips['hit_spark'], point, facing, 1,
                                        draw_order=1))
                break

    def _resolve_enemy_contact(self, dt, player_position, protected_until):
        if dt == 0:
            return
        x0, y0 = player_position
        # shortcut: 한 갱신의 워든 궤적은 선형 근사, 프레임 내 세부 궤적이 필요해지면 행동별 경로를 전달한다.
        vx, vy = (self.player.x - x0) / dt, (self.player.y - y0) / dt
        player_box = self.player.body.bounds_at(player_position)
        first_impact = None
        for times, x, dx, charge_id in self.enemy.motion:
            start, end = times
            span = end - start
            relative_position = x - vx * start, self.enemy.y - vy * start
            enemy_box = self.enemy.body.bounds_at(relative_position)
            relative_motion = dx - vx * span, -vy * span
            fraction = 0 if overlaps(enemy_box, player_box) else blocking_contact(
                enemy_box, player_box, relative_motion)
            if fraction is None:
                continue
            contact = start + span * fraction
            if first_impact is None:
                player_x = x0 + vx * contact
                enemy_x = x + dx * fraction
                side = -1 if player_x < enemy_x else 1 if player_x > enemy_x else self.enemy.facing
                first_impact = contact, player_x, side
            if charge_id is None or charge_id == self._last_contact_charge:
                continue
            self._last_contact_charge = charge_id
            if contact + TIME_EPSILON >= protected_until:
                self.player.take_hit()
                protected_until = contact + self.player.invulnerability_remaining
                self.player.invulnerability_remaining = max(0, protected_until - dt)
                if self.player.hp == 0:
                    break
        if first_impact is not None:
            contact, player_x, side = first_impact
            self._push_player(player_x, side, dt - contact)

    def _push_player(self, contact_x, side, elapsed):
        player, enemy = self.player, self.enemy
        # 접촉 뒤 밀고 들어간 이동만 되돌린다. 이미 적에서 멀어진 이동은 유지한다.
        if side * (player.x - contact_x) < 0:
            player.x = contact_x
        player.begin_enemy_push(side, elapsed)

        _, bottom, _, top = player.hurt_box
        _, enemy_bottom, _, enemy_top = enemy.hurt_box
        if bottom >= enemy_top or enemy_bottom >= top:
            return
        player_left, _, player_right, _ = player.body.bounds
        enemy_left, _, enemy_right, _ = enemy.body.bounds
        gap = enemy_right - player_left if side > 0 else player_right - enemy_left
        target = enemy.x + side * gap
        if side * (player.x - target) < 0:
            player.move_enemy_push(target)
            if side * (player.x - target) < 0:
                enemy.x = player.x - side * gap


class CharacterScene(LevelScene):
    def __init__(self):
        images = ImageStore(ASSETS)
        super().__init__(GameplayLevel(images), view_height=HEIGHT, images=images)
        self.level.mode.event_to_world = self.event_to_world
        self.level.mode.cursor_to_world = self.cursor_to_world

    def cursor_to_world(self):
        if not pico.SDL_GetWindowFlags(pico.window) & pico.SDL_WINDOW_MOUSE_FOCUS:
            return None
        x, y = c_int(), c_int()
        pico.SDL_GetMouseState(byref(x), byref(y))
        point = self.engine.window_to_output(x.value, y.value)
        return None if point is None else self.transform.inverse(*point)

    @property
    def character(self):
        return self.level.player

    def enter(self, engine):
        super().enter(engine)
        self.character.view_bounds = self.transform.bounds
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden | A/D | Space: jump | J: attack | E: create charge | Shift: dash | LMB: charge / attack | RMB: nearest charge | R: restart | F6 / F11 | Esc')

    def handle_event(self, event):
        self.character.view_bounds = self.transform.bounds
        if event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F6:
                size = ALTERNATE_SIZE if self.engine.window_size == DEFAULT_SIZE else DEFAULT_SIZE
                self.engine.set_display(fullscreen=False, window_size=size)
            elif event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
        super().handle_event(event)

    def update(self, dt):
        self.character.view_bounds = self.transform.bounds
        super().update(dt)
        self.level.mode.after_update()


def main():
    print('게임플레이: A/D 이동 / Space 점프 / J 공격 / E 커서 위치에 전하 생성 / Shift 대시 / 좌클릭: 활성 전하 순간이동·그 외 공격 / 우클릭: 가장 가까운 활성 전하 / R 전투 재시작 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    Engine(*DEFAULT_SIZE).run(CharacterScene())
