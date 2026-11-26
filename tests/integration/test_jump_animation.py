import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GRAVITY, GROUND_Y, JUMP_HEIGHT, JUMP_SPEED, SPEED
from game.scene import CharacterScene
from game.training_map import PLATFORMS
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
            for phase, count, duration in (('start', 12, .03), ('rise', 18, .3),
                                            ('fall', 36, .6), ('land', 18, .18)):
                clip = actor.clips[f'jump_{phase}_{direction}']
                self.assertEqual(len(clip.frames), count)
                self.assertAlmostEqual(sum(clip.durations), duration)
                self.assertEqual(clip.loop, phase == 'fall')
                self.assertEqual(clip.frames[0].pivot, (x / 128, 92 / 104))
        self.key(scene, pico.SDLK_d)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.02)
        self.assertEqual((actor.x, actor.y), (0, GROUND_Y))
        self.assertIs(actor.player.clip, actor.clips['jump_start_right'])
        self.key(scene, pico.SDLK_LSHIFT)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        scene.update(.01)
        self.assertEqual(actor.jump_phase, 'rise')
        self.assertEqual(actor.x, 0)
        self.assertIs(actor.player.clip, actor.clips['air_attack'])
        self.assertEqual(actor.player.elapsed, 0)
        scene.update(.2)
        self.assertAlmostEqual(actor.x, SPEED * .2)
        self.assertIs(actor.player.clip, actor.clips['air_attack'])
        self.assertAlmostEqual(actor.player.elapsed, .2)
        self.key(scene, pico.SDLK_d, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_a)
        scene.update(.2)
        self.assertAlmostEqual(actor.y - GROUND_Y, JUMP_HEIGHT)
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])
        scene.update(.01)
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertFalse(draw.call_args.kwargs['flip_x'])
        scene.update(.39)
        self.assertTrue(actor.grounded)
        self.assertIs(actor.player.clip, actor.clips['jump_land_left'])
        x = actor.x
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT, x=0, y=0))
        scene.update(.179)
        self.assertEqual(actor.x, x)
        self.assertEqual(actor.state, 'jump')
        scene.update(.001)
        self.assertNotEqual(actor.state, 'jump')
        scene.update(.01)
        self.assertTrue(actor.grounded)
        self.assertLess(actor.x, x)

    def test_jump_boundaries_preserve_height_and_horizontal_distance_across_dt(self):
        outcomes = []
        for steps in ((1.01,), (.101,) * 10):
            scene = self.scene()
            scene.level.enemy.destroy()
            self.key(scene, pico.SDLK_d)
            self.key(scene, pico.SDLK_SPACE)
            for dt in steps:
                scene.update(dt)
            actor = scene.character
            self.assertTrue(actor.grounded)
            self.assertIsNone(actor.jump_phase)
            self.assertAlmostEqual(actor.x, SPEED * .8)
            outcomes.append((actor.x, actor.y))
        self.assertAlmostEqual(outcomes[0][0], outcomes[1][0])

    def test_dash_returns_to_current_fall_and_focus_does_not_cancel_started_jump(self):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.38)
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
        scene.update(.18)
        self.assertEqual(actor.state, 'idle')
        self.assertFalse(actor.pressed)

    def test_landing_during_dash_waits_for_dash_and_keeps_landing_direction(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.73)
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
        scene.update(.146)
        self.assertEqual(actor.x, x)
        scene.update(.001)
        scene.update(.01)
        self.assertLess(actor.x, x)

    def test_buffered_jump_takes_off_at_ground_contact_in_both_directions(self):
        for facing in (-1, 1):
            scene = self.scene()
            actor = scene.character
            actor.facing = facing
            self.key(scene, pico.SDLK_SPACE)
            scene.update(.71)
            self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
            self.key(scene, pico.SDLK_SPACE)
            scene.update(.119)
            self.assertEqual(actor.jump_phase, 'fall')
            scene.update(.001)
            self.assertEqual(actor.jump_phase, 'rise')
            self.assertAlmostEqual(actor.velocity_y, JUMP_SPEED)
            direction = 'left' if facing < 0 else 'right'
            self.assertIs(actor.player.frame, actor.clips[f'jump_rise_{direction}'].frames[0])
            self.assertIsNone(actor.buffered_action)
            self.assertEqual((actor.x, actor.facing), (0, facing))
            self.assertAlmostEqual(actor.y, GROUND_Y)
            scene.update(.4)
            self.assertAlmostEqual(actor.y - GROUND_Y, JUMP_HEIGHT)
            scene.update(.58)
            self.assertTrue(actor.grounded)
            self.assertEqual(actor.state, 'idle')  # Holding Space does not chain again.

    def platform_edge(self, facing=1):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        left, _, right, actor.y = PLATFORMS[3]
        actor.x = right + actor.body.bounds[2] - 1 if facing > 0 else left + actor.body.bounds[0] + 1
        actor.facing = facing
        self.assertTrue(actor.grounded)
        return scene, actor

    def test_ledge_jump_takes_off_once_and_respects_space_release(self):
        for facing, speed_factor in ((-1, .65), (1, 1)):
            with self.subTest(facing=facing):
                scene, actor = self.platform_edge(facing)
                self.key(scene, pico.SDLK_d if facing > 0 else pico.SDLK_a)
                scene.update(.01)
                scene.update(.079)
                self.assertEqual(actor.jump_phase, 'fall')
                y = actor.y
                self.key(scene, pico.SDLK_SPACE)
                if speed_factor < 1:
                    self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
                scene.update(0)
                self.assertEqual(actor.jump_phase, 'rise')
                self.assertAlmostEqual(actor.velocity_y, JUMP_SPEED * speed_factor)
                self.assertEqual(actor.y, y)
                self.assertIsNone(actor.buffered_action)
                self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
                self.key(scene, pico.SDLK_SPACE)
                scene.update(.01)
                self.assertLess(actor.velocity_y, JUMP_SPEED * speed_factor)
                self.assertEqual(actor.buffered_action, 'jump')

    def test_ledge_jump_expires_and_space_still_buffers_for_landing(self):
        scene, actor = self.platform_edge()
        self.key(scene, pico.SDLK_d)
        scene.update(.01)
        scene.update(.08)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.121)
        self.assertEqual(actor.jump_phase, 'fall')
        self.assertIsNone(actor.buffered_action)
        scene.update(.05)
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.1)
        self.assertEqual(actor.jump_phase, 'rise')
        self.assertIsNone(actor.buffered_action)

    def test_ledge_jump_is_unavailable_after_dash_push_or_teleport(self):
        for action in ('dash', 'push', 'teleport'):
            with self.subTest(action=action):
                scene, actor = self.platform_edge()
                if action == 'dash':
                    self.key(scene, pico.SDLK_LSHIFT)
                    scene.update(.468)
                elif action == 'push':
                    actor.begin_enemy_push(1, .01)
                else:
                    actor.view_bounds = actor.world_bounds
                    self.assertTrue(actor.teleport((actor.x + 10, actor.center[1])))
                self.assertFalse(actor.grounded)
                self.assertEqual(actor.ledge_jump_remaining, 0)
                self.key(scene, pico.SDLK_SPACE)
                scene.update(0)
                self.assertNotAlmostEqual(actor.velocity_y, JUMP_SPEED)
                self.assertEqual(actor.buffered_action, 'jump')

    def test_platform_buffered_tap_matches_split_updates(self):
        outcomes = []
        for steps in ((.16,), (.04,) * 4):
            scene = self.scene()
            actor = scene.character
            platform = PLATFORMS[3]
            self.key(scene, pico.SDLK_SPACE)
            scene.update(.57)
            actor.x = (platform[0] + platform[2]) / 2
            self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
            self.key(scene, pico.SDLK_SPACE)
            self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
            for dt in steps:
                scene.update(dt)
            self.assertEqual(actor.jump_phase, 'rise')
            self.assertGreater(actor.y, platform[3])
            self.assertLess(actor.velocity_y, JUMP_SPEED * .65)
            outcomes.append((actor.y, actor.velocity_y))
        for a, b in zip(*outcomes):
            self.assertAlmostEqual(a, b)

    def test_expired_buffer_lands_and_fresh_late_press_takes_off_immediately(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.7099)
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.25)
        self.assertEqual(actor.jump_phase, 'land')
        self.assertTrue(actor.grounded)
        self.assertIsNone(actor.buffered_action)
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(0)
        self.assertEqual(actor.jump_phase, 'rise')
        self.assertAlmostEqual(actor.velocity_y, JUMP_SPEED)

    def test_air_attack_landing_can_consume_jump_at_contact(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.69)
        self.key(scene, pico.SDLK_j)
        scene.update(.03)
        self.assertEqual(actor.state, 'attack')
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.12)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'rise'))
        self.assertAlmostEqual(actor.velocity_y, JUMP_SPEED - GRAVITY * .01)

    def test_grounded_dash_consumes_jump_only_after_dash_finishes(self):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.73)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.4)
        self.assertTrue(actor.grounded)
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.066)
        self.assertEqual(actor.state, 'dash')
        self.assertTrue(actor.grounded)
        scene.update(.001)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'rise'))
        self.assertAlmostEqual(actor.velocity_y, JUMP_SPEED)
