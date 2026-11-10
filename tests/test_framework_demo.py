import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico
from engine import Engine
from framework_demo import WorldDemo


class FrameworkDemoTests(unittest.TestCase):
    def setUp(self):
        self.app = Engine()
        self.app.output_valid = True
        self.app.output_size = (800, 600)
        self.app.viewport = (0, 0, 800, 600)
        patch.object(pico, 'window', object(), create=True).start()
        patch.object(pico, 'SDL_SetWindowTitle').start()
        self.draw = patch('framework_demo.draw_rect').start()
        self.addCleanup(patch.stopall)
        self.scene = WorldDemo()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)

    def key(self, key):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key))

    def click(self, button, x=460, y=240):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=button, x=x, y=y))

    def test_spawn_moves_once_draw_preserves_state_and_remove(self):
        self.assertEqual(len(self.scene.level.objects), 4)
        self.click(pico.SDL_BUTTON_LEFT)
        obj = self.scene.level.objects[-1]
        self.assertEqual((obj.x, obj.y), (1, 1))
        self.scene.update(.25)
        self.assertEqual((obj.x, obj.y), (1.5, 1))
        state = [(o.x, o.y, o.draw_order) for o in self.scene.level.objects]
        self.scene.draw()
        self.assertEqual([(o.x, o.y, o.draw_order) for o in self.scene.level.objects], state)
        self.assertTrue(self.draw.called)
        self.click(pico.SDL_BUTTON_RIGHT)
        self.assertIsNone(obj.level)
        self.app.output_valid = False
        self.click(pico.SDL_BUTTON_LEFT)
        self.assertEqual(len(self.scene.level.objects), 4)

    def test_level_roundtrip_replaces_objects_and_isolates_mode(self):
        for trigger in (lambda: self.key(pico.SDLK_SPACE),
                        lambda: self.click(pico.SDL_BUTTON_MIDDLE)):
            old = self.scene.level.objects
            speed = self.scene.level.mode.speed
            trigger()
            next_scene = self.app._pending
            self.assertIsInstance(next_scene, WorldDemo)
            self.scene.exit()
            self.assertTrue(all(obj.level is None for obj in old))
            next_scene.enter(self.app)
            self.scene = next_scene
            self.addCleanup(next_scene.exit)
            self.assertEqual(len(next_scene.level.objects), 4)
            self.assertEqual(next_scene.level.mode.speed, -speed)
            self.assertTrue(all(all(obj is not previous for previous in old)
                                for obj in next_scene.level.objects))

    def test_camera_depth_and_display_commands(self):
        objects = self.scene.level.objects
        positions = [(o.x, o.y) for o in objects]
        self.key(pico.SDLK_RIGHT)
        self.key(pico.SDLK_UP)
        self.assertEqual(self.scene.camera_center, (2, 2))
        self.assertEqual([(o.x, o.y) for o in objects], positions)
        self.click(pico.SDL_BUTTON_LEFT, 400, 300)
        self.assertEqual((self.scene.level.objects[-1].x, self.scene.level.objects[-1].y), (2, 2))
        for expected in (1, 2, 0):
            self.key(pico.SDLK_d)
            self.assertEqual(objects[0].draw_order, expected)
        self.key(pico.SDLK_F6)
        self.assertEqual(self.app._windowed_size, (960, 540))
        self.key(pico.SDLK_F11)
        self.assertTrue(self.app._requested_fullscreen)


if __name__ == '__main__':
    unittest.main()
