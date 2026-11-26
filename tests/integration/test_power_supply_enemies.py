"""전원 구역 몬스터의 배치와 공유 전투 판정."""

import unittest
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

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
        self.assertGreaterEqual(len(enemies), 5)
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
