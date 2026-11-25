"""실제 SDL 입력으로 상층 우회와 하층 전투, 전원 복구와 귀환을 검증한다."""

import argparse
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from tests.smoke.character_smoke import push_key
from tests.smoke.combat_reimplementation_smoke import CombatSmoke


class PowerSupplySmoke(CombatSmoke):
    def __init__(self, output_dir, *, charge_route=False):
        super().__init__(output_dir, power_supply=True)
        self.charge_route = charge_route

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

    def click_charge(self, map_x, map_y):
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
        try:
            yield from self.wait_until(lambda: candidate.spent)
        except AssertionError as error:
            raise AssertionError((map_x, map_y, self.map_x(), self.feet_y(), actor.state)) from error
        assert abs(self.map_x() - map_x) <= 5, (map_x, self.map_x())

    def land_at(self, feet_y):
        actor = self.character
        yield from self.wait_until(lambda: actor.grounded)
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
        yield from self.move_to(464)
        yield from self.step_to(590, 1030)
        yield from self.move_to(627)
        yield from self.step_to(722, 918)
        yield from self.move_to(765)
        yield from self.step_to(868, 806)
        yield from self.click_charge(970, 626)
        yield from self.land_at(694)
        yield from self.move_to(804)
        push_key(pico.SDLK_a)
        yield .24
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        assert isclose(self.map_x(), 790), self.map_x()
        self.key_tap(pico.SDLK_w)
        yield .12
        layout = self.level.layout
        assert not layout.power_restored and not layout.reached_output
        self.screenshot = 'locked-output'
        yield .10
        yield from self.move_to(1145)
        yield from self.land_at(1140)

    def cross_upper_balcony(self):
        actor, enemy = self.character, self.level.enemy
        yield from self.step_to(1268, 1030)
        yield from self.move_to(1323)
        yield from self.step_to(1417, 930)
        self.screenshot = 'upper-route-decision'
        yield .10
        yield from self.click_charge(1610, 848)
        assert not actor.grounded
        self.screenshot = 'upper-route-first-charge'
        yield 0
        yield from self.click_charge(1815, 855)
        yield from self.land_at(930)
        self.screenshot = 'upper-route-balcony'
        yield .10
        yield from self.move_to(2260)
        yield from self.land_at(1140)
        assert actor.hp == actor.MAX_HP and enemy.hp == enemy.MAX_HP

    def touch_live_floor(self):
        actor = self.character
        yield from self.move_to(1510)
        push_key(pico.SDLK_d)
        yield from self.wait_until(lambda: actor.hp == actor.MAX_HP - 1)
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        assert self.map_x() < 1722

    def cross_lower_bay(self):
        actor, enemy = self.character, self.level.enemy
        yield from self.touch_live_floor()
        assert enemy.hp == enemy.MAX_HP
        self.screenshot = 'lower-route-live-floor-hit'
        yield .65

        yield from self.move_to(1510)
        push_key(pico.SDLK_d)
        push_key(pico.SDLK_SPACE)
        yield from self.wait_until(lambda: self.map_x() >= 1590)
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        # 선반 아래와 턱 위 사이로 대시하려면 하강할 때 눌러야 한다.
        yield from self.wait_until(lambda: actor.velocity_y < 0 and self.feet_y() >= 1000)
        push_key(pico.SDLK_LSHIFT)
        yield from self.wait_until(lambda: self.map_x() >= 1630)
        push_key(pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        self.screenshot = 'lower-route-live-floor-dash'
        yield from self.wait_until(lambda: self.map_x() >= 1745)
        push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        assert actor.hp == actor.MAX_HP - 1

        assert actor.x < enemy.x and enemy.state == 'windup', enemy.state
        yield from self.click_charge(1940, 1064)
        assert enemy.x < actor.x and not actor.grounded
        self.screenshot = 'lower-route-flank'
        yield from self.wait_until(lambda: self.feet_y() >= 1090)
        push_key(pico.SDLK_a)
        yield from self.wait_until(lambda: actor.x - enemy.x <= 110)
        push_key(pico.SDLK_j)
        push_key(pico.SDLK_a, pico.SDL_KEYUP)
        yield from self.wait_until(lambda: enemy.hp == enemy.MAX_HP - 1)
        push_key(pico.SDLK_j, pico.SDL_KEYUP)
        self.screenshot = 'lower-route-sword-hit'
        yield 0
        yield from self.click_charge(2050, 1060)
        self.screenshot = 'lower-route-retreat'
        yield .10
        assert actor.hp == actor.MAX_HP - 1
        yield from self.move_to(2260)
        yield from self.land_at(1140)

    def exercise(self):
        actor, layout = self.character, self.level.layout
        yield from self.check_intake()
        yield from self.check_locked_output()
        if self.charge_route:
            yield from self.cross_upper_balcony()
        else:
            yield from self.cross_lower_bay()
        yield from self.move_to(2470)
        assert self.power_hint.visible and not layout.power_restored
        self.screenshot = 'relay-before-restoration'
        yield .12
        self.key_tap(pico.SDLK_w)
        yield from self.wait_until(lambda: layout.power_restored)
        yield 0
        assert not self.power_hint.visible
        self.screenshot = 'relay-after-restoration'
        yield .10

        for x, y in ((2590, 1030), (2495, 918), (2574, 806), (2490, 694)):
            yield from self.step_to(x, y)
        yield from self.move_to(2060)
        yield from self.move_to(1550)
        assert actor.grounded and isclose(self.feet_y(), 694), self.feet_y()
        self.screenshot = 'powered-bridge'
        yield .10
        yield from self.move_to(1225)
        yield from self.step_to(1052, 694)
        yield from self.move_to(456)
        yield from self.wait_until(lambda: layout.reached_output)
        self.screenshot = 'output-reached'
        yield .12

        if not self.charge_route:
            yield from self.move_to(850)
            yield from self.move_to(1145)
            yield from self.land_at(1140)
            health = actor.hp
            yield from self.move_to(1630)
            self.screenshot = 'lower-route-floor-after-restoration'
            yield .80
            assert actor.hp == health

        self.key_tap(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        assert not layout.reached_output and not layout.power_restored and self.camera_center[1] == 0
        assert self.character.hp == actor.MAX_HP and self.character.collision_position == layout.player_start
        if not self.charge_route:
            yield from self.move_to(750)
            yield from self.move_to(1300)
            yield from self.touch_live_floor()
            self.screenshot = 'lower-route-floor-after-reset'
            yield 0
        route = 'upper charge chain without combat' if self.charge_route else 'lower hazard, dash, flank and sword'
        print(f'PSU SDL PASS: {route}, shutter, single relay, bridge, output, reset, F6', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--charge-route', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir, charge_route=args.charge_route)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed
