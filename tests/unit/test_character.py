import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import Character, BODY_HEIGHT, GROUND_Y, JUMP_HEIGHT, JUMP_APEX_SECONDS, JUMP_RELEASE_FACTOR
from game.character import DASH_DISTANCE, DASH_SECONDS, SPEED
from game.training_map import TrainingMap
from game_framework import Collider, GameObject, ImageRef, Level, SpriteClip, SpriteFrame, WorldTransform


def key(symbol, kind=pico.SDL_KEYDOWN):
    return SimpleNamespace(type=kind, key=symbol)


class CharacterTests(unittest.TestCase):
    def setUp(self):
        with patch.object(pico, 'renderer', object(), create=True):
            image = ImageRef(Path('synthetic'), SimpleNamespace(w=256, h=104))
            self.clips = {}
            for name, pivot in (('idle', 58), ('run_left', 63), ('run_right', 64)):
                frames = tuple(SpriteFrame(image, (x, 0, 128, 104), (pivot / 128, 92 / 104))
                               for x in (0, 128))
                durations = (.041, .042) if name == 'idle' else (.03, .03)
                self.clips[name] = SpriteClip(frames, durations)
            self.clips['attack'] = SpriteClip(self.clips['idle'].frames, (.05, .05), loop=False)
            self.clips['air_attack'] = SpriteClip(self.clips['idle'].frames, (.15, .15), loop=False)
            for direction in ('left', 'right'):
                frames = self.clips[f'run_{direction}'].frames
                self.clips[f'run_{direction}'] = SpriteClip(frames * 8, (.03,) * 16)
                for phase, times in (('prepare_idle', (.05, .05)), ('prepare_run', (.05, .05)),
                                     ('dash', (.1, .1)), ('recover_idle', (.08, .087)),
                                     ('recover_run', (.08, .087))):
                    self.clips[f'{phase}_{direction}'] = SpriteClip(frames, times, loop=False)
                for phase, duration in (('start', .03), ('rise', .3), ('fall', .6), ('land', .18)):
                    self.clips[f'jump_{phase}_{direction}'] = SpriteClip(
                        frames, (duration / 2,) * 2, loop=phase == 'fall')

        self.character = self.make_character()

    def make_character(self):
        character = Character(self.clips)
        character.view_bounds = (-400, -300, 400, 300)
        return character

    def test_terrain_stops_running_and_dash_and_rejects_teleport_destination(self):
        level = Level()
        level.open()
        self.addCleanup(level.close)
        level.spawn(TrainingMap())
        wall = GameObject()
        wall.colliders = (Collider((80, GROUND_Y, 81, 20), 'terrain', blocks={'player'}),)
        level.spawn(wall)
        actor = level.spawn(self.character)
        actor.clips['dash_fx_right'] = actor.clips['dash_right']
        actor.control(key(pico.SDLK_d))
        level.update(.5)
        self.assertEqual(actor.x, 56)
        actor.x = 0
        actor.control(key(pico.SDLK_LSHIFT))
        level.update(.4)
        self.assertAlmostEqual(actor.x, 56)
        self.assertEqual(actor.dash_phase, 'recover_idle')
        self.assertFalse(actor.teleport((80, -100)))
        self.assertAlmostEqual(actor.x, 56)
        self.assertTrue(actor.teleport((140, -100)))

    def test_lands_on_platform_and_stops_rise_at_ceiling(self):
        level = Level()
        level.open()
        self.addCleanup(level.close)
        level.spawn(TrainingMap())
        terrain = GameObject()
        terrain.colliders = (Collider((-40, -160, 40, -150), 'terrain', blocks={'player'}),
                             Collider((-40, -50, 40, -40), 'terrain', blocks={'player'}))
        level.spawn(terrain)
        actor = level.spawn(self.character)
        actor.y, actor.velocity_y = -140, 300
        actor._machine.jump()
        actor.jump_phase = 'rise'
        level.update(.03)
        self.assertLessEqual(actor.y + BODY_HEIGHT, -50)
        self.assertEqual(actor.jump_phase, 'fall')
        level.update(.2)
        self.assertAlmostEqual(actor.y, -150)
        self.assertTrue(actor.grounded)
        self.assertEqual(actor.jump_phase, 'land')

    def test_dash_world_distance_and_partition(self):
        self.assertEqual(DASH_DISTANCE, BODY_HEIGHT * 2)
        for facing in (-1, 1):
            for viewport in ((0, 0, 1280, 720), (0, 0, 1920, 1080)):
                for steps in ((.467,), (.07, .07, .1, .1, .1, .027)):
                    actor = self.make_character()
                    actor.facing = facing
                    actor.view_bounds = WorldTransform(viewport, view_height=600).bounds
                    actor.control(key(pico.SDLK_LSHIFT))
                    for dt in steps:
                        actor.update(dt)
                    self.assertAlmostEqual(actor.x, facing * DASH_DISTANCE)
                    self.assertEqual(actor.state, 'idle')
                    actor.control(key(pico.SDLK_LSHIFT))
                    actor.update(.1)
                    self.assertAlmostEqual(actor.x, facing * DASH_DISTANCE)

    def test_air_dash_once_and_landing_restores_use(self):
        actor = self.character
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.03)  # Finish the ground startup before testing an air dash.
        actor.update(.1)
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.467)
        self.assertTrue(actor.air_dash_used)
        self.assertFalse(actor.grounded)
        self.assertAlmostEqual(actor.x, DASH_DISTANCE)
        actor.control(key(pico.SDLK_LSHIFT, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.01)
        self.assertEqual(actor.state, 'jump')
        actor.update(.5)
        self.assertTrue(actor.grounded)
        self.assertFalse(actor.air_dash_used)
        actor.update(.18)  # Wait out the landing lock before attempting a new jump.
        actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.03)
        actor.update(.1)
        actor.control(key(pico.SDLK_LSHIFT, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_RSHIFT))
        actor.update(.05)
        self.assertEqual(actor.state, 'dash')

    def test_air_dash_holds_height_and_velocity_for_two_tenths(self):
        for jump_age in (.1, .5):
            actor = self.make_character()
            actor.control(key(pico.SDLK_SPACE))
            actor.update(.03)
            actor.update(jump_age)
            actor.control(key(pico.SDLK_LSHIFT))
            actor.update(.1)
            height, velocity = actor.y, actor.velocity_y
            for dt in (.07, .13):
                actor.update(dt)
                self.assertAlmostEqual(actor.y, height)
                self.assertAlmostEqual(actor.velocity_y, velocity)
            self.assertAlmostEqual(actor.x, DASH_DISTANCE)
            actor.update(.167)
            self.assertNotEqual(actor.y, height)
            actor.update(2 * JUMP_APEX_SECONDS - jump_age - .267 - .001)
            self.assertFalse(actor.grounded)
            actor.update(.001)
            self.assertTrue(actor.grounded)

    def test_jump_release_waits_for_vertical_motion_to_resume_after_dash(self):
        actor = self.character
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.06)
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.10)
        height, velocity = actor.y, actor.velocity_y
        self.assertGreater(velocity, 0)

        actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
        actor.update(.15)
        self.assertEqual((actor.y, actor.velocity_y), (height, velocity))
        actor.update(.07)
        self.assertGreater(actor.y, height)
        self.assertLess(actor.velocity_y, velocity * JUMP_RELEASE_FACTOR)

    def test_dash_phases_lock_inputs_and_select_recovery(self):
        actor = self.character
        actor.facing = -1
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(0)
        actor.control(key(pico.SDLK_SPACE))
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        actor.control(click)
        actor.update(.05)
        self.assertEqual(actor.x, 0)
        self.assertIs(actor.player.clip, self.clips['prepare_idle_left'])
        actor.control(key(pico.SDLK_d))
        actor.update(.05)
        self.assertIs(actor.player.clip, self.clips['dash_left'])
        actor.update(.2)
        self.assertAlmostEqual(actor.x, -DASH_DISTANCE)
        self.assertEqual(actor.facing, -1)
        self.assertIs(actor.player.clip, self.clips['recover_idle_left'])
        actor.control(click)
        actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.167)
        self.assertTrue(actor.grounded)
        self.assertEqual(actor.facing, 1)
        self.assertIs(actor.player.clip, self.clips['run_right'])
        self.assertEqual(actor.player.elapsed, 0)
        self.assertAlmostEqual(actor.x, -DASH_DISTANCE)

    def test_dash_run_recovery_continues_at_frame_fifteen(self):
        for facing, symbol, direction in ((1, pico.SDLK_d, 'right'), (-1, pico.SDLK_a, 'left')):
            actor = self.make_character()
            actor.control(key(symbol))
            actor.update(.01)
            start = actor.x
            actor.control(key(pico.SDLK_LSHIFT))
            actor.update(.05)
            self.assertIs(actor.player.clip, self.clips[f'prepare_run_{direction}'])
            actor.update(.25)
            self.assertIs(actor.player.clip, self.clips[f'recover_run_{direction}'])
            actor.update(.167)
            self.assertAlmostEqual(actor.x, start + facing * DASH_DISTANCE)
            self.assertEqual(actor.state, 'run')
            self.assertIs(actor.player.clip, self.clips[f'run_{direction}'])
            self.assertAlmostEqual(actor.player.elapsed, .45)

    def test_dash_end_selects_idle_when_keys_cancel_or_boundary_blocks(self):
        for at_boundary in (False, True):
            actor = self.make_character()
            actor.control(key(pico.SDLK_d))
            if at_boundary:
                actor.x = 320
            else:
                actor.control(key(pico.SDLK_a))
            actor.control(key(pico.SDLK_LSHIFT))
            actor.update(.3)
            self.assertIs(actor.player.clip, self.clips['recover_idle_right'])
            actor.update(.167)
            self.assertEqual(actor.state, 'idle')
            self.assertIs(actor.player.clip, self.clips['idle'])

    def test_release_during_run_recovery_returns_to_idle_start(self):
        actor = self.character
        actor.control(key(pico.SDLK_d))
        actor.update(.01)
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.3)
        self.assertIs(actor.player.clip, self.clips['recover_run_right'])
        actor.control(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.update(.167)
        self.assertIs(actor.player.clip, self.clips['idle'])
        self.assertEqual(actor.player.elapsed, 0)

    def test_dash_bounds_attack_and_focus_requests(self):
        actor = self.character
        actor.control(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
        actor.update(0)
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.05)
        self.assertEqual(actor.state, 'attack')
        actor.control(key(pico.SDLK_LSHIFT, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_LSHIFT))
        focus = SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=pico.SDL_WINDOWEVENT_FOCUS_LOST)
        actor.control(focus)
        actor.update(.1)
        self.assertEqual(actor.x, 0)
        actor.x = 320
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.15)
        self.assertEqual(actor.x, 330)
        actor.control(focus)
        actor.update(.317)
        self.assertEqual(actor.x, 330)
        self.assertEqual(actor.state, 'idle')
        actor.view_bounds = (-20, -300, 20, 300)
        actor.control(key(pico.SDLK_LSHIFT))
        actor.update(.467)
        self.assertEqual(actor.x, 0)

    def test_jump_reaches_two_body_heights_and_lands_with_split_time(self):
        whole, split = self.character, self.make_character()
        for actor in (whole, split):
            actor.control(key(pico.SDLK_SPACE))
            actor.update(.03)
        whole.update(JUMP_APEX_SECONDS)
        for _ in range(40):
            split.update(JUMP_APEX_SECONDS / 40)
        self.assertEqual(JUMP_HEIGHT, BODY_HEIGHT * 2)
        for actor in (whole, split):
            self.assertAlmostEqual(actor.y - GROUND_Y, JUMP_HEIGHT)
            self.assertAlmostEqual(actor.velocity_y, 0)
            self.assertEqual(actor.x, 0)
            self.assertIs(actor.player.clip, actor.clips['jump_fall_right'])
            self.assertFalse(actor.grounded)
        whole.update(JUMP_APEX_SECONDS)
        for _ in range(40):
            split.update(JUMP_APEX_SECONDS / 40)
        for actor in (whole, split):
            self.assertTrue(actor.grounded)
            actor.update(.18)
            actor.control(key(pico.SDLK_SPACE))
            actor.update(.3)
            self.assertTrue(actor.grounded)
            actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
            actor.control(key(pico.SDLK_SPACE))
            actor.update(.3)
            self.assertFalse(actor.grounded)
            actor.update(2)
            self.assertEqual(actor.y, GROUND_Y)
            self.assertTrue(actor.grounded)

    def test_running_jump_steers_and_draws_at_airborne_position(self):
        actor = self.character
        actor.control(key(pico.SDLK_d))
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.03)
        actor.update(.1)
        self.assertAlmostEqual(actor.x, SPEED * .1)
        self.assertIs(actor.player.clip, actor.clips['jump_rise_right'])
        actor.control(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_a))
        actor.update(.1)
        self.assertEqual(actor.x, 0)
        self.assertIs(actor.player.clip, actor.clips['jump_rise_left'])
        actor.control(key(pico.SDLK_a, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertIs(actor.player.clip, actor.clips['jump_rise_left'])
        with patch('game.character.draw_sprite') as draw:
            actor._draw(WorldTransform((0, 0, 800, 600), view_height=600), 1)
            self.assertEqual(draw.call_args.args[2], (actor.x, actor.y))
        actor.update(.5)
        self.assertTrue(actor.grounded)

    def test_releasing_space_reduces_apex_and_lands_earlier(self):
        peaks = []
        for hold in (.01, .06, .20):
            with self.subTest(hold=hold):
                held, released = self.make_character(), self.make_character()
                for actor in (held, released):
                    actor.control(key(pico.SDLK_SPACE))
                    actor.control(key(pico.SDLK_d))
                    actor.update(hold)
                released.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))

                peak_y = released.y
                for _ in range(60):
                    for actor in (held, released):
                        actor.update(.01)
                    peak_y = max(peak_y, released.y)

                self.assertGreater(peak_y, GROUND_Y)
                self.assertLess(peak_y, GROUND_Y + JUMP_HEIGHT)
                self.assertTrue(released.grounded)
                self.assertFalse(held.grounded)
                self.assertEqual(released.y, GROUND_Y)
                self.assertGreater(released.x, 0)
                peaks.append(peak_y - GROUND_Y)
                held.update(.4)
                self.assertTrue(held.grounded)
        tap, short, medium = peaks
        self.assertAlmostEqual(tap, JUMP_HEIGHT * JUMP_RELEASE_FACTOR ** 2, delta=1)
        self.assertLess(tap + 10, short)
        self.assertLess(short + 10, medium)

    def test_air_attack_preserves_jump_arc_and_resumes_fall(self):
        actor = self.character
        reference = self.make_character()
        for character in (actor, reference):
            character.control(key(pico.SDLK_SPACE))
            character.update(.32)
        actor.control(key(pico.SDLK_j))
        actor.update(0)
        actor.control(key(pico.SDLK_a))
        elapsed = 0
        for dt in (0, .15, .27):
            actor.update(dt)
            reference.update(dt)
            elapsed += dt
            self.assertIs(actor.player.clip, actor.clips['air_attack'])
            self.assertAlmostEqual(actor.x, -SPEED * elapsed)
            self.assertEqual(actor.attack_facing, 1)
            self.assertAlmostEqual(actor.y, reference.y)
            self.assertAlmostEqual(actor.velocity_y, reference.velocity_y)
        actor.update(.02)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'fall'))
        self.assertIs(actor.player.clip, actor.clips['jump_fall_left'])

    def test_air_attack_applies_jump_release_and_ground_attack_buffers_jump(self):
        actor = self.character
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        actor.control(click)
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.03)
        actor.update(.1)
        self.assertNotEqual(actor.state, 'attack')
        actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_SPACE))
        velocity = actor.velocity_y
        actor.control(click)
        actor.update(0)
        self.assertIs(actor.player.clip, actor.clips['air_attack'])
        self.assertEqual(actor.velocity_y, velocity * JUMP_RELEASE_FACTOR)
        actor.update(.7)
        actor.update(.18)
        self.assertTrue(actor.grounded)
        self.assertNotEqual(actor.state, 'attack')
        actor.control(click)
        actor.update(.01)
        actor.update(.045)
        actor.control(key(pico.SDLK_SPACE, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.05)
        self.assertEqual(actor.state, 'attack')
        self.assertTrue(actor.grounded)
        actor.update(.05)
        self.assertEqual(actor.jump_phase, 'start')

    def test_focus_loss_clears_pending_jump_but_airborne_character_lands(self):
        actor = self.character
        lost = SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=pico.SDL_WINDOWEVENT_FOCUS_LOST)
        actor.control(key(pico.SDLK_SPACE))
        actor.control(lost)
        actor.update(.1)
        self.assertTrue(actor.grounded)
        actor.control(key(pico.SDLK_SPACE))
        actor.view_bounds = None
        actor.update(.1)
        self.assertTrue(actor.grounded)
        actor.view_bounds = (-400, -300, 400, 300)
        actor.control(key(pico.SDLK_d))
        actor.control(key(pico.SDLK_SPACE))
        actor.update(.03)
        actor.update(.1)
        x = actor.x
        actor.control(lost)
        actor.view_bounds = None
        actor.update(.7)
        self.assertTrue(actor.grounded)
        self.assertEqual(actor.x, x)
        self.assertFalse(actor.pressed)

    def test_repeat_opposite_keys_and_release(self):
        actor = self.character
        for symbol in (pico.SDLK_d, pico.SDLK_d, pico.SDLK_d):
            actor.control(key(symbol))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 24)
        self.assertIs(actor.player.clip, self.clips['run_right'])

        actor.control(key(pico.SDLK_a))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 24)
        self.assertEqual(actor.facing, 1)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.control(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 0)
        self.assertEqual(actor.facing, -1)
        self.assertIs(actor.player.clip, self.clips['run_left'])
        actor.control(key(pico.SDLK_a, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 0)
        self.assertEqual(actor.facing, -1)
        self.assertIs(actor.player.clip, self.clips['idle'])

    def test_same_elapsed_time_moves_same_distance(self):
        a, b = self.character, self.make_character()
        for actor in (a, b):
            actor.control(key(pico.SDLK_a))
        a.update(.1)
        for _ in range(10):
            b.update(.01)
        self.assertAlmostEqual(a.x, -24)
        self.assertAlmostEqual(a.x, b.x)

    def test_focus_loss_and_minimize_clear_held_keys(self):
        actor = self.character
        for kind in (pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            with self.subTest(kind=kind):
                actor.control(key(pico.SDLK_a))
                actor.update(.1)
                before = actor.x
                actor.control(SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=kind))
                actor.update(.1)
                self.assertEqual(actor.x, before)
                self.assertFalse(actor.pressed)
                self.assertIs(actor.player.clip, self.clips['idle'])
                self.assertEqual(actor.facing, -1)

    def test_same_clip_advances_direction_change_starts_first_frame(self):
        actor = self.character
        actor.update(.041)
        self.assertIs(actor.player.frame, self.clips['idle'].frames[1])
        actor.control(key(pico.SDLK_d))
        actor.update(.04)
        self.assertIs(actor.player.frame, self.clips['run_right'].frames[0])
        actor.update(.03)
        self.assertIs(actor.player.frame, self.clips['run_right'].frames[1])
        actor.control(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_a))
        actor.update(.04)
        self.assertIs(actor.player.frame, self.clips['run_left'].frames[0])

    def test_bounds_include_idle_and_run_extents_and_center_when_narrow(self):
        actor = self.character
        actor.control(key(pico.SDLK_d))
        for _ in range(20):
            actor.update(.1)
        self.assertEqual(actor.x, 330)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-220, -300, 220, 300)
        actor.update(.1)
        self.assertEqual(actor.x, 150)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-67.5, -300, 67.5, 300)
        actor.update(.1)
        self.assertEqual(actor.x, -2.5)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-37.5, -300, 62.5, 300)
        actor.update(.1)
        self.assertEqual(actor.x, 12.5)
        self.assertIs(actor.player.clip, self.clips['idle'])

    def test_draw_flips_idle_left_and_uses_dedicated_run_frames(self):
        actor = self.character
        transform = WorldTransform((0, 0, 800, 600), view_height=600)
        actor.control(key(pico.SDLK_a))
        actor.update(.05)
        with patch('game.character.draw_sprite') as draw:
            actor.render_items()[0].drawable(transform, .8)
            self.assertIs(draw.call_args.args[0], self.clips['run_left'].frames[0])
            self.assertEqual(draw.call_args.args[3:5], ((128, 104), .8))
            self.assertFalse(draw.call_args.kwargs['flip_x'])
            actor.control(key(pico.SDLK_a, pico.SDL_KEYUP))
            actor.update(.05)
            actor.render_items()[0].drawable(transform, 1)
            self.assertIs(draw.call_args.args[0], self.clips['idle'].frames[0])
            self.assertTrue(draw.call_args.kwargs['flip_x'])

    def test_attack_starts_at_first_frame_and_resumes_held_key(self):
        for facing, forward, reverse in ((1, pico.SDLK_d, pico.SDLK_a),
                                          (-1, pico.SDLK_a, pico.SDLK_d)):
            with self.subTest(facing=facing):
                actor = self.make_character()
                actor.control(key(forward))
                actor.update(.1)
                start = actor.x
                actor.control(key(pico.SDLK_j))
                actor.update(.02)
                self.assertEqual(actor.state, 'attack')
                self.assertEqual(actor.player.elapsed, 0)
                self.assertAlmostEqual(actor.x, start + facing * SPEED * .02)
                actor.control(key(forward, pico.SDL_KEYUP))
                actor.control(key(reverse))
                actor.update(.05)
                self.assertAlmostEqual(actor.player.elapsed, .035)
                self.assertEqual(actor.attack_facing, facing)
                self.assertAlmostEqual(actor.x, start - facing * SPEED * .03)
                with patch('game.character.draw_sprite') as draw:
                    actor._draw(WorldTransform((0, 0, 800, 600), view_height=600), 1)
                self.assertEqual(draw.call_args.kwargs['flip_x'], facing < 0)
                actor.update(.10)
                self.assertEqual((actor.state, actor.facing), ('run', -facing))
                self.assertAlmostEqual(actor.x, start - facing * SPEED * .13)

    def test_attack_release_opposite_keys_and_focus_return_to_idle(self):
        for finish in ('release', 'opposite', 'focus'):
            with self.subTest(finish=finish):
                actor = self.make_character()
                actor.control(key(pico.SDLK_a))
                actor.update(.1)
                actor.control(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
                actor.update(.1)
                start = actor.x
                if finish == 'release':
                    actor.control(key(pico.SDLK_a, pico.SDL_KEYUP))
                elif finish == 'opposite':
                    actor.control(key(pico.SDLK_d))
                else:
                    actor.control(SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=pico.SDL_WINDOWEVENT_FOCUS_LOST))
                actor.update(.15)
                self.assertEqual(actor.state, 'idle')
                self.assertEqual(actor.x, start)
                self.assertEqual(actor.facing, -1)

    def test_right_click_and_pending_attack_on_focus_loss_or_invalid_output_are_ignored(self):
        actor = self.character
        actor.control(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_RIGHT))
        actor.update(.1)
        self.assertEqual(actor.state, 'idle')
        for focus in (True, False):
            actor.control(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT))
            if focus:
                actor.control(SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=pico.SDL_WINDOWEVENT_MINIMIZED))
            else:
                actor.view_bounds = None
            actor.update(.1)
            self.assertEqual(actor.state, 'idle')
