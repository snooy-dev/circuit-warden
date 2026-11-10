"""창·출력 상태 조회와 화면 모드 요청."""

from ctypes import byref, c_int

import pico2d.pico2d as pico

WIDTH, HEIGHT = 800, 600

class Display:
    """Engine이 초기화한 표시 상태를 사용하는 내부 기반 클래스."""

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
