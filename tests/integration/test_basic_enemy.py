"""실제 적 PNG와 기존 공격 시트의 전투 연결·수명 검사."""

import ctypes
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

from game.scene import CharacterScene, DEFAULT_SIZE


class BasicEnemySceneTests(unittest.TestCase):
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
        self.app = Mock(reset_generation=0, output_valid=True, viewport=(0, 0, 800, 600),
                        fullscreen=False, window_size=DEFAULT_SIZE)

    def pixels(self):
        pixels = (ctypes.c_ubyte * (800 * 600 * 4))()
        self.assertEqual(pico.SDL_RenderReadPixels(pico.renderer, None,
                                                  pico.SDL_PIXELFORMAT_RGBA32, pixels, 800 * 4), 0)
        return bytes(pixels)

    def test_real_sprite_draws_both_directions_and_releases_texture(self):
        previous = None
        for facing in (-1, 1):
            scene = CharacterScene()
            scene.enter(self.app)
            try:
                enemy = scene.level.enemy
                image = enemy.frame.image
                self.assertIsNot(image, previous)
                self.assertEqual(enemy.frame.rect, (0, 0, 128, 96))
                self.assertEqual(enemy.frame.pivot, (76 / 128, 80 / 96))
                enemy.facing = facing
                scene.update(0)
                pico.SDL_SetRenderDrawColor(pico.renderer, 20, 30, 40, 255)
                pico.SDL_RenderClear(pico.renderer)
                with patch.object(enemy, 'render_items', return_value=()):
                    scene.draw()
                without_enemy = self.pixels()
                scene.draw()
                self.assertNotEqual(self.pixels(), without_enemy)
                self.assertEqual(sum(obj is enemy for obj in scene.level.objects), 1)
            finally:
                scene.exit()
            self.assertTrue(image.closed)
            self.assertEqual(scene.level.objects, ())
            previous = image

    def test_real_attack_sheet_hits_three_times_in_both_directions(self):
        for facing in (-1, 1):
            scene = CharacterScene()
            scene.enter(self.app)
            try:
                actor, enemy = scene.character, scene.level.enemy
                actor.x = enemy.x - facing * 60
                actor.facing = facing
                with patch.object(enemy, 'update'):
                    scene.update(0)
                    for hp in (2, 1, 0):
                        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                           button=pico.SDL_BUTTON_LEFT))
                        scene.update(0)
                        scene.update(.15)
                        self.assertEqual(enemy.hp, hp)
                        scene.update(.02)
                        self.assertEqual(enemy.hp, hp)
                        scene.update(.23)
                self.assertIsNone(enemy.level)
                self.assertNotIn(enemy, scene.level.objects)
            finally:
                scene.exit()
