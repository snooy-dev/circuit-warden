"""실제 SDL 입력으로 첫 레벨의 점프, 전하, 도착과 초기화를 검증한다."""

import argparse
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
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
        assert layout.power_entry[0] < actor.x and layout.power_entry[1] > actor.y
        assert self.level.enemy.collision_position == layout.enemy_start
        assert all(actor.can_place_center(point) for site in layout.charge_sites for point in site)
        assert actor.spawn_opacity == 0.0
        initial_angle = layout.rotor_angle
        strike = self.level.power_entry_effect
        assert strike.position == layout.power_entry
        self.screenshot = 'power-entry-inlet'
        yield from self.wait_until(lambda: strike.player.elapsed >= self.level.power_entry_impact)
        self.screenshot = 'power-entry-arc'
        yield .04
        assert 0 < actor.spawn_opacity < 1
        yield from self.wait_until(lambda: actor.spawn_opacity == 1.0)
        assert strike.level is None and self.level.power_entry_effect is None
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

        yield from self.move_to(374)
        yield from self.step_to(488, 1016)
        yield from self.move_to(738)
        yield from self.wait_until(lambda: actor.grounded and isclose(actor.y, -180))
        yield from self.move_to(962)
        yield from self.step_to(1080, 1026)
        yield from self.move_to(1136)
        yield from self.step_to(1250, 914)
        yield from self.move_to(1270)
        yield from self.step_to(1186, 802)
        self.screenshot = 'distribution-service-shaft'

        candidate = self.level.charges[4]
        assert candidate.active
        point = self.transform.point(*candidate.position)
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = pico.SDL_BUTTON_LEFT
        event.button.x, event.button.y = map(round, point)
        assert pico.SDL_PushEvent(event) == 1
        yield from self.wait_until(lambda: candidate.spent and self.level.mode.teleport_link is not None)
        yield from self.wait_until(lambda: actor.grounded and isclose(actor.y, 266))
        yield from self.move_to(804)
        push_key(pico.SDLK_a)
        yield .17
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        assert isclose(actor.x, layout._point(790, 0)[0])
        across = layout._point(680, 652.5)
        assert actor.can_place_center(across) and not actor.can_teleport(across)
        self.screenshot = 'distribution-locked-output'
        yield .12

        push_key(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        actor = self.character
        assert layout.power_stage == 0 and not layout.reached_output
        push_key(pico.SDLK_w)
        push_key(pico.SDLK_w, pico.SDL_KEYUP)
        yield .08
        assert layout.power_stage == 0
        for x in (700, 1140, 1458):
            yield from self.move_to(x)
        push_key(pico.SDLK_d)
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: actor.velocity_y < 0 and actor.y <= -42)
        push_key(pico.SDLK_LSHIFT)
        yield from self.wait_until(lambda: actor.state == 'dash')
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.screenshot = 'distribution-conversion'
        yield from self.wait_until(lambda: actor.x >= layout._point(1854, 0)[0])
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: actor.grounded and actor.state in ('idle', 'run'))
        yield from self.step_to(1926, 1084)
        for x in (2360, 2760, 3090):
            yield from self.move_to(x)
        assert layout.near_relay(actor) and len(layout.closed_shutters) == 2
        self.screenshot = 'distribution-relay'
        yield .12
        push_key(pico.SDLK_w)
        push_key(pico.SDLK_w, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: layout.power_stage == 1)
        assert len(layout.colliders) == len(layout.terrain) + 3 and len(layout.closed_shutters) == 2

        for x in (2660, 2145):
            yield from self.move_to(x)
        yield from self.step_to(2270, 1026)
        yield from self.move_to(2234)
        yield from self.step_to(2154, 914)
        yield from self.step_to(2238, 802)
        yield from self.step_to(2320, 694)

        yield from self.move_to(2508)
        yield from self.wait_until(lambda: layout.arc_phase == 0)
        yield from self.wait_until(lambda: layout.arc_phase == 1)
        hp = actor.hp
        yield from self.move_to(2534)
        assert layout.arc_phase == 1 and actor.hp == hp
        self.screenshot = 'distribution-arc-warning'
        yield from self.wait_until(lambda: actor.hp < hp)
        assert layout.arc_phase == 2 and actor.hp == hp - 1
        yield from self.wait_until(lambda: layout.arc_phase == 0 and actor.grounded)
        yield from self.move_to(2780)
        yield from self.move_to(3060)
        assert actor.grounded and isclose(actor.y, 266)
        self.screenshot = 'distribution-powered-bridge'
        yield .12
        yield from self.move_to(3615)
        assert layout.near_relay(actor)
        push_key(pico.SDLK_w)
        push_key(pico.SDLK_w, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: layout.power_stage == 2)
        assert not layout.closed_shutters and len(layout.colliders) == len(layout.terrain) + 1
        self.screenshot = 'distribution-breaker'
        yield from self.move_to(3810)
        yield from self.step_to(3902, 576)
        yield from self.move_to(3875)
        yield from self.step_to(3762, 480)
        yield from self.step_to(3650, 410)
        assert self.camera_center[1] > 360
        yield from self.move_to(3170)
        yield from self.step_to(3060, 386)
        self.screenshot = 'distribution-return-duct'
        yield from self.move_to(2580)
        yield from self.move_to(2338)
        yield from self.step_to(2206, 426)
        yield from self.move_to(1800)
        yield from self.move_to(1396)
        yield from self.wait_until(lambda: actor.grounded and isclose(actor.y, 266))
        yield from self.move_to(1316)
        yield from self.step_to(1130, 694)
        yield from self.move_to(698)
        yield from self.move_to(456)
        yield from self.wait_until(lambda: layout.reached_output)
        self.screenshot = 'distribution-output'
        yield .12
        push_key(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        push_key(pico.SDLK_r, pico.SDL_KEYUP)
        assert not layout.reached_output and layout.power_stage == 0 and self.camera_center[1] == 0
        assert len(layout.closed_shutters) == 2 and len(layout.colliders) == len(layout.terrain) + 2
        print('PSU SDL PASS: locked output, relay, arc, bridge, breaker, return duct, output, reset, F6', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed
