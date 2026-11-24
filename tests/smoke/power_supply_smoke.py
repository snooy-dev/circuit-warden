"""실제 SDL 입력으로 첫 레벨의 점프, 전하, 도착과 초기화를 검증한다."""

import argparse
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from game.teleport_link import TeleportLink
from tests.smoke.character_smoke import push_key
from tests.smoke.combat_reimplementation_smoke import CombatSmoke


class PowerSupplySmoke(CombatSmoke):
    def __init__(self, output_dir):
        super().__init__(output_dir, power_supply=True)

    def enter(self, engine):
        CharacterScene.enter(self, engine)
        self.scenario = self.exercise()

    def move_to(self, map_x, *, jump=False):
        actor = self.character
        x, _ = self.level.layout._point(map_x, 0)
        direction = 1 if x > actor.x else -1
        key = pico.SDLK_d if direction > 0 else pico.SDLK_a
        if jump:
            yield from self.wait_until(lambda: actor.state in ('idle', 'run') and actor.grounded)
        push_key(key)
        if jump:
            push_key(pico.SDLK_SPACE)
        try:
            yield from self.wait_until(lambda: direction * (actor.x - x) >= 0)
        except AssertionError as error:
            raise AssertionError((map_x, actor.x + self.level.layout.half_width,
                                  actor.y, actor.state, actor.jump_phase)) from error
        push_key(key, pico.SDL_KEYUP)
        if jump:
            yield from self.wait_until(lambda: actor.grounded)
            push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield .035

    def step_to(self, x, y):
        yield from self.move_to(x, jump=True)
        assert isclose(self.character.y, self.level.layout._point(x, y)[1]), (x, y, self.character.y)

    def exercise(self):
        actor = self.character
        layout = self.level.layout
        assert actor.collision_position == layout.player_start and actor.grounded
        assert layout.power_entry == layout.player_start
        assert self.level.enemy.collision_position == layout.enemy_start
        assert all(actor.can_place_center(point) for site in layout.charge_sites for point in site)
        assert actor.spawn_opacity == 0.0
        initial_angle = layout.rotor_angle
        self.screenshot = 'power-entry-inlet'
        yield from self.wait_until(lambda: any(isinstance(obj, TeleportLink) for obj in self.level.objects))
        link = next(obj for obj in self.level.objects if isinstance(obj, TeleportLink))
        assert link.start == layout.power_entry and link.end == actor.center
        self.screenshot = 'power-entry-arc'
        yield .04
        assert 0 < actor.spawn_opacity < 1
        yield from self.wait_until(lambda: actor.spawn_opacity == 1.0)
        assert actor.collision_position == layout.player_start
        self.screenshot = 'power-supply-intake'
        yield .24
        assert self._pixel_size == (640, 360)
        angle_delta = (layout.rotor_angle - initial_angle) % 360
        assert 0 < angle_delta < layout.rotor_speed
        self.screenshot = 'power-supply-fan-rotated'
        yield .04
        push_key(pico.SDLK_F6)
        push_key(pico.SDLK_F6, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: self.engine.window_size == ALTERNATE_SIZE)
        assert layout.bounds[0] <= self.transform.bounds[0] + 1e-6
        yield 0
        assert self._pixel_size == (512, 360)
        push_key(pico.SDLK_F6)
        push_key(pico.SDLK_F6, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: self.engine.window_size == DEFAULT_SIZE)

        yield from self.move_to(970)
        assert self.level.enemy.x < layout.enemy_start[0]
        yield from self.step_to(1120, 444)
        yield from self.step_to(1256, 348)
        self.screenshot = 'power-supply-heatsink'
        yield .06
        # 전투 검사 후 지형 경로를 동일 조건으로 검증한다.
        push_key(pico.SDLK_j)
        yield from self.wait_until(lambda: actor.state == 'attack')
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        self.level.enemy.destroy()
        yield .32
        yield from self.move_to(1545)
        yield from self.wait_until(lambda: actor.grounded and isclose(actor.y, -180))
        yield from self.step_to(1425, 444)
        yield from self.step_to(1290, 348)
        yield from self.move_to(1711)
        yield from self.wait_until(lambda: actor.grounded)
        yield from self.step_to(1858, 420)
        yield from self.step_to(2029, 324)
        self.screenshot = 'power-supply-gallery'
        yield .06

        candidate = self.level.charges[9]
        point = self.transform.point(*candidate.position)
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = pico.SDL_BUTTON_LEFT
        event.button.x, event.button.y = map(round, point)
        assert pico.SDL_PushEvent(event) == 1
        yield from self.wait_until(lambda: candidate.spent and self.level.mode.teleport_link is not None)
        self.screenshot = 'power-supply-discharge'
        yield .2

        yield from self.move_to(2495)
        yield from self.wait_until(lambda: actor.grounded)
        yield from self.step_to(2608, 444)
        yield from self.step_to(2760, 348)
        yield from self.move_to(3120)
        yield from self.move_to(3490)
        yield from self.wait_until(lambda: layout.reached_output)
        self.screenshot = 'power-supply-output'
        yield .45
        assert self.transform.bounds[2] <= layout.bounds[2] + 1e-6
        push_key(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        assert not layout.reached_output and self.character.collision_position == layout.player_start
        assert self.level.enemy.collision_position == layout.enemy_start
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        assert self.character.spawn_opacity == 0.0
        push_key(pico.SDLK_d)
        yield from self.wait_until(lambda: self.character.x > layout.player_start[0])
        assert self.character.spawn_opacity == 1.0
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        print('PSU SDL PASS: intake, two heatsinks, reverse crossing, gallery, charge, output, R, F6', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed
