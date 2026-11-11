import gc
import unittest
import weakref
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d.pico2d as pico
from engine import Engine
from game_framework import (GameObject, Level, LevelScene, RenderItem, Renderer, WorldTransform,
                            draw_rect)


class WorldRenderingTests(unittest.TestCase):
    def setUp(self):
        self.level = Level()
        self.level.open()
        self.addCleanup(self.level.close)
        self.renderer = Renderer()
        self.transform = WorldTransform((0, 0, 800, 600), view_height=10)

    def obj(self, *items):
        obj = GameObject()
        obj.render_items = lambda: items
        return self.level.spawn(obj)

    def test_projection_inverse_lengths_aspect_and_invalid_output(self):
        transform = WorldTransform((20, 30, 1200, 600), center=(4, -3), view_height=10)
        self.assertEqual(transform.point(4, -3), (620, 330))
        self.assertEqual(transform.point(5, -2), (680, 270))
        self.assertEqual(transform.length(2), 120)
        self.assertEqual(transform.bounds, (-6, -8, 14, 2))
        for point in ((-10, 50), (4, -3), (10.25, -6.5)):
            self.assertEqual(transform.inverse(*transform.point(*point)), point)
        self.assertEqual(WorldTransform((0, 0, 600, 600), view_height=10).bounds,
                         (-5, -5, 5, 5))
        for viewport in ((0, 0, 0, 600), (0, 0, 800, 0)):
            invalid = WorldTransform(viewport, view_height=10)
            self.assertIsNone(invalid.point(1, 2))
            self.assertIsNone(invalid.inverse(1, 2))
            draw = Mock()
            self.obj(RenderItem(draw))
            self.renderer.draw(self.level, invalid)
            draw.assert_not_called()
        for kwargs in ({'view_height': 0}, {'view_height': float('nan')},
                       {'center': (float('inf'), 0)}, {'viewport': (0, 0, -1, 20)}):
            with self.assertRaises(ValueError):
                WorldTransform(**({'viewport': (0, 0, 800, 600)} | kwargs))

    def test_global_image_sort_ties_restore_and_update_order_is_unchanged(self):
        log = []
        a = self.obj()
        b = self.obj()
        order = [2]
        a.render_items = lambda: (RenderItem(lambda *args: log.append('body'), order[0]),
                                 RenderItem(lambda *args: log.append('weapon'), 3))
        b.render_items = lambda: (RenderItem(lambda *args: log.append('other'), 1),)
        self.renderer.draw(self.level, self.transform)
        self.assertEqual(log, ['other', 'body', 'weapon'])
        order[0] = 1
        log.clear()
        self.renderer.draw(self.level, self.transform)
        self.assertEqual(log, ['body', 'other', 'weapon'])
        self.assertEqual(self.level.objects, (a, b))
        log.clear()
        a.update = lambda dt: log.append('A')
        b.update = lambda dt: log.append('B')
        self.level.update(.1)
        self.assertEqual(log, ['A', 'B'])
        self.assertEqual(self.renderer.world_items, [])

    def test_culling_uses_each_image_extent_and_keeps_update(self):
        draws = [Mock() for _ in range(7)]
        obj = self.obj(
            RenderItem(draws[0], bounds=(100, 100, 101, 101)),
            RenderItem(draws[1], bounds=(-20, -1, 0, 1)),
            RenderItem(draws[2], bounds=(0, 5, 1, 6)),
            RenderItem(draws[3], bounds=None),
            RenderItem(draws[4], visible=False),
            RenderItem(draws[5], opacity=0),
            RenderItem(draws[6], bounds=(-1, -1, 1, 1), opacity=.5))
        obj.update = Mock()
        self.level.update(.1)
        self.renderer.draw(self.level, self.transform)
        obj.update.assert_called_once_with(.1)
        for i in (0, 4, 5):
            draws[i].assert_not_called()
        for i in (1, 2, 3, 6):
            draws[i].assert_called_once()
        draws[6].assert_called_once_with(self.transform, .5)
        moved = WorldTransform((0, 0, 800, 600), center=(100, 100), view_height=10)
        self.renderer.draw(self.level, moved)
        draws[0].assert_called_once()
        self.assertIs(obj.level, self.level)

    def test_item_validation_and_immutable_order(self):
        for kwargs in ({'draw_order': 1.5}, {'bounds': (2, 0, 1, 2)},
                       {'bounds': (0, 0, float('nan'), 1)}, {'opacity': -1},
                       {'opacity': float('inf')}, {'opacity': 1.1}):
            with self.assertRaises((TypeError, ValueError)):
                RenderItem(Mock(), **kwargs)
        with self.assertRaises(FrozenInstanceError):
            RenderItem(Mock()).draw_order = 1

    def test_culling_keeps_a_pixel_rounding_margin(self):
        near, far = Mock(), Mock()
        self.obj(RenderItem(near, bounds=(0, 5.005, 1, 6)),
                 RenderItem(far, bounds=(0, 5.1, 1, 6)))
        self.renderer.draw(self.level, self.transform)
        near.assert_called_once()
        far.assert_not_called()

    def test_mutation_and_reentrant_dispatch_are_rejected_during_collection_and_draw(self):
        obj = self.obj()
        for action in (lambda: self.level.spawn(GameObject()), obj.destroy,
                       self.level.close, self.level.open,
                       lambda: self.level.update(.1),
                       lambda: self.level.handle_event(object()),
                       lambda: self.renderer.draw(self.level, self.transform)):
            for phase in ('collect', 'draw'):
                with self.subTest(action=action, phase=phase):
                    def invoke(*args):
                        with self.assertRaises(RuntimeError):
                            action()
                        return ()
                    obj.render_items = invoke if phase == 'collect' else lambda: (RenderItem(invoke),)
                    self.renderer.draw(self.level, self.transform)
                    self.assertIs(obj.level, self.level)
        obj.render_items = lambda: ()
        self.level.update(.1)

    def test_lazy_collection_keeps_guards_and_cleans_after_failure(self):
        obj = self.obj()
        calls = []
        def items():
            calls.append('iterate')
            yield RenderItem(lambda *args: calls.append('draw'))
            with self.assertRaises(RuntimeError):
                self.level.spawn(GameObject())
            with self.assertRaises(RuntimeError):
                self.renderer.draw(self.level, self.transform)
            raise ValueError('lazy collection')
        obj.render_items = items
        with self.assertRaisesRegex(ValueError, 'lazy collection'):
            self.renderer.draw(self.level, self.transform)
        self.assertEqual(calls, ['iterate'])
        self.assertEqual(self.renderer.world_items, [])
        self.assertFalse(self.level._rendering)
        self.assertFalse(self.renderer._drawing)
        obj.render_items = lambda: ()
        self.renderer.draw(self.level, self.transform)

    def test_collection_and_draw_failures_release_references_and_guard(self):
        for phase in ('collect', 'draw'):
            with self.subTest(phase=phase):
                obj = self.obj(RenderItem(Mock()))
                def fail(*args):
                    raise ValueError('render')
                bad = self.obj()
                bad.render_items = fail if phase == 'collect' else lambda: (RenderItem(fail),)
                with self.assertRaisesRegex(ValueError, 'render'):
                    self.renderer.draw(self.level, self.transform)
                self.assertEqual(self.renderer.world_items, [])
                ref = weakref.ref(obj)
                obj.destroy()
                del obj
                bad.destroy()
                gc.collect()
                self.assertIsNone(ref())
                self.level.update(.1)


class LevelSceneTests(unittest.TestCase):
    def setUp(self):
        self.app = Engine()
        self.app.output_size = (1600, 1200)
        self.app.viewport = (0, 0, 1600, 1200)
        self.app.output_valid = True
        self.level = Level()
        self.scene = LevelScene(self.level)
        self.scene.enter(self.app)
        self.addCleanup(self.scene.exit)

    def test_scene_update_draw_input_and_reopen(self):
        obj = self.level.spawn(GameObject())
        state = [0]
        obj.update = lambda dt: state.__setitem__(0, state[0] + dt)
        draw = Mock()
        obj.render_items = lambda: (RenderItem(draw),)
        self.scene.update(.1)
        self.scene.draw()
        self.assertEqual(state, [.1])
        draw.assert_called_once_with(self.scene.transform, 1)
        mouse = SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN, x=460, y=240)
        self.assertEqual(self.scene.event_to_world(mouse), (1, 1))
        self.assertIsNone(self.scene.event_to_world(SimpleNamespace(type=pico.SDL_MOUSEWHEEL)))
        self.app.output_valid = False
        self.assertIsNone(self.scene.event_to_world(mouse))
        self.scene.draw()
        self.assertEqual(draw.call_count, 1)
        self.scene.exit()
        self.scene.exit()
        self.assertIsNone(obj.level)
        self.assertIsNone(self.scene.engine)
        self.scene.enter(self.app)
        self.assertEqual(self.level.objects, ())

    def test_reset_event_or_missed_generation_fails_explicitly(self):
        obj = self.level.spawn(GameObject())
        self.app.reset_generation += 1
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_TARGETS_RESET))
        self.scene.draw()
        with self.assertRaisesRegex(RuntimeError, '리셋'):
            self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_DEVICE_RESET))
        self.app.reset_generation += 1
        with self.assertRaisesRegex(RuntimeError, '리셋'):
            self.scene.draw()
        self.scene.exit()
        self.assertIsNone(obj.level)
        self.assertEqual(self.scene.renderer.world_items, [])

    def test_cleanup_failure_still_releases_scene_and_all_objects(self):
        a, b = [self.level.spawn(GameObject()) for _ in range(2)]
        a.on_destroy = Mock(side_effect=ValueError('cleanup'))
        b.on_destroy = Mock()
        with self.assertRaisesRegex(ValueError, 'cleanup'):
            self.scene.exit()
        b.on_destroy.assert_called_once()
        self.assertEqual(self.level.objects, ())
        self.assertIsNone(self.scene.engine)
        self.assertEqual(self.scene.renderer.world_items, [])

    def test_later_target_event_cannot_hide_a_missed_device_reset(self):
        self.app.reset_generation += 2
        self.scene.handle_event(SimpleNamespace(type=pico.SDL_RENDER_TARGETS_RESET))
        with self.assertRaisesRegex(RuntimeError, '리셋'):
            self.scene.draw()


if __name__ == '__main__':
    unittest.main()
