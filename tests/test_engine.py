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
        self.pico.get_events = patch.object(engine, 'poll_events').start()
        self.pico.get_events.side_effect = [[], [event(1)]]
        for name in ('SDL_WINDOW_FULLSCREEN', 'SDL_WINDOW_MINIMIZED',
                     'SDL_RENDER_TARGETS_RESET', 'SDL_RENDER_DEVICE_RESET'):
            setattr(self.pico, name, getattr(engine.pico, name))
        patch.object(engine.Engine, '_query_display',
                     return_value=((800, 600), (800, 600), 0)).start()
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

    def test_display_snapshot_dpi_and_wheel(self):
        self.pico.SDL_MOUSEMOTION = 10
        self.pico.SDL_MOUSEBUTTONDOWN = 11
        self.pico.SDL_MOUSEBUTTONUP = 12
        self.pico.SDL_MOUSEWHEEL = 13
        with patch.object(self.app, '_query_display', return_value=((800, 600), (1600, 1200), 0)):
            self.app._refresh_display()
        self.assertEqual(self.app.viewport, (0, 0, 1600, 1200))
        self.assertEqual(self.pico.canvas_height, 1200)
        for kind in (10, 11, 12):
            self.assertEqual(self.app.event_to_output(event(kind, x=200, y=150)), (400, 300))
        self.assertIsNone(self.app.event_to_output(event(13, x=1, y=-2)))

    def test_minimized_and_zero_output_keep_updates_and_quit(self):
        for state in (((800, 600), (0, 0), 0),
                      ((800, 600), (800, 600), self.pico.SDL_WINDOW_MINIMIZED),
                      ((0, 0), (800, 600), 0)):
            with self.subTest(state=state), patch.object(self.app, '_query_display', return_value=state):
                self.pico.get_events.side_effect = [[], [event(1)]]
                scene = self.scene()
                self.app.run(scene)
                scene.update.assert_called_once()
                scene.draw.assert_not_called()
                self.assertIsNone(self.app.window_to_output(1, 2))

    def test_external_resize_between_update_and_draw_skips_frame(self):
        scene = self.scene()
        changed = ((900, 700), (900, 700), 0)
        scene.update.side_effect = lambda dt: setattr(self.app._query_display, 'return_value', changed)
        self.app.run(scene)
        scene.draw.assert_not_called()

    def test_external_resize_during_draw_skips_present(self):
        scene = self.scene()
        changed = ((900, 700), (900, 700), 0)
        scene.draw.side_effect = lambda: setattr(self.app._query_display, 'return_value', changed)
        self.app.run(scene)
        scene.draw.assert_called_once()
        self.pico.update_canvas.assert_not_called()

    def test_reset_events_visible_before_callbacks_and_generation_persists(self):
        reset = event(self.pico.SDL_RENDER_DEVICE_RESET)
        self.pico.get_events.side_effect = [[reset], [], [event(1)]]
        scene = self.scene()
        seen = []
        scene.update.side_effect = lambda dt: seen.append((self.app.render_resets, self.app.reset_generation))
        self.app.run(scene)
        scene.handle_event.assert_called_once_with(reset)
        self.assertEqual(seen, [((reset.type,), 1), ((), 1)])

    def test_display_request_deferred_and_fullscreen_failure_cleans_up(self):
        self.pico.SDL_SetWindowFullscreen.return_value = -1
        self.pico.get_events.side_effect = [[], [event(1)]]
        scene = self.scene()
        scene.update.side_effect = lambda dt: self.app.set_display(fullscreen=True)
        with self.assertRaisesRegex(RuntimeError, '전체화면 전환 실패'):
            self.app.run(scene)
        scene.draw.assert_called_once()
        scene.exit.assert_called_once()
        self.pico.close_canvas.assert_called_once()
        self.assertFalse(self.app.fullscreen)

    def test_fullscreen_return_restores_window_size_and_resize_request(self):
        self.pico.SDL_SetWindowFullscreen.return_value = 0
        self.pico.SDL_SetWindowSize.reset_mock()
        self.app.set_display(fullscreen=True)
        self.pico.SDL_SetWindowFullscreen.assert_not_called()
        self.app._apply_display()
        self.pico.SDL_SetWindowFullscreen.assert_called_once()
        self.pico.SDL_SetWindowSize.assert_not_called()
        self.app.fullscreen = True
        self.app.set_display(fullscreen=False)
        self.app._apply_display()
        self.pico.SDL_SetWindowSize.assert_called_with(self.pico.window, 800, 600)
        self.app.set_display(window_size=(1024, 720))
        self.app._apply_display()
        self.pico.SDL_SetWindowSize.assert_called_with(self.pico.window, 1024, 720)


class SDLBoundaryTests(unittest.TestCase):
    def test_invalid_sizes(self):
        for size in ((0, 600), (-1, 2), (1.5, 2), (True, 2)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                engine.Engine(*size)
        with self.assertRaises(ValueError):
            engine.Engine().set_display(window_size=(0, 1))

    def test_native_size_query_and_error(self):
        def window_size(window, w, h):
            w._obj.value, h._obj.value = 640, 480
        def output_size(renderer, w, h):
            w._obj.value, h._obj.value = 1280, 960
            return 0
        with patch.object(engine.pico, 'SDL_GetWindowSize', side_effect=window_size), \
             patch.object(engine.pico, 'SDL_GetRendererOutputSize', side_effect=output_size) as query, \
             patch.object(engine.pico, 'SDL_GetWindowFlags', return_value=0), \
             patch.object(engine.pico, 'window', None, create=True), \
             patch.object(engine.pico, 'renderer', None, create=True):
            app = engine.Engine()
            self.assertEqual(app._query_display(), ((640, 480), (1280, 960), 0))
            query.side_effect = None
            query.return_value = -1
            with self.assertRaisesRegex(RuntimeError, '출력 크기 조회 실패'):
                app._query_display()

    def test_sdl_event_fields_and_repeat_filter(self):
        from ctypes import memmove, sizeof
        pico = engine.pico
        raws = []
        def raw(kind):
            value = pico.SDL_Event()
            value.type = kind
            raws.append(value)
            return value
        raw(pico.SDL_MOUSEMOTION).motion.x = 123
        raws[-1].motion.y = 45
        raw(pico.SDL_MOUSEBUTTONDOWN).button.button = 3
        raws[-1].button.x, raws[-1].button.y = 20, 30
        raw(pico.SDL_MOUSEWHEEL).wheel.x = 1
        raws[-1].wheel.y = -2
        raw(pico.SDL_KEYDOWN).key.repeat = 1
        raw(pico.SDL_KEYUP).key.keysym.sym = pico.SDLK_SPACE
        raw(pico.SDL_WINDOWEVENT).window.event = pico.SDL_WINDOWEVENT_SIZE_CHANGED
        raws[-1].window.data1, raws[-1].window.data2 = 1000, 700
        raw(pico.SDL_RENDER_TARGETS_RESET)
        raw(pico.SDL_RENDER_DEVICE_RESET)
        raw(pico.SDL_QUIT)
        def poll(target):
            if not raws:
                return 0
            memmove(target, byref(raws.pop(0)), sizeof(pico.SDL_Event))
            return 1
        from ctypes import byref
        with patch.object(pico, 'SDL_PollEvent', side_effect=poll):
            events = engine.poll_events()
        self.assertEqual(len(events), 8)
        self.assertEqual((events[0].x, events[0].y), (123, 45))
        self.assertEqual((events[1].button, events[1].x, events[1].y), (3, 20, 30))
        self.assertEqual((events[2].x, events[2].y), (1, -2))
        self.assertEqual(events[3].key, pico.SDLK_SPACE)
        self.assertEqual((events[4].event, events[4].data1, events[4].data2),
                         (pico.SDL_WINDOWEVENT_SIZE_CHANGED, 1000, 700))
        self.assertEqual([e.type for e in events[-3:]],
                         [pico.SDL_RENDER_TARGETS_RESET, pico.SDL_RENDER_DEVICE_RESET, pico.SDL_QUIT])


if __name__ == '__main__':
    unittest.main()
