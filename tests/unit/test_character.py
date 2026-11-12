import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico

from game.character import Character
from game_framework import ImageRef, SpriteClip, SpriteFrame, WorldTransform


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
        self.character = self.make_character()

    def make_character(self):
        character = Character(self.clips)
        character.view_bounds = (-400, -300, 400, 300)
        return character

    def test_repeat_opposite_keys_and_release(self):
        actor = self.character
        for symbol in (pico.SDLK_d, pico.SDLK_d, pico.SDLK_d):
            actor.control(key(symbol))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 18)
        self.assertIs(actor.player.clip, self.clips['run_right'])

        actor.control(key(pico.SDLK_a))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 18)
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
        self.assertAlmostEqual(a.x, -18)
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

    def test_attack_starts_at_first_frame_ignores_clicks_and_resumes_held_key(self):
        actor = self.character
        actor.control(key(pico.SDLK_d))
        actor.update(.1)
        start = actor.x
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        actor.control(click)
        actor.update(.1)
        self.assertEqual(actor.state, 'attack')
        self.assertEqual(actor.player.elapsed, 0)
        self.assertEqual(actor.x, start)
        actor.control(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.control(key(pico.SDLK_a))
        actor.update(.05)
        actor.control(click)
        self.assertEqual(actor.player.elapsed, .05)
        self.assertEqual(actor.facing, 1)
        actor.update(.05)
        self.assertEqual(actor.state, 'run')
        self.assertEqual(actor.facing, -1)
        self.assertEqual(actor.x, start)
        actor.update(.1)
        self.assertEqual(actor.x, start - 18)
        actor.control(click)
        actor.update(.1)
        self.assertEqual(actor.state, 'attack')
        self.assertEqual(actor.player.elapsed, 0)
        with patch('game.character.draw_sprite') as draw:
            actor._draw(WorldTransform((0, 0, 800, 600), view_height=600), 1)
            self.assertTrue(draw.call_args.kwargs['flip_x'])

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
                actor.update(.1)
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
