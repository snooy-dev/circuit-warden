import unittest
from types import SimpleNamespace

import pico2d.pico2d as pico

from tests.unit import test_character


class InputBufferTests(unittest.TestCase):
    setUp = test_character.CharacterTests.setUp
    make_character = test_character.CharacterTests.make_character

    def press(self, symbol):
        self.character.control(test_character.key(symbol))

    def attack(self):
        self.character.control(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                              button=pico.SDL_BUTTON_LEFT))

    def test_last_action_executes_once_when_attack_unlocks(self):
        actor = self.character
        self.attack()
        actor.update(0)
        actor.update(.05)
        self.press(pico.SDLK_LSHIFT)
        self.press(pico.SDLK_SPACE)
        actor.update(.05)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'start'))
        self.assertIsNone(actor.buffered_action)
        actor.update(1.1)
        self.assertEqual(actor.state, 'idle')
        self.assertTrue(actor.grounded)

    def test_expired_input_cannot_fire_after_large_update(self):
        actor = self.character
        self.press(pico.SDLK_LSHIFT)
        actor.update(0)
        self.press(pico.SDLK_SPACE)
        actor.update(.5)
        self.assertEqual(actor.state, 'idle')
        self.assertIsNone(actor.buffered_action)

    def test_landing_buffers_attack_but_never_attacks_in_air(self):
        actor = self.character
        self.press(pico.SDLK_SPACE)
        actor.update(.12 + .75)
        self.attack()
        actor.update(.1)
        self.assertEqual((actor.state, actor.jump_phase), ('jump', 'land'))
        self.assertIsNone(actor.buffered_action)
        actor.update(.08)
        self.attack()
        actor.update(.05)
        self.assertEqual(actor.state, 'attack')

    def test_focus_loss_clears_buffer(self):
        actor = self.character
        self.attack()
        actor.update(0)
        self.press(pico.SDLK_SPACE)
        actor.control(SimpleNamespace(type=pico.SDL_WINDOWEVENT,
                                      event=pico.SDL_WINDOWEVENT_FOCUS_LOST))
        actor.update(.1)
        self.assertEqual(actor.state, 'idle')
        self.assertIsNone(actor.buffered_action)

    def test_air_dash_limit_still_applies_to_buffer(self):
        actor = self.character
        self.press(pico.SDLK_SPACE)
        actor.update(.12)
        self.press(pico.SDLK_LSHIFT)
        actor.update(.4)
        actor.control(test_character.key(pico.SDLK_LSHIFT, pico.SDL_KEYUP))
        self.press(pico.SDLK_LSHIFT)
        actor.update(.067)
        self.assertEqual(actor.state, 'jump')
        self.assertTrue(actor.air_dash_used)
        actor.update(.034)
        self.assertIsNone(actor.buffered_action)
