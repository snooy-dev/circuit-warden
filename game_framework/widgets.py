"""Canvas의 텍스트, 버튼 및 키보드·포인터 입력."""

from pathlib import Path

import pico2d.pico2d as pico

from .drawing import draw_image
from .ui import UIElement, _visible_ui


FONT_PATH = Path(pico.__file__).with_name('data') / 'ConsolaMalgun.ttf'


class Label(UIElement):
    def __init__(self, text, *, size=24, color=(235, 246, 244), font_path=FONT_PATH, **layout):
        super().__init__(**layout)
        self.text, self.size, self.color = text, size, color
        self.font_path = font_path
        self._rendered_style = None
        self._image = None

    def draw(self, origin, transform, opacity):
        self._draw_text(origin, transform, opacity)

    def _draw_text(self, origin, transform, opacity, *, center_y=False):
        if not self.text:
            self._image = self._rendered_style = None
            return
        style = self.text, self.size, tuple(self.color), self.font_path
        if style != self._rendered_style:
            # 두 배로 래스터화해 고해상도 출력에서도 텍스트 확대를 줄인다.
            font = pico.TTF_OpenFont(str(self.font_path).encode('utf-8'), self.size * 2)
            if not font:
                raise RuntimeError(f'UI 폰트를 열 수 없습니다: {self.font_path}')
            try:
                surface = pico.TTF_RenderUTF8_Blended(
                    font, self.text.encode('utf-8'), pico.SDL_Color(*self.color, 255))
                if not surface:
                    raise RuntimeError(f'UI 텍스트 생성 실패: {pico.SDL_GetError()!r}')
                try:
                    texture = pico.SDL_CreateTextureFromSurface(pico.renderer, surface)
                    if not texture:
                        raise RuntimeError(f'UI 텍스처 생성 실패: {pico.SDL_GetError()!r}')
                    self._image = pico.Image(texture)
                    self._rendered_style = style
                finally:
                    pico.SDL_FreeSurface(surface)
            finally:
                pico.TTF_CloseFont(font)
        x, y = origin
        width, height = self._image.w / 2, self._image.h / 2
        if center_y:
            y -= height / 2
        draw_image(self._image, transform, (x, y, x + width, y + height), opacity)

    def on_destroy(self):
        self._image = self._rendered_style = None


class Button(Label):
    def __init__(self, text, activate, *, width=340, height=58, size=22, **layout):
        super().__init__(text, size=size, bounds=(0, 0, width, height), **layout)
        self.activate = activate
        self.focused = False

    def draw(self, origin, transform, opacity):
        x, y = origin
        self._draw_text((x, y + self.bounds[3] / 2), transform, opacity, center_y=True)


class ButtonInput:
    def __init__(self, canvas):
        self.canvas = canvas
        self._focused = self._pressed = None

    def focus(self, button):
        if button is self._focused:
            return
        if self._focused is not None:
            self._focused.focused = False
        self._focused = button
        if button is not None:
            button.focused = True

    def reset(self):
        self.focus(None)
        self._pressed = None

    def handle_event(self, event, transform, output_point=None):
        """출력 픽셀을 받아 활성 Canvas의 버튼에 입력을 전달한다."""
        if event.type == pico.SDL_WINDOWEVENT:
            if event.event in (pico.SDL_WINDOWEVENT_LEAVE, pico.SDL_WINDOWEVENT_FOCUS_LOST):
                self._pressed = None
            return
        if event.type not in (pico.SDL_KEYDOWN, pico.SDL_MOUSEMOTION,
                              pico.SDL_MOUSEBUTTONDOWN, pico.SDL_MOUSEBUTTONUP):
            return
        if not transform.valid:
            self._pressed = None
            return
        _, _, width, height = transform.bounds
        targets = [(element, bounds) for element, _, bounds in _visible_ui(self.canvas, transform)
                   if isinstance(element, Button) and bounds is not None
                   and bounds[0] < width and bounds[1] < height and bounds[2] > 0 and bounds[3] > 0]
        if event.type == pico.SDL_KEYDOWN:
            self._handle_key(event.key, [button for button, _ in targets])
            return
        if event.type != pico.SDL_MOUSEMOTION and event.button != pico.SDL_BUTTON_LEFT:
            return
        target = None
        if output_point is not None:
            x, y = transform.inverse(*output_point)
            if 0 <= x < width and 0 <= y < height:
                target = next((button for button, (l, t, r, b) in reversed(targets)
                               if l <= x < r and t <= y < b), None)
        if target is not None:
            self.focus(target)
        if event.type == pico.SDL_MOUSEBUTTONDOWN:
            self._pressed = target
        elif event.type == pico.SDL_MOUSEBUTTONUP:
            pressed, self._pressed = self._pressed, None
            if target is not None and target is pressed:
                target.activate()

    def _handle_key(self, key, buttons):
        if not buttons:
            return
        previous = key in (pico.SDLK_UP, pico.SDLK_LEFT)
        if previous or key in (pico.SDLK_DOWN, pico.SDLK_RIGHT, pico.SDLK_TAB):
            if self._focused not in buttons:
                self.focus(buttons[-1] if previous else buttons[0])
                return
            step = -1 if previous else 1
            self.focus(buttons[(buttons.index(self._focused) + step) % len(buttons)])
        elif key in (pico.SDLK_RETURN, pico.SDLK_KP_ENTER, pico.SDLK_SPACE):
            if self._focused not in buttons:
                self.focus(buttons[0])
            self._pressed = None
            self._focused.activate()
