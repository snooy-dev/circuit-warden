"""전원 구역 몬스터의 배치와 공유 전투 판정."""

import unittest
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.enemy import CoolingFan, Enemy, LeakingCapacitor
from game.scene import CharacterScene, DEFAULT_SIZE
from game_framework.collision import overlaps


class PowerSupplyEnemyTests(unittest.TestCase):
    def setUp(self):
        surface = pico.SDL_CreateRGBSurfaceWithFormat(0, 800, 600, 32, pico.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface)
        self.addCleanup(pico.SDL_FreeSurface, surface)
        renderer = pico.SDL_CreateSoftwareRenderer(surface)
        self.assertTrue(renderer)
        self.addCleanup(pico.SDL_DestroyRenderer, renderer)
        self.enterContext(patch.object(pico, 'renderer', renderer, create=True))
        self.enterContext(patch.object(pico, 'canvas_height', 600, create=True))
        self.enterContext(patch.object(pico, 'window', None, create=True))
        self.enterContext(patch.object(pico, 'SDL_SetWindowTitle'))
        self.scene = CharacterScene(power_supply=True)
        self.scene.enter(Mock(reset_generation=0, output_valid=True, viewport=(0, 0, 800, 600),
                              fullscreen=False, window_size=DEFAULT_SIZE))
        self.addCleanup(self.scene.exit)
        self.level = self.scene.level
        self.level.finish_power_entry()

    def test_spawns_clear_terrain_and_controls_and_reset(self):
        level = self.level
        layout = level.layout
        enemies = tuple(level.enemies)
        self.assertEqual([type(enemy) for enemy in enemies].count(Enemy), 5)
        self.assertEqual(sum(isinstance(enemy, CoolingFan) for enemy in enemies), 2)
        self.assertEqual(sum(isinstance(enemy, LeakingCapacitor) for enemy in enemies), 2)
        self.assertNotIn(None, {enemy.room for enemy in enemies})
        self.assertFalse({'intake', 'relay-tower', 'output-terminal'} & {enemy.room for enemy in enemies})
        terrain = tuple(c.bounds for c in layout.terrain) + tuple(b for _, b in layout.devices)
        for enemy in enemies:
            with self.subTest(room=enemy.room, position=enemy.collision_position):
                left, bottom, _, top = enemy.body.bounds_at((enemy.x_limits[0], enemy.y))
                right = enemy.body.bounds_at((enemy.x_limits[1], enemy.y))[2]
                swept = (left, bottom, right, top)
                self.assertFalse(any(overlaps(swept, b) for b in (*terrain, layout.busbar)))
                self.assertEqual(layout.room_at((left, top)), enemy.room)
                self.assertEqual(layout.room_at((right, top)), enemy.room)
                if not isinstance(enemy, CoolingFan):
                    self.assertTrue(any(b[3] == bottom and b[0] <= left and right <= b[2]
                                        for b in terrain))
                if enemy.attack_body is not enemy.body:
                    pulse = enemy.attack_body.bounds_at(enemy.collision_position)
                    self.assertFalse(any(overlaps(pulse, b) for b in terrain))
        positions = [enemy.collision_position for enemy in enemies]
        first = enemies[0]
        first.take_hit()
        first.x += 10
        enemies[-1].destroy()
        level.reset_combat()
        self.assertTrue(all(enemy.level is None for enemy in enemies))
        self.assertEqual([enemy.collision_position for enemy in level.enemies], positions)
        self.assertTrue(all(enemy.hp == enemy.MAX_HP for enemy in level.enemies))
        self.assertIs(level.enemies[0].clips, first.clips)

    def test_one_swing_hits_each_eligible_enemy_once(self):
        level = self.level
        actor = level.player
        first, second = level.enemies[:2]
        second.x, second.y, second.room = first.x + 20, first.y, first.room
        actor.x, actor.y, actor.facing = first.x - 82, first.y, 1
        for enemy in (first, second):
            enemy.state, enemy.state_remaining = 'recover', 3
        event = Mock(type=pico.SDL_KEYDOWN, key=pico.SDLK_j)
        self.scene.handle_event(event)
        for _ in range(30):
            self.scene.update(1 / 60)
        self.assertEqual((first.hp, second.hp), (2, 2))
        self.assertEqual(actor.hp, actor.MAX_HP)

    def test_dust_charge_and_recoil_cannot_leave_its_lane(self):
        enemy = self.level.enemies[0]
        actor = self.level.player
        actor.x, actor.y = enemy.x, enemy.y + 110
        enemy.x = enemy.x_limits[1] - 4
        enemy.state, enemy.state_remaining, enemy.facing = 'charge', .28, 1
        enemy.update(.1)
        self.assertEqual(enemy.x, enemy.x_limits[1])
        enemy.take_hit(1)
        enemy.update(.07)
        self.assertEqual(enemy.x, enemy.x_limits[1])

    def test_fan_warns_then_crosses_fixed_lane_in_both_directions(self):
        fan = next(enemy for enemy in self.level.enemies if isinstance(enemy, CoolingFan))
        actor = self.level.player
        actor.x, actor.y = fan.x - 110, fan.y - 28
        start = fan.collision_position
        fan.update(.38)
        self.assertEqual((fan.state, fan.facing, fan.collision_position), ('windup', 1, start))
        self.assertTrue(all(charge is None for _, _, _, charge in fan.motion))
        fan.update(.74)
        self.assertEqual((fan.state, fan.x, fan.y), ('recover', fan.x_limits[1], start[1]))
        self.assertIn(1, [charge for _, _, _, charge in fan.motion])
        actor.x = fan.x - 75
        fan.update(1.77)
        self.assertEqual((fan.state, fan.x, fan.y, fan.facing),
                         ('recover', fan.x_limits[0], start[1], -1))

    def test_capacitor_discharges_outside_its_body_after_windup(self):
        level = self.level
        cap = next(enemy for enemy in level.enemies if isinstance(enemy, LeakingCapacitor))
        actor = level.player
        actor.x, actor.y = cap.x - 104, cap.y
        start = cap.collision_position
        self.assertFalse(overlaps(actor.hurt_box, cap.hurt_box))
        self.assertTrue(actor.can_place_center(actor.center))
        level.update(.81)
        self.assertEqual((cap.state, actor.hp), ('windup', actor.MAX_HP))
        level.update(.05)
        self.assertEqual((cap.state, actor.hp, cap.collision_position),
                         ('charge', actor.MAX_HP - 1, start))
        self.assertEqual(cap.last_contact_charge, 1)

    def test_pulse_can_be_jumped_and_protection_consumes_its_contact(self):
        for airborne in (True, False):
            with self.subTest(airborne=airborne):
                level = self.level
                level.reset_combat()
                level.finish_power_entry()
                cap = next(enemy for enemy in level.enemies if isinstance(enemy, LeakingCapacitor))
                actor = level.player
                actor.x, actor.y = cap.x + 80, cap.y + (84 if airborne else 0)
                cap.state, cap.state_remaining = 'windup', .01
                cap._charge_id = 1
                actor.teleport_guard_remaining = 0 if airborne else .05
                level.update(.02)
                self.assertEqual(actor.hp, actor.MAX_HP)
                self.assertEqual(cap.last_contact_charge, None if airborne else 1)
                if not airborne:
                    level.update(.1)
                    self.assertEqual(actor.hp, actor.MAX_HP)
