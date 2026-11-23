"""플레이 레벨 배치와 장면·창 조작."""

from math import inf
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine, HEIGHT
from game_framework import Collider, GameObject, ImageStore, Level, LevelScene, RenderItem, draw_rect
from game_framework.collision import TIME_EPSILON, blocking_contact, overlaps

from .character import GROUND_Y, Character, load_clips
from .effects import SpriteEffect
from .enemy import Enemy, load_enemy_clips
from .charge import Charge, ChargeArt
from .mode import GameplayMode
from .teleport_link import LinkArt, TeleportLink


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
DEFAULT_SIZE = (1280, 720)
ALTERNATE_SIZE = (1024, 720)


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
        self.link_art = None

    def on_open(self):
        self.spawn(_Ground())
        self.player = self.spawn(Character(load_clips(self.images)))
        self.enemy = self.spawn(Enemy(load_enemy_clips(self.images)))
        self._last_hit_attack = 0
        self._last_contact_charge = None

        art = ChargeArt(self.images)
        self.link_art = LinkArt(self.images)
        self.charges = [self.spawn(Charge(art, position)) for position in
                        ((-320, -80), (-160, 70), (140, -50), (320, 140), (0, 200))]

    def reset_combat(self):
        clips, enemy_clips = self.player.clips, self.enemy.clips
        view_bounds = self.player.view_bounds
        for obj in self.objects:
            if isinstance(obj, (SpriteEffect, TeleportLink)):
                obj.destroy()
        self.mode.pending_charge = self.mode.teleport_link = self.mode.last_charge = None
        self.player.destroy()
        self.enemy.destroy()
        self.player = self.spawn(Character(clips))
        self.player.view_bounds = view_bounds
        self.enemy = self.spawn(Enemy(enemy_clips))
        for charge in self.charges:
            charge.active = charge.in_range(self.player.center)
        self._last_hit_attack = 0
        self._last_contact_charge = None

    def update(self, dt):
        if self.player is None or self.player.level is not self or self.player.hp == 0:
            return
        player_position = self.player.collision_position
        protected_until = self.player.invulnerability_remaining
        super().update(dt)
        if self.enemy.level is not self:
            return
        self._resolve_sword()
        if self.enemy.level is self:
            self._resolve_enemy_contact(dt, player_position, protected_until)

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
            if self.enemy.body.overlap_contact(sword, relative_position, position,
                                               times, motion, window) is not None:
                self._last_hit_attack = attack_id
                self.enemy.take_hit()
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

    @property
    def character(self):
        return self.level.player

    def enter(self, engine):
        super().enter(engine)
        self.character.view_bounds = self.transform.bounds
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden | A/D | Space: jump | Shift: dash | LMB: charge / attack | RMB: nearest charge | R: restart | F6 / F11 | Esc')

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
    print('게임플레이: A/D 이동 / Space 점프 / Shift 대시 / 왼쪽 클릭: 활성 전하 순간이동·그 외 공격 / 우클릭: 가장 가까운 활성 전하 / R 전투 재시작 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    Engine(*DEFAULT_SIZE).run(CharacterScene())
