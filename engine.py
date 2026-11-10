"""창 하나와 활성 장면 하나를 실행하는 Pico2D 기반 루프."""

from time import perf_counter, sleep
from ctypes import byref, c_int

import pico2d.pico2d as pico

WIDTH, HEIGHT = 800, 600
FRAME_SECONDS = 1 / 60
MAX_DT = 0.1
_active_engine = None


def poll_events():
    """Pico2D 형식의 입력과 원본 창/렌더 이벤트를 함께 보존한다."""
    raw = pico.SDL_Event()
    events = []
    while pico.SDL_PollEvent(byref(raw)):
        event = pico.Event(raw.type)
        if raw.type in (pico.SDL_KEYDOWN, pico.SDL_KEYUP):
            if raw.key.repeat:
                continue
            event.key = raw.key.keysym.sym
        elif raw.type == pico.SDL_MOUSEMOTION:
            event.x, event.y = raw.motion.x, raw.motion.y
        elif raw.type in (pico.SDL_MOUSEBUTTONDOWN, pico.SDL_MOUSEBUTTONUP):
            event.button = raw.button.button
            event.x, event.y = raw.button.x, raw.button.y
        elif raw.type == pico.SDL_MOUSEWHEEL:
            event.x, event.y = raw.wheel.x, raw.wheel.y
            event.direction = raw.wheel.direction
        elif raw.type == pico.SDL_WINDOWEVENT:
            event.event = raw.window.event
            event.data1, event.data2 = raw.window.data1, raw.window.data2
        elif raw.type not in (pico.SDL_QUIT, pico.SDL_RENDER_TARGETS_RESET,
                              pico.SDL_RENDER_DEVICE_RESET):
            continue
        events.append(event)
    return events


class Scene:
    def enter(self, engine: 'Engine') -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        pass

    def exit(self) -> None:
        pass


class Engine:
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

    @staticmethod
    def _validate_size(width, height):
        if any(type(value) is not int or value <= 0 for value in (width, height)):
            raise ValueError('창 크기는 양의 정수여야 합니다.')

    def set_display(self, *, fullscreen=None, window_size=None):
        """요청은 다음 프레임 입력 전에 적용한다. 실패는 예외로 전달한다."""
        if window_size is not None:
            self._validate_size(*window_size)
            self._windowed_size = tuple(window_size)
        if fullscreen is not None:
            self._requested_fullscreen = bool(fullscreen)
        self._display_request = True

    def window_to_output(self, x, y):
        """좌상단 창 좌표를 좌상단 출력 픽셀로 변환한다. 무효 출력은 None."""
        if not self.output_valid:
            return None
        return (x * self.output_size[0] / self.window_size[0],
                y * self.output_size[1] / self.window_size[1])

    def event_to_output(self, event):
        if event.type not in (pico.SDL_MOUSEMOTION, pico.SDL_MOUSEBUTTONDOWN,
                              pico.SDL_MOUSEBUTTONUP):
            return None
        return self.window_to_output(event.x, event.y)

    def _query_display(self):
        width, height, out_width, out_height = c_int(), c_int(), c_int(), c_int()
        pico.SDL_GetWindowSize(pico.window, byref(width), byref(height))
        if pico.SDL_GetRendererOutputSize(pico.renderer, byref(out_width), byref(out_height)) != 0:
            raise RuntimeError(f'출력 크기 조회 실패: {pico.SDL_GetError()!r}')
        flags = pico.SDL_GetWindowFlags(pico.window)
        return ((width.value, height.value), (out_width.value, out_height.value), flags)

    def _refresh_display(self):
        window, output, flags = self._query_display()
        self.window_size, self.output_size = window, output
        self.fullscreen = bool(flags & pico.SDL_WINDOW_FULLSCREEN)
        self.output_valid = (min(*window, *output) > 0 and
                             not flags & pico.SDL_WINDOW_MINIMIZED)
        self.viewport = (0, 0, *output)
        # resize_canvas는 창 크기도 바꾸므로 실제 출력의 y 변환 높이만 맞춘다.
        pico.canvas_width, pico.canvas_height = output
        if not self.fullscreen and self.output_valid:
            self._windowed_size = window
        return window, output, flags

    def _apply_display(self):
        if self._display_request is None:
            return
        self._display_request = None
        target = self._requested_fullscreen
        if target != self.fullscreen:
            flags = pico.SDL_WINDOW_FULLSCREEN_DESKTOP if target else 0
            if pico.SDL_SetWindowFullscreen(pico.window, flags) != 0:
                self._requested_fullscreen = self.fullscreen
                raise RuntimeError(f'전체화면 전환 실패: {pico.SDL_GetError()!r}')
        if not target:
            pico.SDL_SetWindowSize(pico.window, *self._windowed_size)

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
