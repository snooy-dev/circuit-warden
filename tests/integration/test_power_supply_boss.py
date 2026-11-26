"""보스의 세 공격, 몸통 고도, 셔터와 재시작."""

from types import SimpleNamespace

import pico2d.pico2d as pico

from game_framework.collision import overlaps
from .test_power_supply_enemies import PowerSupplyFixture


class PowerSupplyBossTests(PowerSupplyFixture):
    def place(self, map_x, map_y):
        self.level.player.x, self.level.player.y = self.level.layout._point(map_x, map_y)

    def test_gate_requires_both_relay_and_boss_and_resets(self):
        level = self.level
        actor, layout, boss = level.player, level.layout, level.boss
        self.assertIn(layout.boss_gate, layout.closed_shutters)
        self.place(2180, 1376)
        layout.interact(actor)
        self.assertTrue(layout.power_restored)
        self.place(2256, 656)
        floor = actor.y
        self.assertLess(level.blocking_contact(actor, actor.body, (150, 0)), 1)
        actor.y += 112
        self.assertLess(level.blocking_contact(actor, actor.body, (150, 0)), 1)
        actor.y = floor
        self.assertTrue(layout.blocks_teleport(actor, *layout._point(2332, 614.5)))
        self.place(3504, 656)
        self.assertFalse(layout.check_output(actor))
        for _ in range(boss.MAX_HP):
            boss.take_hit()
        level.update(.016)
        self.assertIsNone(boss.level)
        self.assertNotIn(layout.boss_gate, layout.closed_shutters)
        self.assertTrue(layout.check_output(actor))
        self.place(2256, 656)
        self.assertIsNone(level.blocking_contact(actor, actor.body, (150, 0)))
        level.reset_combat()
        self.assertIsNot(level.boss, boss)
        self.assertEqual(level.boss.hp, boss.MAX_HP)
        self.assertIn(layout.boss_gate, layout.closed_shutters)
        self.assertFalse(layout.power_restored or layout.boss_defeated or layout.reached_output)

    def test_lash_warns_and_only_damages_its_locked_side(self):
        for face, cross in ((-1, False), (1, False), (-1, True)):
            with self.subTest(face=face, cross=cross):
                level = self.level
                level.reset_combat()
                level.finish_power_entry()
                boss, actor = level.boss, level.player
                actor.x, actor.y = boss.x + face * 137, boss.floor
                level.update(.90)
                self.assertEqual((boss.state, boss.facing, actor.hp), ('lash_windup', face, 5))
                if cross:
                    actor.x = boss.x - face * 137
                level.update(.12)
                self.assertEqual(actor.hp, 5 if cross else 4)
                self.assertEqual(boss.state, 'lash')

    def test_bolt_sweeps_player_without_pushing_into_boss_body(self):
        level = self.level
        boss, actor = level.boss, level.player
        actor.x, actor.y = boss.x - 302, boss.floor
        level.update(1.04)
        self.assertEqual((boss.state, actor.hp), ('shot_windup', 5))
        level.update(.64)
        self.assertEqual((boss.state, actor.hp, boss.last_contact_charge), ('shot', 4, 1))
        self.assertLess(actor.x, boss.x - 302)
        level.update(.26)
        self.assertEqual(actor.hp, 4)

    def test_leap_allows_underpass_then_slam_uses_marked_low_area(self):
        level = self.level
        boss, actor = level.boss, level.player
        actor.x, actor.y = boss.x - 185, boss.floor
        boss._charge_id = 2
        level.update(.4)
        self.assertEqual(boss.state, 'jump_windup')
        landing = boss.landing
        actor.x = landing - 110
        level.update(.91)
        self.assertEqual(boss.state, 'leap')
        self.assertGreater(boss.y, boss.floor + 180)
        self.assertTrue(actor.can_place_center((boss.x, actor.center[1])))
        self.assertFalse(overlaps(actor.hurt_box, boss.hurt_box))
        level.update(.44)
        self.assertEqual((boss.state, boss.x, boss.y, actor.hp), ('slam', landing, boss.floor, 4))
        self.assertEqual(boss.last_contact_charge, 3)

    def test_retreat_clears_projectile_and_keeps_damage(self):
        boss, actor = self.level.boss, self.level.player
        actor.x, actor.y = boss.x - 300, boss.floor
        self.level.update(1.19)
        self.assertIsNotNone(boss.bolt)
        boss.take_hit(1)
        self.place(872, 776)
        self.level.update(.016)
        self.assertEqual((boss.hp, boss.state, boss.bolt), (7, 'idle', None))
        self.assertIn(self.level.layout.boss_gate, self.level.layout.closed_shutters)

    def test_ground_sword_does_not_hit_boss_above_its_sweep(self):
        boss, actor = self.level.boss, self.level.player
        actor.x, actor.y = boss.x - 185, boss.floor
        boss._charge_id = 2
        self.level.update(1.27)
        self.assertEqual(boss.state, 'leap')
        actor.x, actor.facing = boss.x - 105, 1
        actor.view_bounds = self.level.layout.rooms[boss.room]
        actor.control(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_j))
        self.level.update(.016)
        self.level.update(.22)
        self.assertTrue(actor.attack_sweeps)
        self.assertEqual(boss.hp, boss.MAX_HP)
