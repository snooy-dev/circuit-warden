import unittest
from types import SimpleNamespace

import pico2d.pico2d as pico

from game.charge import Charge, ACTIVATION_DISTANCE, _pixels, compose
from game.character import BODY_HEIGHT, GROUND_Y
from tests.unit import test_character as fixtures


class ChargeTeleportTests(unittest.TestCase):
    setUp = fixtures.CharacterTests.setUp
    make_character = fixtures.CharacterTests.make_character

    def test_cancel_every_action_clears_requests_and_lands(self):
        for action, elapsed in (('idle', 0), ('attack', 0), ('jump', .04), ('jump', .2),
                                ('jump', .6), ('jump', .94), ('dash', .04), ('dash', .15), ('dash', .35)):
            with self.subTest(action=action, elapsed=elapsed):
                actor = self.make_character()
                if action != 'idle':
                    actor._queue_action(action)
                    actor.update(elapsed)
                actor._queue_action('jump')
                actor.pressed.add(pico.SDLK_a)
                actor.facing = -1
                actor.air_dash_used = True
                self.assertTrue(actor.teleport((130, 100)))
                self.assertEqual(actor.center, (130, 100))
                self.assertEqual((actor.state, actor.jump_phase, actor.velocity_y), ('jump', 'fall', 0))
                self.assertIsNone(actor.buffered_action)
                self.assertIsNone(actor.dash_phase)
                self.assertFalse(actor.attack_requested or actor.jump_requested or actor.dash_requested)
                self.assertTrue(actor.air_dash_used)
                self.assertEqual(actor.facing, -1)
                actor.update(.05)
                self.assertLess(actor.x, 130)
                self.assertLess(actor.center[1], 100)
                actor.pressed.clear()
                actor.update(1)
                self.assertTrue(actor.grounded)
                self.assertFalse(actor.air_dash_used)
                self.assertEqual(actor.state, 'idle')

    def test_invalid_destination_does_not_cancel_and_ground_arrival_resets(self):
        actor = self.character
        actor._queue_action('attack')
        actor.update(0)
        before = (actor.center, actor.state, actor.player.clip)
        for destination in ((0, GROUND_Y), (400, 0), (0, 300), (float('nan'), 0)):
            self.assertFalse(actor.teleport(destination))
            self.assertEqual((actor.center, actor.state, actor.player.clip), before)
        actor.view_bounds = None
        self.assertFalse(actor.teleport((0, 0)))
        actor.view_bounds = (-400, -300, 400, 300)
        actor.air_dash_used = True
        self.assertTrue(actor.teleport((30, GROUND_Y + BODY_HEIGHT / 2)))
        self.assertTrue(actor.grounded)
        self.assertFalse(actor.air_dash_used)

    def test_distance_boundary_and_transition_reversal_partition(self):
        center = self.character.center
        charge = Charge(None, (center[0] + ACTIVATION_DISTANCE, center[1]))
        self.assertTrue(charge.in_range(self.character.center))
        self.character.x -= .0001
        self.assertFalse(charge.in_range(self.character.center))
        results = []
        for hz in (48, 144):
            charge = Charge(None, (0, 0))
            mode = SimpleNamespace(activation_origin=(0, 0))
            charge._level = SimpleNamespace(mode=mode)
            for active, duration in ((True, .125), (False, .125), (True, .25), (False, .5)):
                mode.activation_origin = (0, 0) if active else (1000, 0)
                previous = charge.value, charge.velocity
                charge.update(0)
                self.assertEqual((charge.value, charge.velocity), previous)
                for _ in range(round(duration * hz)):
                    charge.update(1 / hz)
                    self.assertTrue(0 <= charge.value <= 1)
            results.append((charge.value, charge.velocity))
        for a, b in zip(*results):
            self.assertAlmostEqual(a, b, places=10)
        for dt in (-1, float('nan')):
            with self.assertRaises(ValueError):
                charge.update(dt)

    def test_premultiplied_color_and_pulse_over(self):
        red = _pixels(bytes((255, 0, 0, 255)))
        blue = _pixels(bytes((0, 0, 255, 255)))
        result = compose(red, blue, {}, {}, .5, 0, 0)
        self.assertEqual(result[:4], bytes((128, 0, 128, 255)))
        result = compose(red, {}, {}, {}, .5, 0, 0)
        self.assertEqual(result[:4], bytes((255, 0, 0, 128)))
        pulse = _pixels(bytes((0, 255, 0, 128)))
        result = compose(red, red, pulse, pulse, .5, 0, 0)
        self.assertEqual(result[:4], bytes((127, 128, 0, 255)))
