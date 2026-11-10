import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main


class DemoTests(unittest.TestCase):
    def test_space_switches_both_ways(self):
        for alternate in (False, True):
            scene = main.CheckScene(alternate)
            app = Mock()
            scene.enter(app)
            scene.handle_event(SimpleNamespace(type=main.pico.SDL_KEYDOWN,
                                               key=main.pico.SDLK_SPACE))
            self.assertEqual(app.change_scene.call_args.args[0].alternate, not alternate)

    def test_mouse_coordinates_and_time_motion(self):
        scene = main.CheckScene()
        app = Mock(output_size=(800, 600))
        app.event_to_output.return_value = (120, 80)
        scene.enter(app)
        scene.handle_event(SimpleNamespace(type=main.pico.SDL_MOUSEMOTION, x=120, y=80))
        self.assertEqual(scene.pointer, (120, main.HEIGHT - 1 - 80))
        before = scene.x
        scene.update(.1)
        self.assertGreater(scene.x, before)
        scene.x = main.WIDTH - 41
        scene.update(.1)
        self.assertLess(scene.x, 40)
        with patch.object(main.pico, 'draw_rectangle') as draw:
            scene.draw()
        self.assertEqual(draw.call_count, 3)

    def test_display_keys_and_invalid_pointer(self):
        scene = main.CheckScene()
        app = Mock(fullscreen=False, window_size=(800, 600))
        scene.enter(app)
        scene.handle_event(SimpleNamespace(type=main.pico.SDL_KEYDOWN, key=main.pico.SDLK_F11))
        app.set_display.assert_called_with(fullscreen=True)
        scene.handle_event(SimpleNamespace(type=main.pico.SDL_KEYDOWN, key=main.pico.SDLK_F6))
        app.set_display.assert_called_with(fullscreen=False, window_size=(1024, 720))
        app.window_size = (1024, 720)
        scene.handle_event(SimpleNamespace(type=main.pico.SDL_KEYDOWN, key=main.pico.SDLK_F6))
        app.set_display.assert_called_with(fullscreen=False, window_size=(800, 600))
        before = scene.pointer
        app.event_to_output.return_value = None
        scene.handle_event(SimpleNamespace(type=main.pico.SDL_MOUSEMOTION, x=1, y=2))
        self.assertEqual(scene.pointer, before)


if __name__ == '__main__':
    unittest.main()
