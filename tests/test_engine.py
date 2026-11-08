import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import engine


def event(kind, **values):
    return SimpleNamespace(type=kind, **values)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.pico = Mock()
        self.pico.SDL_QUIT = 1
        self.pico.SDL_KEYDOWN = 2
        self.pico.SDLK_ESCAPE = 27
        self.pico.window = self.pico.renderer = None
        self.pico.open_canvas.side_effect = self.open_canvas
        self.pico.get_events.side_effect = [[], [event(1)]]
        self.pico.clear_canvas.side_effect = lambda: self.log.append('clear')
        self.pico.update_canvas.side_effect = lambda: self.log.append('present')
        self.addCleanup(patch.stopall)
        patch.object(engine, 'pico', self.pico).start()
        self.clock = patch.object(engine, 'perf_counter', return_value=0.0).start()
        self.sleep = patch.object(engine, 'sleep').start()
        self.app = engine.Engine()

    def open_canvas(self, *args):
        self.pico.window = self.pico.renderer = object()

    def scene(self, name='A'):
        scene = Mock(spec=engine.Scene)
        scene.enter.side_effect = lambda app: self.log.append(name + '.enter')
        scene.handle_event.side_effect = lambda evt: self.log.append(evt)
        scene.update.side_effect = lambda dt: self.log.append((name + '.update', dt))
        scene.draw.side_effect = lambda: self.log.append(name + '.draw')
        scene.exit.side_effect = lambda: self.log.append(name + '.exit')
        return scene

    def test_event_order_and_frame_order(self):
        key, mouse = event(2, key=32), event(3, x=4, y=5)
        self.pico.get_events.side_effect = [[key, mouse], [event(1)]]
        scene = self.scene()
        self.app.run(scene)
        self.assertEqual(self.log, ['A.enter', key, mouse, ('A.update', 0),
                                   'clear', 'A.draw', 'present', 'A.exit'])
        self.assertIs(scene.handle_event.call_args_list[0].args[0], key)
        self.pico.close_canvas.assert_called_once()

    def test_quit_and_escape_skip_remaining_work(self):
        for quit_event in (event(1), event(2, key=27)):
            with self.subTest(event=quit_event):
                self.pico.get_events.side_effect = [[quit_event, event(3)]]
                scene = self.scene()
                self.app.run(scene)
                scene.handle_event.assert_not_called()
                scene.update.assert_not_called()
                scene.draw.assert_not_called()
                scene.exit.assert_called_once()

    def test_callback_failures_close_window(self):
        for callback in ('enter', 'handle_event', 'update', 'draw', 'exit'):
            with self.subTest(callback=callback):
                self.pico.get_events.side_effect = [[event(3)], [event(1)]]
                self.pico.close_canvas.reset_mock()
                scene = self.scene()
                getattr(scene, callback).side_effect = ValueError(callback)
                with self.assertRaisesRegex(ValueError, callback):
                    self.app.run(scene)
                scene.exit.assert_called_once()
                self.pico.close_canvas.assert_called_once()

    def test_window_partial_failure_cleans_up(self):
        for result in ('exception', 'null_window', 'null_renderer'):
            with self.subTest(result=result):
                def fail(*args):
                    if result == 'exception':
                        raise OSError('open')
                    self.pico.window = None if result == 'null_window' else object()
                    self.pico.renderer = None if result == 'null_renderer' else object()
                self.pico.open_canvas.side_effect = fail
                self.pico.close_canvas.reset_mock()
                scene = self.scene()
                with self.assertRaises((OSError, RuntimeError)):
                    self.app.run(scene)
                scene.enter.assert_not_called()
                self.pico.close_canvas.assert_called_once()

    def test_nested_engines_rejected_and_reusable_after_close_failure(self):
        for nested in (self.app, engine.Engine()):
            scene = self.scene()
            scene.enter.side_effect = lambda app: nested.run(self.scene())
            with self.assertRaises(RuntimeError):
                self.app.run(scene)
        self.pico.get_events.side_effect = [[event(1)]]
        self.pico.close_canvas.side_effect = OSError('close')
        with self.assertRaisesRegex(OSError, 'close'):
            self.app.run(self.scene())
        self.pico.close_canvas.side_effect = None
        self.pico.get_events.side_effect = [[event(1)]]
        self.app.run(self.scene())

    def test_cleanup_error_preserves_original_context(self):
        scene = self.scene()
        scene.update.side_effect = ValueError('update')
        scene.exit.side_effect = OSError('exit')
        with self.assertRaises(OSError) as caught:
            self.app.run(scene)
        self.assertIsInstance(caught.exception.__context__, ValueError)
        self.pico.close_canvas.assert_called_once()

    def test_stop_in_each_callback_prevents_later_work(self):
        for callback in ('enter', 'handle_event', 'update', 'draw'):
            with self.subTest(callback=callback):
                self.pico.get_events.side_effect = [[event(3), event(3)]]
                self.pico.update_canvas.reset_mock()
                scene = self.scene()
                getattr(scene, callback).side_effect = lambda *args: self.app.stop()
                self.app.run(scene)
                self.pico.update_canvas.assert_not_called()
                scene.exit.assert_called_once()
                if callback in ('enter', 'handle_event'):
                    scene.update.assert_not_called()
                if callback != 'draw':
                    scene.draw.assert_not_called()

    def test_dt_clamped_and_sleep_accounts_for_work(self):
        self.clock.side_effect = [0, .005, 5, 5.2, 6]
        self.pico.get_events.side_effect = [[], [], [event(1)]]
        scene = self.scene()
        self.app.run(scene)
        self.assertEqual([c.args[0] for c in scene.update.call_args_list], [0, .1])
        self.assertAlmostEqual(self.sleep.call_args_list[0].args[0], 1 / 60 - .005)
        self.assertEqual(self.sleep.call_args_list[1].args[0], 0)

    def test_last_transition_wins_at_frame_boundary_and_dt_resets(self):
        a, b, c = self.scene('A'), self.scene('B'), self.scene('C')
        a.handle_event.side_effect = lambda evt: self.app.change_scene(b)
        a.update.side_effect = lambda dt: self.app.change_scene(c)
        self.pico.get_events.side_effect = [[event(3)], [], [event(1)]]
        self.clock.side_effect = [0, .01, 100, 100.01, 101]
        self.app.run(a)
        b.enter.assert_not_called()
        c.update.assert_called_once_with(0)
        self.assertEqual(self.log, ['A.enter', 'clear', 'A.draw', 'present',
                                   'A.exit', 'C.enter', ('C.update', 0),
                                   'clear', 'C.draw', 'present', 'C.exit'])

    def test_pending_transition_loses_to_stop(self):
        a, b = self.scene(), self.scene('B')
        a.handle_event.side_effect = lambda evt: self.app.change_scene(b)
        self.pico.get_events.side_effect = [[event(3), event(1)]]
        self.app.run(a)
        b.enter.assert_not_called()
        a.update.assert_not_called()

    def test_transition_exit_failure_does_not_enter_next_scene(self):
        a, b = self.scene(), self.scene('B')
        a.update.side_effect = lambda dt: self.app.change_scene(b)
        a.exit.side_effect = ValueError('exit')
        with self.assertRaisesRegex(ValueError, 'exit'):
            self.app.run(a)
        a.exit.assert_called_once()
        b.enter.assert_not_called()
        self.pico.close_canvas.assert_called_once()

    def test_transition_enter_failure_exits_both_scenes_once(self):
        a, b = self.scene(), self.scene('B')
        a.update.side_effect = lambda dt: self.app.change_scene(b)
        b.enter.side_effect = ValueError('enter')
        with self.assertRaisesRegex(ValueError, 'enter'):
            self.app.run(a)
        a.exit.assert_called_once()
        b.exit.assert_called_once()

    def test_stop_during_transition_exit_prevents_enter(self):
        a, b = self.scene(), self.scene('B')
        a.update.side_effect = lambda dt: self.app.change_scene(b)
        a.exit.side_effect = self.app.stop
        self.app.run(a)
        b.enter.assert_not_called()

    def test_transition_callbacks_defer_followup_until_next_boundary(self):
        for callback in ('enter', 'exit'):
            with self.subTest(callback=callback):
                a, b, c = self.scene('A'), self.scene('B'), self.scene('C')
                a.update.side_effect = lambda dt: self.app.change_scene(b)
                owner = b if callback == 'enter' else a
                getattr(owner, callback).side_effect = lambda *args: self.app.change_scene(c)
                self.pico.get_events.side_effect = [[], [], [], [event(1)]]
                self.app.run(a)
                b.update.assert_called_once_with(0)
                c.update.assert_called_once_with(0)
                for scene in (a, b, c):
                    scene.enter.assert_called_once()
                    scene.exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
