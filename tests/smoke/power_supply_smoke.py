"""실제 SDL 입력으로 전원 구역의 상·하층 탐색, 복구와 귀환을 검증한다."""

import argparse
from ctypes import c_ubyte
from math import isclose
from pathlib import Path

import pico2d.pico2d as pico

from engine import Engine
from game.character import SPEED
from game.enemy import Enemy
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from tests.smoke.character_smoke import push_key
from tests.smoke.combat_reimplementation_smoke import CombatSmoke


class PowerSupplySmoke(CombatSmoke):
    def __init__(self, output_dir, *, upper=False, hatch=False):
        super().__init__(output_dir, power_supply=True)
        self.upper = upper
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
        deadline = self.elapsed + max(3, abs(map_x - self.map_x()) / SPEED + 1)
        while direction * (self.map_x() - map_x) < 0:
            assert self.elapsed < deadline, (map_x, self.map_x(), self.feet_y(),
                                             actor.state, actor.jump_phase)
            yield 0
        push_key(key, pico.SDL_KEYUP)
        if jump:
            yield from self.wait_until(lambda: actor.grounded)
            push_key(pico.SDLK_SPACE, pico.SDL_KEYUP)
        yield .035

    def step_to(self, x, y):
        yield from self.move_to(x, jump=True)
        assert isclose(self.feet_y(), y), (x, y, self.feet_y())

    def click_charge(self, map_x, map_y, *, blocked=False, at_room_edge=False):
        actor = self.character
        layout = self.level.layout
        center = layout._point(map_x, map_y)
        candidate, = (charge for charge in self.level.charges
                      if all(abs(value - target) <= 4 for value, target in zip(charge.position, center)))
        assert candidate.active, (map_x, map_y, self.map_x(), self.feet_y())
        point = self.transform.point(*candidate.position)
        output_w, output_h = self.engine.output_size
        window_w, window_h = self.engine.window_size
        window_x, window_y = point[0] * window_w / output_w, point[1] * window_h / output_h
        if at_room_edge:
            assert actor.can_place_center(candidate.position)
            assert layout.blocks_teleport(actor, *candidate.position)
            assert not candidate.render_items()
            assert window_w <= window_x < window_w + 40, window_x
            window_x = window_w - 1
        event = pico.SDL_Event()
        event.type = pico.SDL_MOUSEBUTTONDOWN
        event.button.button = pico.SDL_BUTTON_LEFT
        event.button.x, event.button.y = round(window_x), round(window_y)
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

    def capture(self, name):
        _, bottom, _, top = self.level.layout.rooms[self.active_room]
        if top - bottom < self.view_height:
            width, height = self.engine.output_size
            rgba = (c_ubyte * 4)()
            for y in (5, height - 6):
                rect = pico.SDL_Rect(width // 2, y, 1, 1)
                assert pico.SDL_RenderReadPixels(pico.renderer, rect, pico.SDL_PIXELFORMAT_RGBA32,
                                                 rgba, 4) == 0
                assert tuple(rgba[:3]) == (0, 0, 0), (name, y, tuple(rgba))
        super().capture(name)

    def check_room_view(self, room, *, wall=None, tolerance=1e-6):
        assert self.active_room == room, (self.active_room, room, self.character.center)
        left, bottom, right, top = self.level.layout.rooms[room]
        view_left, view_bottom, view_right, view_top = self.transform.bounds
        assert left <= view_left + 1e-6 and right >= view_right - 1e-6, (
            room, self.transform.bounds, (left, bottom, right, top))
        if top - bottom >= self.view_height:
            assert bottom <= view_bottom + 1e-6 and top >= view_top - 1e-6, (
                room, self.transform.bounds, (left, bottom, right, top))
        else:
            assert isclose(view_bottom + view_top, bottom + top, abs_tol=1e-6), room
        if wall == 'left':
            assert isclose(view_left, left, abs_tol=tolerance), (room, view_left, left)
        if wall == 'right':
            assert isclose(view_right, right, abs_tol=tolerance), (room, view_right, right)

    def cross_room(self, edge_x, origin, destination, feet_y, *, east, block_charge=None):
        direction = 1 if east else -1
        exit_wall, entry_wall = ('right', 'left') if east else ('left', 'right')
        key = pico.SDLK_d if east else pico.SDLK_a
        yield from self.move_to(edge_x - direction * 65)
        yield from self.land_at(feet_y)
        yield .65
        self.check_room_view(origin, wall=exit_wall, tolerance=6)
        self.screenshot = f'doorway-{origin}-{exit_wall}'
        yield 0
        if block_charge is not None:
            yield from self.click_charge(*block_charge, blocked=True, at_room_edge=True)
            assert self.active_room == origin

        push_key(key)
        for _ in self.wait_until(lambda: self.map_x() >= edge_x if east else self.map_x() < edge_x):
            self.check_room_view(origin, wall=exit_wall, tolerance=6)
            yield 0
        self.check_room_view(destination, wall=entry_wall)
        self.screenshot = f'doorway-{destination}-entered-{entry_wall}'
        yield from self.wait_until(lambda: direction * (self.map_x() - edge_x) >= 65)
        push_key(key, pico.SDL_KEYUP)
        yield .035
        yield from self.land_at(feet_y)

    def check_intake(self):
        actor = self.character
        layout = self.level.layout
        assert actor.collision_position == layout.player_start and actor.grounded
        assert layout.power_entry[0] < actor.x and layout.power_entry[1] > actor.y
        assert all(not isinstance(obj, Enemy) for obj in self.level.objects)
        self.check_room_view('service-core', wall='left')
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
        self.check_room_view('service-core')
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
        actor = self.character
        yield from self.move_to(1160)
        yield from self.land_at(1750)
        yield from self.move_to(1648)
        yield from self.land_at(1750)
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

    def reach_lower_capacitors(self):
        yield from self.cross_room(3440, 'service-core', 'heat-exchangers', 1750, east=True,
                                   block_charge=(3460, 1690))
        yield from self.cross_room(3440, 'heat-exchangers', 'service-core', 1750, east=False)
        yield from self.cross_room(3440, 'service-core', 'heat-exchangers', 1750, east=True)
        yield from self.move_to(3675)
        yield from self.step_to(3770, 1650)
        yield from self.move_to(3955)
        yield from self.step_to(4040, 1550)
        yield from self.move_to(4380)
        yield from self.land_at(1640)
        yield from self.move_to(4600)
        yield from self.land_at(1750)

        yield from self.cross_room(4880, 'heat-exchangers', 'capacitor-reservoir', 1750, east=True)
        yield from self.move_to(5260)
        yield from self.step_to(5465, 1750)
        yield from self.move_to(5625)
        yield from self.step_to(5720, 1670)

    def cross_lower_filter(self):
        yield from self.move_to(6070)
        yield from self.land_at(1750)

        yield from self.cross_room(6320, 'capacitor-reservoir', 'filter-gallery', 1750, east=True)
        yield from self.move_to(6545)
        yield from self.step_to(6640, 1630)
        yield from self.move_to(6739)
        yield from self.step_to(6840, 1540)
        yield from self.move_to(7090)
        yield from self.land_at(1650)
        yield from self.move_to(7189)
        yield from self.step_to(7280, 1570)
        yield from self.move_to(7480)
        yield from self.land_at(1694)
        yield from self.move_to(7610)
        yield from self.land_at(1750)

    def climb_capacitor_shaft(self):
        lower_camera = self.camera_center[1]
        self.check_room_view('capacitor-reservoir')
        for x, y in ((5810, 1550), (5940, 1430), (5810, 1310), (5940, 1190), (5810, 1070)):
            yield from self.step_to(x, y)
        self.check_room_view('return-capacitors')
        assert self.camera_center[1] > lower_camera + 250 and not self.level.layout.power_restored
        self.screenshot = 'unpowered-capacitor-shaft-ascent'
        yield 0

    def descend_capacitor_shaft(self):
        upper_camera = self.camera_center[1]
        for x, y in ((5940, 1190), (5810, 1310), (5940, 1430), (5810, 1550), (5720, 1670)):
            yield from self.move_to(x)
            yield from self.land_at(y)
        self.check_room_view('capacitor-reservoir')
        assert self.camera_center[1] < upper_camera - 250 and not self.level.layout.power_restored
        self.screenshot = 'unpowered-capacitor-shaft-descent'
        yield 0

    def reach_relay(self):
        yield from self.cross_room(7760, 'filter-gallery', 'relay-tower', 1750, east=True)
        yield from self.move_to(8450)

    def reach_upper_capacitors(self):
        layout = self.level.layout
        yield from self.click_charge(1480, 938)
        yield from self.click_charge(1730, 930)
        yield from self.land_at(1000)
        assert not layout.power_restored
        self.screenshot = 'unpowered-upper-bridge-crossing'
        yield 0
        yield from self.move_to(2240)
        yield from self.land_at(1060)
        yield from self.move_to(2455)
        yield from self.click_charge(2730, 956)
        yield from self.land_at(1000)
        yield from self.cross_room(3440, 'service-core', 'return-exchangers', 1000, east=True)
        yield from self.move_to(3645)
        yield from self.step_to(3750, 970)
        yield from self.move_to(3940)
        yield from self.step_to(4130, 1030)
        yield from self.move_to(4375)
        yield from self.step_to(4460, 910)
        yield from self.move_to(4740)
        yield from self.land_at(1000)
        yield from self.cross_room(4880, 'return-exchangers', 'return-capacitors', 1000, east=True)

    def explore_service_loft(self):
        yield from self.move_to(5210)
        yield from self.step_to(5340, 920)
        yield from self.click_charge(5552, 730)
        yield from self.land_at(795)
        yield from self.step_to(5390, 670)
        yield from self.step_to(5225, 660)
        self.screenshot = 'unpowered-service-loft'
        yield from self.cross_room(4880, 'diagnostic-loft', 'return-exchangers', 660, east=False)
        yield from self.move_to(4700)
        yield from self.land_at(1000)
        assert not self.level.layout.power_restored
        yield from self.cross_room(4880, 'return-exchangers', 'return-capacitors', 1000, east=True)

    def reach_upper_filters(self):
        yield from self.move_to(5210)
        yield from self.step_to(5340, 920)
        yield from self.move_to(5545)
        yield from self.land_at(1020)
        yield from self.move_to(5835)
        yield from self.land_at(1070)
        yield from self.click_charge(6045, 935)
        yield from self.land_at(1000)
        yield from self.cross_room(6320, 'return-capacitors', 'return-filters', 1000, east=True)
        yield from self.move_to(6545)
        yield from self.step_to(6640, 915)
        yield from self.move_to(7005)
        yield from self.land_at(970)
        yield from self.step_to(7130, 910)

    def descend_filter_chute(self):
        layout = self.level.layout
        yield from self.move_to(7690)
        yield from self.land_at(1000)
        push_key(pico.SDLK_d)
        yield .35
        push_key(pico.SDLK_d, pico.SDL_KEYUP)
        assert isclose(self.map_x(), 7696), self.map_x()
        self.key_tap(pico.SDLK_w)
        yield .05
        assert not layout.power_restored
        self.screenshot = 'unpowered-tower-shutter'
        yield 0
        self.check_room_view('return-filters')
        upper_camera = self.camera_center[1]
        self.screenshot = 'unpowered-filter-chute-entry'
        yield from self.move_to(7460)
        yield from self.land_at(1694)
        self.check_room_view('filter-gallery')
        assert self.camera_center[1] < upper_camera - 250 and not layout.power_restored
        self.screenshot = 'unpowered-filter-chute-landing'
        yield from self.move_to(7610)
        yield from self.land_at(1750)

    def ascend_return(self):
        lower_camera = self.camera_center[1]
        for x, y, feet in ((8595, 1565, 1630), (8590, 1324, 1390), (8415, 1204, 1270),
                           (8230, 1074, 1140), (8000, 934, 1000)):
            yield from self.click_charge(x, y)
            self.screenshot = f'return-charge-{feet}'
            yield from self.land_at(feet)
        yield from self.wait_until(lambda: self.camera_center[1] > lower_camera + 250)

    def return_to_core(self):
        yield from self.cross_room(7760, 'relay-tower', 'return-filters', 1000, east=False)
        yield from self.move_to(7506)
        yield from self.step_to(7360, 910)
        yield from self.move_to(6970)
        yield from self.land_at(970)
        yield from self.move_to(6805)
        yield from self.step_to(6690, 915)
        yield from self.move_to(6500)
        yield from self.land_at(1000)

        yield from self.cross_room(6320, 'return-filters', 'return-capacitors', 1000, east=False)
        yield from self.move_to(6004)
        yield from self.step_to(5820, 1070)
        yield from self.move_to(5775)
        yield from self.step_to(5650, 1020)
        yield from self.move_to(5535)
        yield from self.step_to(5410, 920)
        yield from self.move_to(5200)
        yield from self.land_at(1000)

        yield from self.cross_room(4880, 'return-capacitors', 'return-exchangers', 1000, east=False)
        yield from self.move_to(4645)
        yield from self.step_to(4520, 910)
        yield from self.move_to(4250)
        yield from self.land_at(1030)
        yield from self.move_to(4125)
        yield from self.step_to(3950, 970)
        yield from self.move_to(3600)
        yield from self.land_at(1000)
        yield from self.cross_room(3440, 'return-exchangers', 'service-core', 1000, east=False)

        yield from self.move_to(2664)
        yield from self.step_to(2464, 1060)
        yield from self.move_to(2130)
        yield from self.step_to(2028, 1000)
        yield from self.move_to(1480)
        yield from self.land_at(1000)
        self.screenshot = 'powered-bridge-over-shaft'
        yield .12

    def exercise(self):
        actor, layout = self.character, self.level.layout
        yield from self.check_intake()
        yield from self.check_locked_output()
        if self.upper:
            yield from self.reach_upper_capacitors()
            yield from self.explore_service_loft()
            yield from self.reach_upper_filters()
            yield from self.descend_filter_chute()
        else:
            yield from self.descend_shaft()
            yield from self.reach_transformer()
            yield from self.cross_transformer()
            yield from self.reach_lower_capacitors()
            yield from self.climb_capacitor_shaft()
            yield from self.descend_capacitor_shaft()
            yield from self.cross_lower_filter()
        yield from self.reach_relay()
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
        yield from self.return_to_core()
        yield from self.move_to(900)
        yield from self.wait_until(lambda: layout.reached_output)
        self.screenshot = 'output-reached'
        yield .12

        self.key_tap(pico.SDLK_r)
        yield from self.wait_until(lambda: self.character is not actor)
        assert not layout.reached_output and not layout.power_restored and not layout.hatch_released
        assert layout.half_height - self.camera_center[1] == 960
        self.check_room_view('service-core', wall='left')
        assert all(not isinstance(obj, Enemy) for obj in self.level.objects)
        assert self.character.hp == actor.MAX_HP and self.character.collision_position == layout.player_start
        yield from self.wait_until(lambda: self.character.spawn_opacity == 1)
        self.screenshot = 'intake-after-reset'
        yield 0
        route = ('upper bridge crossing, service loft and filter chute' if self.upper
                 else 'lower busbar and bidirectional capacitor shaft')
        hatch = 'hatch opened and climbed' if self.hatch else 'hatch left closed'
        print(f'PSU SDL PASS: {route}, {hatch}, doorway cameras and masks, relay, '
              'charged tower climb, powered bridge, output, enemy-free reset, F6', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    route = parser.add_mutually_exclusive_group()
    route.add_argument('--upper', action='store_true')
    route.add_argument('--hatch', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = PowerSupplySmoke(args.output_dir, upper=args.upper, hatch=args.hatch)
    Engine(*DEFAULT_SIZE).run(scene)
    assert scene.passed
