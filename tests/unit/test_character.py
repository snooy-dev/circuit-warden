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
        self.character = self.make_character()

    def make_character(self):
        character = Character(self.clips)
        character.view_bounds = (-400, -300, 400, 300)
        return character

    def test_aliases_repeat_and_opposite_keys(self):
        actor = self.character
        for symbol in (pico.SDLK_d, pico.SDLK_d, pico.SDLK_RIGHT):
            actor.handle_event(key(symbol))
        actor.handle_event(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 18)
        self.assertIs(actor.player.clip, self.clips['run_right'])

        actor.handle_event(key(pico.SDLK_a))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 18)
        self.assertEqual(actor.facing, 1)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.handle_event(key(pico.SDLK_RIGHT, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 0)
        self.assertEqual(actor.facing, -1)
        self.assertIs(actor.player.clip, self.clips['run_left'])
        actor.handle_event(key(pico.SDLK_a, pico.SDL_KEYUP))
        actor.update(.1)
        self.assertAlmostEqual(actor.x, 0)
        self.assertEqual(actor.facing, -1)
        self.assertIs(actor.player.clip, self.clips['idle'])

    def test_same_elapsed_time_moves_same_distance(self):
        a, b = self.character, self.make_character()
        for actor in (a, b):
            actor.handle_event(key(pico.SDLK_LEFT))
        a.update(.1)
        for _ in range(10):
            b.update(.01)
        self.assertAlmostEqual(a.x, -18)
        self.assertAlmostEqual(a.x, b.x)

    def test_focus_loss_and_minimize_clear_held_keys(self):
        actor = self.character
        for kind in (pico.SDL_WINDOWEVENT_FOCUS_LOST, pico.SDL_WINDOWEVENT_MINIMIZED):
            with self.subTest(kind=kind):
                actor.handle_event(key(pico.SDLK_a))
                actor.update(.1)
                before = actor.x
                actor.handle_event(SimpleNamespace(type=pico.SDL_WINDOWEVENT, event=kind))
                actor.update(.1)
                self.assertEqual(actor.x, before)
                self.assertFalse(actor.pressed)
                self.assertIs(actor.player.clip, self.clips['idle'])
                self.assertEqual(actor.facing, -1)

    def test_same_clip_advances_direction_change_starts_first_frame(self):
        actor = self.character
        actor.update(.041)
        self.assertIs(actor.player.frame, self.clips['idle'].frames[1])
        actor.handle_event(key(pico.SDLK_d))
        actor.update(.04)
        self.assertIs(actor.player.frame, self.clips['run_right'].frames[0])
        actor.update(.03)
        self.assertIs(actor.player.frame, self.clips['run_right'].frames[1])
        actor.handle_event(key(pico.SDLK_d, pico.SDL_KEYUP))
        actor.handle_event(key(pico.SDLK_LEFT))
        actor.update(.04)
        self.assertIs(actor.player.frame, self.clips['run_left'].frames[0])

    def test_bounds_include_idle_and_run_extents_and_center_when_narrow(self):
        actor = self.character
        actor.handle_event(key(pico.SDLK_RIGHT))
        for _ in range(20):
            actor.update(.1)
        self.assertEqual(actor.x, 260)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-220, -300, 220, 300)
        actor.update(.1)
        self.assertEqual(actor.x, 80)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-135, -300, 135, 300)
        actor.update(.1)
        self.assertEqual(actor.x, -5)
        self.assertIs(actor.player.clip, self.clips['idle'])
        actor.view_bounds = (-75, -300, 125, 300)
        actor.update(.1)
        self.assertEqual(actor.x, 25)
        self.assertIs(actor.player.clip, self.clips['idle'])

    def test_draw_flips_idle_left_and_uses_dedicated_run_frames(self):
        actor = self.character
        transform = WorldTransform((0, 0, 800, 600), view_height=600)
        actor.handle_event(key(pico.SDLK_LEFT))
        actor.update(.05)
        with patch('game.character.draw_sprite') as draw:
            actor.render_items()[0].drawable(transform, .8)
            self.assertIs(draw.call_args.args[0], self.clips['run_left'].frames[0])
            self.assertEqual(draw.call_args.args[3:5], ((256, 208), .8))
            self.assertFalse(draw.call_args.kwargs['flip_x'])
            actor.handle_event(key(pico.SDLK_LEFT, pico.SDL_KEYUP))
            actor.update(.05)
            actor.render_items()[0].drawable(transform, 1)
            self.assertIs(draw.call_args.args[0], self.clips['idle'].frames[0])
            self.assertTrue(draw.call_args.kwargs['flip_x'])
