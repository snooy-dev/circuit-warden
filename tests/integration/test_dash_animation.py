import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GRAVITY, SPEED
from game.scene import CharacterScene
from game.training_map import LOW_WALL, WALLS
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

    def test_air_dash_switches_sheet_frames_at_the_movement_boundary(self):
        for steps in ((.1, .05), (.15,)):
            with self.subTest(steps=steps):
                scene = self.enter_scene()
                actor = scene.character
                self.key(scene, pico.SDLK_SPACE)
                scene.update(.12)  # Finish the ground startup before entering the air dash.
                scene.update(.05)
                initial_y = actor.y
                boundary_y = initial_y + actor.velocity_y * .1 - .5 * GRAVITY * .1 ** 2
                self.key(scene, pico.SDLK_LSHIFT)
                scene.update(0)
                self.assertIs(actor.player.clip, actor.clips['air_prepare_right'])
                self.assertIs(actor.player.frame, actor.clips['air-dash'].frames[0])
                objects = scene.level.objects

                for step in steps:
                    scene.update(step)
                    if step == .1:
                        self.assertEqual(actor.x, 0)
                self.assertIs(actor.player.clip, actor.clips['air_dash_right'])
                self.assertIn(actor.player.frame, actor.clips['air-dash'].frames[2:])
                self.assertAlmostEqual(actor.player.elapsed, .05)
                self.assertAlmostEqual(actor.x, 41.5)
                self.assertAlmostEqual(actor.y, boundary_y)

                scene.update(.15)
                self.assertIs(actor.player.clip, actor.clips['recover_idle_right'])
                self.assertAlmostEqual(actor.x, 166)
                recovery_y = actor.y
                scene.update(.166)
                self.assertEqual(scene.level.objects, objects)
                self.assertNotEqual(actor.y, recovery_y)
                self.assertAlmostEqual(actor.x, 166)
                scene.update(.001)
                self.assertEqual(actor.state, 'jump')
                self.assertEqual(actor.jump_phase, 'fall')
                self.assertAlmostEqual(actor.x, 166)

    def test_left_dash_mirrors_the_body_and_early_recovery_actions_expire(self):
        scene = self.enter_scene()
        actor = scene.character
        self.key(scene, pico.SDLK_a)
        scene.update(.05)
        start_x = actor.x
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(0)
        self.assertIs(actor.player.clip, actor.clips['prepare_run_left'])
        scene.update(.1)
        self.assertIs(actor.player.clip, actor.clips['dash_left'])
        self.assertIs(actor.player.frame.image, actor.clips['ground-dash'].frames[0].image)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        scene.update(.2)
        self.assertIs(actor.player.clip, actor.clips['recover_run_left'])
        self.key(scene, pico.SDLK_a, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_d)
        self.key(scene, pico.SDLK_SPACE)
        self.key(scene, pico.SDLK_LSHIFT, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_RSHIFT)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        scene.update(.166)
        self.assertIs(actor.player.clip, actor.clips['recover_run_left'])
        self.assertEqual(actor.facing, -1)
        self.assertAlmostEqual(actor.x, start_x - 166)
        scene.update(.001)
        scene.update(.01)
        self.assertIs(actor.player.clip, actor.clips['run_right'])
        self.assertGreater(actor.x, start_x - 166)
        self.assertTrue(actor.grounded)

    def test_dash_from_wall_stops_outward_and_moves_inward(self):
        for edge_direction in (-1, 1):
            for inward in (False, True):
                scene = self.enter_scene()
                actor = scene.character
                scene.update(0)
                actor.x = (WALLS[1][0] - actor.body.bounds[2] if edge_direction > 0
                           else WALLS[0][2] - actor.body.bounds[0])
                actor.facing = -edge_direction if inward else edge_direction
                start = actor.x
                self.key(scene, pico.SDLK_LSHIFT)
                scene.update(.1)
                scene.update(.2)
                if inward:
                    self.assertAlmostEqual(actor.x, start - edge_direction * 166)
                else:
                    self.assertEqual(actor.x, start)
                    self.assertEqual(actor.dash_phase, 'recover_idle')

    def test_ground_dash_run_recovery_displays_sprint_at_normal_move_speed(self):
        scene = self.enter_scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_a)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.467)
        self.assertEqual(actor.state, 'run')
        self.assertAlmostEqual(actor.x, -166)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertIs(draw.call_args.args[0], actor.clips['sprint'].frames[0])
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        scene.update(.1)
        self.assertAlmostEqual(actor.x, -166 - SPEED * .1)

    def test_near_wall_uses_idle_recovery_and_scene_exit_releases_dash_sheet(self):
        scene = self.enter_scene()
        scene.level.enemy.destroy()
        actor = scene.character
        edge = LOW_WALL[0] - actor.body.bounds[2]
        actor.x = edge - 1
        self.key(scene, pico.SDLK_d)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.3)
        self.assertIs(actor.player.clip, actor.clips['recover_idle_right'])
        self.assertEqual(actor.x, edge)
        image = actor.clips['ground-dash'].frames[0].image
        self.assertFalse(image.closed)
        scene.exit()
        self.assertTrue(image.closed)
        self.assertEqual(scene.level.objects, ())
