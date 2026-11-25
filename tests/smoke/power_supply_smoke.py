"""실제 SDL 입력으로 전원 구역의 분기·복구·보스 공간·출력 동선을 검사한다."""

import argparse
import os
from ctypes import byref
from itertools import count
from math import hypot, isclose
from pathlib import Path
from unittest.mock import patch

import pico2d.pico2d as pico

from engine import Engine
from game.character import SPEED
from game.charge import CLICK_RADIUS
from game.scene import DEFAULT_SIZE, CharacterScene
from tests.smoke.character_smoke import CharacterSmoke, push_key


class PowerSupplySmoke(CharacterScene):
    capture = CharacterSmoke.capture

    def __init__(self, output_dir):
        super().__init__(power_supply=True)
        self.output_dir = output_dir
        self.elapsed = self.next_step = 0
        self.rooms = []
        self.screenshot = None
        self.passed = False

    def enter(self, engine):
        super().enter(engine)
        self.scenario = self.exercise()

    def update(self, dt):
        super().update(dt)
        self.elapsed += dt
        if not self.rooms or self.rooms[-1] != self.active_room:
            self.rooms.append(self.active_room)
        if self.elapsed >= self.next_step:
            try:
                self.next_step = self.elapsed + next(self.scenario)
            except StopIteration:
                self.passed = True
                self.engine.stop()

    def draw(self):
        super().draw()
        if self.screenshot and self.output_dir:
            self.capture(self.screenshot)
        self.screenshot = None

    @property
    def layout(self):
        return self.level.layout

    @property
    def feet(self):
        return (self.character.x + self.layout.half_width,
                self.layout.half_height - self.character.y)

    def wait_until(self, condition, *, expected, timeout=3):
        deadline = self.elapsed + timeout
        while not condition():
            assert self.elapsed < deadline, (expected, self.active_room, self.feet,
                                             self.character.state, self.rooms)
            yield 0

    def tap(self, key):
        push_key(key)
        push_key(key, pico.SDL_KEYUP)
        yield 0

    def move_to(self, x, *, jump=False):
        direction = 1 if x >= self.feet[0] else -1
        key = pico.SDLK_d if direction > 0 else pico.SDLK_a
        if jump:
            yield from self.wait_until(lambda: self.character.grounded, expected='점프 전 착지')
            push_key(pico.SDLK_SPACE)
        distance = abs(self.feet[0] - x)
        if distance > .05:
            push_key(key)
        if jump:
            yield from self.wait_until(lambda: not self.character.grounded, expected='이륙')
        if distance > .05:
            yield from self.wait_until(lambda: direction * (self.feet[0] - x) >= -.05,
                                       expected=x, timeout=max(3, distance / SPEED + 1))
            push_key(key, pico.SDL_KEYUP)
        if jump:
            yield from self.wait_until(lambda: self.character.grounded, expected='점프 후 착지')
            push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield 0

    def land_at(self, y):
        yield from self.wait_until(lambda: self.character.grounded, expected=('착지', y))
        assert isclose(self.feet[1], y, abs_tol=.01), (y, self.feet, self.active_room, tuple(self.rooms))

    def walk(self, *waypoints):
        for x, y in waypoints:
            yield from self.move_to(x)
            yield from self.land_at(y)

    def jump(self, *waypoints):
        for x, y in waypoints:
            yield from self.move_to(x, jump=True)
            yield from self.land_at(y)

    def expect_room(self, room):
        assert self.active_room == room, (room, self.active_room, self.feet, self.rooms)
        left, bottom, right, top = self.layout.rooms[room]
        cx, cy = self.camera_center
        assert left < cx < right and bottom < cy < top, (room, self.camera_center)

    def shot(self, name):
        self.screenshot = name
        yield 0

    def blocked_input(self, key):
        before = self.active_room
        push_key(key)
        yield .45
        stop = self.feet
        yield .3
        push_key(key, pico.SDL_KEYUP)
        yield 0
        assert self.active_room == before and self.feet == stop, (before, stop, self.feet)
        assert not self.layout.reached_output

    def click_charge(self, map_x, map_y, *, blocked_by_room=None):
        actor = self.character
        x, y = self.layout._point(map_x, map_y)
        charge = min(self.level.charges, key=lambda item: (
            (item.position[0] - x) ** 2 + (item.position[1] - y) ** 2))
        assert charge.active and actor.can_place_center(charge.position), (map_x, map_y, self.feet)
        if blocked_by_room:
            assert self.active_room != blocked_by_room == self.layout.room_at(charge.position)
            assert self.layout.blocks_teleport(actor, *charge.position)
            assert not actor.can_teleport(charge.position)
            assert not charge.render_items()
        else:
            assert actor.can_teleport(charge.position), (map_x, map_y, self.feet)
        output_x, output_y = self.transform.point(*charge.position)
        window_w, window_h = self.engine.window_size
        output_w, output_h = self.engine.output_size
        click = pico.SDL_Event()
        click.type = pico.SDL_MOUSEBUTTONDOWN
        click.button.button = pico.SDL_BUTTON_LEFT
        click.button.x = min(max(round(output_x * window_w / output_w), 0), window_w - 1)
        click.button.y = min(max(round(output_y * window_h / output_h), 0), window_h - 1)
        click_point = self.transform.inverse(*self.engine.window_to_output(click.button.x, click.button.y))
        assert hypot(click_point[0] - charge.position[0], click_point[1] - charge.position[1]) <= CLICK_RADIUS
        before = self.feet
        assert pico.SDL_PushEvent(byref(click)) == 1
        if blocked_by_room:
            yield .2
            assert not charge.spent and self.feet == before, (blocked_by_room, before, self.feet)
        else:
            yield from self.wait_until(lambda: charge.spent, expected=('전하 이동', map_x, map_y))
            assert isclose(actor.x, charge.position[0], abs_tol=.01)

    def check_intake(self):
        actor = self.character
        assert self.active_room == 'intake' and self.level.enemy is None
        assert actor.collision_position == self.layout.player_start and actor.grounded
        assert not self.layout.power_restored and not self.layout.reached_output
        yield from self.wait_until(lambda: actor.spawn_opacity == 1, expected='낙뢰 등장 종료')
        assert self.level.power_entry_effect is None
        yield from self.shot('intake')

    def common_route(self):
        yield from self.walk((1650, 2096))
        self.expect_room('central-distribution')
        yield from self.tap(pico.SDLK_w)
        assert not self.layout.power_restored

    def lower_route(self):
        yield from self.walk((1800, 2216), (1944, 2336), (1660, 2816))
        self.expect_room('coolant-sump')
        yield from self.walk((1158, 2816))
        self.expect_room('thermal-bank')
        yield from self.shot('thermal-bank')
        health = self.character.hp
        yield from self.jump((1048, 2696))
        yield from self.walk((306, 2816))
        assert self.character.hp == health
        self.expect_room('cooling-chimney')
        yield from self.jump((207, 2680), (303, 2568), (207, 2440), (303, 2332))
        yield from self.walk((264, 2332))
        yield from self.jump((164, 2196), (270, 2104), (184, 1960), (268, 1848), (180, 1720))
        yield from self.shot('cooling-chimney')
        yield from self.walk((143, 1720))
        yield from self.jump((72, 1608), (159, 1488))
        yield from self.walk((223, 1488))
        yield from self.jump((306, 1376))
        yield from self.walk((760, 1376))
        self.expect_room('filter-gallery')
        yield from self.walk((1630, 1376))
        assert self.rooms == ['intake', 'central-distribution', 'coolant-sump', 'thermal-bank',
                              'cooling-chimney', 'filter-gallery', 'relay-tower'], self.rooms

    def upper_route(self):
        yield from self.walk((1718, 2096))
        yield from self.jump((1900, 2096))
        yield from self.walk((3120, 2096))
        self.expect_room('capacitor-reservoir')
        yield from self.click_charge(3304, 1904)
        yield from self.land_at(1976)
        yield from self.climb_to_diagnostics()
        yield from self.shot('diagnostic-loft')

        yield from self.walk((3376, 1376))
        assert self.layout.interaction_hint(self.character) == 'W  RELEASE HATCH'
        yield from self.tap(pico.SDLK_w)
        assert self.layout.hatch_released and not self.layout.power_restored
        yield from self.walk((3196, 1976))
        self.expect_room('capacitor-reservoir')
        yield from self.climb_to_diagnostics()
        yield from self.walk((3286, 1376))
        yield from self.jump((3098, 1376))
        yield from self.walk((2810, 1376))
        assert self.rooms == [
            'intake', 'central-distribution', 'capacitor-reservoir', 'diagnostic-loft',
            'capacitor-reservoir', 'diagnostic-loft', 'relay-tower'
        ], self.rooms

    def climb_to_diagnostics(self):
        yield from self.walk((3410, 1976))
        yield from self.click_charge(3544, 1788)
        yield from self.land_at(1856)
        yield from self.walk((3650, 1856))
        yield from self.jump((3732, 1736))
        yield from self.walk((3870, 1736))
        yield from self.jump((3970, 1616))
        yield from self.jump((3880, 1496))
        yield from self.walk((3756, 1496))
        yield from self.jump((3638, 1376))
        self.expect_room('diagnostic-loft')

    def relay_to_gallery(self):
        yield from self.walk((2265, 1376))
        yield from self.jump((2175, 1256))
        yield from self.walk((2014, 1256))
        yield from self.jump((1925, 1136))
        yield from self.walk((1802, 1136))
        yield from self.jump((1711, 1016))
        yield from self.walk((1658, 1016))

    def check_unpowered_gate(self):
        yield from self.walk((2810, 1376))
        yield from self.click_charge(2912, 1310, blocked_by_room='diagnostic-loft')
        yield from self.relay_to_gallery()
        yield from self.blocked_input(pico.SDLK_a)
        self.expect_room('relay-tower')
        assert isclose(self.feet[0], 1592, abs_tol=.01) and self.feet[1] == 1016, self.feet
        yield from self.shot('locked-arena-access')
        yield from self.walk((2240, 1376))

    def check_shortcut(self):
        start = len(self.rooms)
        yield from self.walk((2640, 1616))
        self.expect_room('central-distribution')
        yield from self.walk((2450, 1736), (2260, 1856), (2050, 1976), (2212, 2096))
        yield from self.jump((2126, 1976), (2220, 1856))
        yield from self.walk((2330, 1856))
        yield from self.jump((2428, 1736))
        yield from self.walk((2552, 1736))
        yield from self.jump((2650, 1616), (2580, 1496), (2708, 1376))
        self.expect_room('relay-tower')
        yield from self.walk((2678, 1376))
        yield from self.jump((2518, 1376))
        assert self.rooms[start:] == ['central-distribution', 'relay-tower'], self.rooms

    def reach_output(self):
        yield from self.relay_to_gallery()
        yield from self.walk((1228, 1016))
        self.expect_room('filter-gallery')
        yield from self.jump((1144, 896))
        yield from self.walk((940, 896))
        yield from self.jump((872, 776))
        yield from self.jump((993, 656))
        self.expect_room('load-test-chamber')
        assert not self.layout.reached_output
        yield from self.shot('arena-entry')
        yield from self.walk((2200, 656))
        self.expect_room('load-test-chamber')
        assert not self.layout.reached_output
        yield from self.walk((self.layout.output[0] + self.layout.half_width, 656))
        self.expect_room('output-terminal')

    def exercise(self):
        for route in (self.lower_route, self.upper_route):
            yield from self.check_intake()
            self.rooms[:] = ['intake']
            start = self.elapsed
            actor = self.character
            closed = self.layout.closed_shutters
            yield from self.common_route()
            yield from route()
            self.expect_room('relay-tower')
            assert not self.layout.power_restored and not self.layout.reached_output
            yield from self.check_unpowered_gate()
            yield from self.walk((self.layout.relay[0] + self.layout.half_width, 1376))
            assert self.layout.interaction_hint(actor) == 'W  RESTORE POWER'
            yield from self.tap(pico.SDLK_w)
            assert self.layout.power_restored and self.layout.closed_shutters != closed
            assert not self.layout.reached_output and self.layout.interaction_hint(actor) is None
            yield from self.shot(f'{route.__name__}-relay')
            if route == self.lower_route:
                yield from self.check_shortcut()
            yield from self.reach_output()
            assert self.rooms[-3:] == ['filter-gallery', 'load-test-chamber', 'output-terminal'], self.rooms
            assert self.layout.reached_output and actor.hp > 0
            yield from self.shot(f'{route.__name__}-output')
            print(f'{route.__name__} ({self.elapsed - start:.2f}s SDL): {" -> ".join(self.rooms)}',
                  flush=True)
            yield from self.tap(pico.SDLK_r)
            assert self.character is not actor and self.character.hp == actor.MAX_HP
            assert self.layout.closed_shutters == closed
            assert self.active_room == 'intake'
            assert self.character.collision_position == self.layout.player_start
            assert not self.layout.power_restored and not self.layout.reached_output
            assert not self.layout.hatch_released


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--visible', action='store_true', help='실제 창을 열고 실시간으로 실행')
    args = parser.parse_args()
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir)
    engine = Engine(*DEFAULT_SIZE)
    if args.visible:
        engine.run(scene)
    else:
        os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SDL_RENDER_DRIVER='software')
        # 프레임 시작과 대기 직전에 읽는 두 시각으로 60Hz 간격을 재현한다.
        with (patch('engine.loop.perf_counter', count(0, 1 / 120).__next__),
              patch('engine.loop.sleep', lambda _: None)):
            engine.run(scene)
    assert scene.passed


if __name__ == '__main__':
    main()
