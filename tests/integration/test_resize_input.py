import unittest
from types import SimpleNamespace
from unittest.mock import DEFAULT, patch

import pico2d.pico2d as pico

from engine import Engine, loop
from game.scene import ALTERNATE_SIZE, DEFAULT_SIZE, CharacterScene
from tests.integration import test_character_scene


class ResizeInputTests(unittest.TestCase):
    setUp = test_character_scene.CharacterSceneTests.setUp

    def test_f6_keeps_charge_click_in_same_or_next_input_batch(self):
        f6 = SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_F6)
        click = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, button=pico.SDL_BUTTON_LEFT)
        quit_event = SimpleNamespace(type=pico.SDL_QUIT)
        for batches in ([[f6, click], [], [quit_event]], [[f6], [click], [quit_event]]):
            with self.subTest(batches=batches):
                app, scene = Engine(*DEFAULT_SIZE), CharacterScene()
                size = DEFAULT_SIZE
                observed = []
                draw = scene.draw

                def open_canvas(*args):
                    pico.window = object()
                    pico.renderer = self.renderer

                def set_size(window, width, height):
                    nonlocal size
                    size = width, height

                def record_draw():
                    observed.append((app.window_size, scene.character.x, scene.character.state))
                    draw()

                def initial_input_batches():
                    target = scene.level.charges[2]
                    click.x, click.y = map(round, scene.transform.point(*target.position))
                    yield from batches

                with patch.multiple(pico, hide_lattice=DEFAULT, SDL_SetWindowResizable=DEFAULT,
                                    close_canvas=DEFAULT), \
                     patch.object(pico, 'open_canvas', side_effect=open_canvas), \
                     patch.object(pico, 'SDL_SetWindowSize', side_effect=set_size), \
                     patch.object(app, '_query_display', side_effect=lambda: (size, size, 0)), \
                     patch.object(loop, 'poll_events', side_effect=initial_input_batches()), \
                     patch.object(loop, 'sleep'), \
                     patch.object(scene, 'draw', side_effect=record_draw):
                    app.run(scene)

                self.assertEqual([window for window, _, _ in observed], [DEFAULT_SIZE, ALTERNATE_SIZE])
                self.assertEqual(observed[-1], (ALTERNATE_SIZE, scene.level.charges[2].position[0], 'jump'))
