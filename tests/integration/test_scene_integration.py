import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico

import engine.loop as engine
from game_framework import Canvas, GameMode, GameObject, ImageStore, Level, LevelScene, RenderItem, UIElement


def app():
    result = engine.Engine()
    result.output_valid = True
    result.output_size = (800, 600)
    result.viewport = (0, 0, 800, 600)
    return result


class SceneIntegrationTests(unittest.TestCase):
    def test_images_close_after_objects_and_ui_despite_errors(self):
        log = []
        images = SimpleNamespace(closed=False)
        def close_images():
            if not images.closed:
                images.closed = True
                log.append('images')
                raise ValueError('image-clean')
        images.close = close_images
        level, canvas = Level(), Canvas((800, 600))
        scene = LevelScene(level, canvas, images=images)
        scene.enter(app())
        obj, node = level.spawn(GameObject()), canvas.add(UIElement())
        def fail_world():
            log.append('world')
            raise ValueError('world-clean')
        obj.on_destroy = fail_world
        node.on_destroy = lambda: log.append('ui')
        with self.assertRaises(BaseExceptionGroup) as caught:
            scene.exit()
        self.assertEqual(log, ['world', 'ui', 'images'])
        self.assertEqual([str(e) for e in caught.exception.exceptions],
                         ['world-clean', 'image-clean'])
        scene.exit()
        self.assertEqual(log, ['world', 'ui', 'images'])
        self.assertIsNone(scene.engine)
        with self.assertRaises(RuntimeError):
            scene.enter(app())

    def test_partial_load_failure_closes_images_before_canvas_shutdown(self):
        store = ImageStore(Path(__file__).parent)
        raw = SimpleNamespace(texture=object(), w=2, h=2)
        log = []
        level = Level()
        def start():
            store.load('test_scene_integration.py')
            store.load('nonexistent-sprite.png')
        level.on_open = start
        scene = LevelScene(level, images=store)
        with patch.object(pico, 'renderer', object(), create=True), \
                patch.object(pico, 'load_image', return_value=raw), \
                patch.object(pico, 'SDL_DestroyTexture', side_effect=lambda t: log.append('image')):
            with self.assertRaisesRegex(OSError, 'nonexistent-sprite.png'):
                scene.enter(app())
            scene.exit()
        self.assertEqual(log, ['image'])
        self.assertIsNone(raw.texture)
        self.assertTrue(store.closed)

    def scene(self):
        scene = LevelScene(Level(), Canvas((800, 600)))
        scene.enter(app())
        self.addCleanup(scene.exit)
        return scene

    def test_joint_snapshot_mode_world_ui_order_and_cross_mutation(self):
        scene = self.scene()
        level, canvas, log = scene.level, scene.canvas, []
        world = level.spawn(GameObject())
        removed = canvas.add(UIElement())
        ui = canvas.add(UIElement())
        child = canvas.add(UIElement(), ui)
        fresh_world, fresh_ui = GameObject(), UIElement()
        fresh_world.update = lambda dt: log.append('new-world')
        fresh_ui.update = lambda dt: log.append('new-ui')
        removed.update = lambda dt: log.append('removed')
        child.update = lambda dt: log.append('child')
        def mode(dt):
            log.append('mode')
            if fresh_ui.canvas is None:
                canvas.add(fresh_ui)
        def world_update(dt):
            log.append('world')
            canvas.remove(removed)
        def ui_update(dt):
            log.append('ui')
            if fresh_world.level is None:
                level.spawn(fresh_world)
            world.destroy()
        level.mode.on_update = mode
        world.update, ui.update = world_update, ui_update
        scene.update(.1)
        self.assertEqual(log, ['mode', 'world', 'ui', 'child'])
        log.clear()
        scene.update(.1)
        self.assertEqual(log, ['mode', 'new-world', 'ui', 'child', 'new-ui'])
        self.assertIsNone(world.level)
        self.assertIsNone(removed.canvas)

    def test_world_created_ui_waits_but_renders_in_same_frame(self):
        scene = self.scene()
        node = UIElement()
        node.update, node.draw = Mock(), Mock()
        obj = scene.level.spawn(GameObject())
        obj.update = lambda dt: scene.canvas.add(node)
        scene.update(.1)
        node.update.assert_not_called()
        scene.draw()
        node.draw.assert_called_once()

    def test_cross_dispatch_reentry_and_failure_release_both_guards(self):
        scene = self.scene()
        for callback in (lambda: scene.canvas.update(.1), lambda: scene.update(.1)):
            with self.subTest(callback=callback):
                scene.level.mode.on_update = lambda dt: callback()
                with self.assertRaises(RuntimeError):
                    scene.update(.1)
                self.assertFalse(scene.level._dispatching)
                self.assertFalse(scene.canvas._dispatching)
        scene.level.mode.on_update = lambda dt: None
        node = scene.canvas.add(UIElement())
        node.update = lambda dt: scene.level.handle_event(object())
        with self.assertRaises(RuntimeError):
            scene.update(.1)
        node.update = lambda dt: None
        scene.update(.1)
        self.assertFalse(scene.level._dispatching)
        self.assertFalse(scene.canvas._dispatching)

    def test_world_then_ui_and_cross_render_mutation_rejected(self):
        scene = self.scene()
        log = []
        obj = scene.level.spawn(GameObject())
        node = scene.canvas.add(UIElement(draw_order=-999))
        obj.render_items = lambda: (RenderItem(lambda *args: log.append('world'), 999),)
        node.draw = lambda *args: log.append('ui')
        scene.draw()
        self.assertEqual(log, ['world', 'ui'])
        for phase in ('collect', 'world', 'ui'):
            with self.subTest(phase=phase):
                obj.render_items = lambda: (RenderItem(lambda *args: None),)
                node.draw = lambda *args: None
                if phase == 'collect':
                    obj.render_items = lambda: (scene.canvas.add(UIElement()),)
                elif phase == 'world':
                    obj.render_items = lambda: (RenderItem(lambda *args: scene.canvas.close()),)
                else:
                    node.draw = lambda *args: scene.level.spawn(GameObject())
                with self.assertRaises(RuntimeError):
                    scene.draw()
                self.assertEqual(scene.renderer.world_items, [])
                self.assertEqual(scene.renderer.ui_items, [])
                self.assertFalse(scene.level._rendering)
                self.assertFalse(scene.canvas._rendering)
                self.assertFalse(scene.renderer._drawing)
        obj.render_items, node.draw = lambda: (), lambda *args: None
        scene.draw()

    def test_level_start_failure_also_cleans_canvas_preserving_errors(self):
        level, canvas = Level(), Canvas((800, 600))
        node = canvas.add(UIElement())
        node.on_destroy = Mock(side_effect=ValueError('ui-clean'))
        level.mode.on_start = Mock(side_effect=ValueError('start'))
        scene = LevelScene(level, canvas)
        with self.assertRaises(BaseExceptionGroup) as caught:
            scene.enter(app())
        self.assertIn('start', str(caught.exception.exceptions[0]))
        self.assertIn('ui-clean', str(caught.exception.exceptions[1]))
        self.assertIsNone(node.canvas)
        self.assertIsNone(scene.engine)
        node.on_destroy.assert_called_once()
        scene.exit()

    def test_canvas_preparation_failure_closes_open_level_and_canvas(self):
        level, canvas = Level(), Canvas((800, 600))
        node = canvas.add(UIElement())
        ended = level.mode.on_end = Mock()
        scene = LevelScene(level, canvas)
        with patch.object(canvas, 'transform', side_effect=ValueError('ui-prepare')):
            with self.assertRaisesRegex(ValueError, 'ui-prepare'):
                scene.enter(app())
        ended.assert_called_once()
        self.assertIsNone(node.canvas)
        self.assertIsNone(scene.engine)
        self.assertEqual(level.objects, ())

    def test_exit_attempts_both_cleanups_and_preserves_all_errors(self):
        scene = self.scene()
        obj = scene.level.spawn(GameObject())
        node = scene.canvas.add(UIElement())
        obj.on_destroy = Mock(side_effect=ValueError('world-clean'))
        node.on_destroy = Mock(side_effect=ValueError('ui-clean'))
        with self.assertRaises(BaseExceptionGroup) as caught:
            scene.exit()
        self.assertEqual([str(e) for e in caught.exception.exceptions],
                         ['world-clean', 'ui-clean'])
        self.assertEqual(scene.level.objects, ())
        self.assertEqual(scene.canvas.roots, ())
        self.assertIsNone(scene.engine)
        scene.exit()
        obj.on_destroy.assert_called_once()
        node.on_destroy.assert_called_once()

    def test_output_and_dpi_use_same_viewport_without_rewriting_coordinates(self):
        scene = self.scene()
        obj = scene.level.spawn(GameObject())
        node = scene.canvas.add(UIElement(x=-80, y=20, anchor=(1, 0)))
        drawn = node.draw = Mock()
        scene.engine.window_size = (600, 300)
        scene.engine.output_size = (1200, 600)
        scene.engine.viewport = (0, 0, 1200, 600)
        event = SimpleNamespace(type=engine.pico.SDL_MOUSEMOTION, x=300, y=150)
        self.assertEqual(scene.event_to_world(event), (0, 0))
        self.assertEqual(scene.event_to_ui(event), (600, 300))
        scene.draw()
        self.assertEqual(drawn.call_args.args[0], (1120, 20))
        self.assertEqual((node.x, node.y), (-80, 20))
        self.assertIs(obj.level, scene.level)
        scene.engine.output_valid = False
        drawn.reset_mock()
        self.assertIsNone(scene.event_to_world(event))
        self.assertIsNone(scene.event_to_ui(event))
        scene.draw()
        drawn.assert_not_called()

    def test_engine_draw_failure_cleans_both_owners(self):
        for fail_ui in (False, True):
            with self.subTest(fail_ui=fail_ui):
                scene = LevelScene(Level(), Canvas((800, 600)))
                node = scene.canvas.add(UIElement())
                obj = GameObject()
                fail = Mock(side_effect=ValueError('draw-failure'))
                obj.render_items = lambda: (RenderItem(fail if not fail_ui else lambda *a: None),)
                scene.level.on_open = lambda: scene.level.spawn(obj)
                if fail_ui:
                    node.draw = fail
                backend = Mock()
                backend.SDL_WINDOW_FULLSCREEN = engine.pico.SDL_WINDOW_FULLSCREEN
                backend.SDL_WINDOW_MINIMIZED = engine.pico.SDL_WINDOW_MINIMIZED
                def opened(*args):
                    backend.window = backend.renderer = object()
                backend.open_canvas.side_effect = opened
                with patch('engine.display.pico', backend), patch.object(engine, 'pico', backend), patch.object(engine, 'poll_events', return_value=[]), patch.object(engine.Engine, '_query_display', return_value=((800, 600), (800, 600), 0)):
                    with self.assertRaisesRegex(ValueError, 'draw-failure'):
                        engine.Engine().run(scene)
                self.assertIsNone(scene.engine)
                self.assertIsNone(obj.level)
                self.assertIsNone(node.canvas)
                self.assertEqual(scene.renderer.world_items, [])
                self.assertEqual(scene.renderer.ui_items, [])
                backend.close_canvas.assert_called_once()


if __name__ == '__main__':
    unittest.main()
