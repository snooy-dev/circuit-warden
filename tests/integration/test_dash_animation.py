import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GRAVITY
from game.scene import CharacterScene
from tests.integration import test_character_scene


class DashAnimationTests(unittest.TestCase):
    setUp = test_character_scene.CharacterSceneTests.setUp

    def enter_scene(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        return scene

    def key(self, scene, key, event_type=pico.SDL_KEYDOWN):
        scene.handle_event(SimpleNamespace(type=event_type, key=key))

    def effects(self, scene, direction):
        clip = scene.character.clips[f'dash_fx_{direction}']
        return [obj for obj in scene.level.objects if getattr(obj, 'player', None)
                and obj.player.clip is clip]

    def test_airborne_effect_starts_at_the_movement_boundary_and_expires_on_time(self):
        for steps in ((.1, .05), (.15,)):
            with self.subTest(steps=steps):
                scene = self.enter_scene()
                actor = scene.character
                self.key(scene, pico.SDLK_SPACE)
                scene.update(.05)
                initial_y = actor.y
                boundary_y = initial_y + actor.velocity_y * .1 - .5 * GRAVITY * .1 ** 2
                self.key(scene, pico.SDLK_LSHIFT)
                scene.update(0)
                self.assertIs(actor.player.clip, actor.clips['prepare_idle_right'])
                self.assertEqual(self.effects(scene, 'right'), [])

                for step in steps:
                    scene.update(step)
                    if step == .1:
                        self.assertEqual(actor.x, 0)
                effect, = self.effects(scene, 'right')
                self.assertIs(actor.player.clip, actor.clips['dash_right'])
                self.assertAlmostEqual(effect.player.elapsed, .05)
                self.assertAlmostEqual(actor.x, 41.5)
                origin = effect.position
                self.assertEqual(origin[0], 0)
                self.assertAlmostEqual(origin[1], boundary_y)
                self.assertLess(initial_y, origin[1])
                self.assertAlmostEqual(origin[1], actor.y)

                scene.update(.15)
                self.assertIs(actor.player.clip, actor.clips['recover_idle_right'])
                self.assertAlmostEqual(actor.x, 166)
                recovery_y = actor.y
                scene.update(.166)
                self.assertIs(effect.level, scene.level)
                self.assertAlmostEqual(effect.player.elapsed, .366)
                self.assertEqual(effect.position, origin)
                self.assertNotEqual(actor.y, recovery_y)
                self.assertAlmostEqual(actor.x, 166)
                scene.update(.001)
                self.assertIsNone(effect.level)
                self.assertEqual(actor.state, 'idle')
                self.assertAlmostEqual(actor.x, 166)

    def test_left_dash_draws_baked_direction_and_ignores_actions_through_recovery(self):
        scene = self.enter_scene()
        actor = scene.character
        self.key(scene, pico.SDLK_a)
        scene.update(.05)
        start_x = actor.x
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(0)
        self.assertIs(actor.player.clip, actor.clips['prepare_run_left'])
        scene.update(.1)
        effect, = self.effects(scene, 'left')
        self.assertEqual(effect.position, (start_x, actor.y))
        self.assertIs(actor.player.clip, actor.clips['dash_left'])
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertFalse(draw.call_args.kwargs['flip_x'])
        with patch('game.effects.draw_sprite') as draw:
            effect._draw(scene.transform, 1)
            self.assertEqual(draw.call_args.args[0].pivot, (287 / 384, 112 / 128))
            self.assertEqual(draw.call_args.args[2], effect.position)
            self.assertFalse(draw.call_args.kwargs['flip_x'])
        scene.update(.2)
        self.assertIs(actor.player.clip, actor.clips['recover_run_left'])
        self.key(scene, pico.SDLK_a, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_d)
        self.key(scene, pico.SDLK_SPACE)
        self.key(scene, pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_RSHIFT)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
        scene.update(.166)
        self.assertIs(actor.player.clip, actor.clips['recover_run_left'])
        self.assertEqual(actor.facing, -1)
        self.assertAlmostEqual(actor.x, start_x - 166)
        scene.update(.001)
        scene.update(.01)
        self.assertIs(actor.player.clip, actor.clips['run_right'])
        self.assertGreater(actor.x, start_x - 166)
        self.assertTrue(actor.grounded)

    def test_wall_uses_idle_recovery_and_scene_exit_releases_live_effect(self):
        scene = self.enter_scene()
        actor = scene.character
        self.key(scene, pico.SDLK_d)
        scene.update(3)
        edge = actor.x
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.3)
        self.assertIs(actor.player.clip, actor.clips['recover_idle_right'])
        self.assertEqual(actor.x, edge)
        effect, = self.effects(scene, 'right')
        image = effect.player.frame.image
        self.assertIs(effect.level, scene.level)
        self.assertFalse(image.closed)
        scene.exit()
        self.assertIsNone(effect.level)
        self.assertTrue(image.closed)
        self.assertEqual(scene.level.objects, ())
