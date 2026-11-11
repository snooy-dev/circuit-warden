"""창 하나와 활성 장면 하나를 실행하는 Pico2D 기반 루프."""

from time import perf_counter, sleep

import pico2d.pico2d as pico

from .display import Display, WIDTH, HEIGHT
from .events import poll_events
from .scene import Scene

FRAME_SECONDS = 1 / 60
MAX_DT = 0.1
_active_engine = None


class Engine(Display):
    def __init__(self, width=WIDTH, height=HEIGHT, *, fullscreen=False):
        self._validate_size(width, height)
        self._windowed_size = (width, height)
        self._requested_fullscreen = bool(fullscreen)
        self._display_request = None
        self.window_size = (width, height)
        self.output_size = (0, 0)
        self.viewport = (0, 0, 0, 0)
        self.fullscreen = False
        self.output_valid = False
        self.render_resets = ()
        self.reset_generation = 0
        self._running = False
        self._scene = None
        self._pending = None

    def stop(self) -> None:
        self._running = False

    def change_scene(self, scene: Scene) -> None:
        self._pending = scene

    def _leave_scene(self) -> None:
        scene, self._scene = self._scene, None
        if scene is not None:
            scene.exit()

    def run(self, initial_scene: Scene) -> None:
        global _active_engine
        if _active_engine is not None:
            raise RuntimeError('Pico2D 엔진은 동시에 하나만 실행할 수 있습니다.')
        _active_engine = self
        self._running = True
        self._pending = None
        # Pico2D는 부분 생성 실패와 이전 실행의 핸들을 자체 정리하지 않는다.
        pico.window = pico.renderer = None
        pico.audio_on = False
        try:
            pico.open_canvas(*self._windowed_size)
            if not pico.window or not pico.renderer:
                raise RuntimeError('Pico2D 창 또는 렌더러를 생성하지 못했습니다.')
            pico.hide_lattice()
            pico.SDL_SetWindowResizable(pico.window, pico.SDL_TRUE)
            self.fullscreen = False
            self._display_request = True
            self._apply_display()
            self._refresh_display()
            self._scene = initial_scene
            self._scene.enter(self)
            previous = None
            while self._running:
                started = perf_counter()
                dt = 0.0 if previous is None else min(started - previous, MAX_DT)
                previous = started
                self._apply_display()
                events = poll_events()
                # 이벤트 펌프가 반영한 크기를 입력 전달 전에 확정한다.
                frame_display = self._refresh_display()
                self.render_resets = tuple(event.type for event in events if event.type in (
                    pico.SDL_RENDER_TARGETS_RESET, pico.SDL_RENDER_DEVICE_RESET))
                self.reset_generation += len(self.render_resets)
                for event in events:
                    if event.type == pico.SDL_QUIT or (
                        event.type == pico.SDL_KEYDOWN and event.key == pico.SDLK_ESCAPE
                    ):
                        self.stop()
                    else:
                        self._scene.handle_event(event)
                    if not self._running:
                        break
                if not self._running:
                    break
                self._scene.update(dt)
                if not self._running:
                    break
                if self.output_valid and self._query_display() == frame_display:
                    pico.clear_canvas()
                    self._scene.draw()
                    if not self._running:
                        break
                    if self._query_display() == frame_display:
                        pico.update_canvas()
                if self._pending is not None:
                    next_scene, self._pending = self._pending, None
                    self._leave_scene()
                    if not self._running:
                        break
                    self._scene = next_scene
                    self._scene.enter(self)
                    previous = None
                if self._running:
                    sleep(max(0.0, FRAME_SECONDS - (perf_counter() - started)))
        finally:
            self._running = False
            self.output_valid = False
            try:
                self._leave_scene()
            finally:
                self._pending = None
                try:
                    pico.close_canvas()
                finally:
                    pico.window = pico.renderer = None
                    _active_engine = None
