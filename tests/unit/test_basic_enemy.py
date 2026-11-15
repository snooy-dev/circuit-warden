import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GROUND_Y
from game import enemy as enemy_rules
from game.scene import GameplayLevel
from game_framework import ImageRef, SpriteClip, SpriteFrame


class CombatFixture(unittest.TestCase):
    def setUp(self):
        with patch.object(pico, 'renderer', object(), create=True):
            image = ImageRef(Path('synthetic'), SimpleNamespace(w=128, h=104))
            frame = SpriteFrame(image, (0, 0, 128, 104), (.5, 92 / 104))
        idle = SpriteClip((frame,), (.5,))
        attack = SpriteClip((frame,) * 7, (.05,) * 7, loop=False)
        clips = dict(idle=idle, run_left=idle, run_right=idle, attack=attack, sword_trail=attack)
        clips.update(prepare_idle_right=SpriteClip((frame,), (.1,), loop=False),
                     dash_right=SpriteClip((frame,), (.2,), loop=False),
                     dash_fx_right=attack)
        self.level = GameplayLevel(None)
        with patch('game.scene.load_clips', return_value=clips), patch(
                'game.scene.load_enemy_frame', return_value=frame):
            self.level.open()
        self.addCleanup(self.level.close)
        self.actor = self.level.player
        self.enemy = self.level.enemy
        self.actor.view_bounds = (-500, -300, 500, 300)
        self.enemy.x = 70

    def click(self):
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.update(0)

class BasicEnemyTests(CombatFixture):
    def setUp(self):
        super().setUp()
        self.enemy.state, self.enemy.state_remaining = 'recover', 10

    def test_active_window_once_per_swing_and_removal(self):
        for hp in (2, 1, 0):
            self.click()
            self.level.update(.099)
            self.assertEqual(self.enemy.hp, hp + 1)
            self.level.update(.001)
            self.assertEqual(self.enemy.hp, hp)
            for _ in range(26):
                self.level.update(.01)
            self.assertEqual(self.enemy.hp, hp)
        self.assertIsNone(self.enemy.level)
        self.assertNotIn(self.enemy, self.level.objects)

    def test_direction_and_strict_contact_edges(self):
        for facing, x, y, expected in ((-1, -70, GROUND_Y, 2),
                                        (-1, 70, GROUND_Y, 3),
                                        (1, 127, GROUND_Y, 3),
                                        (1, 70, GROUND_Y + 70, 3)):
            with self.subTest(facing=facing, x=x, y=y):
                self.actor.facing = facing
                self.enemy.x, self.enemy.y, self.enemy.hp = x, y, 3
                self.click()
                self.level.update(.15)
                self.assertEqual(self.enemy.hp, expected)
                self.level.update(.3)

    def test_split_long_update_keeps_active_attack_snapshot(self):
        self.click()
        self.level.update(.05)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_a))
        self.level.update(.5)
        self.assertEqual(self.actor.facing, -1)
        self.assertEqual(self.enemy.hp, 2)
        self.level.update(.05)
        self.assertEqual(self.enemy.hp, 2)

    def test_inactive_attack_and_trail_cannot_hit(self):
        self.enemy.x = 220
        self.click()
        self.level.update(.2)
        self.enemy.x = 70
        self.level.update(.01)
        self.level.update(.3)
        self.assertEqual(self.enemy.hp, 3)



class EnemyChargeTests(CombatFixture):
    def start_charge(self):
        self.level.update(enemy_rules.IDLE_SECONDS)
        self.level.update(.01)
        self.assertEqual(self.enemy.state, 'windup')
        self.level.update(self.enemy.state_remaining)
        self.assertEqual(self.enemy.state, 'charge')

    def test_approach_then_locks_charge_direction_during_windup(self):
        self.enemy.x = 220
        self.level.update(enemy_rules.IDLE_SECONDS + .1)
        self.assertEqual(self.enemy.state, 'approach')
        self.assertLess(self.enemy.x, 220)
        self.level.update(1.4)
        self.assertEqual((self.enemy.state, self.enemy.facing), ('windup', -1))
        self.assertAlmostEqual(self.enemy.x, enemy_rules.WINDUP_RANGE)
        self.assertEqual(self.actor.hp, 5)
        self.actor.x = 150
        self.level.update(self.enemy.state_remaining + .1)
        self.assertEqual((self.enemy.state, self.enemy.facing), ('charge', -1))
        self.assertLess(self.enemy.x, enemy_rules.WINDUP_RANGE)
        self.assertEqual(self.actor.hp, 5)

    def test_swept_charge_hits_once_and_leaves_recovery(self):
        self.start_charge()
        self.level.update(.14)
        self.assertEqual(self.actor.hp, 4)
        self.assertAlmostEqual(self.actor.invulnerability_remaining, .75 - (.14 - 4 / 350))
        self.actor.invulnerability_remaining = 0
        self.level.update(.16)
        self.assertEqual((self.enemy.state, self.actor.hp), ('recover', 4))

    def test_dash_movement_does_not_prevent_charge_damage(self):
        self.start_charge()
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_LSHIFT))
        self.level.update(.14)
        self.assertEqual((self.actor.state, self.actor.dash_phase), ('dash', 'dash'))
        self.assertEqual(self.actor.hp, 4)

    def test_long_update_reaches_charge_but_height_can_avoid_it(self):
        for airborne, expected_hp in ((True, 5), (False, 4)):
            with self.subTest(airborne=airborne):
                self.level.reset_combat()
                self.actor, self.enemy = self.level.player, self.level.enemy
                self.enemy.x = 70
                if airborne:
                    self.actor.y += 79
                with patch.object(self.actor, 'update'):
                    self.level.update(enemy_rules.IDLE_SECONDS + enemy_rules.WINDUP_SECONDS
                                      + enemy_rules.CHARGE_SECONDS + .05)
                self.assertEqual((self.enemy.state, self.actor.hp), ('recover', expected_hp))

    def test_player_protection_expires_and_dead_player_can_reset(self):
        self.click()
        self.actor.take_hit()
        self.actor.take_hit()
        self.assertEqual(self.actor.hp, 4)
        self.actor.update(.75)
        self.actor.take_hit()
        self.assertEqual(self.actor.hp, 3)
        for _ in range(4):
            self.actor.invulnerability_remaining = 0
            self.actor.take_hit()
        self.assertEqual(self.actor.hp, 0)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_d))
        self.level.update(3)
        self.assertEqual((self.enemy.state, self.actor.x, self.actor.pressed), ('idle', 0, set()))

        reset = SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_r)
        self.level.handle_event(reset)
        player, enemy = self.level.player, self.level.enemy
        self.assertEqual((player.hp, player.x, enemy.hp, enemy.x), (5, 0, 3, 220))
        self.assertIsNone(self.actor.level)
        self.assertIsNone(self.enemy.level)
        self.assertEqual(len(self.level.objects), 3)
        self.level.handle_event(reset)
        self.assertIs(self.level.player, player)
        self.assertIs(self.level.enemy, enemy)

    def test_sword_hits_enemy_leaving_during_active_window(self):
        self.start_mid_swing()
        self.enemy.x, self.enemy.facing = 110, 1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 2)

    def test_buffer_split_preserves_contact_in_first_substep(self):
        self.enemy.x = 220
        self.enemy.state, self.enemy.state_remaining = 'recover', 10
        self.click()
        self.level.update(.04)
        self.level.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT))
        self.level.update(.07)
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = 110, 1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 2)

    def test_enemy_entering_at_sword_window_end_is_not_hit(self):
        self.start_mid_swing()
        self.enemy.x, self.enemy.facing = 144.5, -1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 3)

    def test_enemy_entering_after_sword_active_window_is_not_hit(self):
        self.start_mid_swing()
        self.enemy.x, self.enemy.facing = 152, -1
        self.level.update(.1)
        self.assertEqual(self.enemy.hp, 3)

    def start_mid_swing(self):
        self.enemy.x = 220
        self.enemy.state, self.enemy.state_remaining = 'recover', 10
        self.click()
        self.level.update(.15)
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS

    def test_charge_contact_ending_before_protection_expires_is_not_hit(self):
        self.actor.invulnerability_remaining = .05
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = -65, -1
        self.level.update(.1)
        self.assertEqual(self.actor.hp, 5)

    def test_charge_can_hit_warden_before_the_warden_moves_away(self):
        self.enemy.state, self.enemy.state_remaining = 'charge', enemy_rules.CHARGE_SECONDS
        self.enemy.x, self.enemy.facing = 0, 1
        self.actor.x = 20
        with patch.object(self.actor, 'update', side_effect=lambda dt: setattr(self.actor, 'x', 103)):
            self.level.update(.1)
        self.assertEqual(self.actor.hp, 4)

    def test_lethal_sword_hit_prevents_same_frame_charge_damage(self):
        self.start_charge()
        self.enemy.hp = 1
        self.click()
        self.level.update(.15)
        self.assertIsNone(self.enemy.level)
        self.assertEqual(self.actor.hp, 5)
