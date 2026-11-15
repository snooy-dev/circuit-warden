import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GROUND_Y
from game.scene import GameplayLevel
from game_framework import ImageRef, SpriteClip, SpriteFrame


class BasicEnemyTests(unittest.TestCase):
    def setUp(self):
        with patch.object(pico, 'renderer', object(), create=True):
            image = ImageRef(Path('synthetic'), SimpleNamespace(w=128, h=104))
            frame = SpriteFrame(image, (0, 0, 128, 104), (.5, 92 / 104))
        idle = SpriteClip((frame,), (.5,))
        attack = SpriteClip((frame,) * 7, (.05,) * 7, loop=False)
        clips = dict(idle=idle, run_left=idle, run_right=idle, attack=attack, sword_trail=attack)
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
                                        (1, 115, GROUND_Y, 3),
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
