import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import GRAVITY, GROUND_Y, JUMP_HEIGHT, JUMP_RELEASE_FACTOR, JUMP_SPEED, SPEED
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
        for direction in ('left', 'right'):
            for phase, count, duration in (('start', 4, .03), ('rise', 5, .298),
                                            ('fall', 6, .32), ('land', 5, .18)):
                clip = actor.clips[f'jump_{phase}_{direction}']
                self.assertEqual(len(clip.frames), count)
                self.assertAlmostEqual(sum(clip.durations), duration)
                self.assertEqual(clip.loop, phase == 'fall')
                self.assertEqual(clip.frames[0].pivot, (.5, 136 / 224))
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
        self.assertAlmostEqual(actor.player.elapsed, .16)
        self.key(scene, pico.SDLK_d, pico.SDL_KEYUP)
        self.key(scene, pico.SDLK_a)
        scene.update(.2)
        self.assertAlmostEqual(actor.y - GROUND_Y, JUMP_HEIGHT)
        self.assertEqual(actor.jump_phase, 'fall')
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])
        scene.update(.30)
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertTrue(draw.call_args.kwargs['flip_x'])
        self.key(scene, pico.SDLK_a, pico.SDL_KEYUP)
        scene.update(.10)
        self.assertTrue(actor.grounded)
        self.assertIs(actor.player.clip, actor.clips['jump_land_left'])
        x = actor.x
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        scene.update(.179)
        self.assertEqual(actor.x, x)
        self.assertEqual(actor.state, 'jump')
        scene.update(.001)
        self.assertNotEqual(actor.state, 'jump')
        self.key(scene, pico.SDLK_a)
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
            self.assertAlmostEqual(actor.x, SPEED * .98)
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

    def test_landing_during_dash_keeps_dash_direction_until_recovery(self):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.73)
        self.key(scene, pico.SDLK_LSHIFT)
        scene.update(.15)
        self.assertTrue(actor.grounded)
        self.key(scene, pico.SDLK_a)
        scene.update(.30)
        self.assertEqual((actor.state, actor.dash_facing), ('dash', 1))
        scene.update(.017)
        self.assertNotEqual(actor.state, 'dash')
        x = actor.x
        scene.update(.01)
        self.assertEqual((actor.state, actor.facing), ('run', -1))
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

    def test_jump_can_lift_a_ground_attack_without_restarting_it(self):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_j)
        scene.update(.08)
        elapsed = actor.player.elapsed
        height = actor.y
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.03)
        self.assertEqual((actor.state, actor.jump_phase), ('attack', 'rise'))
        self.assertGreater(actor.y, height)
        self.assertIs(actor.player.clip, actor.clips['attack'])
        self.assertGreater(actor.player.elapsed, elapsed)
        scene.update(.42)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'fall'))

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

    def test_attack_recovery_dash_uses_direction_and_keeps_last_sweep(self):
        for airborne in (False, True):
            with self.subTest(airborne=airborne):
                scene = self.scene()
                scene.level.enemy.destroy()
                actor = scene.character
                if airborne:
                    self.key(scene, pico.SDLK_SPACE)
                    scene.update(.12)
                self.key(scene, pico.SDLK_j)
                scene.update(0)
                scene.update(.18)
                self.key(scene, pico.SDLK_a)
                self.key(scene, pico.SDLK_LSHIFT)
                scene.update(.04)
                self.assertEqual((actor.state, actor.attack_facing), ('attack', 1))
                scene.update(.033)
                self.assertEqual((actor.state, actor.dash_facing), ('dash', -1))
                self.assertEqual(actor.air_dash_used, airborne)
                self.assertTrue(actor.attack_sweeps)
                scene.update(.11)
                self.assertFalse(actor.attack_sweeps)

    def test_recovery_dash_respects_buffer_expiry_and_air_dash_limit(self):
        for spent in (False, True):
            with self.subTest(spent=spent):
                scene = self.scene()
                scene.level.enemy.destroy()
                actor = scene.character
                if spent:
                    self.key(scene, pico.SDLK_SPACE)
                    scene.update(.12)
                    actor.air_dash_used = True
                self.key(scene, pico.SDLK_j)
                scene.update(0)
                scene.update(.21 if spent else .08)
                self.key(scene, pico.SDLK_LSHIFT)
                scene.update(.225 if not spent else .101)
                self.assertEqual(actor.state, 'attack')
                self.assertIsNone(actor.buffered_action)

    def test_landing_keeps_movement_through_contact(self):
        scene = self.scene()
        scene.level.enemy.destroy()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.80)
        self.key(scene, pico.SDLK_d)
        scene.update(.06)
        self.assertTrue(actor.grounded)
        self.assertEqual(actor.state, 'run')
        self.assertAlmostEqual(actor.x, SPEED * .06)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(scene.transform, 1)
            self.assertIs(draw.call_args.args[0], actor.clips['jump_land_right'].frames[2])
            scene.update(.05)
            actor._draw(scene.transform, 1)
            self.assertIn(draw.call_args.args[0], actor.clips['walk'].frames)
        self.assertAlmostEqual(actor.x, SPEED * .11)

    def test_releasing_jump_preserves_the_current_rise_frame(self):
        scene = self.scene()
        actor = scene.character
        self.key(scene, pico.SDLK_SPACE)
        scene.update(.10)
        frame, elapsed, speed = actor.player.frame, actor.player.elapsed, actor.velocity_y
        self.key(scene, pico.SDLK_SPACE, pico.SDL_KEYUP)
        scene.update(0)
        self.assertAlmostEqual(actor.velocity_y, speed * JUMP_RELEASE_FACTOR)
        self.assertAlmostEqual(actor.player.elapsed, elapsed)
        self.assertIs(actor.player.frame, frame)
        scene.update(.03)
        self.assertGreater(actor.player.elapsed, elapsed)

    def test_air_dash_returns_to_the_live_air_pose_and_hurt_displays_its_sheet(self):
        for action in ('dash', 'hurt'):
            with self.subTest(action=action):
                scene = self.scene()
                scene.level.enemy.destroy()
                actor = scene.character
                if action == 'dash':
                    self.key(scene, pico.SDLK_SPACE)
                    scene.update(.10)
                    self.key(scene, pico.SDLK_LSHIFT)
                    scene.update(.435)
                else:
                    actor.take_hit(-1)
                    scene.update(.09)
                self.assertEqual((actor.state, actor.jump_phase), (action, 'rise'))
                self.assertFalse(actor.grounded)
                with patch('game.character.draw_sprite') as draw:
                    actor._draw(scene.transform, 1)
                    clip = 'jump_rise_right' if action == 'dash' else 'hurt'
                    frames = actor.clips[clip].frames
                    self.assertIn(draw.call_args.args[0], frames[1:])
                    self.assertFalse(draw.call_args.kwargs['flip_x'])

    def test_landing_allows_ground_attack_or_dash(self):
        for symbol, expected in ((pico.SDLK_j, 'attack'), (pico.SDLK_LSHIFT, 'dash')):
            with self.subTest(expected=expected):
                scene = self.scene()
                scene.level.enemy.destroy()
                actor = scene.character
                self.key(scene, pico.SDLK_SPACE)
                scene.update(.831)
                self.assertEqual(actor.jump_phase, 'land')
                self.key(scene, symbol)
                scene.update(0)
                self.assertEqual(actor.state, expected)
                self.assertIsNone(actor.jump_phase)
                self.assertFalse(actor.air_dash_used)

    def test_early_input_during_hurt_starts_after_recoil(self):
        for symbol, expected in ((pico.SDLK_j, 'attack'), (pico.SDLK_LSHIFT, 'dash')):
            with self.subTest(expected=expected):
                scene = self.scene()
                scene.level.enemy.destroy()
                actor = scene.character
                self.assertTrue(actor.take_hit(1))
                self.key(scene, symbol)
                scene.update(.105)
                self.assertEqual(actor.state, 'hurt')
                scene.update(.016)
                self.assertEqual(actor.state, expected)

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
