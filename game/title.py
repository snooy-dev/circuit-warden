"""게임 진입 전 타이틀과 화면 설정."""

from pathlib import Path

import pico2d.pico2d as pico

from engine import Scene
from game_framework import (
    Button, ButtonInput, Canvas, ImageStore, Label, Renderer, SpriteFrame,
    UIElement, draw_rect, draw_sprite,
)
from game_framework.drawing import draw_horizontal_gradient


FONTS = Path(__file__).resolve().parents[1] / 'assets' / 'ui'
DISPLAY_FONT = FONTS / 'BarlowCondensed-Bold.ttf'
MENU_FONT = FONTS / 'BarlowCondensed-Medium.ttf'
TITLE_COLOR = (232, 232, 219)
ITEM_COLOR = (184, 192, 189)
FOCUS_COLOR = (144, 220, 208)


class MenuItem(Button):
    def __init__(self, text, action, *, width=260, **layout):
        super().__init__(text, action, font_path=MENU_FONT, width=width, height=52,
                         size=34, color=ITEM_COLOR, **layout)

    def draw(self, origin, transform, opacity):
        x, y = origin
        self.color = TITLE_COLOR if self.focused else ITEM_COLOR
        if self.focused:
            mid = y + self.bounds[3] / 2
            draw_rect(transform, (x - 25, mid, x - 10, mid + 2), FOCUS_COLOR, opacity)
        super().draw(origin, transform, opacity)


class TitleScene(Scene):
    def __init__(self, new_game, *, sizes, art_path):
        self.new_game = new_game
        self.sizes = sizes
        self.canvas = Canvas(sizes[0])
        self.input = ButtonInput(self.canvas)
        self.renderer = Renderer()
        self.images = ImageStore(art_path.parent)
        self.art_name = art_path.name
        self.engine = None
        self._starting = False

        self.menu = self.canvas.add(UIElement(anchor=(.5, .5), x=-512, y=-222))
        self.settings = self.canvas.add(UIElement(
            anchor=(.5, .5), x=-512, y=-222, visible=False))
        self.canvas.add(Label('CIRCUIT WARDEN', size=102, font_path=DISPLAY_FONT,
                              color=TITLE_COLOR), self.menu)
        self.start = self.canvas.add(MenuItem('New Game', self._start_game, y=204), self.menu)
        self.open_settings = self.canvas.add(MenuItem(
            'Settings', lambda: self._show_settings(True), y=266), self.menu)
        self.canvas.add(MenuItem('Quit', lambda: self.engine.stop(), y=328), self.menu)

        self.canvas.add(Label('Settings', size=66, font_path=DISPLAY_FONT,
                              color=TITLE_COLOR), self.settings)
        self.mode = self.canvas.add(MenuItem(
            'Display Mode', self._toggle_mode, width=440, y=138), self.settings)
        size = self.canvas.add(MenuItem(
            'Window Size', self._cycle_size, width=440, y=200), self.settings)
        self.mode_value = self.canvas.add(Label('', x=250, y=7, size=32,
                                                font_path=MENU_FONT), self.mode)
        self.size_value = self.canvas.add(Label('', x=250, y=7, size=32,
                                                font_path=MENU_FONT), size)
        self.canvas.add(MenuItem('Back', lambda: self._show_settings(False), y=298), self.settings)
        self.input.focus(self.start)

    @property
    def transform(self):
        viewport = self.engine.viewport if self.engine.output_valid else (0, 0, 0, 0)
        return self.canvas.transform(viewport)

    def enter(self, engine):
        self.engine = engine
        self._windowed_size = engine.window_size if not engine.fullscreen else self.sizes[0]
        pico.SDL_SetWindowTitle(pico.window, b'Circuit Warden')
        image = self.images.load(self.art_name)
        self.backdrop = SpriteFrame(image, (0, 0, image.width, image.height))

    def handle_event(self, event):
        if self._starting:
            return
        if event.type == pico.SDL_RENDER_DEVICE_RESET:
            raise RuntimeError('타이틀을 그리려면 렌더링 자원을 다시 만들어야 합니다.')
        self.input.handle_event(event, self.transform, self.engine.event_to_output(event))

    def handle_escape(self):
        if self._starting:
            return True
        if self.settings.visible:
            self._show_settings(False)
            return True
        return False

    def update(self, dt):
        if not self.engine.fullscreen and self.engine.output_valid:
            self._windowed_size = self.engine.window_size
        if self.settings.visible:
            mode = 'Fullscreen' if self.engine.fullscreen else 'Windowed'
            self.mode_value.text = mode
            width, height = self._windowed_size
            self.size_value.text = f'{width} × {height}'
        self.canvas.update(dt)

    def draw(self):
        transform = self.transform
        if not transform.valid:
            return
        width, height = transform.logical_size
        art_width, art_height = self.backdrop.rect[2:]
        scale = max(width / art_width, height / art_height)
        draw_sprite(self.backdrop, transform, (width / 2, height / 2),
                    (art_width * scale, art_height * scale))
        draw_horizontal_gradient(transform, transform.bounds, (4, 9, 13),
                                 left_opacity=.95, right_opacity=.18)
        self.renderer.draw_ui(self.canvas, transform)

    def exit(self):
        self.input.reset()
        try:
            self.canvas.close()
        finally:
            self.images.close()
            self.engine = None

    def _start_game(self):
        self._starting = True
        self.engine.change_scene(self.new_game())

    def _show_settings(self, visible):
        self.settings.visible = visible
        self.menu.visible = not visible
        self.input.reset()
        self.input.focus(self.mode if visible else self.open_settings)

    def _toggle_mode(self):
        self.engine.set_display(fullscreen=not self.engine.fullscreen)

    def _cycle_size(self):
        index = self.sizes.index(self._windowed_size) if self._windowed_size in self.sizes else -1
        size = self.sizes[(index + 1) % len(self.sizes)]
        self.engine.set_display(fullscreen=False, window_size=size)
