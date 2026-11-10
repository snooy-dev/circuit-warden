import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d.pico2d as pico
from engine import Engine
from framework_demo import WorldDemo, UIDemo, FrameworkDemo


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



class UIDemoTests(unittest.TestCase):
    def setUp(self):
        self.app = Engine()
        self.app.output_valid = True
        self.app.output_size = (1600, 1200)
        self.app.viewport = (0, 0, 1600, 1200)
        patch.object(pico, 'window', object(), create=True).start()
        patch.object(pico, 'SDL_SetWindowTitle').start()
        self.draw = patch('framework_demo.draw_rect').start()
        self.addCleanup(patch.stopall)
        self.scene = UIDemo()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)

    def key(self, key):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key))

    def test_ui_only_movement_hidden_updates_and_subtree_removal(self):
        self.assertFalse(hasattr(self.scene, 'level'))
        initial = self.scene.back.x
        self.key(pico.SDLK_RIGHT)
        self.scene.draw()
        self.assertEqual(self.scene.back.x, initial + 20)
        child_bounds = (210, 140, 440, 270)
        self.assertTrue(any(call.args[1] == child_bounds for call in self.draw.call_args_list))
        self.key(pico.SDLK_h)
        self.draw.reset_mock()
        with patch.object(self.scene.child, 'update') as update:
            self.scene.update(.1)
            update.assert_called_once_with(.1)
        self.scene.draw()
        self.assertFalse(any(call.args[1] == child_bounds for call in self.draw.call_args_list))
        self.key(pico.SDLK_DELETE)
        self.assertIsNone(self.scene.back.canvas)
        self.assertIsNone(self.scene.child.canvas)
        self.assertEqual(self.scene.back.children, ())

    def test_dpi_input_inverse_wheel_zero_and_anchor_resize(self):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=320, y=240))
        self.assertEqual((self.scene.pointer.x, self.scene.pointer.y), (320, 240))
        self.assertIsNone(self.scene.event_to_ui(SimpleNamespace(type=pico.SDL_MOUSEWHEEL)))
        self.app.output_size = (1200, 600)
        self.app.viewport = (0, 0, 1200, 600)
        self.scene.draw()
        self.assertTrue(any(call.args[1] == (1120, 20, 1180, 50)
                            for call in self.draw.call_args_list))
        self.assertEqual((self.scene.corner.x, self.scene.corner.y), (-80, 20))
        self.app.output_valid = False
        self.draw.reset_mock()
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=10, y=10))
        self.scene.draw()
        self.draw.assert_not_called()
        self.assertEqual((self.scene.pointer.x, self.scene.pointer.y), (320, 240))

    def test_order_display_reset_and_cleanup_failure(self):
        self.key(pico.SDLK_d)
        self.assertEqual(self.scene.back.draw_order, 2)
        self.key(pico.SDLK_F6)
        self.assertEqual(self.app._windowed_size, (960, 540))
        self.key(pico.SDLK_F11)
        self.assertTrue(self.app._requested_fullscreen)
        self.key(pico.SDLK_r)
        self.assertIsInstance(self.app._pending, UIDemo)
        self.app.reset_generation += 1
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_TARGETS_RESET))
        self.scene.draw()
        self.app.reset_generation += 2
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_TARGETS_RESET))
        with self.assertRaisesRegex(RuntimeError, '리셋'):
            self.scene.draw()
        with self.assertRaisesRegex(RuntimeError, '리셋'):
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_DEVICE_RESET))
        with patch.object(self.scene.child, 'on_destroy', side_effect=ValueError('cleanup')):
            with self.assertRaisesRegex(ValueError, 'cleanup'):
                self.scene.exit()
        self.assertEqual(self.scene.canvas.roots, ())
        self.assertEqual(self.scene.renderer.ui_items, [])
        self.assertIsNone(self.scene.engine)


class IntegratedDemoTests(unittest.TestCase):
    def setUp(self):
        self.app = Engine()
        self.app.output_valid = True
        self.app.output_size = (800, 600)
        self.app.viewport = (0, 0, 800, 600)
        patch.object(pico, 'window', object(), create=True).start()
        patch.object(pico, 'SDL_SetWindowTitle').start()
        self.draw = patch('framework_demo.draw_rect').start()
        self.addCleanup(patch.stopall)
        self.scene = FrameworkDemo()
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)

    def test_integrated_roundtrip_cleans_both_and_recreates_ui(self):
        for key in (pico.SDLK_SPACE, pico.SDLK_SPACE):
            old_world, old_roots = self.scene.level.objects, self.scene.canvas.roots
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=key))
            successor = self.app._pending
            self.assertIsInstance(successor, FrameworkDemo)
            self.scene.exit()
            self.assertTrue(all(obj.level is None for obj in old_world))
            self.assertTrue(all(node.canvas is None for node in old_roots))
            self.assertEqual(self.scene.canvas.roots, ())
            successor.enter(self.app)
            self.scene = successor
            self.addCleanup(successor.exit)
            self.assertEqual(len(successor.level.objects), 4)
            self.assertEqual(len(successor.canvas.roots), 4)
        self.assertEqual(self.scene.variant, 0)

    def test_ui_fixed_while_camera_moves_pointer_matches_input_and_subtree_deletes(self):
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEMOTION, x=460, y=240))
        self.assertEqual((self.scene.pointer.x, self.scene.pointer.y), (460, 240))
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                               button=pico.SDL_BUTTON_LEFT, x=460, y=240))
        self.assertEqual((self.scene.level.objects[-1].x, self.scene.level.objects[-1].y), (1, 1))
        self.scene.level.objects[0].draw_order = 1000000
        self.scene.draw()
        panel_bounds = self.draw.call_args_list[-5].args[1]
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_RIGHT))
        self.draw.reset_mock()
        self.scene.draw()
        self.assertEqual(self.draw.call_args_list[-5].args[1], panel_bounds)
        self.assertEqual((self.scene.panel.x, self.scene.panel.y), (280, 220))
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_h))
        self.assertFalse(self.scene.panel.visible)
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_KEYDOWN, key=pico.SDLK_DELETE))
        self.assertIsNone(self.scene.panel.canvas)
        self.assertIsNone(self.scene.child.canvas)
        self.assertEqual(self.scene.panel.children, ())


if __name__ == '__main__':
    unittest.main()
