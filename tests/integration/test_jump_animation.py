import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GROUND_Y, JUMP_HEIGHT
from game.scene import CharacterScene
from tests.integration import test_character_scene


class JumpAnimationTests(unittest.TestCase):
    setUp = test_character_scene.CharacterSceneTests.setUp

    def scene(self):
        scene = CharacterScene()
        scene.enter(self.app)
        self.addCleanup(scene.exit)
        scene.update(0)
        return scene

    def key(self, scene, symbol, kind=pico.SDL_KEYDOWN):
        scene.handle_event(SimpleNamespace(type=kind, key=symbol))

    def test_real_assets_and_start_air_land_locks(self):
        scene = self.scene()
        actor = scene.character
        for direction, x in (('left', 63), ('right', 64)):
            for phase, count, duration in (('start', 12, .2), ('rise', 18, .3),
                                            ('fall', 36, .6), ('land', 18, .3)):
                clip = actor.clips[f'jump_{phase}_{direction}']
                self.assertEqual(len(clip.frames), count)
                self.assertAlmostEqual(sum(clip.durations), duration)
                self.assertEqual(clip.loop, phase == 'fall')
                self.assertEqual(clip.frames[0].pivot, (x / 128, 92 / 104))
        self.key(scene, pico.SDLK_d)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.1)
        self.assertEqual((actor.x, actor.y), (0, GROUND_Y))
        self.assertIs(actor.player.clip, actor.clips['jump_start_right'])
        self.key(scene, pico.SDLK_LSHIFT)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
        scene.update(.1)
        self.assertEqual(actor.jump_phase, 'rise')
        self.assertEqual(actor.x, 0)
        scene.update(.2)
        self.assertEqual(actor.x, 36)
        self.assertIs(actor.player.clip, actor.clips['jump_rise_right'])
        self.assertAlmostEqual(actor.player.elapsed, .15)
        self.key(scene, pico.SDLK_d, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_a)
        scene.update(.2)
        self.assertAlmostEqual(actor.y - GROUND_Y, JUMP_HEIGHT)
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertFalse(draw.call_args.kwargs['flip_x'])
        scene.update(.4)
        self.assertTrue(actor.grounded)
        self.assertIs(actor.player.clip, actor.clips['jump_land_left'])
        x = actor.x
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
        scene.update(.299)
        self.assertEqual(actor.x, x)
        self.assertEqual(actor.state, 'jump')
        scene.update(.001)
        self.assertNotEqual(actor.state, 'jump')
        scene.update(.01)
        self.assertTrue(actor.grounded)
        self.assertLess(actor.x, x)

    def test_jump_boundaries_preserve_height_and_horizontal_distance_across_dt(self):
        outcomes = []
        for steps in ((1.3,), (.1,) * 13):
            scene = self.scene()
            self.key(scene, pico.SDLK_d)
            self.key(scene, pico.SDLK_SPACE)
            for dt in steps:
                scene.update(dt)
            actor = scene.character
            self.assertTrue(actor.grounded)
            self.assertIsNone(actor.jump_phase)
            self.assertAlmostEqual(actor.x, 144)
            outcomes.append((actor.x, actor.y))
        self.assertAlmostEqual(outcomes[0][0], outcomes[1][0])

    def test_dash_returns_to_current_fall_and_focus_does_not_cancel_started_jump(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.55)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.467)
        self.assertEqual(actor.state, 'jump')
        self.assertEqual(actor.jump_phase, 'fall')
        self.assertIs(actor.player.clip, actor.clips['jump_fall_right'])
        scene.handle_event(SimpleNamespace(type=pico.SDL_WINDOWEVENT,
                                          event=pico.SDL_WINDOWEVENT_FOCUS_LOST))
        scene.update(.183)
        self.assertTrue(actor.grounded)
        self.assertIs(actor.player.clip, actor.clips['jump_land_right'])
        scene.update(.3)
        self.assertEqual(actor.state, 'idle')
        self.assertFalse(actor.pressed)

    def test_landing_during_dash_waits_for_dash_and_keeps_landing_direction(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.9)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.15)
        self.assertTrue(actor.grounded)
        self.key(scene, pico.SDLK_a)
        scene.update(.35)
        self.assertEqual(actor.jump_phase, 'land')
        self.assertAlmostEqual(actor.jump_elapsed, .033)
        self.assertEqual(actor.facing, 1)
        self.assertIs(actor.player.clip, actor.clips['jump_land_right'])
        x = actor.x
        scene.update(.266)
        self.assertEqual(actor.x, x)
        scene.update(.001)
        scene.update(.01)
        self.assertLess(actor.x, x)
