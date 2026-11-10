import unittest
import weakref
import gc
from unittest.mock import Mock

from game_framework import (GameMode, GameObject, Level, Canvas, UIElement, UITransform, Renderer)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.level = Level()
        self.level.open()

    def test_ownership_id_lookup_and_single_registration(self):
        obj = GameObject()
        obj.destroy()
        self.assertIs(self.level.spawn(obj), obj)
        self.assertIs(self.level.get(obj.id), obj)
        self.assertIs(obj.level, self.level)
        other = Level()
        other.open()
        for level in (other, self.level):
            with self.assertRaises(RuntimeError):
                level.spawn(obj)
        for field in ('level', 'id'):
            with self.assertRaises(AttributeError):
                setattr(obj, field, None)
        obj.on_destroy = Mock()
        obj.destroy()
        obj.destroy()
        obj.on_destroy.assert_called_once_with()
        self.assertIsNone(obj.level)
        self.assertIsNone(self.level.get(obj.id))
        with self.assertRaises(RuntimeError):
            other.spawn(obj)
        next_obj = self.level.spawn(GameObject())
        self.assertGreater(next_obj.id, obj.id)
        with self.assertRaises(TypeError):
            self.level.spawn(object())
        self.level.close()
        with self.assertRaises(RuntimeError):
            self.level.spawn(GameObject())

    def test_equal_objects_remove_by_identity(self):
        class EqualObject(GameObject):
            def __eq__(self, other):
                return True
        a, b = [self.level.spawn(EqualObject()) for _ in range(2)]
        b.destroy()
        self.assertEqual(len(self.level.objects), 1)
        self.assertIs(self.level.objects[0], a)

    def test_initial_layout_mode_order_and_reopen(self):
        log, created = [], []
        class Layout(Level):
            def on_open(self):
                created.append(self.spawn(GameObject()))
                log.append('layout')
        level = Layout()
        level.mode.on_start = lambda: log.append(len(level.objects))
        level.open()
        first = created[0]
        with self.assertRaises(RuntimeError):
            level.open()
        level.close()
        level.open()
        self.assertEqual(log, ['layout', 1, 'layout', 1])
        self.assertIsNot(first, level.objects[0])
        self.assertIsNone(first.level)
        self.assertGreater(level.objects[0].id, first.id)

    def test_mode_is_per_level_and_rules_are_isolated(self):
        class Rules(GameMode):
            def on_start(self):
                self.total = 0
            def on_update(self, dt):
                self.total += dt
        mode = Rules()
        a, b = Level(mode), Level(Rules())
        a.open()
        b.open()
        a.update(.25)
        self.assertEqual((a.mode.total, b.mode.total), (.25, 0))
        self.assertIs(mode.level, a)
        with self.assertRaises(RuntimeError):
            Level(mode)
        a.close()
        with self.assertRaises(RuntimeError):
            Level(mode)
        with self.assertRaises(TypeError):
            Level(object())

    def test_mode_first_and_registration_order_with_original_values(self):
        log = []
        a, b = [self.level.spawn(GameObject()) for _ in range(2)]
        for name, obj in [('mode', self.level.mode), ('a', a), ('b', b)]:
            event_method = 'on_event' if name == 'mode' else 'handle_event'
            update_method = 'on_update' if name == 'mode' else 'update'
            setattr(obj, event_method, lambda value, n=name: log.append((n, value)))
            setattr(obj, update_method, lambda value, n=name: log.append((n, value)))
        event = object()
        self.level.handle_event(event)
        self.level.update(.25)
        self.assertEqual(log, [(n, v) for v in (event, .25) for n in ('mode', 'a', 'b')])
        self.assertIs(log[1][1], event)

    def test_mutation_in_mode_or_object_waits_for_next_dispatch(self):
        for method, hook, value in [('update', 'on_update', .1),
                                     ('handle_event', 'on_event', object())]:
            for mutate_in_mode in (False, True):
                with self.subTest(method=method, mode=mutate_in_mode):
                    level = Level()
                    level.open()
                    a, b, c = [GameObject() for _ in range(3)]
                    level.spawn(a)
                    level.spawn(b)
                    setattr(b, method, Mock())
                    setattr(c, method, Mock())
                    def mutate(unused):
                        a.destroy()
                        b.destroy()
                        level.spawn(c)
                    owner, callback = (level.mode, hook) if mutate_in_mode else (a, method)
                    setattr(owner, callback, mutate)
                    getattr(level, method)(value)
                    getattr(b, method).assert_not_called()
                    getattr(c, method).assert_not_called()
                    self.assertEqual(level.objects, (c,))
                    setattr(owner, callback, lambda unused: None)
                    getattr(level, method)(value)
                    getattr(c, method).assert_called_once_with(value)

    def test_dispatch_reentry_rejected_and_error_resets_guard(self):
        for outer, inner in [('update', 'update'), ('update', 'handle_event'),
                             ('handle_event', 'update'), ('handle_event', 'handle_event')]:
            hook = 'on_update' if outer == 'update' else 'on_event'
            setattr(self.level.mode, hook, lambda value: getattr(self.level, inner)(value))
            with self.assertRaisesRegex(RuntimeError, '재진입'):
                getattr(self.level, outer)(.1)
            setattr(self.level.mode, hook, Mock())
            getattr(self.level, outer)(.1)

    def test_destroy_reentrancy_and_cleanup_registration_rejection(self):
        obj = self.level.spawn(GameObject())
        def destroy():
            self.assertIsNone(obj.level)
            self.assertEqual(self.level.objects, ())
            obj.destroy()
            with self.assertRaises(RuntimeError):
                self.level.spawn(GameObject())
            raise ValueError('destroy')
        obj.on_destroy = Mock(side_effect=destroy)
        with self.assertRaisesRegex(ValueError, 'destroy'):
            obj.destroy()
        obj.destroy()
        obj.on_destroy.assert_called_once()
        self.level.spawn(GameObject())

    def test_self_destroy_on_spawn_and_failed_spawn_cannot_be_reused(self):
        obj = GameObject()
        obj.on_spawn = obj.destroy
        self.level.spawn(obj)
        self.assertEqual(self.level.objects, ())
        obj = GameObject()
        obj.on_spawn = Mock(side_effect=ValueError('spawn'))
        obj.on_destroy = Mock()
        with self.assertRaisesRegex(ValueError, 'spawn'):
            self.level.spawn(obj)
        obj.on_destroy.assert_called_once()
        self.assertIsNone(obj.level)
        with self.assertRaises(RuntimeError):
            self.level.spawn(obj)

    def test_spawn_and_cleanup_errors_preserved(self):
        obj = GameObject()
        obj.on_spawn = Mock(side_effect=ValueError('spawn'))
        obj.on_destroy = Mock(side_effect=OSError('destroy'))
        with self.assertRaises(BaseExceptionGroup) as caught:
            self.level.spawn(obj)
        self.assertEqual([str(e) for e in caught.exception.exceptions], ['spawn', 'destroy'])
        self.assertIsNone(obj.level)
        self.assertEqual(self.level.objects, ())

    def test_close_attempts_all_cleanup_and_preserves_errors(self):
        a, b = [self.level.spawn(GameObject()) for _ in range(2)]
        self.level.mode.on_end = Mock(side_effect=ValueError('end'))
        a.on_destroy = Mock(side_effect=OSError('a'))
        b.on_destroy = Mock(side_effect=RuntimeError('b'))
        with self.assertRaises(BaseExceptionGroup) as caught:
            self.level.close()
        self.assertEqual([str(e) for e in caught.exception.exceptions], ['end', 'a', 'b'])
        self.assertEqual(self.level.objects, ())
        for obj in (a, b):
            self.assertIsNone(obj.level)
            obj.on_destroy.assert_called_once()
        self.level.close()
        self.level.mode.on_end.assert_called_once()

    def test_close_in_dispatch_stops_later_calls_and_cannot_reopen(self):
        a = self.level.spawn(GameObject())
        a.update = Mock()
        def close(dt):
            self.level.close()
            with self.assertRaises(RuntimeError):
                self.level.open()
        self.level.mode.on_update = close
        self.level.update(.1)
        a.update.assert_not_called()
        self.level.open()

    def test_close_callbacks_cannot_register_and_nested_close_is_harmless(self):
        obj = self.level.spawn(GameObject())
        def cleanup():
            self.level.close()
            with self.assertRaises(RuntimeError):
                self.level.spawn(GameObject())
            with self.assertRaises(RuntimeError):
                self.level.open()
        self.level.mode.on_end = Mock(side_effect=cleanup)
        obj.on_destroy = Mock(side_effect=cleanup)
        self.level.close()
        self.level.mode.on_end.assert_called_once()
        obj.on_destroy.assert_called_once()

    def test_partial_open_failure_cleans_layout_and_mode_and_can_retry(self):
        for fail_layout in (False, True):
            with self.subTest(layout=fail_layout):
                level = Level()
                obj = GameObject()
                level.on_open = lambda: level.spawn(obj)
                failing = 'on_open' if fail_layout else 'on_start'
                target = level if fail_layout else level.mode
                original = getattr(target, failing)
                def fail():
                    original()
                    raise ValueError('start')
                setattr(target, failing, fail)
                level.mode.on_end = Mock(side_effect=OSError('end'))
                with self.assertRaises(BaseExceptionGroup) as caught:
                    level.open()
                self.assertEqual([str(e) for e in caught.exception.exceptions], ['start', 'end'])
                self.assertEqual(level.objects, ())
                self.assertIsNone(obj.level)
                level.on_open = lambda: level.spawn(GameObject())
                level.mode.on_start = lambda: None
                level.open()
                self.assertEqual(len(level.objects), 1)

    def test_inactive_dispatch_and_closed_during_open(self):
        level = Level()
        level.mode.on_update = Mock()
        level.mode.on_event = Mock()
        level.update(.1)
        level.handle_event(object())
        level.mode.on_update.assert_not_called()
        level.mode.on_event.assert_not_called()
        for callback in ('on_open', 'on_start'):
            with self.subTest(callback=callback):
                level = Level()
                obj = GameObject()
                level.on_open = lambda: level.spawn(obj)
                owner = level if callback == 'on_open' else level.mode
                setattr(owner, callback, level.close)
                with self.assertRaises(RuntimeError):
                    level.open()
                self.assertIsNone(obj.level)
                self.assertEqual(level.objects, ())
                with self.assertRaises(RuntimeError):
                    level.spawn(GameObject())

    def test_dispatch_snapshot_does_not_retain_removed_objects(self):
        for fail in (False, True):
            obj = self.level.spawn(GameObject())
            ref = weakref.ref(obj)
            def update(dt):
                self.level.objects[0].destroy()
                if fail:
                    raise ValueError('update')
            obj.update = update
            del obj
            if fail:
                with self.assertRaises(ValueError):
                    self.level.update(.1)
            else:
                self.level.update(.1)
            gc.collect()
            self.assertIsNone(ref())



class CanvasTests(unittest.TestCase):
    def setUp(self):
        self.canvas = Canvas((800, 600))
        self.addCleanup(self.canvas.close)
        self.renderer = Renderer()
        self.transform = self.canvas.transform((0, 0, 800, 600))

    def node(self, parent=None, **kwargs):
        return self.canvas.add(UIElement(**kwargs), parent)

    def test_single_attachment_and_read_only_tree(self):
        root = self.node()
        child = self.node(root)
        self.assertEqual(self.canvas.roots, (root,))
        self.assertEqual(root.children, (child,))
        self.assertIs(child.parent, root)
        for canvas, parent, element in ((self.canvas, None, root),
                                         (Canvas((1, 1)), None, child),
                                         (self.canvas, UIElement(), UIElement())):
            with self.assertRaises(RuntimeError):
                canvas.add(element, parent)
        for field in ('parent', 'canvas', 'children'):
            with self.assertRaises(AttributeError):
                setattr(child, field, None)
        self.canvas.remove(root)
        self.canvas.remove(root)
        for node in (root, child):
            self.assertIsNone(node.canvas)
            self.assertIsNone(node.parent)
            self.assertEqual(node.children, ())
            with self.assertRaises(RuntimeError):
                self.canvas.add(node)

    def test_subtree_detaches_before_child_first_cleanup_and_preserves_failures(self):
        a, other = self.node(), self.node()
        b, c = self.node(a), None
        c = self.node(b)
        log = []
        def clean(node, name):
            self.assertTrue(all(n.canvas is None and n.parent is None and not n.children
                                for n in (a, b, c)))
            with self.assertRaises(RuntimeError):
                self.canvas.add(UIElement())
            log.append(name)
            if node is not b:
                raise ValueError(name)
        for node, name in ((a, 'a'), (b, 'b'), (c, 'c')):
            node.on_destroy = lambda n=node, v=name: clean(n, v)
        with self.assertRaises(BaseExceptionGroup) as result:
            self.canvas.remove(a)
        self.assertEqual(log, ['c', 'b', 'a'])
        self.assertEqual(len(result.exception.exceptions), 2)
        self.assertEqual(self.canvas.roots, (other,))
        self.canvas.remove(a)
        self.assertEqual(log, ['c', 'b', 'a'])

    def test_whole_dfs_snapshot_and_membership_check_even_when_hidden(self):
        a, b = self.node(visible=False), self.node()
        child = self.node(b)
        log = []
        def mutate(dt):
            log.append('a')
            self.canvas.remove(child)
            new = self.node(b)
            new.update = lambda dt: log.append('new')
            a.update = lambda dt: log.append('a')
        a.update = mutate
        b.update = lambda dt: log.append('b')
        child.update = lambda dt: log.append('removed')
        self.canvas.update(.1)
        self.assertEqual(log, ['a', 'b'])
        self.canvas.update(.1)
        self.assertEqual(log, ['a', 'b', 'a', 'b', 'new'])

    def test_update_failure_reentrancy_and_reference_release(self):
        node = self.node()
        def fail(dt):
            with self.assertRaises(RuntimeError):
                self.canvas.update(dt)
            raise ValueError('update')
        node.update = fail
        with self.assertRaisesRegex(ValueError, 'update'):
            self.canvas.update(.1)
        node.update = lambda dt: None
        self.canvas.update(.1)
        ref = weakref.ref(node)
        self.canvas.remove(node)
        del node
        gc.collect()
        self.assertIsNone(ref())

    def test_deep_tree_and_bulk_close_are_iterative(self):
        nodes, parent = [], None
        for _ in range(1500):
            parent = self.node(parent)
            nodes.append(parent)
        self.canvas.update(.1)
        self.renderer.draw_ui(self.canvas, self.transform)
        nodes[0].on_destroy = Mock(side_effect=ValueError('close'))
        with self.assertRaisesRegex(ValueError, 'close'):
            self.canvas.close()
        self.assertEqual(self.canvas.roots, ())
        self.assertTrue(all(n.canvas is None and not n.children for n in nodes))
        self.canvas.close()
        with self.assertRaises(RuntimeError):
            self.node()

    def test_sibling_sort_contiguous_subtrees_ties_and_update_order(self):
        a, b = self.node(), self.node(draw_order=1)
        child = self.node(a, draw_order=999)
        log = []
        for node, name in ((a, 'a'), (child, 'child'), (b, 'b')):
            node.draw = lambda *args, name=name: log.append(name)
        self.renderer.draw_ui(self.canvas, self.transform)
        self.assertEqual(log, ['a', 'child', 'b'])
        a.draw_order = 2
        log.clear()
        self.renderer.draw_ui(self.canvas, self.transform)
        self.assertEqual(log, ['b', 'a', 'child'])
        a.draw_order = b.draw_order = 0
        log.clear()
        self.renderer.draw_ui(self.canvas, self.transform)
        self.assertEqual(log, ['a', 'child', 'b'])
        for node, name in ((a, 'a'), (child, 'child'), (b, 'b')):
            node.update = lambda dt, name=name: log.append(name)
        log.clear()
        self.canvas.update(.1)
        self.assertEqual(log, ['a', 'child', 'b'])
        self.assertEqual(self.canvas.roots, (a, b))
        self.assertEqual(self.renderer.ui_items, [])

    def test_anchor_parent_offset_self_culling_opacity_and_subtree_hiding(self):
        parent = self.node(x=-100, y=10, bounds=(0, 0, 10, 10), opacity=0)
        child = self.node(parent, x=110, y=20, bounds=(0, 0, 30, 30), opacity=.5)
        corner = self.node(x=-40, y=-20, anchor=(1, 1))
        parent.draw, child.draw, corner.draw = Mock(), Mock(), Mock()
        transform = self.canvas.transform((20, 30, 1600, 900))
        self.renderer.draw_ui(self.canvas, transform)
        parent.draw.assert_not_called()
        child.draw.assert_called_once_with((10, 30), transform, .5)
        corner.draw.assert_called_once_with((1026 + 2 / 3, 580), transform, 1)
        parent.visible = False
        child.draw.reset_mock()
        self.renderer.draw_ui(self.canvas, transform)
        child.draw.assert_not_called()
        parent.visible, parent.opacity = True, 1
        self.renderer.draw_ui(self.canvas, transform)
        parent.draw.assert_not_called()
        child.draw.assert_called_once()

    def test_ui_culling_keeps_unknown_partial_boundary_and_pixel_margin(self):
        nodes = [self.node(bounds=b) for b in (None, (-10, 0, 5, 10),
                    (800, 0, 810, 10), (800.5, 0, 810, 10), (802, 0, 810, 10))]
        for node in nodes:
            node.draw = Mock()
        self.renderer.draw_ui(self.canvas, self.transform)
        self.assertTrue(all(n.draw.called for n in nodes[:4]))
        nodes[-1].draw.assert_not_called()

    def test_render_mutation_and_failure_release_guards_and_references(self):
        node = self.node()
        actions = [lambda: self.node(), lambda: self.canvas.remove(node), self.canvas.close,
                   lambda: self.canvas.update(.1), lambda: setattr(node, 'draw_order', 1),
                   lambda: self.renderer.draw_ui(self.canvas, self.transform)]
        for action in actions:
            def draw(*args):
                with self.assertRaises(RuntimeError):
                    action()
            node.draw = draw
            self.renderer.draw_ui(self.canvas, self.transform)
        node.draw = Mock(side_effect=ValueError('draw'))
        with self.assertRaisesRegex(ValueError, 'draw'):
            self.renderer.draw_ui(self.canvas, self.transform)
        self.assertEqual(self.renderer.ui_items, [])
        node.draw = Mock()
        self.renderer.draw_ui(self.canvas, self.transform)
        self.canvas.update(.1)
        self.canvas.remove(node)
        self.assertIsNone(node.canvas)

    def test_transform_roundtrip_sizes_font_lengths_and_zero_output(self):
        for viewport, scale, size in (((20, 30, 1600, 1200), 2, (800, 600)),
                ((20, 30, 1200, 600), 1, (1200, 600)),
                ((0, 0, 600, 900), .75, (800, 1200))):
            transform = self.canvas.transform(viewport)
            self.assertEqual(transform.scale, scale)
            self.assertEqual(transform.logical_size, size)
            self.assertEqual(transform.length(18), 18 * scale)
            self.assertEqual(transform.point(0, 0), tuple(viewport[:2]))
            for point in ((0, 0), (17.5, 22), (-40, 900)):
                self.assertEqual(transform.inverse(*transform.point(*point)), point)
        node = self.node()
        node.draw = Mock()
        for viewport in ((0, 0, 0, 600), (0, 0, 800, 0)):
            transform = self.canvas.transform(viewport)
            self.assertIsNone(transform.point(1, 2))
            self.assertIsNone(transform.inverse(1, 2))
            self.assertIsNone(transform.logical_size)
            self.renderer.draw_ui(self.canvas, transform)
        node.draw.assert_not_called()

    def test_validation_and_collection_error_recovery(self):
        for size in ((0, 1), (1, float('inf')), (1, 2, 3)):
            with self.assertRaises(ValueError):
                Canvas(size)
        for kwargs in ({'anchor': (-.1, 0)}, {'x': float('nan')},
                {'opacity': 2}, {'bounds': (1, 0, 0, 1)}, {'draw_order': .5}):
            with self.assertRaises((ValueError, TypeError)):
                UIElement(**kwargs)
        with self.assertRaises(ValueError):
            self.node(self.node(), anchor=(1, 0))
        node = self.node()
        node.opacity = float('nan')
        with self.assertRaises(ValueError):
            self.renderer.draw_ui(self.canvas, self.transform)
        self.assertEqual(self.renderer.ui_items, [])
        node.opacity = 1
        self.renderer.draw_ui(self.canvas, self.transform)


if __name__ == '__main__':
    unittest.main()
