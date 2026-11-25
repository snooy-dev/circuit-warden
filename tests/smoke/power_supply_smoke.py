"""실제 SDL 입력으로 전원 구역의 하강, 점검 덮개, 복구와 귀환을 검증한다."""

import argparse
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from tests.smoke.character_smoke import push_key
from tests.smoke.combat_reimplementation_smoke import CombatSmoke


class PowerSupplySmoke(CombatSmoke):
    def __init__(self, output_dir, *, hatch=False):
        super().__init__(output_dir, power_supply=True)
        self.hatch = hatch

    def enter(self, engine):
        CharacterScene.enter(self, engine)
        self.scenario = self.exercise()

    def map_x(self):
        return self.character.x + self.level.layout.half_width

    def feet_y(self):
        return self.level.layout.half_height - self.character.y

    def key_tap(self, key):
        push_key(key)
        push_key(key, pico.SDL_KEYUP)

    def move_to(self, map_x, *, jump=False):
        actor = self.character
        direction = 1 if map_x > self.map_x() else -1
        key = pico.SDLK_d if direction > 0 else pico.SDLK_a
        if jump:
            yield from self.wait_until(lambda: actor.state in ('idle', 'run') and actor.grounded)
        push_key(key)
        if jump:
            push_key(pico.SDLK_SPACE)
        try:
            yield from self.wait_until(lambda: direction * (self.map_x() - map_x) >= 0)
        except AssertionError as error:
            raise AssertionError((map_x, self.map_x(), self.feet_y(),
                                  actor.state, actor.jump_phase)) from error
        push_key(key, pico.SDL_KEYUP)
        if jump:
            yield from self.wait_until(lambda: actor.grounded)
            push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield .035

    def step_to(self, x, y):
        yield from self.move_to(x, jump=True)
        assert isclose(self.feet_y(), y), (x, y, self.feet_y())

    def click_charge(self, map_x, map_y, *, blocked=False):
        actor = self.character
        layout = self.level.layout
        center = layout._point(map_x, map_y)
        candidate, = (charge for charge in self.level.charges
                      if all(abs(value - target) <= 4 for value, target in zip(charge.position, center)))
        assert candidate.active, (map_x, map_y, self.map_x(), self.feet_y())
        point = self.transform.point(*candidate.position)
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = pico.SDL_BUTTON_LEFT
        event.button.x, event.button.y = map(round, point)
        assert pico.SDL_PushEvent(event) == 1
        if blocked:
            start = self.map_x()
            yield .2
            assert not candidate.spent and abs(self.map_x() - start) < 1
            return
        try:
            yield from self.wait_until(lambda: candidate.spent)
        except AssertionError as error:
            raise AssertionError((map_x, map_y, self.map_x(), self.feet_y(), actor.state)) from error
        assert abs(self.map_x() - map_x) <= 5, (map_x, self.map_x())

    def land_at(self, feet_y):
        actor = self.character
        try:
            yield from self.wait_until(lambda: actor.grounded)
        except AssertionError as error:
            raise AssertionError((self.map_x(), feet_y, self.feet_y(), actor.state)) from error
        assert isclose(self.feet_y(), feet_y), (self.map_x(), feet_y, self.feet_y())

    def check_intake(self):
        actor = self.character
        layout = self.level.layout
        assert actor.collision_position == layout.player_start and actor.grounded
        assert layout.power_entry[0] < actor.x and layout.power_entry[1] > actor.y
        assert self.level.enemy.collision_position == layout.enemy_start
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
        self.key_tap(pico.SDLK_F6)
        yield from self.wait_until(lambda: self.engine.window_size == ALTERNATE_SIZE)
        assert layout.bounds[0] <= self.transform.bounds[0] + 1e-6
        yield 0
        assert self._pixel_size == (512, 360)
        self.key_tap(pico.SDLK_F6)
        yield from self.wait_until(lambda: self.engine.window_size == DEFAULT_SIZE)

    def check_locked_output(self):
        for x in (700, 1120, 1308):
            yield from self.move_to(x)
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: self.feet_y() < 1000)
        yield from self.move_to(1232)
        yield from self.land_at(1000)
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        push_key(pico.SDLK_a)
        yield .24
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        assert isclose(self.map_x(), 1204), self.map_x()
        self.key_tap(pico.SDLK_w)
        layout = self.level.layout
        yield from self.click_charge(1040, 934, blocked=True)
        assert not layout.power_restored and not layout.reached_output
        self.screenshot = 'locked-output'
        yield .10

    def descend_shaft(self):
        yield from self.move_to(1360)
        yield from self.land_at(1100)
        junction_camera = self.camera_center[1]
        self.screenshot = 'junction-output-and-shaft'
        yield .10
        yield from self.move_to(1421)
        yield from self.land_at(1140)
        for x, y, shot in ((1570, 1250, 'shaft-first-landing'),
                           (1460, 1370, 'shaft-second-landing'),
                           (1368, 1490, 'gallery-arrival')):
            yield from self.move_to(x)
            yield from self.land_at(y)
            self.screenshot = shot
            yield .10
        yield from self.wait_until(lambda: self.camera_center[1] < junction_camera - 250)

    def reach_transformer(self):
        layout = self.level.layout
        yield from self.move_to(1065)
        yield from self.land_at(1490)
        self.key_tap(pico.SDLK_w)
        yield .05
        assert not layout.hatch_released and not layout.power_restored
        self.screenshot = 'gallery-over-closed-hatch'
        yield .10
        for x in (650, 370):
            yield from self.move_to(x)
        yield from self.land_at(1750)
        self.screenshot = 'western-drop-turnaround'
        yield .10
        yield from self.move_to(950)
        yield from self.step_to(1065, 1620)
        assert self.power_hint.visible and self.power_hint.text == 'W  RELEASE HATCH'
        self.screenshot = 'hatch-from-below'
        yield from self.click_charge(1065, 1408, blocked=True)
        if self.hatch:
            self.key_tap(pico.SDLK_w)
            yield from self.wait_until(lambda: layout.hatch_released)
            assert not layout.power_restored
            yield from self.step_to(975, 1490)
            self.screenshot = 'hatch-gallery-reconnection'
            yield .12
            yield from self.move_to(1065)
            yield from self.land_at(1620)

    def cross_transformer(self):
        actor, enemy = self.character, self.level.enemy
        yield from self.move_to(1240)
        yield from self.land_at(1750)
        push_key(pico.SDLK_a)
        yield from self.wait_until(lambda: actor.facing == -1 and 0 < actor.x - enemy.x <= 105)
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        self.key_tap(pico.SDLK_j)
        yield from self.wait_until(lambda: enemy.hp == enemy.MAX_HP - 1)
        self.screenshot = 'transformer-sword-hit'
        yield from self.move_to(1410)
        yield from self.step_to(1530, 1750)
        yield from self.move_to(1648)
        health = actor.hp
        push_key(pico.SDLK_d)
        yield from self.wait_until(lambda: actor.hp == health - 1)
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        assert 1686 <= self.map_x() < 1848
        self.screenshot = 'live-busbar-hit'
        yield .42
        yield from self.move_to(1648)
        yield from self.click_charge(1890, 1666)
        self.screenshot = 'transformer-busbar-crossing'
        yield from self.land_at(1750)
        assert actor.hp == health - 1

    def ascend_return(self):
        lower_camera = self.camera_center[1]
        yield from self.move_to(2720)
        yield from self.step_to(2605, 1628)
        for x, y, feet in ((2580, 1325, 1388), (2580, 1074, 1142), (2730, 956, 1000)):
            yield from self.click_charge(x, y)
            self.screenshot = f'return-charge-{feet}'
            yield from self.land_at(feet)
        yield from self.move_to(2664)
        yield from self.step_to(2464, 1060)
        yield from self.move_to(2130)
        yield from self.step_to(2028, 1000)
        yield from self.move_to(1480)
        yield from self.land_at(1000)
        assert self.camera_center[1] > lower_camera + 250
        self.screenshot = 'powered-bridge-over-shaft'
        yield .12

    def exercise(self):
        actor, layout = self.character, self.level.layout
        yield from self.check_intake()
        yield from self.check_locked_output()
        yield from self.descend_shaft()
        yield from self.reach_transformer()
        yield from self.cross_transformer()
        for x in (2260, 2680):
            yield from self.move_to(x)
        assert self.power_hint.visible and self.power_hint.text == 'W  RESTORE POWER'
        assert not layout.power_restored and layout.hatch_released == self.hatch
        self.screenshot = 'relay-before-restoration'
        yield .12
        self.key_tap(pico.SDLK_w)
        yield from self.wait_until(lambda: layout.power_restored)
        yield 0
        assert not self.power_hint.visible and layout.hatch_released == self.hatch
        self.screenshot = 'relay-after-restoration'
        yield .10

        yield from self.ascend_return()
        yield from self.move_to(900)
        yield from self.wait_until(lambda: layout.reached_output)
        self.screenshot = 'output-reached'
        yield .12

        self.key_tap(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        assert not layout.reached_output and not layout.power_restored and not layout.hatch_released
        assert self.camera_center[1] == 0
        assert self.character.hp == actor.MAX_HP and self.character.collision_position == layout.player_start
        yield from self.wait_until(lambda: self.character.spawn_opacity == 1)
        self.screenshot = 'intake-after-reset'
        yield 0
        route = 'hatch opened and climbed' if self.hatch else 'hatch left closed'
        print(f'PSU SDL PASS: {route}, shaft, sword, busbar, charged climb, bridge, output, reset, F6', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--hatch', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir, hatch=args.hatch)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed
