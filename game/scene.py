"""플레이 레벨 배치와 장면·창 조작."""

import argparse
import json
from ctypes import byref, c_int
from math import expm1, hypot
from pathlib import Path
from random import choice

import pico2d.pico2d as pico

from engine import Engine, HEIGHT
from engine.rendering.drawing import _sdl
from game_framework import Canvas, ImageStore, Label, Level, LevelScene
from game_framework.collision import CONTACT_EPSILON, TIME_EPSILON, blocking_contact, overlaps

from .character import DASH_KEYS, MOVE_KEYS, PUSHBACK_SECONDS, Character, _load_clip, load_clips
from .effects import SpriteEffect
from .enemy import CHARGE_SPEED, Enemy, load_enemy_clips
from .charge import ACTIVATION_DISTANCE, CLICK_RADIUS, Charge, ChargeArt
from .mode import GameplayMode
from .power_supply_map import PowerSupplyMap
from .story_intro import PowerOpening
from .teleport_link import DURATION, LinkArt, TeleportLink
from .title import MENU_FONT, TitleScene
from .training_map import WORLD_BOUNDS, TrainingMap


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'warden'
COMBAT_ASSETS = ASSETS.parent / 'combat'
POWER_SUPPLY_ASSETS = ASSETS.parent / 'levels' / 'power-supply'
DEFAULT_SIZE = (1280, 720)
ALTERNATE_SIZE = (1024, 720)
POWER_SUPPLY_PIXEL_HEIGHT = 360
POWER_ENTRY_SHAKE_STEP = .025
POWER_ENTRY_SHAKE = ((2, 3), (0, -2), (1, 1), (0, -1))
POWER_ENTRY_KEYS = MOVE_KEYS | DASH_KEYS | {pico.SDLK_SPACE, pico.SDLK_j, pico.SDLK_e}
CAST_COOLDOWN = .8
ENVIRONMENT_RECHARGE = 2.5
TOP_EXIT_MARGIN = 24
CAMERA_FOLLOW_SECONDS = .22
SWORD_HIT_STOP = .045
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


class GameplayLevel(Level):
    def __init__(self, images, *, power_supply=False):
        super().__init__(GameplayMode())
        self.images = images
        self.player = None
        self.enemy = None
        self._last_hit_attack = 0
        self._last_contact_charge = None
        self._sword_stop_remaining = 0.0
        self.charges = []
        self.charge_art = None
        self.skill_charge = None
        self._cast_cooldown = 0.0
        self.link_art = None
        self.combat_clips = {}
        self.power_supply = power_supply
        self.power_entry_effect = None
        self.world_bounds = WORLD_BOUNDS
        self.environment_sites = ENVIRONMENT_SITES

    def on_open(self):
        if self.power_supply:
            self.layout = self.spawn(PowerSupplyMap(self.images))
            self.world_bounds = self.layout.bounds
            self.environment_sites = self.layout.charge_sites
        else:
            self.spawn(TrainingMap())
        self._spawn_combatants(load_clips(self.images), load_enemy_clips(self.images))
        self._last_hit_attack = 0
        self._last_contact_charge = None

        self.charge_art = ChargeArt(self.images)
        self.link_art = LinkArt(self.images)
        self.combat_clips = load_combat_clips(self.images)
        self._reset_environment()
        if self.power_supply:
            data = json.loads((POWER_SUPPLY_ASSETS / 'power-entry.json').read_text(encoding='utf-8'))
            self.power_entry_clip = _load_clip(self.images, data, POWER_SUPPLY_ASSETS)
            self.power_entry_scale = data['scale']
            self.power_entry_impact = data['impactMs'] / 1000
            self.power_entry_reveal = sum(self.power_entry_clip.durations) - self.power_entry_impact
            if self.power_entry_clip.loop or not (0 < self.power_entry_impact and self.power_entry_reveal > 0):
                raise ValueError('등장 효과는 타격 시점이 있는 단발 클립이어야 합니다.')
            texture = self.power_entry_clip.frames[0].image._borrow().texture
            _sdl(pico.SDL_SetTextureScaleMode(texture, pico.SDL_ScaleModeNearest))
            self._start_power_entry()

    def _start_power_entry(self):
        self.player.spawn_opacity = 0.0
        self.power_entry_effect = self.spawn(SpriteEffect(
            self.power_entry_clip, self.layout.power_entry, 1, self.power_entry_scale, draw_order=1))

    def finish_power_entry(self):
        self.power_entry_effect.destroy()
        self.power_entry_effect = None
        self.player.spawn_opacity = 1.0

    def _update_power_entry(self):
        animation = self.power_entry_effect.player
        if animation.finished:
            self.finish_power_entry()
            return
        elapsed = max(0.0, animation.elapsed - self.power_entry_impact)
        self.player.spawn_opacity = elapsed / self.power_entry_reveal

    def _spawn_combatants(self, clips, enemy_clips):
        self.player = self.spawn(Character(clips))
        self.player.world_bounds = self.world_bounds
        self.enemy = self.spawn(Enemy(enemy_clips))
        if self.power_supply:
            self.player.x, self.player.y = self.layout.player_start
            self.enemy.x, self.enemy.y = self.layout.enemy_start

    def _reset_environment(self):
        previous = tuple(charge.position for charge in self.charges)
        for charge in self.charges:
            charge.destroy()
        self.charges = [
            self.spawn(Charge(self.charge_art, choice([point for point in site if point != last])))
            for site, last in zip(self.environment_sites, previous or (None,) * len(self.environment_sites),
                                  strict=True)
        ]

    def _update_environment(self):
        for index, site in enumerate(self.environment_sites):
            charge = self.charges[index]
            if charge.spent_elapsed + TIME_EPSILON < ENVIRONMENT_RECHARGE:
                continue
            positions = [point for point in site if point != charge.position
                         and self.player.can_place_center(point) and self._clear_of_charges(point)]
            if positions:
                self.charges[index] = self.spawn(Charge(self.charge_art, choice(positions)))
                charge.destroy()

    def _clear_of_charges(self, position):
        return all(
            hypot(position[0] - charge.position[0], position[1] - charge.position[1]) >= CLICK_RADIUS
            for charge in self.charges if charge.level is self and not charge.spent)

    def cast_charge(self, position):
        if position is None or self.skill_charge is not None or self._cast_cooldown > TIME_EPSILON:
            return
        x, y = self.mode.activation_origin
        distance = hypot(position[0] - x, position[1] - y)
        if (CLICK_RADIUS <= distance <= ACTIVATION_DISTANCE
                and self.player.can_teleport(position) and self._clear_of_charges(position)):
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
        self._spawn_combatants(clips, enemy_clips)
        self.player.view_bounds = view_bounds
        if self.power_supply:
            self.layout.reset()
            self._start_power_entry()
        self._reset_environment()
        self._last_hit_attack = 0
        self._last_contact_charge = None
        self._sword_stop_remaining = 0.0

    def update(self, dt):
        if self._sword_stop_remaining:
            stopped = min(dt, self._sword_stop_remaining)
            self._sword_stop_remaining -= stopped
            dt -= stopped
            if not dt:
                return
        if self.player is None or self.player.level is not self or self.player.hp == 0:
            return
        self._cast_cooldown = max(0.0, self._cast_cooldown - dt)
        player_position = self.player.collision_position
        protected_until = max(self.player.invulnerability_remaining, self.player.teleport_guard_remaining)
        super().update(dt)
        if self.power_entry_effect is not None:
            self._update_power_entry()
        self._update_environment()
        if self.enemy.level is self:
            self._resolve_sword()
        if self.enemy.level is self:
            self._resolve_enemy_contact(dt, player_position, protected_until)
        if self.power_supply:
            self.layout.check_arc(self.player)
        if self.player.hp == 0:
            for obj in self.objects:
                if isinstance(obj, SpriteEffect):
                    obj.destroy()

    def _resolve_sword(self):
        for sweep in self.player.attack_sweeps:
            if sweep.attack_id == self._last_hit_attack:
                continue
            vx, vy = sweep.velocity
            sword_x, sword_y = sweep.origin
            sword_start, sword_end = sweep.times
            for times, x, dx, _ in self.enemy.motion:
                enemy_start, enemy_end = times
                start, end = max(sword_start, enemy_start), min(sword_end, enemy_end)
                if start > end:
                    continue
                enemy_vx = dx / (enemy_end - enemy_start)
                span = end - start
                x += enemy_vx * (start - enemy_start)
                relative_position = x - vx * (start - sword_start), self.enemy.y - vy * (start - sword_start)
                relative_motion = (enemy_vx - vx) * span, -vy * span
                contact = self.enemy.body.overlap_contact(
                    sweep.sword, relative_position, sweep.origin, (start, end), relative_motion,
                    sweep.active_window)
                if contact is None:
                    continue
                enemy_x = x + enemy_vx * (contact - start)
                left, bottom, right, top = self.enemy.hurt_box_at(enemy_x)
                step = contact - sword_start
                sword_left, sword_bottom, sword_right, sword_top = sweep.sword.bounds_at(
                    (sword_x + vx * step, sword_y + vy * step))
                facing = 1 if sweep.sword is self.player.swords[1] else -1
                point = (max(left, sword_left) if facing > 0 else min(right, sword_right),
                         (max(bottom, sword_bottom) + min(top, sword_top)) / 2)
                self._last_hit_attack = sweep.attack_id
                self.enemy.take_hit(facing)
                self.spawn(SpriteEffect(self.combat_clips['hit_spark'], point, facing, 1,
                                        draw_order=1))
                self._sword_stop_remaining = SWORD_HIT_STOP
                return

    def _resolve_enemy_contact(self, dt, player_position, protected_until):
        if dt == 0:
            return
        x0, y0 = player_position
        # shortcut: 한 갱신의 워든 궤적은 선형 근사, 프레임 내 세부 궤적이 필요해지면 행동별 경로를 전달한다.
        vx, vy = (self.player.x - x0) / dt, (self.player.y - y0) / dt
        player_box = self.player.body.bounds_at(player_position)
        first_impact = damage_impact = None
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
            player_x, player_y = x0 + vx * contact, y0 + vy * contact
            enemy_x = x + dx * fraction
            left, _, right, top = self.enemy.hurt_box_at(enemy_x)
            if (vy < 0 and abs(player_y - top) <= TIME_EPSILON
                    and player_box[0] + vx * contact < right and left < player_box[2] + vx * contact):
                side = 0
            else:
                side = -1 if player_x < enemy_x else 1 if player_x > enemy_x else self.enemy.facing
            impact = contact, player_x, player_y, side
            if first_impact is None:
                first_impact = impact
            if charge_id is None or charge_id == self._last_contact_charge:
                continue
            self._last_contact_charge = charge_id
            if contact + TIME_EPSILON >= protected_until:
                damage_impact = impact
                break
        if first_impact is not None:
            contact, player_x, player_y, side = damage_impact or first_impact
            self._push_player(player_x, player_y, side, dt - contact, damage_impact is not None)

    def _push_player(self, contact_x, contact_y, side, elapsed, damaged):
        player, enemy = self.player, self.enemy
        if not side:
            self._eject_from_enemy_top(contact_x, elapsed, damaged)
            return
        if damaged:
            player.x, player.y = contact_x, contact_y
            left, bottom, right, top = player.hurt_box
            impact_x = right if side < 0 else left
            impact_y = (max(bottom, enemy.y) + min(top, enemy.hurt_box[3])) / 2
            if player.take_hit(side, elapsed):
                self._show_player_hit((impact_x, impact_y), side)
        else:
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

    def _eject_from_enemy_top(self, contact_x, elapsed, damaged):
        player, enemy = self.player, self.enemy
        player.x, player.y = contact_x, enemy.hurt_box[3]
        preferred = 1 if contact_x > enemy.x else -1
        if enemy.state == 'charge' or contact_x == enemy.x:
            preferred = -enemy.facing
        options = []
        for side in (preferred, -preferred):
            gap = (enemy.body.bounds[2] - player.body.bounds[0] if side > 0
                   else player.body.bounds[2] - enemy.body.bounds[0])
            pursuit = 0.0
            if enemy.state == 'charge' and side == enemy.facing:
                pursuit = CHARGE_SPEED * enemy.state_remaining
            edge = enemy.x + side * (gap + pursuit)
            target = player.clamped_horizontal_target(edge + side * TOP_EXIT_MARGIN)
            options.append((side * (target - edge), target, side))
        clearance, target, side = options[0]
        if clearance + TIME_EPSILON < TOP_EXIT_MARGIN and options[1][0] > clearance + TIME_EPSILON:
            _, target, side = options[1]
        speed = max(0.0, side * (target - player.x)) / PUSHBACK_SECONDS
        if damaged:
            height = player.y
            if player.take_hit(side, elapsed, speed):
                self._show_player_hit((contact_x, height), side)
        else:
            player.bounce_from_enemy(side, speed, elapsed)

    def _show_player_hit(self, position, facing):
        self.spawn(SpriteEffect(self.combat_clips['hit_spark'], position, facing, 1,
                                draw_order=1))


class CharacterScene(LevelScene):
    def __init__(self, *, power_supply=False, story_intro=False):
        images = ImageStore(ASSETS)
        super().__init__(GameplayLevel(images, power_supply=power_supply),
                         view_height=DEFAULT_SIZE[1] if power_supply else HEIGHT, images=images)
        self.power_canvas = Canvas(DEFAULT_SIZE) if power_supply else None
        if self.power_canvas is not None:
            self.power_hint = self.power_canvas.add(Label('W  ACTIVATE', anchor=(.5, 1), x=-60, y=-53,
                                                          size=26, font_path=MENU_FONT, visible=False))
        self.level.mode.event_to_world = self.event_to_world
        self.level.mode.cursor_to_world = self.cursor_to_world
        self._pixel_target = None
        self._pixel_size = None
        self._story_intro = story_intro
        self.opening = None

    def draw(self):
        if not self.level.power_supply or not self.engine.output_valid:
            return super().draw()

        self.power_hint.visible = self.opening is None and self.level.layout.near_relay(self.character)
        width, height = self.engine.output_size
        grid_height = POWER_SUPPLY_PIXEL_HEIGHT
        grid_width = max(1, round(width * grid_height / height))
        if self._pixel_size != (grid_width, grid_height):
            target = pico.SDL_CreateTexture(pico.renderer, pico.SDL_PIXELFORMAT_RGBA8888,
                                            pico.SDL_TEXTUREACCESS_TARGET, grid_width, grid_height)
            if not target:
                raise RuntimeError(f'픽셀 격자 텍스처 생성 실패: {pico.SDL_GetError()!r}')
            try:
                _sdl(pico.SDL_SetTextureScaleMode(target, pico.SDL_ScaleModeNearest))
            except BaseException:
                pico.SDL_DestroyTexture(target)
                raise
            if self._pixel_target:
                pico.SDL_DestroyTexture(self._pixel_target)
            self._pixel_target = target
            self._pixel_size = grid_width, grid_height

        camera_center, view_height = self.camera_center, self.view_height
        _sdl(pico.SDL_SetRenderTarget(pico.renderer, self._pixel_target))
        try:
            # 월드·입력 좌표를 유지한 채 같은 픽셀 격자에 합성한다.
            _sdl(pico.SDL_RenderSetScale(pico.renderer, grid_width / width, grid_height / height))
            _sdl(pico.SDL_RenderClear(pico.renderer))
            if self.opening is not None:
                self.camera_center, self.view_height = self.opening.camera(
                    camera_center, view_height, width / height)
            entry = self.level.power_entry_effect
            if entry is not None:
                since_impact = entry.player.elapsed - self.level.power_entry_impact
                if 0 <= since_impact < POWER_ENTRY_SHAKE_STEP * len(POWER_ENTRY_SHAKE):
                    dx, dy = POWER_ENTRY_SHAKE[int(since_impact / POWER_ENTRY_SHAKE_STEP)]
                    pixel = self.view_height / grid_height
                    cx, cy = self.camera_center
                    self.camera_center = cx + dx * pixel, cy + dy * pixel
            super().draw()
            if self.opening is not None:
                self.opening.draw(self.transform)
        finally:
            self.camera_center, self.view_height = camera_center, view_height
            _sdl(pico.SDL_SetRenderTarget(pico.renderer, None))
        _sdl(pico.SDL_RenderCopy(pico.renderer, self._pixel_target, None, None))
        if self.opening is not None:
            canvas = self.opening.canvas
            self.renderer.draw_ui(canvas, canvas.transform(self.engine.viewport))
        elif self.power_hint.visible:
            canvas = self.power_canvas
            self.renderer.draw_ui(canvas, canvas.transform(self.engine.viewport))

    def exit(self):
        try:
            if self._pixel_target:
                pico.SDL_DestroyTexture(self._pixel_target)
                self._pixel_target = self._pixel_size = None
            if self.opening is not None:
                opening, self.opening = self.opening, None
                opening.close()
            if self.power_canvas is not None:
                self.power_canvas.close()
                self.power_canvas = None
        finally:
            super().exit()

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
        if self.level.power_supply:
            self.camera_center = (self.character.x, 0)
            self._follow_camera(0, self.character.x)
            if self._story_intro:
                self.opening = PowerOpening(self.level, DEFAULT_SIZE)
        self.character.view_bounds = self.transform.bounds
        self._set_title()

    def _set_title(self):
        name = b'Circuit Warden'
        if self.level.power_supply:
            name += b' | Power Supply'
            if self.level.layout.reached_output:
                name += b' | Output reached'
        if self.level.power_supply:
            name += b' | W: power'
        pico.SDL_SetWindowTitle(pico.window, name + b' | A/D | Space: jump | J: attack | E: create charge | Shift: dash | LMB: charge / attack | RMB: nearest charge | R: restart | F6 / F11 | Esc')

    def handle_event(self, event):
        if event.type == pico.SDL_KEYDOWN:
            if event.key == pico.SDLK_F6:
                size = ALTERNATE_SIZE if self.engine.window_size == DEFAULT_SIZE else DEFAULT_SIZE
                self.engine.set_display(fullscreen=False, window_size=size)
            elif event.key == pico.SDLK_F11:
                self.engine.set_display(fullscreen=not self.engine.fullscreen)
        if self.opening is not None:
            if event.type in (pico.SDL_RENDER_DEVICE_RESET, pico.SDL_RENDER_TARGETS_RESET):
                super().handle_event(event)
            viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
            self.opening.input.handle_event(event, self.opening.canvas.transform(viewport),
                                            self.engine.event_to_output(event))
            return
        previous_player = self.character
        previous_player.view_bounds = self.transform.bounds
        if self.level.power_entry_effect is not None and (
                event.type == pico.SDL_KEYDOWN and event.key in POWER_ENTRY_KEYS
                or event.type == pico.SDL_MOUSEBUTTONDOWN
                and event.button in (pico.SDL_BUTTON_LEFT, pico.SDL_BUTTON_RIGHT)):
            self.level.finish_power_entry()
        super().handle_event(event)
        if self.character is not previous_player:
            self.camera_center = (self.character.x, 0)
            self._set_title()
        self._follow_camera(0, self.character.x)
        self.character.view_bounds = self.transform.bounds

    def handle_escape(self):
        if self.opening is None:
            return False
        self.opening.skip()
        return True

    def update(self, dt):
        if self.opening is not None:
            self._follow_camera(0, self.character.x)
            if self.opening.skipped or (self.engine.output_valid and self.opening.update(dt)):
                opening, self.opening = self.opening, None
                opening.close()
                self.character.view_bounds = self.transform.bounds
            return
        self.character.view_bounds = self.transform.bounds
        previous_x = self.character.x
        super().update(dt)
        self.level.mode.after_update()
        if self.level.power_supply and self.level.layout.check_output(self.character):
            self._set_title()
        self._follow_camera(dt, previous_x)
        self.character.view_bounds = self.transform.bounds

    def _follow_camera(self, dt, previous_x):
        bounds = self.transform.bounds
        if bounds is None:
            return
        left, _, right, top = self.level.world_bounds
        half_width = min((bounds[2] - bounds[0]) / 2, (right - left) / 2)
        low, high = left + half_width, right - half_width
        camera_x = min(max(self.camera_center[0], low), high)
        player = self.character
        target = min(max(player.x, low), high)
        if target != camera_x and abs(player.x - previous_x) <= CONTACT_EPSILON:
            direction = player.move_direction or (1 if target > camera_x else -1)
            contact = self.level.blocking_contact(player, player.body, (direction, 0))
            if contact is not None and contact <= CONTACT_EPSILON:
                target = camera_x
        follow = -expm1(-dt / CAMERA_FOLLOW_SECONDS)
        camera_x += (target - camera_x) * follow
        camera_y = self.camera_center[1]
        if self.level.power_supply:
            target_y = min(max(player.y, 0), max(0, top - self.view_height / 2))
            camera_y += (target_y - camera_y) * follow
        self.camera_center = (camera_x, camera_y)


def main():
    parser = argparse.ArgumentParser(description='Circuit Warden')
    parser.add_argument('--training', action='store_true', help='플랫폼 훈련장으로 시작')
    args = parser.parse_args()
    print('게임플레이: A/D 이동 / Space 점프 / J 공격 / E 커서 위치에 전하 생성 / Shift 대시 / 좌클릭: 활성 전하 순간이동·그 외 공격 / 우클릭: 가장 가까운 활성 전하 / R 전투 재시작 / F6 창 크기 / F11 전체화면 / Escape 종료', flush=True)
    scene = CharacterScene() if args.training else TitleScene(
        lambda: CharacterScene(power_supply=True, story_intro=True),
        sizes=(DEFAULT_SIZE, ALTERNATE_SIZE),
        art_path=POWER_SUPPLY_ASSETS / 'far.png')
    Engine(*DEFAULT_SIZE).run(scene)
