"""플레이 레벨 배치와 장면·창 조작."""

from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine, HEIGHT
from game_framework import GameObject, ImageStore, Level, LevelScene, RenderItem, draw_rect

from .character import GROUND_Y, Character, load_clips
from .combat import TIME_EPSILON, first_contact
from .effects import SpriteEffect
from .enemy import Enemy, load_enemy_clips
from .mode import GameplayMode


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
DEFAULT_SIZE = (1280, 720)
ALTERNATE_SIZE = (1024, 720)


class _Ground(GameObject):
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

    def on_open(self):
        self.spawn(_Ground())
        self.player = self.spawn(Character(load_clips(self.images)))
        self.enemy = self.spawn(Enemy(load_enemy_clips(self.images)))
        self._last_hit_attack = 0
        self._last_contact_charge = None

    def reset_combat(self):
        clips, enemy_clips = self.player.clips, self.enemy.clips
        view_bounds = self.player.view_bounds
        for obj in self.objects:
            if isinstance(obj, SpriteEffect):
                obj.destroy()
        self.player.destroy()
        self.enemy.destroy()
        self.player = self.spawn(Character(clips))
        self.player.view_bounds = view_bounds
        self.enemy = self.spawn(Enemy(enemy_clips))
        self._last_hit_attack = 0
        self._last_contact_charge = None

    def update(self, dt):
        if self.player is None or self.player.level is not self or self.player.hp == 0:
            return
        player_box = self.player.hurt_box
        protected_until = self.player.invulnerability_remaining
        super().update(dt)
        if self.enemy.level is not self:
            return
        self._resolve_sword()
        if self.enemy.level is self:
            self._resolve_charge(dt, player_box, protected_until)

    def _resolve_sword(self):
        attack = self.player.active_attack
        if attack is None:
            return
        attack_id, box, window = attack
        if attack_id == self._last_hit_attack:
            return
        for times, x, dx, _ in self.enemy.motion:
            if first_contact(self.enemy.hurt_box_at(x), box, times, (dx, 0), window) is not None:
                self._last_hit_attack = attack_id
                self.enemy.take_hit()
                break

    def _resolve_charge(self, dt, player_box, protected_until):
        if dt == 0:
            return
        end_box = self.player.hurt_box
        # shortcut: 한 갱신의 워든 궤적은 선형 근사, 프레임 내 세부 궤적이 필요해지면 행동별 경로를 전달한다.
        vx, vy = (end_box[0] - player_box[0]) / dt, (end_box[1] - player_box[1]) / dt
        for times, x, dx, charge_id in self.enemy.motion:
            if charge_id is None or charge_id == self._last_contact_charge:
                continue
            start, end = times
            span = end - start
            left, bottom, right, top = self.enemy.hurt_box_at(x)
            relative_box = (left - vx * start, bottom - vy * start,
                            right - vx * start, top - vy * start)
            contact = first_contact(relative_box, player_box, times, (dx - vx * span, -vy * span))
            if contact is None:
                continue
            self._last_contact_charge = charge_id
            if contact + TIME_EPSILON >= protected_until:
                self.player.take_hit()
                protected_until = contact + self.player.invulnerability_remaining
                self.player.invulnerability_remaining = max(0, protected_until - dt)
                if self.player.hp == 0:
                    break


class CharacterScene(LevelScene):
    def __init__(self):
        images = ImageStore(ASSETS)
        super().__init__(GameplayLevel(images), view_height=HEIGHT, images=images)

    @property
    def character(self):
        return self.level.player

    def enter(self, engine):
        super().enter(engine)
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden | A/D | Space: jump | Shift: dash | Left click: attack | R: restart | F6 / F11 | Esc')

    def handle_event(self, event):
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


def main():
    print('게임플레이: A/D 이동 / Space 점프 / 왼쪽 클릭 공격 / R 전투 재시작 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    Engine(*DEFAULT_SIZE).run(CharacterScene())
